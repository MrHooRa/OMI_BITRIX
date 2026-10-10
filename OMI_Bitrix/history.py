"""Bounded, cancellable, profile-scoped in-memory ingestion."""
import copy
import hashlib
import json
import threading
import time
import uuid
from datetime import datetime, timezone

from diwany import DiwanError
from bitrix import BitrixClient
from task_intelligence import TaskIndex


def connection_scope(store, pid, source):
    """Shared cache identity for readers and the history scheduler; no secrets returned."""
    if source == "bitrix":
        policy = store.get("recommendation_policy", {}, profile_id=pid)
        value = [store.get("webhook_url", "", profile_id=pid), sorted(p["id"] for p in store.projects(pid)),
                 policy.get("category_field", ""), policy.get("data_fields", {})]
    else:
        value = [store.get("diwan_config", {}, profile_id=pid), store.get("diwan_token_protected", "", profile_id=pid)]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class History:
    def __init__(self):
        self.lock = threading.RLock()
        self.profiles = {}
        self.slots = threading.BoundedSemaphore(4)

    def _state(self, profile):
        # Expire inactive caches; running jobs remain until completion/cancellation.
        cutoff = time.monotonic() - 12 * 3600
        for key in list(self.profiles):
            item = self.profiles[key]
            if item["touched"] < cutoff and not any(j["status"] == "running" for j in item["jobs"].values()):
                del self.profiles[key]
        state = self.profiles.setdefault(profile, {"generations": {}, "sources": {}, "indexes": {}, "jobs": {}, "touched": 0})
        state["touched"] = time.monotonic()
        return state

    def bind_scope(self, profile, source, fingerprint):
        with self.lock:
            scopes = self._state(profile).setdefault("scopes", {})
            if source in scopes and scopes[source] != fingerprint:
                self.invalidate(profile, source)
            scopes[source] = fingerprint

    def invalidate(self, profile, source="diwan"):
        with self.lock:
            state = self._state(profile)
            state["generations"][source] = state["generations"].get(source, 0) + 1
            state["sources"].pop(source, None)
            state["indexes"].pop(source, None)
            for job in state["jobs"].values():
                if job["source"] == source and job["status"] == "running":
                    job["cancel"].set()

    def source(self, profile, source):
        with self.lock:
            state = {"records": [], "complete": False, "updated_at": None, "error": None}
            state.update(self._state(profile)["sources"].get(source, {}))
            return copy.deepcopy(state)

    def index(self, profile, source):
        with self.lock:
            return self._state(profile)["indexes"].get(source)

    def update_record(self, profile, source, record, generation):
        with self.lock:
            state = self._state(profile)
            if state["generations"].get(source, 0) != generation:
                raise DiwanError("connection_changed", 409)
            for i, old in enumerate(state["sources"].get(source, {}).get("records", [])):
                if old["id"] == record["id"]:
                    state["sources"][source]["records"][i] = record
                    return

    def generation(self, profile, source="diwan"):
        with self.lock:
            return self._state(profile)["generations"].get(source, 0)

    def start(self, profile, source, producer):
        with self.lock:
            state = self._state(profile)
            if any(j["source"] == source and j["status"] == "running" for j in state["jobs"].values()):
                raise DiwanError("sync_running", 409)
            if not self.slots.acquire(blocking=False):
                raise DiwanError("server_busy", 409)
            job_id = uuid.uuid4().hex
            job = {"id": job_id, "source": source, "status": "running", "pages": 0,
                   "count": 0, "error": None, "started_at": now(),
                   "cancel": threading.Event(), "generation": state["generations"].get(source, 0)}
            # Retain only the most recent job per source.
            state["jobs"] = {k: j for k, j in state["jobs"].items()
                             if j["source"] != source or j["status"] == "running"}
            state["jobs"][job_id] = job

        def run():
            records, keys = [], set()
            index = None
            error = None
            try:
                for page, rows in producer(job["cancel"].is_set):
                    if job["cancel"].is_set():
                        raise DiwanError("cancelled", 409)
                    for row in rows:
                        key = (row["source"], row["id"])
                        if key not in keys:
                            records.append(row)
                            keys.add(key)
                    if len(records) > 100000:
                        raise DiwanError("record_limit", 409)
                    with self.lock:
                        job.update(pages=page, count=len(records))
                previous = self.index(profile, source)
                previous_domains = previous.domain_model if previous and hasattr(previous.domain_model,"topics") else None
                index = TaskIndex(records, previous_domains=previous_domains)
                index.preview = None
            except DiwanError as exc:
                error = exc.code
            except Exception:
                error = "sync_failed"
            finally:
                with self.lock:
                    current = self._state(profile)
                    stale = current["generations"].get(source, 0) != job["generation"] or job["cancel"].is_set()
                    job.update(status="cancelled" if stale else ("failed" if error else "complete"),
                               error="cancelled" if stale else error, finished_at=now())
                    if not stale:
                        old = current["sources"].get(source, {})
                        if not error:
                            current["sources"][source] = {
                                "records": records, "complete": not error,
                                "updated_at": now(), "revision": uuid.uuid4().hex, "error": error}
                            current["indexes"][source] = index
                        else:
                            old["error"] = error
                            current["sources"][source] = old
                self.slots.release()

        threading.Thread(target=run, name="history-" + job_id[:8], daemon=True).start()
        return job_id

    def job(self, profile, job_id, cancel=False):
        with self.lock:
            job = self._state(profile)["jobs"].get(job_id)
            if not job:
                raise DiwanError("not_found", 404)
            if cancel:
                job["cancel"].set()
            return {k: v for k, v in job.items() if k not in {"cancel", "generation"}}


def bitrix_record(row, category_field="", data_fields=None):
    category_value = row.get(BitrixClient._camel(category_field)) if category_field else None
    tags = row.get("tags") or []
    if isinstance(tags, dict):
        tags = list(tags.values())
    if isinstance(tags, str):
        tags = [tags]
    tags = [str(t.get("name", "")) if isinstance(t, dict) else str(t) for t in tags]
    responsible = row.get("responsible") or {}
    return {
        "source": "bitrix", "id": str(row["id"]), "request_id": "",
        "title": str(row.get("title") or ""), "description": str(row.get("description") or ""),
        "category": str(category_value or (tags[0] if tags else "")),
        "project_id": str(row.get("groupId") or ""),
        "creator_id": str(row.get("createdBy") or ""),
        "auditor_ids": [str(v) for v in (row.get("auditors") or [])],
        "modified_at": row.get("changedDate"),
        "rating": row.get("mark"),
        "tags": tags, "status": str(row.get("status") or ""),
        "status_label": str(row.get("status") or ""), "completed": str(row.get("status")) == "5",
        "assignee_id": str(row.get("responsibleId") or ""),
        "assignee_name": str(responsible.get("name") or row.get("responsibleName") or "") if isinstance(responsible, dict) else "",
        "created_at": row.get("createdDate"), "completed_at": row.get("closedDate"),
        "deadline": row.get("deadline"), "priority": int(row.get("priority") or 0),
        "fields": [], "actions": [],
        "attributes": {name: row.get(BitrixClient._camel(code)) for name, code in (data_fields or {}).items()},
    }


def bitrix_pages(client, projects, cancelled, category_field="", active_only=False, data_fields=None):
    count = 0
    for project in projects:
        start, cursors = 0, set()
        while True:
            if cancelled():
                raise DiwanError("cancelled", 409)
            if start in cursors or count >= 2000:
                raise DiwanError("pagination_stalled", 409)
            cursors.add(start)
            payload = client._call_raw("tasks.task.list", {
                "filter": {"GROUP_ID": int(project["id"]), **({"!STATUS": 5} if active_only else {})},
                "select": ["ID", "TITLE", "DESCRIPTION", "STATUS", "RESPONSIBLE_ID",
                           "GROUP_ID", "TAGS", "PRIORITY", "CREATED_DATE", "CLOSED_DATE", "DEADLINE", "CREATED_BY", "AUDITORS", "CHANGED_DATE", "MARK"] + ([category_field] if category_field else []) + list((data_fields or {}).values()),
                "order": {"ID": "asc"}, "start": start})
            node = payload.get("result") or {}
            rows = node.get("tasks", []) if isinstance(node, dict) else node
            if not isinstance(rows, list):
                raise DiwanError("invalid_response")
            count += 1
            yield count, [bitrix_record(client._normalize_task(t), category_field, data_fields) for t in rows]
            nxt = payload.get("next")
            if nxt is None:
                break
            start = int(nxt)
