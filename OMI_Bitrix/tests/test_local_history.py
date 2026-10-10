"""Persistent history, scoped credentials, JSON columns and long Windows paths."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_diwany as fixtures
from diwan_columns import display_fields, validate_columns
from diwany import DiwanClient, DiwanError, normalize, validate_config
from history import History, connection_scope
from history_scheduler import HistoryScheduler
from workspace import (filesystem_path, display_path, ensure_workspace, task_folder,
                       safe_name, note_path, read_fields, save_fields, count_artifacts)


class FakeIndex:
    def __init__(self, records, **kwargs):
        self.records = records
        self.domain_model = None
        self.preview = None


def wait_job(history, pid, job):
    for _ in range(500):
        result = history.job(pid, job)
        if result["status"] != "running":
            return result
        time.sleep(.01)
    raise AssertionError("History worker did not finish")


class PersistentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "history.sqlite3"
        self.history = History(self.path)
        self.history.bind_scope("one", "diwan_analysis", "service-one")
        self.patch_index = patch("history.TaskIndex", FakeIndex)
        self.patch_index.start()
        self.addCleanup(self.patch_index.stop)
        self.rows = [{"source": "diwan", "id": str(i), "title": "مراجعة فاتورة " + str(i)} for i in range(125)]

    def save(self, rows=None):
        job = self.history.start("one", "diwan_analysis", lambda _: iter([(1, rows if rows is not None else self.rows)]))
        self.assertEqual(wait_job(self.history, "one", job)["status"], "complete")

    def test_restart_restores_search_and_sql_pagination(self):
        self.save()
        restored = History(self.path)
        restored.bind_scope("one", "diwan_analysis", "service-one")
        self.assertTrue(restored.metadata("one", "diwan_analysis")["complete"])
        with patch.object(restored, "source", side_effect=AssertionError("Must page from SQLite")):
            rows, count = restored.page("one", "diwan_analysis", 2)
            self.assertEqual((len(rows), count, rows[0]["id"]), (50, 125, "50"))
            rows, count = restored.page("one", "diwan_analysis", query="فاتورة 124")
            self.assertEqual((count, rows[0]["id"]), (1, "124"))
            self.assertEqual(restored.page("one", "diwan_analysis", query="' OR 1=1 --"), ([], 0))

    def test_connection_and_profile_isolation_survive_restart(self):
        self.save()
        restored = History(self.path)
        restored.bind_scope("two", "diwan_analysis", "service-one")
        self.assertEqual(restored.page("two", "diwan_analysis"), ([], 0))
        restored.bind_scope("one", "diwan_analysis", "service-two")
        self.assertEqual(restored.page("one", "diwan_analysis"), ([], 0))
        previous = History(self.path)
        previous.bind_scope("one", "diwan_analysis", "service-one")
        self.assertEqual(previous.page("one", "diwan_analysis"), ([], 0))

    def test_unchanged_refresh_reuses_index_revision_and_preview(self):
        self.save()
        previous = self.history.index("one", "diwan_analysis")
        previous.preview = ["cached pairs"]
        revision = self.history.metadata("one", "diwan_analysis")["revision"]
        with patch("history.TaskIndex", side_effect=AssertionError("Unchanged data must reuse index")):
            self.save()
        self.assertIs(self.history.index("one", "diwan_analysis"), previous)
        self.assertEqual(previous.preview, ["cached pairs"])
        self.assertEqual(self.history.metadata("one", "diwan_analysis")["revision"], revision)

    def test_failed_refresh_retains_last_good_snapshot_after_restart(self):
        self.save()
        def failed(_):
            yield 1, [{"source": "diwan", "id": "partial"}]
            raise DiwanError("source_unavailable")
        job = self.history.start("one", "diwan_analysis", failed)
        self.assertEqual(wait_job(self.history, "one", job)["status"], "failed")
        restored = History(self.path)
        restored.bind_scope("one", "diwan_analysis", "service-one")
        self.assertEqual(restored.metadata("one", "diwan_analysis")["count"], 125)
        self.assertEqual(restored.metadata("one", "diwan_analysis")["error"], "source_unavailable")

    def test_disk_failure_does_not_publish_unsaved_records(self):
        self.save()
        with patch.object(self.history.database, "save", side_effect=OSError("disk full")):
            job = self.history.start("one", "diwan_analysis", lambda _: iter([(1, [{"source": "diwan", "id": "new"}])]))
            result = wait_job(self.history, "one", job)
        self.assertEqual(result["error"], "cache_write_failed")
        self.assertEqual(self.history.page("one", "diwan_analysis")[1], 125)

    def test_restore_builds_index_in_background_without_blocking_page(self):
        self.save()
        restored = History(self.path)
        restored.bind_scope("one", "diwan_analysis", "service-one")
        entered, release = threading.Event(), threading.Event()
        def slow(records, **kwargs):
            entered.set()
            release.wait(4)
            return FakeIndex(records)
        with patch("history.TaskIndex", side_effect=slow) as factory:
            self.assertIsNone(restored.index("one", "diwan_analysis"))
            self.assertTrue(entered.wait(1))
            self.assertEqual(restored.page("one", "diwan_analysis")[1], 125)
            self.assertIsNone(restored.index("one", "diwan_analysis"))
            self.assertEqual(factory.call_count, 1)
            restored.invalidate("one", "diwan_analysis")
            release.set()
            for _ in range(100):
                if not restored._state("one").get("building"):
                    break
                time.sleep(.01)
        self.assertIsNone(restored.index("one", "diwan_analysis"))
        self.assertEqual(restored.page("one", "diwan_analysis"), ([], 0))

    def test_restart_scheduler_reuses_fresh_cache_without_network(self):
        store = fixtures.ConfigStore(Path(self.directory.name) / "settings.sqlite3")
        store.set_many({"signed_profile_active": True, "webhook_url": "https://bitrix.internal/rest/1/test/"}, profile_id="one")
        store.replace_projects([{"id": "1", "name": "Project"}], profile_id="one")
        scope = connection_scope(store, "one", "bitrix")
        self.history.bind_scope("one", "bitrix", scope)
        job = self.history.start("one", "bitrix", lambda _: iter([(1, [{"source": "bitrix", "id": "1"}])]))
        self.assertEqual(wait_job(self.history, "one", job)["status"], "complete")
        restored = History(self.path)
        scheduler = HistoryScheduler(store, fixtures.MemoryVault(), restored)
        with patch("history_scheduler.bitrix_pages", side_effect=AssertionError("No network on reopen")):
            self.assertIsNone(scheduler.refresh("one", "bitrix"))
            self.assertEqual(restored.page("one", "bitrix")[1], 1)
        with patch("history_scheduler.bitrix_pages", return_value=iter([(1, [])])) as fetch:
            job = scheduler.refresh("one", "bitrix", force=True)
            self.assertEqual(wait_job(restored, "one", job)["status"], "complete")
            self.assertEqual(fetch.call_count, 1)


class ColumnAndCredentialTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post
    connect = fixtures.AppTests.connect

    def test_token_kept_for_same_service_settings_and_identical_token(self):
        self.connect(self.a)
        pid = self.pid(self.a)
        vault = fixtures.main.app.extensions["diwan_vault"]
        candidate = {**fixtures.CONFIG, "current_user_id": "employee", "roles_confirmed": True}
        self.assertEqual(self.post(self.a, "/api/diwany/config", candidate).status_code, 200)
        self.assertEqual(vault.get(pid), "personal-test-token")
        with patch("diwany.DiwanClient.list_page", return_value=[]), patch.object(vault, "save", side_effect=AssertionError("Don't re-save identical token")):
            self.assertEqual(self.post(self.a, "/api/diwany/token", {"token": "personal-test-token"}).status_code, 200)
        self.assertEqual(self.a.get("/tasks").status_code, 200)
        self.assertEqual(self.a.get("/diwany").status_code, 200)

    def test_token_removed_when_service_host_changes(self):
        self.connect(self.a)
        candidate = {key: value.replace("diwan.internal", "another.internal") if isinstance(value, str) else value for key, value in fixtures.CONFIG.items()}
        self.assertEqual(self.post(self.a, "/api/diwany/config", candidate).status_code, 200)
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(self.pid(self.a)))

    def test_json_columns_are_persisted_profile_scoped_and_do_not_touch_token(self):
        self.connect(self.a)
        pid = self.pid(self.a)
        history = History(Path(self.directory.name) / "history.sqlite3")
        fixtures.main.app.extensions["diwan_history"] = history
        row = normalize({"id": "81", "subject": "مهمة", "department": {"name": "المالية"}, "token": "must-not-display"}, validate_config(fixtures.CONFIG))
        history.bind_scope(pid, "diwan", connection_scope(fixtures.main.STORE, pid, "diwan"))
        with patch("history.TaskIndex", FakeIndex):
            job = history.start(pid, "diwan", lambda _: iter([(1, [row])]))
            self.assertEqual(wait_job(history, pid, job)["status"], "complete")
        available = self.a.get("/api/diwany/columns").json
        self.assertIn("json:department.name", [column["key"] for column in available["available"]])
        self.assertNotIn("json:token", [column["key"] for column in available["available"]])
        selected = [{"key": "task:id", "label": "ID"}, {"key": "json:department.name", "label": "القسم"}]
        self.assertEqual(self.post(self.a, "/api/diwany/columns", {"columns": selected}).status_code, 200)
        self.assertEqual(fixtures.main.app.extensions["diwan_vault"].get(pid), "personal-test-token")
        fixtures.main.app.extensions["diwan_history"] = History(history.database.path)
        result = self.a.get("/api/diwany/tasks").json
        self.assertEqual(result["records"][0]["display_values"], ["81", "المالية"])
        self.assertEqual(result["columns"], selected)
        self.assertNotIn("must-not-display", json.dumps(result))
        self.assertNotIn("display_fields", result["records"][0])
        self.assertNotEqual(self.b.get("/api/diwany/columns").json["selected"], selected)
        self.assertEqual(self.b.get("/api/diwany/tasks").json["records"], [])

    def test_columns_validation_and_safe_json_flattening(self):
        row = {"nested": {"name": "<script>alert(1)</script>", "apiKey": "hidden"}, "authorization": {"access": "hidden"}, "items": [{"name": "first"}], "nothing": None}
        self.assertEqual(display_fields(row), {"nested.name": "<script>alert(1)</script>", "items.0.name": "first", "nothing": ""})
        for bad in ([], [{"key": "json:password"}], [{"key": "task:unknown"}], [{"key": "task:id"}]*2, [{"key": "task:id", "label": "a"*81}]):
            with self.assertRaises(DiwanError):
                validate_columns(bad)


class WorkspacePathTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_new_task_uses_short_note_and_preserves_legacy_document(self):
        task = {"id": "152916", "title": "بيانات طويلة "*30}
        created = ensure_workspace(self.root, "Project", task, employee_name="Employee")
        self.assertLessEqual(len(created["folder"].name), 64)
        self.assertEqual(created["note"].name, "Task.md")
        legacy_folder = task_folder(self.root, "Project", {**task, "id": "2"})
        legacy_folder.mkdir()
        legacy = legacy_folder / (safe_name(legacy_folder.name) + ".md")
        legacy.write_text("Preserve this documentation", encoding="utf-8")
        self.assertEqual(ensure_workspace(self.root, "Project", {**task, "id": "2"})["note"], legacy)
        self.assertTrue(legacy.read_text(encoding="utf-8").startswith("Preserve this documentation"))

    @unittest.skipUnless(os.name == "nt", "Windows long-path contract")
    def test_windows_long_unicode_paths_and_nested_artifacts(self):
        root = self.root / ("long-root-"*8) / ("مجلد-"*16)
        result = ensure_workspace(root, "Project", {"id": "1", "title": "طلب طويل "*20})
        self.assertGreater(len(str(result["note"])), 260)
        save_fields(result["note"], {"objective": "الحفظ يعمل"}, result["folder"])
        self.assertEqual(read_fields(result["note"])["objective"], "الحفظ يعمل")
        artifact = filesystem_path(result["folder"] / "04_Output" / ("nested-"*10) / "نتيجة.txt")
        artifact.parent.mkdir(parents=True)
        artifact.write_text("ok", encoding="utf-8")
        save_fields(result["note"], read_fields(result["note"]), result["folder"])
        self.assertEqual(count_artifacts(result["folder"])["04_Output"], 1)
        self.assertIn("نتيجة.txt", filesystem_path(result["note"]).read_text(encoding="utf-8"))
        self.assertEqual(display_path(filesystem_path(result["note"])), str(result["note"]))
        self.assertFalse(str(result["folder"]).startswith("\\\\?\\"))

    def test_large_project_scanned_once_per_sync(self):
        cache = {}
        with patch.object(Path, "iterdir", autospec=True, return_value=iter([])) as scan:
            for i in range(1000):
                task_folder(self.root, "Project", {"id": str(i), "title": "Task"}, directory_cache=cache)
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(len(next(iter(cache.values()))), 1000)

    def test_reassignment_keeps_legacy_folder_note_and_evidence(self):
        from workspace import move_workspace
        task = {"id": "81", "title": "Long legacy title "*8}
        original = self.root / "Bitrix Work" / "Old" / "Project" / safe_name("81 - " + task["title"])
        original.mkdir(parents=True)
        old_note = original / (safe_name(original.name) + ".md")
        old_note.write_text("Original documentation", encoding="utf-8")
        moved = move_workspace(self.root, "Project", task, "Old", "New")
        self.assertTrue(moved["moved"])
        self.assertEqual(moved["folder"].name, original.name)
        self.assertTrue(filesystem_path(moved["note"]).read_text(encoding="utf-8").startswith("Original documentation"))
        self.assertEqual(note_path(task_folder(self.root, "Project", task, "New")), moved["note"])


class MatchingPerformanceTests(unittest.TestCase):
    def test_semantic_peak_computed_once_for_large_candidate_pool(self):
        from task_intelligence import TaskIndex
        class Scores:
            calls = 0
            def __ge__(self, value):
                return self
            def nonzero(self):
                return (range(1000),)
            def __getitem__(self, index):
                return .91
            def max(self):
                self.calls += 1
                return .91
        rows = [{"source": "bitrix", "id": str(i), "title": "supplier invoice review", "description": "invoice reconciliation", "tags": []} for i in range(1000)]
        with patch("semantic_engine.get_encoder", return_value=None):
            index = TaskIndex(rows)
        scores = Scores()
        index.semantic = SimpleNamespace(status="ready", query=lambda _: (None, scores))
        with patch("recommendation_matching.get_reranker", return_value=None), patch.object(index, "model_summary", return_value={"id": "test"}):
            results = index.related("supplier invoice review", limit=10)
        self.assertEqual(len(results), 10)
        self.assertEqual(scores.calls, 1)


def export_fixtures(output):
    output.mkdir(parents=True, exist_ok=True)
    case = ColumnAndCredentialTests()
    case.setUp()
    try:
        case.connect(case.a)
        pid = case.pid(case.a)
        history = fixtures.main.app.extensions["diwan_history"]
        row = normalize({"id": "81", "requestId": "MQR-81", "subject": "Invoice review / مراجعة فاتورة", "department": {"name": "المالية"}}, validate_config(fixtures.CONFIG))
        for cache in ("diwan", "diwan_analysis"):
            history.bind_scope(pid, cache, connection_scope(fixtures.main.STORE, pid, "diwan"))
            with patch("history.TaskIndex", FakeIndex):
                job = history.start(pid, cache, lambda _: iter([(1, [row])]))
                wait_job(history, pid, job)
        for lang in ("en", "ar"):
            fixtures.main.STORE.set("ui_language", lang, profile_id=pid)
            for page in ("connections", "diwany"):
                (output / f"{page}-{lang}.html").write_text(case.a.get("/" + page).get_data(as_text=True), encoding="utf-8")
            (output / f"columns-{lang}.json").write_text(case.a.get("/api/diwany/columns").get_data(as_text=True), encoding="utf-8")
            (output / f"tasks-{lang}.json").write_text(case.a.get("/api/diwany/tasks").get_data(as_text=True), encoding="utf-8")
    finally:
        case.doCleanups()


if __name__ == "__main__":
    if "--export" in sys.argv:
        export_fixtures(Path(sys.argv[sys.argv.index("--export") + 1]))
    else:
        unittest.main()
