"""Profile-scoped automatic suggestions; one bounded-by-task queue per source.

Only completed historical evidence may produce a named recommendation. Results
stay in RAM and never initiate source assignment or external messaging.
"""
import hashlib
import json
import threading
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime

from history import now
from recommendations import rank, VERSION, task_supervisors
from sla import TZ


TASK_FIELDS = ("source", "id", "title", "description", "project_id", "category", "creator_id",
               "auditor_ids", "assignee_id", "status", "priority", "tags", "deadline", "created_at")
LOAD_FIELDS = ("source", "id", "assignee_id", "title", "description", "priority", "tags", "status",
               "awaiting_executor", "created_at")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def compact_suggestion(result):
    if not result.get("candidates"):
        return {"status": "no_evidence", "generated_at": now(), "version": result.get("version")}
    first = result["candidates"][0]
    return {"status": "ready", "generated_at": now(), "version": result.get("version"),
            "employee": {"id": first["id"], "name": first["name"]},
            "reason": {"similar_completed": first["similar_completed"],
                       "evidence_patterns": first.get("evidence_patterns", 0),
                       "active_tasks": first["active_tasks"], "priority_load": first.get("priority_load", 0),
                       "retrieval_similarity": first.get("retrieval_similarity"),
                       "evidence_level": first.get("evidence_level", "limited"),
                       "evidence": [{k: e.get(k) for k in ("source", "id", "title", "similarity")}
                                    for e in first.get("examples", [])[:1]]}}


class SuggestionWorker:
    def __init__(self, service):
        self.service = service
        self.jobs = OrderedDict()
        self.thread = None

    def readiness(self, state, include_links=True):
        service = self.service
        reasons = []
        if state.get("error") or state.get("directory_error"):
            reasons.append("source_unavailable")
        if not state.get("checked_at") or service.clock() - state.get("checked_epoch", 0) > 120:
            reasons.append("workload_old")
        if not state.get("history_complete"):
            reasons.append("history_incomplete")
        if include_links and any(not item.get("complete") or not item.get("open_fresh")
               for item in state.get("evidence_sources", [])):
            reasons.append("linked_evidence_unavailable")
        return reasons

    def sync(self, context, state, journal, shared):
        """Replace changed pending work; identical polls retain the cached result."""
        service = self.service
        if not service.automatic_suggestions:
            return
        with service.lock:
            cache = state.setdefault("suggestions", {})
            tasks = [t for t in state["active"]
                     if journal["tasks"].get(t["id"], {}).get("state") == "needs_assignment"
                     and context["user"] in task_supervisors(t)]
            wanted = {t["id"] for t in tasks}
            for tid in list(cache):
                if tid not in wanted:
                    cache.pop(tid)
                    self.jobs.pop((context["key"], tid), None)
            if not tasks:
                return
            reasons = self.readiness(state, include_links=False)
            if not reasons:
                prepared, workload, opened = service.ranking_inputs(context, state)
                reasons = self.readiness(state)
            if reasons:
                for task in tasks:
                    cache[task["id"]] = {"status": "unavailable", "status_reasons": reasons}
                    self.jobs.pop((context["key"], task["id"]), None)
                return
            directory = service.directory(context, state)
            load = [{k: row.get(k) for k in LOAD_FIELDS} for rows in workload.values() for row in rows]
            load.sort(key=lambda r: (str(r["source"]), str(r["id"])))
            # Check timestamps express freshness; they do not change ranking inputs.
            dependency = digest([VERSION, state["history_version"], state.get("federated_revision"),
                                 context["policy"], context["user"], state.get("generation", 0), sorted(directory, key=lambda p: p["id"]), load,
                                 datetime.now(TZ).date().isoformat()])
            for task in tasks:
                tid, key = task["id"], (context["key"], task["id"])
                operation = shared["tasks"].get(tid, {}).get("operation", {})
                if operation.get("status") in {"pending", "uncertain"}:
                    cache[tid] = {"status": "unavailable", "status_reasons": ["assignment_unresolved"]}
                    self.jobs.pop(key, None)
                    continue
                revision = digest([dependency, {k: task.get(k) for k in TASK_FIELDS}])
                previous = cache.get(tid, {})
                if previous.get("revision") == revision and (
                        previous.get("status") in {"pending", "ready", "no_evidence"} or
                        (previous.get("status") == "failed" and service.clock() < previous.get("retry_at", 0))):
                    continue
                cache[tid] = {"status": "pending", "revision": revision}
                self.jobs[key] = {"context": deepcopy(context), "state": state, "revision": revision,
                                  "generation": state.get("generation", 0),
                                  "task": deepcopy(task), "directory": deepcopy(directory),
                                  "prepared": prepared, "workload": deepcopy(workload), "opened": opened}
            if self.jobs and (not self.thread or not self.thread.is_alive()):
                self.thread = threading.Thread(target=self.run, name="suggestions-" + service.source_name, daemon=True)
                self.thread.start()

    def run(self):
        service = self.service
        while True:
            with service.lock:
                if not self.jobs:
                    self.thread = None
                    return
                _, job = self.jobs.popitem(last=False)
                context, state, task = job["context"], job["state"], job["task"]
                if state.get("suggestions", {}).get(task["id"], {}).get("revision") != job["revision"]:
                    continue
            try:
                result = rank(task, [], job["directory"], context["policy"],
                              prepared=job["prepared"], workload=job["workload"], open_index=job["opened"])
                suggestion = compact_suggestion(result)
            except Exception:
                suggestion = {"status": "failed", "retry_at": service.clock() + 300}
            try:
                self.publish(job, suggestion)
            except Exception:
                # A journal failure must not kill the worker or leave the task pending forever.
                with service.lock:
                    cached = state.get("suggestions", {}).get(task["id"], {})
                    if cached.get("revision") == job["revision"]:
                        state["suggestions"][task["id"]] = {
                            "status": "failed", "retry_at": service.clock() + 300,
                            "revision": job["revision"]}

    def publish(self, job, suggestion):
        service = self.service
        context, state, task = job["context"], job["state"], job["task"]
        with service.lock:
            pid = context["key"].split(":", 1)[0]
            latest = service.context(pid)
            cached = state.get("suggestions", {}).get(task["id"], {})
            if (not latest or latest["key"] != context["key"] or latest["policy"] != context["policy"]
                    or latest["user"] != context["user"]
                    or state.get("generation", 0) != job["generation"]
                    or cached.get("revision") != job["revision"]):
                return
            # Source access/roles/decisions may have changed during inference.
            shared = service.journal.read(context["shared_key"])
            journal = service.journal.read(context["key"])
            current = next((r for r in state["active"] if r["id"] == task["id"]), None)
            operation = shared["tasks"].get(task["id"], {}).get("operation", {})
            decision = shared["tasks"].get(task["id"], {}).get("decision")
            from recommendations import assignment_state
            if (not current or context["user"] not in task_supervisors(current)
                    or assignment_state(current, context["policy"], {"decision": decision}) != "needs_assignment"
                    or operation.get("status") in {"pending", "uncertain"}
                    or any(current.get(k) != task.get(k) for k in TASK_FIELDS)):
                state["suggestions"].pop(task["id"], None)
                return
            reasons = self.readiness(state)
            if reasons:
                suggestion = {"status": "unavailable", "status_reasons": reasons}
            suggestion["revision"] = job["revision"]
            if suggestion["status"] == "ready":
                row = journal["tasks"].get(task["id"])
                if row is not None:
                    ident = suggestion["employee"]["id"]
                    if row.get("suggested_employee_id") != ident:
                        row.update(suggested_employee_id=ident, read_by=[],
                                   alert_id=digest([task["id"], now(), ident]))
                        service.journal.write(context["key"], journal)
            state["suggestions"][task["id"]] = suggestion


    def visible(self, context, state, task):
        suggestion = state.get("suggestions", {}).get(task["id"], {"status": "pending"})
        reasons = self.readiness(state)
        if reasons:
            return {"status": "unavailable", "status_reasons": reasons}
        if task.get("operation", {}).get("status") in {"pending", "uncertain"}:
            return {"status": "unavailable", "status_reasons": ["assignment_unresolved"]}
        return {k: deepcopy(v) for k, v in suggestion.items() if k not in {"revision", "retry_at"}}
