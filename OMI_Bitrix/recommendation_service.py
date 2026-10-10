"""Bitrix recommendation inbox and minimal durable decision journal; no task database."""
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from bitrix import BitrixClient
from history import bitrix_pages, now, connection_scope
from recommendations import rank, assignment_state, DEFAULT_WEIGHTS, VERSION, task_supervisors, pending_review
from sla import parse, TZ
from recommendation_matching import RelevanceIndex
from notification_suggestions import SuggestionWorker


def decision_evidence(result):
    """Save decision evidence IDs/scores, without copying source narratives."""
    if not result:
        return None
    return {"compact": True, "version": result.get("version"), "stale": result.get("stale"),
            "candidates": [{"id": c["id"], "score": c.get("score"),
                            "similar_completed": c.get("similar_completed"),
                            "evidence": [{"id": e.get("id"), "source": e.get("source")}
                                         for e in c.get("examples", [])]}
                           for c in result.get("candidates", [])]}


class DecisionJournal:
    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.RLock()

    def path(self, key):
        return self.root / (hashlib.sha256(key.encode()).hexdigest() + ".json")

    def read(self, key):
        with self.lock:
            path = self.path(key)
            if not path.exists():
                return {"tasks": {}, "audit": []}
            return json.loads(path.read_text(encoding="utf-8"))

    def write(self, key, value):
        with self.lock:
            self.root.mkdir(parents=True, exist_ok=True)
            path = self.path(key)
            if len(value.get("audit", [])) > 1000:
                older = value["audit"][:-1000]
                with path.with_suffix(".audit.jsonl").open("a", encoding="utf-8") as archive:
                    for event in older:
                        archive.write(json.dumps(event, ensure_ascii=False) + "\n")
                    archive.flush()
                    os.fsync(archive.fileno())
                value["audit"] = value["audit"][-1000:]
            temp = path.with_suffix(".tmp")
            with temp.open("w", encoding="utf-8") as output:
                json.dump(value, output, ensure_ascii=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temp, path)

    def audit(self, state, event):
        state["audit"].append({"at": now(), **event})


class RecommendationService:
    source_name = "bitrix"
    def __init__(self, store, history, root, clock=time.time, automatic_suggestions=True):
        self.store, self.history, self.clock = store, history, clock
        self.journal = DecisionJournal(root)
        self.lock = threading.RLock()
        self.states = {}
        self.thread = None
        self.unified_directory = None
        self.automatic_suggestions = automatic_suggestions
        self.suggestions = SuggestionWorker(self)

    def context(self, pid):
        url = self.store.get("webhook_url", "", profile_id=pid)
        projects = self.store.projects(pid)
        if not url or not projects or not self.store.get("signed_profile_active", False, profile_id=pid):
            return None
        scope = hashlib.sha256(json.dumps([url, sorted(p["id"] for p in projects)]).encode()).hexdigest()
        portal = urlsplit(url)
        source_key = portal.scheme.lower() + "://" + portal.netloc.lower() + portal.path.split("/rest/")[0].rstrip("/")
        return {"key": pid + ":" + scope, "shared_key": "bitrix:" + source_key, "url": url, "projects": projects,
                "policy": {**self.store.get("recommendation_policy", {}, profile_id=pid),
                           "tag_priorities": self.store.get("intelligence_settings", {}, profile_id=pid).get("tag_priorities", {})},
                "user": str((self.store.get("bitrix_user", {}, profile_id=pid) or {}).get("ID", ""))}

    def _state(self, context):
        return self.states.setdefault(context["key"], {"next": 0, "checked_at": None,
            "error": None, "running": False, "active": [], "directory": [],
            "members": [], "active_ids": set(), "prepared": None, "history_version": None})

    def source_directory(self, context, state):
        discovered = {}
        for record in state["active"] + (state["prepared"].records if state["prepared"] else []):
            ident = record.get("assignee_id")
            if ident and ident != "0":
                entry = discovered.setdefault(ident, {"id": ident, "name": record.get("assignee_name") or ident,
                    "enabled": False, "active": True, "projects": [], "categories": [],
                    "away_from": "", "away_to": "", "basis": "history_unconfirmed"})
                if record.get("project_id") and record["project_id"] not in entry["projects"]:
                    entry["projects"].append(record["project_id"])
        for member in state["members"]:
            ident = member["id"]
            discovered[ident] = {"id": ident, "name": member["name"], "enabled": ident in state["active_ids"],
                "active": ident in state["active_ids"], "projects": member["projects"], "categories": [],
                "away_from": "", "away_to": "", "basis": "project_membership"}
        for entry in context["policy"].get("employees", []):
            discovered[entry["id"]] = {**entry, "basis": "configured"}
        for ident, status in state.get("user_status", {}).items():
            if ident in discovered and not status:
                discovered[ident]["active"] = False
        for ident, entry in discovered.items():
            details = state.get("user_metadata", {}).get(ident, {})
            for key in ("email", "department", "position"):
                if details.get(key):
                    entry[key] = details[key]
            entry.pop("capacity", None)
        return sorted(discovered.values(), key=lambda e: e["name"])

    def directory(self, context, state):
        if self.unified_directory:
            pid = context["key"].split(":", 1)[0]
            return self.unified_directory.source_people(pid, self.source_name)
        return self.source_directory(context, state)

    def ranking_inputs(self, context, state):
        index, active, statuses = state["prepared"], state["active"], []
        if self.unified_directory:
            index, active, statuses = self.unified_directory.inputs(
                context["key"].split(":", 1)[0], self.source_name, index, active, state)
        workload = defaultdict(list)
        opened = []
        for row in active:
            if not row.get("awaiting_executor") and not pending_review(row):
                workload[row.get("assignee_id", "")].append(row)
                opened.append(row)
        state["evidence_sources"] = statuses
        signature = hashlib.sha256(json.dumps([opened, index.domain_rules, state.get("history_version"), state.get("federated_revision")], sort_keys=True).encode()).hexdigest()
        if state.get("open_revision") != signature:
            state["ranking_open_index"] = RelevanceIndex(opened, domain_rules=index.domain_rules, domain_model=index.domain_model)
            state["open_revision"] = signature
        return index, workload, state["ranking_open_index"]

    def _prepare(self, context, state):
        pid = context["key"].split(":", 1)[0]
        cache = "diwan_analysis" if self.source_name == "diwan" else "bitrix"
        self.history.bind_scope(pid, cache, connection_scope(self.store, pid, self.source_name))
        source = self.history.source(pid, cache, copy_records=False)
        rules = self.store.get("task_domain_rules", [], profile_id=pid)
        version = (source.get("revision") or source["updated_at"], json.dumps(rules, sort_keys=True))
        if version != state["history_version"] or state["prepared"] is None:
            historical_index = self.history.index(pid, cache)
            if source["records"] and historical_index is None:
                if state["prepared"] is None or state.get("warming_version") != version:
                    state["prepared"] = RelevanceIndex([])
                    state["warming_version"] = version
                state["history_complete"] = False
                state["completed_lookup"] = {}
                return
            instant = datetime.now(TZ)
            rows = [r for r in source["records"] if r.get("completed") and parse(r.get("completed_at"))
                    and parse(r["completed_at"]) < instant and parse(r.get("created_at"))
                    and parse(r["created_at"]) < parse(r["completed_at"])]
            discovered = historical_index.domain_model if historical_index and hasattr(historical_index.domain_model,"topics") else None
            state["prepared"] = RelevanceIndex(rows, domain_rules=rules, domain_model=discovered)
            state["history_version"] = version
            state["completed_lookup"] = {r["id"]: r for r in state["prepared"].records}
        state["history_complete"] = source["complete"] and not source["error"]

    def task_policy(self, context, state, task):
        return context["policy"]

    def process(self, context, state, verified_at=None):
        journal = self.journal.read(context["key"])
        shared = self.journal.read(context["shared_key"])
        for task in state["active"]:
            entry = journal["tasks"].setdefault(task["id"], {})
            common = shared["tasks"].get(task["id"], {})
            if task["id"] not in shared["tasks"] and entry.get("decision"):
                common = shared["tasks"][task["id"]] = {"decision": entry["decision"]}
            decision = common.get("decision") or {}
            changed = (decision.get("expected_creator") != task.get("creator_id") or
                       decision.get("expected_assignee") != task.get("assignee_id"))
            # Only a source read started after this decision may invalidate it.
            # Cached snapshots cannot erase a newer decision from another profile.
            if decision and changed and verified_at and parse(decision.get("at")) and parse(decision["at"]) <= parse(verified_at):
                common["decision"] = None
                common["invalidated_at"] = now()
                decision = {}
            if decision:
                entry["decision"] = decision
            else:
                entry.pop("decision", None)
        self.journal.write(context["shared_key"], shared)
        if len(journal["tasks"]) + len({r["id"] for r in state["active"]} - journal["tasks"].keys()) > 100000:
            raise ValueError("journal_capacity")
        directory = self.directory(context, state)
        state["directory"] = directory
        active_ids = set()
        for task in state["active"]:
            previous = journal["tasks"].get(task["id"], {})
            decision = previous.get("decision") or {}
            if decision and (decision.get("expected_creator") != task.get("creator_id") or decision.get("expected_assignee") != task.get("assignee_id")):
                previous.pop("decision", None)
            task["awaiting_executor"] = assignment_state(task, self.task_policy(context, state, task),
                                                         journal["tasks"].get(task["id"])) == "needs_assignment"
        workload = defaultdict(list)
        for task in state["active"]:
            if not task["awaiting_executor"] and not pending_review(task):
                workload[task.get("assignee_id", "")].append(task)
        state["workload"] = workload
        for task in state["active"]:
            tid = task["id"]
            active_ids.add(tid)
            previous = journal["tasks"].get(tid, {})
            fingerprint = hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()
            status = assignment_state(task, self.task_policy(context, state, task), previous)
            recipients = sorted(task_supervisors(task))
            # Keep legacy journal fields intact; new entries contain decision metadata only.
            row = {**previous, "id": tid, "project_id": task.get("project_id"),
                   "assignee_id": task.get("assignee_id"), "creator_id": task.get("creator_id"),
                   "auditor_ids": task.get("auditor_ids", []), "state": status,
                   "fingerprint": fingerprint, "recipient_ids": recipients,
                   "first_seen": previous.get("first_seen", now()), "last_seen": now()}
            if status == "needs_assignment" and previous.get("state") != status:
                row.update(alert_id=hashlib.sha256((tid + now()).encode()).hexdigest(), read_by=[])
                self.journal.audit(journal, {"event": "needs_assignment", "task_id": tid,
                    "recipient_ids": recipients})
            if previous and previous.get("assignee_id") != row["assignee_id"]:
                self.journal.audit(journal, {"event": "assignee_changed", "task_id": tid,
                    "before": previous.get("assignee_id"), "after": row["assignee_id"]})
            journal["tasks"][tid] = row
        for tid, row in journal["tasks"].items():
            if tid not in active_ids and row.get("state") == "needs_assignment":
                row["state"] = "no_longer_open"
            closed = state.get("completed_lookup", {}).get(tid)
            if tid not in active_ids and closed and row.get("state") != "closed":
                row["state"] = "closed"
                outcome = {k: closed.get(k) for k in ("completed_at", "assignee_id", "deadline", "rating", "attributes")}
                row["outcome"] = outcome
                self.journal.audit(journal, {"event": "observed_completion", "task_id": tid, "outcome": outcome})
        self.journal.write(context["key"], journal)
        self.suggestions.sync(context, state, journal, shared)

    def refresh(self, pid, force=False):
        with self.lock:
            context = self.context(pid)
            if not context:
                return
            state = self._state(context)
            if state["running"] or (not force and self.clock() < state["next"]):
                return
            generation = state.get("generation", 0)
            state["running"] = True
            state["next"] = self.clock() + 60
        try:
            verified_at = datetime.now(timezone.utc).isoformat()
            api = BitrixClient(context["url"])
            # Read all accessible open tasks; failed/partial pages never publish.
            active = [r for _, page in bitrix_pages(api, context["projects"], lambda: False,
                      context["policy"].get("category_field", ""), active_only=True, data_fields=context["policy"].get("data_fields", {})) for r in page]
            if len(active) > 100000:
                raise ValueError("active_capacity")
            members, active_ids = None, None
            directory_error = state.get("directory_error")
            if force or not state.get("directory_checked") or directory_error or self.clock() >= state["directory_checked"] + 7200:
                try:
                    members = api.project_members([p["id"] for p in context["projects"]])
                    active_ids = set()
                    user_status, user_metadata = {}, {}
                    start = 0
                    while True:
                        payload = api._call_raw("user.get", {"start": start,
                                               "select": ["ID", "ACTIVE", "NAME", "LAST_NAME", "EMAIL", "UF_DEPARTMENT", "WORK_POSITION"]})
                        user_status.update({str(u["ID"]): u.get("ACTIVE") in (True, "Y", 1) for u in payload.get("result", [])})
                        for user in payload.get("result", []):
                            user_metadata[str(user["ID"])] = {"email": str(user.get("EMAIL") or ""),
                                "department": ", ".join(str(v) for v in user.get("UF_DEPARTMENT", [])) if isinstance(user.get("UF_DEPARTMENT"), list) else str(user.get("UF_DEPARTMENT") or ""),
                                "position": str(user.get("WORK_POSITION") or "")}
                        active_ids = {ident for ident, active in user_status.items() if active}
                        if payload.get("next") is None:
                            break
                        start = int(payload["next"])
                except Exception:
                    members = None
                    directory_error = "directory_unavailable"
                else:
                    directory_error = None
            with self.lock:
                # A source switch while a request was running must discard that response.
                latest = self.context(pid)
                if not latest or latest["key"] != context["key"]:
                    return
                if generation != state.get("generation", 0) or context["policy"] != latest["policy"]:
                    state["next"] = 0
                    return
                context = latest
                state["active"] = active
                state["directory_error"] = directory_error
                if members is not None:
                    state.update(members=members, active_ids=active_ids, user_status=user_status, user_metadata=user_metadata, directory_checked=self.clock())
                self._prepare(context, state)
                state.update(checked_at=now(), checked_epoch=self.clock(), error=None)
                self.process(context, state, verified_at=verified_at)
        except Exception:
            with self.lock:
                state.update(error="source_or_journal_unavailable", next=self.clock() + 300)
        finally:
            with self.lock:
                state["running"] = False

    def snapshot(self, pid):
        with self.lock:
            context = self.context(pid)
            if not context:
                return {"configured": False, "tasks": [], "employees": [], "notifications": []}
            state = self._state(context)
            if self.automatic_suggestions:
                self._prepare(context, state)
            shared = self.journal.read(context["shared_key"])
            signature = json.dumps(shared["tasks"], sort_keys=True)
            if state.get("shared_signature") != signature and state.get("prepared") is not None:
                self.process(context, state)
                state["shared_signature"] = signature
            journal = self.journal.read(context["key"])
            self.suggestions.sync(context, state, journal, shared)
            # Render source content from the current profile-scoped RAM snapshot.
            rows = [{**journal["tasks"].get(r["id"], {}), **r,
                     "operation": {k:v for k,v in shared["tasks"].get(r["id"], {}).get("operation", {}).items()
                                   if k in {"target", "status", "at", "follow_up", "warnings"}}}
                    for r in state["active"]]
            active_ids = {a["id"] for a in state["active"]}
            for row in rows:
                if row.get("state") == "needs_assignment":
                    row["suggestion"] = self.suggestions.visible(context, state, row)
            visible = [r for r in rows if context["user"] in r.get("recipient_ids", []) and r["state"] == "needs_assignment"]
            return {"configured": True, "user_id": context["user"], "projects": context["projects"],
                "policy": {"weights": DEFAULT_WEIGHTS, "top_n": 3, "intake_ids": [], "supervisor_ids": [], **context["policy"]},
                "tasks": [{k: r.get(k) for k in ("id", "title", "state", "assignee_id", "recipient_ids", "project_id", "creator_id", "description", "deadline", "priority", "category", "operation", "suggestion")} for r in rows if r["id"] in active_ids and context["user"] in task_supervisors(r)],
                "employees": self.directory(context, state), "notifications": visible,
                "unread": sum(context["user"] not in r.get("read_by", []) for r in visible),
                "checked_at": state["checked_at"], "error": state["error"] or state.get("directory_error"),
                "directory_checked_at": state.get("directory_checked"), "running": state["running"],
                "history_ready": state.get("history_complete", False), "poll_seconds": 60,
                "detected_supervisors": [{"id": m["id"], "name": m["name"], "projects": [p for p, role in m.get("roles", {}).items() if role in {"A", "E"}]} for m in state["members"] if any(role in {"A", "E"} for role in m.get("roles", {}).values())],
                "completed_evidence": len(state["prepared"].records) if state["prepared"] else 0}

    def recommend(self, pid, task_id=None, text="", project_id="", category="", exclude_id=None, live_record=None):
        with self.lock:
            context = self.context(pid)
            if not context:
                raise ValueError("Connect Diwan and configure its task roles first" if self.source_name == "diwan" else "Connect Bitrix first")
            state = self._state(context)
            self._prepare(context, state)
            task = next((r for r in state["active"] if r["id"] == str(task_id)), None) if task_id else {
                "id": str(exclude_id or "preview"), "source": self.source_name, "title": text, "description": "", "project_id": project_id, "category": category}
            if live_record is not None:
                task = live_record
            if task_id and task is not None and context["user"] not in task_supervisors(task):
                raise PermissionError("Only this task owner or observer can request assignment recommendations")
            if task is None:
                raise ValueError("Refresh open tasks before recommending")
            if state["checked_at"] is None:
                raise ValueError("Open-task refresh has not completed")
            prepared, workload, open_index = self.ranking_inputs(context, state)
            directory = self.directory(context, state)
            generation = state.get("generation", 0)
            history_version = state.get("history_version")
            checked_epoch = state.get("checked_epoch")
        # CPU inference must not hold the service-wide refresh/snapshot lock.
        result = rank(task, [], directory, context["policy"],
                      prepared=prepared, workload=workload, open_index=open_index)
        with self.lock:
            latest = self.context(pid)
            changed = (not latest or latest["key"] != context["key"] or latest["policy"] != context["policy"]
                       or generation != state.get("generation", 0)
                       or history_version != state.get("history_version")
                       or checked_epoch != state.get("checked_epoch"))
            reasons = ["snapshot_changed"] if changed else []
            if state.get("directory_error"):
                reasons.append("directory_unavailable")
            if state["error"]:
                reasons.append("source_unavailable")
            elif self.clock() - state.get("checked_epoch", 0) > 120:
                reasons.append("workload_old")
            if not state.get("history_complete", False):
                reasons.append("history_incomplete")
            if any(not item["open_fresh"] for item in state.get("evidence_sources", [])):
                reasons.append("linked_workload_old")
            result.update(status_reasons=reasons, task_id=task["id"], stale=changed or bool(state["error"] or state.get("directory_error")) or self.clock() - state.get("checked_epoch", 0) > 120 or any(not s["open_fresh"] for s in state.get("evidence_sources", [])), history_ready=state.get("history_complete", False), evidence_sources=state.get("evidence_sources", []))
            return result

    def decision(self, pid, task, kind, actor, result=None, reason=""):
        with self.lock:
            context = self.context(pid)
            state = self._state(context)
            # Callers supply a permission-checked, freshly read source task.
            if task["id"] not in {r["id"] for r in state["active"]}:
                state["active"].append(task)
            if state["prepared"] is None:
                self._prepare(context, state)
            state["generation"] = state.get("generation", 0) + 1
            journal = self.journal.read(context["key"])
            row = journal["tasks"].setdefault(task["id"], {"id": task["id"]})
            row["decision"] = {"kind": kind, "actor": actor, "expected_assignee": task["assignee_id"], "expected_creator": task.get("creator_id"), "at": datetime.now(timezone.utc).isoformat()}
            shared = self.journal.read(context["shared_key"])
            shared["tasks"].setdefault(task["id"], {})["decision"] = row["decision"]
            self.journal.write(context["shared_key"], shared)
            self.journal.audit(journal, {"event": kind, "task_id": task["id"], "actor": actor,
                "selected_employee": task["assignee_id"], "reason": reason[:500], "recommendation": decision_evidence(result)})
            self.journal.write(context["key"], journal)
            state = self._state(context)
            state["active"] = [task if r["id"] == task["id"] else r for r in state["active"]]
            self.process(context, state)

    def operation(self, pid, task_id, target=None, status=None, **metadata):
        with self.lock:
            context = self.context(pid)
            journal = self.journal.read(context["shared_key"])
            row = journal["tasks"].setdefault(task_id, {})
            previous = row.get("operation") or {}
            if status:
                if status == "pending" and previous.get("status") in {"pending", "uncertain"}:
                    raise ValueError("Assignment outcome requires reconciliation")
                row["operation"] = {**previous, "target": target or previous.get("target"), "status": status, "at": now(), **metadata}
                self.journal.write(context["shared_key"], journal)
            return previous

    def mark_read(self, pid, task_id):
        with self.lock:
            context = self.context(pid)
            if not context:
                raise ValueError("Not connected")
            journal = self.journal.read(context["key"])
            row = journal["tasks"].get(task_id)
            if not row or context["user"] not in row.get("recipient_ids", []):
                raise ValueError("Notification unavailable")
            row["read_by"] = sorted(set(row.get("read_by", []) + [context["user"]]))
            self.journal.write(context["key"], journal)

    def start(self, stop_event):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            def run():
                while not stop_event.is_set():
                    for pid in self.store.profile_ids():
                        try:
                            self.refresh(pid)
                        except Exception:
                            pass
                    stop_event.wait(15)
            self.thread = threading.Thread(target=run, name="recommendation-watch", daemon=True)
            self.thread.start()
