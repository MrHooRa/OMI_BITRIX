"""Read-only history refresh, independent of browser tabs and workspace synchronization."""
import hashlib
import json
import threading
import time
from datetime import datetime, timezone

from bitrix import BitrixClient
from diwany import DiwanClient, DiwanError
from history import bitrix_pages, connection_scope

INTERVAL_SECONDS = 2 * 60 * 60
RETRY_SECONDS = 5 * 60


class HistoryScheduler:
    def __init__(self, store, vault, history, clock=time.time):
        self.store, self.vault, self.history, self.clock = store, vault, history, clock
        self.lock = threading.RLock()
        self.entries = {}
        self.thread = None

    @staticmethod
    def cache_key(source):
        # Filtered Diwan browsing must never replace the full analysis corpus.
        return "diwan_analysis" if source == "diwan" else "bitrix"

    def configuration(self, pid, source):
        if not self.store.get("signed_profile_active", False, profile_id=pid):
            return None
        if source == "bitrix":
            url = self.store.get("webhook_url", "", profile_id=pid)
            projects = self.store.projects(pid)
            return {"url": url, "projects": projects, "category_field": self.store.get("recommendation_policy", {}, profile_id=pid).get("category_field", ""), "data_fields": self.store.get("recommendation_policy", {}, profile_id=pid).get("data_fields", {})} if url and projects else None
        config = self.store.get("diwan_config", {}, profile_id=pid)
        if config and self.vault.present(pid):
            return {"config": config, "credential": self.store.get("diwan_token_protected", "", profile_id=pid)}
        return None

    def refresh(self, pid, source, force=False):
        if source not in {"bitrix", "diwan"}:
            raise DiwanError("invalid_input", 400)
        with self.lock:
            config = self.configuration(pid, source)
            key, cache = (pid, source), self.cache_key(source)
            fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
            self.history.bind_scope(pid, cache, connection_scope(self.store, pid, source))
            entry = self.entries.get(key)
            if not entry or entry["fingerprint"] != fingerprint:
                self.history.invalidate(pid, cache)
                entry = {"fingerprint": fingerprint, "next": 0, "job_id": None,
                         "error": None, "handled": None}
                self.entries[key] = entry
            if config is None:
                entry["enabled"] = False
                return None
            entry["enabled"] = True
            if entry["job_id"]:
                try:
                    job = self.history.job(pid, entry["job_id"])
                except DiwanError:
                    job = {"status": "cancelled"}
                if job["status"] == "running":
                    return entry["job_id"]
                if entry["handled"] != entry["job_id"]:
                    entry["handled"] = entry["job_id"]
                    entry["error"] = job.get("error")
                    if job["status"] != "complete":
                        entry["next"] = min(entry["next"], self.clock() + RETRY_SECONDS)
            if not force and self.clock() < entry["next"]:
                return None
            try:
                if source == "bitrix":
                    api = BitrixClient(config["url"])
                    producer = lambda cancelled: bitrix_pages(api, config["projects"], cancelled, config.get("category_field", ""), data_fields=config.get("data_fields", {}))
                else:
                    api = DiwanClient(config["config"], self.vault.get(pid))
                    producer = lambda cancelled: api.iter_analysis_pages({}, cancelled)
                job_id = self.history.start(pid, cache, producer)
            except Exception as exc:
                entry["error"] = exc.code if isinstance(exc, DiwanError) else "sync_failed"
                entry["next"] = self.clock() + RETRY_SECONDS
                if force:
                    raise DiwanError(entry["error"], 409) from None
                return None
            entry.update(job_id=job_id, next=self.clock() + INTERVAL_SECONDS, error=None)
            return job_id

    def tick(self, pid=None):
        for profile in ([pid] if pid else self.store.profile_ids()):
            for source in ("bitrix", "diwan"):
                self.refresh(profile, source)

    def status(self, pid, source):
        with self.lock:
            entry = self.entries.get((pid, source), {})
            job = None
            if entry.get("job_id"):
                try:
                    job = self.history.job(pid, entry["job_id"])
                except DiwanError:
                    pass
            due = entry.get("next")
            return {"enabled": entry.get("enabled", False), "interval_seconds": INTERVAL_SECONDS,
                    "next_run_at": datetime.fromtimestamp(due, timezone.utc).isoformat() if due else None,
                    "error": entry.get("error"), "job": job}

    def start(self, stop_event):
        with self.lock:
            if self.thread and self.thread.is_alive():
                return self.thread
            def run():
                while not stop_event.is_set():
                    try:
                        self.tick()
                    except Exception:
                        # A temporary settings/database failure must not kill the scheduler.
                        pass
                    stop_event.wait(15)
            self.thread = threading.Thread(target=run, name="history-refresh", daemon=True)
            self.thread.start()
            return self.thread
