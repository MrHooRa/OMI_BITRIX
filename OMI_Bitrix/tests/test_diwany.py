"""Offline contract, security, pagination and analysis regression coverage."""
import copy
import io
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from xml.etree import ElementTree

_TEMP = tempfile.TemporaryDirectory()
os.environ["OMI_DATA_DIR"] = _TEMP.name

import app as main
from diwany import DiwanClient, DiwanError, validate_config, records_from, form_fields
from history import History, connection_scope
from history_scheduler import HistoryScheduler
from recommendation_service import RecommendationService
from security import CredentialVault
from storage import ConfigStore
from sla import estimate, business_deadline, parse, evaluate
from task_intelligence import analyze, effective_priority
from planner import build_today_plan
from datetime import datetime, timedelta
from xlsx_report import build_workbook

CONFIG = {"list_url": "https://diwan.internal/list", "list_method": "POST",
          "detail_url": "https://diwan.internal/details/{task_id}", "detail_method": "GET",
          "delegate_url": "https://diwan.internal/delegate", "delegate_method": "POST",
          "task_id_field": "id", "assignee_field": "assignTo", "recipient_kind": "email",
          "completed_statuses": "5", "delegation_confirmed": True}


class ClientTests(unittest.TestCase):
    def test_config_rejects_unsafe_urls_and_methods(self):
        for value in ("http://diwan.internal/list", "https://u:p@internal/list", "https://internal/list?token=x"):
            with self.assertRaises(DiwanError):
                validate_config({**CONFIG, "list_url": value})
        with self.assertRaises(DiwanError):
            validate_config({**CONFIG, "delegate_method": "GET"})

    def test_all_pages_deduplicates_and_does_not_stop_at_short_page(self):
        pages = [[{"id": 1}, {"id": 2}], [{"id": 2}, {"id": 3}], []]
        calls = []
        def transport(url, method, data):
            calls.append(data)
            return {"result": {"data": pages[data["pageNumber"] - 1]}}
        client = DiwanClient(validate_config(CONFIG), "test", transport)
        records = [r for _, page in client.iter_pages() for r in page]
        self.assertEqual([r["id"] for r in records], ["1", "2", "3"])
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[0]["filter"]["statusId"], 0)

    def test_repeated_page_fails_explicitly(self):
        client = DiwanClient(validate_config(CONFIG), "test", lambda *args: [{"id": 1}])
        with self.assertRaisesRegex(DiwanError, "pagination_stalled"):
            list(client.iter_pages())

    def test_top_level_list_and_empty_page(self):
        self.assertEqual(records_from([]), [])
        self.assertEqual(records_from({"result": {"data": []}}), [])
        for bad in (None, {"result": None}, {"success": False}):
            with self.assertRaises(DiwanError):
                records_from(bad)

    def test_missing_id_does_not_fall_back_to_ticket(self):
        client = DiwanClient(validate_config(CONFIG), "test", lambda *args: [{"requestId": "MQR-1"}])
        with self.assertRaisesRegex(DiwanError, "missing_task_id"):
            list(client.iter_pages())

    def test_duplicate_arabic_fields_preserved(self):
        fields = form_fields({"viewForm": {"controls": [
            {"id": "a", "label": "الطلب", "value": "أ"},
            {"id": "b", "label": "الطلب", "value": "ب"}]}})
        self.assertEqual(len(fields), 2)

    def test_details_use_internal_id(self):
        calls = []
        def transport(url, method, payload):
            calls.append((url, payload))
            return {"result": {"data": {"id": "81", "requestId": "MQR-7"}}}
        client = DiwanClient(validate_config(CONFIG), "test", transport)
        self.assertEqual(client.details("81")["requestId"], "MQR-7")
        self.assertTrue(calls[0][0].endswith("/81"))

    def test_detail_identity_mismatch_fails(self):
        client = DiwanClient(validate_config(CONFIG), "test", lambda *args: {"id": 7})
        with self.assertRaisesRegex(DiwanError, "task_id_mismatch"):
            client.details("8")

    def test_delegation_is_confirmed_by_readback(self):
        calls = []
        def transport(url, method, data):
            calls.append((url, method, data))
            return {"success": True} if method == "POST" else {"id": "81", "assignTo": "employee@internal.example"}
        client = DiwanClient(validate_config(CONFIG), "test", transport)
        client.delegate("81", "MQR-7", {"value": "employee@internal.example"})
        self.assertEqual(calls[0][2]["taskId"], "81")
        self.assertEqual(calls[0][2]["requestId"], "MQR-7")

    def test_uncertain_delegation_is_not_reported_successful(self):
        client = DiwanClient(validate_config(CONFIG), "test", lambda *args: {"id": "81"})
        with self.assertRaisesRegex(DiwanError, "delegation_uncertain"):
            client.delegate("81", "MQR-7", {"value": "employee@internal.example"})

    def test_disabled_delegation_never_calls_source(self):
        client = DiwanClient({**validate_config(CONFIG), "delegation_confirmed": False}, "test",
                             lambda *args: self.fail("Network call"))
        with self.assertRaises(DiwanError):
            client.delegate("1", "MQR-1", {"value": "employee@internal.example"})


class HistoryTests(unittest.TestCase):
    def test_invalidation_prevents_late_job_repopulation(self):
        history = History()
        wait, begun = threading.Event(), threading.Event()
        def producer(cancelled):
            begun.set()
            wait.wait(2)
            yield 1, [{"source": "diwan", "id": "1"}]
        job = history.start("a", "diwan", producer)
        self.assertTrue(begun.wait(1))
        history.invalidate("a")
        wait.set()
        for _ in range(100):
            if history.job("a", job)["status"] != "running":
                break
            time.sleep(.01)
        self.assertEqual(history.source("a", "diwan")["records"], [])
        self.assertEqual(history.job("a", job)["status"], "cancelled")
        with self.assertRaises(DiwanError):
            history.job("b", job)

    def test_failed_refresh_keeps_last_good_records(self):
        history = History()
        with history.lock:
            history._state("a")["sources"]["diwan"] = {"records": [{"id": "old"}], "complete": True}
        def producer(cancelled):
            raise DiwanError("source_unavailable")
            yield
        job = history.start("a", "diwan", producer)
        for _ in range(100):
            if history.job("a", job)["status"] != "running":
                break
            time.sleep(.01)
        self.assertEqual(history.source("a", "diwan")["records"], [{"id": "old"}])
        self.assertEqual(history.source("a", "diwan")["error"], "source_unavailable")


class AnalysisTests(unittest.TestCase):
    def record(self, number=1):
        return {"source": "diwan", "id": str(number), "title": "تحليل ضريبة القيمة",
                "description": "", "category": "Tax", "completed": True, "assignee_id": "a",
                "created_at": "2026-01-01T08:00:00+03:00",
                "completed_at": "2026-01-02T08:00:00+03:00", "tags": []}

    def test_sparse_duration_is_unknown(self):
        self.assertFalse(estimate([self.record()])["available"])

    def test_duration_is_elapsed_not_effort(self):
        result = estimate([self.record(i) for i in range(3)])
        self.assertEqual(result["median"], 24)

    def test_arabic_recommendation_and_absence(self):
        records = [self.record(i) for i in range(4)]
        result = analyze(records, "تحليل ضريبه القيمه", {}, [{"value": "a", "name_en": "A"}])
        self.assertEqual(result["category"], "Tax")
        # Similarity does not run a second category-count assignment model.
        self.assertEqual(result["recommendations"], [])
        self.assertEqual(len(result["related"]), 4)
        result = analyze(records, "تحليل ضريبه القيمه", {}, [{
            "value": "a", "away_from": "2000-01-01", "away_to": "2099-01-01"}])
        self.assertEqual(result["recommendations"], [])

    def test_source_ids_are_not_merged(self):
        records = [self.record(), {**self.record(2), "source": "bitrix"}]
        result = analyze(records, "تحليل ضريبة القيمة", {}, [], source="diwan")
        self.assertEqual(len(result["related"]), 1)

    def test_priority_rule_does_not_change_source(self):
        record = {"priority": 1, "tags": ["urgent"]}
        self.assertEqual(effective_priority(record, {"tag_priorities": {"urgent": 3}}), 3)
        self.assertEqual(record["priority"], 1)

    def test_calendar_skips_weekend_and_holiday(self):
        start = parse("2026-10-01T15:00:00+03:00")  # Thursday
        result = business_deadline(start, 2, {"holidays": ["2026-10-04"]})
        self.assertEqual(result.isoformat(), "2026-10-05T09:00:00+03:00")

    def test_temporal_evaluation_no_future_leakage(self):
        self.assertEqual(evaluate([self.record(i) for i in range(10)])["samples"], 0)

    def test_planner_includes_overdue_and_excludes_completed_future_queue(self):
        from planner import LOCAL_TZ
        now = datetime.now(LOCAL_TZ)
        tasks = [
            {"id": "late", "deadline": (now - timedelta(days=1)).isoformat(), "status": "2"},
            {"id": "done", "deadline": now.isoformat(), "status": "5"},
            {"id": "future", "deadline": (now + timedelta(days=2)).isoformat(), "status": "2"},
            {"id": "started", "deadline": (now + timedelta(days=2)).isoformat(), "status": "3"},
        ]
        plan = build_today_plan(tasks)
        self.assertEqual({p["task"]["id"] for p in plan}, {"late", "started"})
        self.assertEqual(sum(p["minutes"] for p in plan), 480)
        with self.assertRaises(ValueError):
            build_today_plan(tasks, total_minutes=481)

    def test_xlsx_keeps_formula_text_as_string_and_valid_xml(self):
        data = build_workbook([("Diwan", [["ID", "Text"], ["1", "=1+1\x00"]], [12, 20])])
        with ZipFile(io.BytesIO(data)) as archive:
            for name in archive.namelist():
                if name.endswith(".xml") or name.endswith(".rels"):
                    ElementTree.fromstring(archive.read(name))
            sheet = archive.read("xl/worksheets/sheet1.xml")
            self.assertNotIn(b"<f>", sheet)
            self.assertIn(b"=1+1", sheet)


class MemoryVault:
    def __init__(self):
        self.values = {}
    def present(self, pid):
        return pid in self.values
    def save(self, pid, token):
        self.values[pid] = token
    def get(self, pid):
        return self.values.get(pid, "")
    def remove(self, pid):
        self.values.pop(pid, None)


class AppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        main.STORE = ConfigStore(Path(self.directory.name) / "test.sqlite3")
        main.app.extensions["diwan_store"] = main.STORE
        main.app.extensions["diwan_history"] = History()
        main.app.extensions["diwan_vault"] = MemoryVault()
        main.app.extensions["history_scheduler"] = HistoryScheduler(main.STORE, main.app.extensions["diwan_vault"], main.app.extensions["diwan_history"])
        main.app.extensions["recommendations"] = RecommendationService(main.STORE, main.app.extensions["diwan_history"], Path(self.directory.name) / "recommendations", automatic_suggestions=False)
        from diwan_recommendations import DiwanRecommendationService
        main.app.extensions["diwan_recommendations"] = DiwanRecommendationService(main.STORE, main.app.extensions["diwan_history"], Path(self.directory.name) / "recommendations", main.app.extensions["diwan_vault"], automatic_suggestions=False)
        main.app.config["TESTING"] = True
        self.a, self.b = main.app.test_client(), main.app.test_client()
        self.a.get("/connections")
        self.b.get("/connections")

    def post(self, client, url, data, method="POST"):
        with client.session_transaction() as session:
            token = session["csrf_token"]
        return client.open(url, method=method, json=data, headers={"X-CSRF-Token": token})

    def pid(self, client):
        return main.PROFILE_SIGNER.loads(client.get_cookie(main.PROFILE_COOKIE).value)

    def connect(self, client):
        self.assertEqual(self.post(client, "/api/diwany/config", CONFIG).status_code, 200)
        with patch("diwany.DiwanClient.list_page", return_value=[]):
            self.assertEqual(self.post(client, "/api/diwany/token", {"token": "personal-test-token"}).status_code, 200)

    def test_history_api_loads_and_shows_similarity_without_manual_fetch(self):
        from history import bitrix_record
        pid = self.pid(self.a)
        main.STORE.set("webhook_url", "https://bitrix.internal/rest/1/test/", profile_id=pid)
        main.STORE.replace_projects([{"id": "1", "name": "Test"}], profile_id=pid)
        rows = [bitrix_record({"id": str(i), "title": "invoice review", "description": "supplier invoice reconciliation", "responsibleId": str(i), "groupId": "1", "status": "2"}) for i in (1, 2)]
        with patch("history_scheduler.bitrix_pages", return_value=iter([(1, rows)])):
            self.a.get("/api/intelligence")
            scheduler = main.app.extensions["history_scheduler"]
            job_id = scheduler.status(pid, "bitrix")["job"]["id"]
            for _ in range(200):
                if main.app.extensions["diwan_history"].job(pid, job_id)["status"] != "running":
                    break
                time.sleep(.005)
            data = self.a.get("/api/intelligence?pairs=1").get_json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["pairs"]), 1)
        self.assertEqual(data["coverage"]["bitrix"]["schedule"]["interval_seconds"], 7200)
        result = self.post(self.a, "/api/intelligence/analyze", {"source": "bitrix", "task_id": "1"}).get_json()
        self.assertEqual([m["task"]["id"] for m in result["result"]["related"]], ["2"])
        self.assertEqual(self.b.get("/api/intelligence").get_json()["total"], 0)
        self.assertIn(b"Find similar", self.a.get("/tasks").data)

    def test_pages_work_without_bitrix_setup(self):
        for path in ("/connections", "/diwany", "/tasks", "/settings", "/setup"):
            response = self.a.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(b"csrf-token", response.data)

    def test_csrf_rejects_mutation(self):
        self.assertEqual(self.a.post("/api/diwany/config", json=CONFIG).status_code, 403)

    def test_signed_cookie_cannot_select_another_profile(self):
        original = self.pid(self.a)
        self.b.set_cookie(main.PROFILE_COOKIE, original)
        self.b.get("/diwany")
        self.assertNotEqual(self.pid(self.b), original)

    def test_two_profile_tokens_and_configuration_are_separate(self):
        self.connect(self.a)
        self.assertFalse(main.app.extensions["diwan_vault"].present(self.pid(self.b)))
        self.assertEqual(main.STORE.get("diwan_config", {}, profile_id=self.pid(self.b)), {})
        for url in ("/diwany", "/connections", "/settings"):
            self.assertNotIn(b"personal-test-token", self.a.get(url).data)

    def test_failed_replacement_preserves_token(self):
        self.connect(self.a)
        with patch("diwany.DiwanClient.list_page", side_effect=DiwanError("token_invalid", 401)):
            result = self.post(self.a, "/api/diwany/token", {"token": "invalid"})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(main.app.extensions["diwan_vault"].get(self.pid(self.a)), "personal-test-token")

    def test_endpoint_change_removes_old_credentials(self):
        self.connect(self.a)
        result = self.post(self.a, "/api/diwany/config", {**CONFIG, "list_url": "https://other.internal/list"})
        self.assertEqual(result.status_code, 200)
        self.assertFalse(main.app.extensions["diwan_vault"].present(self.pid(self.a)))

    def test_removal_does_not_affect_other_profile(self):
        self.connect(self.a)
        self.connect(self.b)
        self.post(self.a, "/api/diwany/token", {}, "DELETE")
        self.assertTrue(main.app.extensions["diwan_vault"].present(self.pid(self.b)))

    def test_details_and_job_cannot_cross_profiles(self):
        self.assertEqual(self.a.get("/api/diwany/tasks/secret").status_code, 404)
        self.assertEqual(self.a.get("/api/diwany/jobs/secret").status_code, 404)

    def test_invalid_calendar_and_recipient_are_rejected(self):
        self.assertEqual(self.post(self.a, "/api/intelligence/settings", {"working_days": []}).status_code, 400)
        self.post(self.a, "/api/diwany/config", CONFIG)
        self.assertEqual(self.post(self.a, "/api/diwany/employees",
                                  {"employees": [{"value": "bad-email"}]}).status_code, 400)

    def test_all_templates_parse_and_translation_keys_exist(self):
        from i18n import TRANSLATIONS
        import re
        for name in main.app.jinja_env.list_templates():
            source = main.app.jinja_env.loader.get_source(main.app.jinja_env, name)[0]
            main.app.jinja_env.parse(source)
            for key in re.findall(r"t\('([^']+)'\)", source):
                if key.startswith("d_"):
                    self.assertIn(key, TRANSLATIONS["en"], name)
                    self.assertIn(key, TRANSLATIONS["ar"], name)

    @unittest.skipUnless(os.name == "nt", "Windows DPAPI")
    def test_dpapi_roundtrip_bound_to_profile(self):
        vault = CredentialVault(main.STORE)
        vault.save("one", "test-secret")
        self.assertEqual(vault.get("one"), "test-secret")
        sealed = main.STORE.get("diwan_token_protected", profile_id="one")
        self.assertNotIn("test-secret", sealed)
        main.STORE.set("diwan_token_protected", sealed, profile_id="two")
        with self.assertRaises(RuntimeError):
            vault.get("two")



    def test_mocked_full_list_details_delegate_export_flow(self):
        self.connect(self.a)
        main.STORE.set("diwan_config",validate_config({**CONFIG,"supervisor_field":"supervisor","current_user_id":"owner","roles_confirmed":True}),profile_id=self.pid(self.a))
        person = {"value": "person@internal.example", "name_en": "Person"}
        self.assertEqual(self.post(self.a, "/api/diwany/employees", {"employees":[person]}).status_code, 200)
        assigned = {"value": ""}
        def remote(api, url, method, payload=None):
            if "/list" in url:
                return {"result": {"data": [{"id":"81","requestId":"MQR-7","serviceName":"Tax"}] if payload["pageNumber"] == 1 else []}}
            if "/delegate" in url:
                self.assertEqual(payload["taskId"], "81")
                self.assertEqual(payload["requestId"], "MQR-7")
                assigned["value"] = payload["assignTo"]
                return {"success": True}
            return {"result": {"data": {"id":"81","requestId":"MQR-7","supervisor":"owner","assignTo":assigned["value"],
                "viewForm":{"controls":[{"id":"f1","label":"سبب الطلب","value":"اختبار"}]}}}}
        with patch.object(DiwanClient, "_request", remote):
            response = self.post(self.a, "/api/diwany/sync", {})
            self.assertEqual(response.status_code, 202)
            job_id = response.json["job_id"]
            for _ in range(100):
                state = self.a.get("/api/diwany/jobs/" + job_id).json["job"]
                if state["status"] != "running":
                    break
                time.sleep(.01)
            self.assertEqual(state["status"], "complete")
            self.assertEqual(self.a.get("/api/diwany/tasks").json["total"], 1)
            detail = self.a.get("/api/diwany/tasks/81")
            self.assertEqual(detail.json["task"]["fields"][0]["label"], "سبب الطلب")
            self.assertEqual(self.b.get("/api/diwany/tasks").json["total"], 0)
            delegated = self.post(self.a, "/api/diwany/tasks/81/delegate",
                                  {"recipient":person["value"],"confirmed":True})
            self.assertEqual(delegated.status_code, 200, delegated.json)
            duplicate = self.post(self.a, "/api/diwany/tasks/81/delegate",
                                  {"recipient":person["value"],"confirmed":True})
            self.assertEqual(duplicate.json["code"], "already_assigned")
        export = self.a.get("/diwany/export.xlsx")
        self.assertEqual(export.status_code, 200)
        with ZipFile(io.BytesIO(export.data)) as book:
            self.assertIn(b"MQR-7", book.read("xl/worksheets/sheet1.xml"))
            self.assertIn("سبب الطلب", book.read("xl/worksheets/sheet2.xml").decode())

    def test_uncertain_mutation_blocks_blind_retry(self):
        self.connect(self.a)
        main.STORE.set("diwan_config",validate_config({**CONFIG,"supervisor_field":"supervisor","current_user_id":"owner","roles_confirmed":True}),profile_id=self.pid(self.a))
        pid = self.pid(self.a)
        # Seed a fresh cache for the updated configuration, as ingestion does.
        main.app.extensions["diwan_history"].bind_scope(pid, "diwan", connection_scope(main.STORE, pid, "diwan"))
        record = {"source":"diwan","id":"81","request_id":"MQR-7"}
        with main.app.extensions["diwan_history"].lock:
            main.app.extensions["diwan_history"]._state(pid)["sources"]["diwan"] = {"records":[record]}
        self.post(self.a,"/api/diwany/employees",{"employees":[{"value":"a@internal.example"}]})
        with patch.object(DiwanClient, "details", return_value={"id":"81","requestId":"MQR-7","supervisor":"owner"}), \
             patch.object(DiwanClient, "delegate", side_effect=DiwanError("source_unavailable")) as mutation:
            first = self.post(self.a,"/api/diwany/tasks/81/delegate",{"recipient":"a@internal.example","confirmed":True})
            second = self.post(self.a,"/api/diwany/tasks/81/delegate",{"recipient":"a@internal.example","confirmed":True})
        self.assertEqual(first.status_code, 502)
        self.assertEqual(second.json["code"], "delegation_uncertain")
        self.assertEqual(mutation.call_count, 1)

    def test_workspace_probe_cleans_up_local_test_files(self):
        folder = Path(self.directory.name) / "مساحة عمل"
        folder.mkdir()
        response = self.post(self.a,"/api/workspace/test",{"path":str(folder)})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["long_path"])
        self.assertEqual(list(folder.iterdir()), [])

    def test_bitrix_complete_never_runs_when_comment_fails(self):
        from unittest.mock import Mock
        api = Mock()
        api.send_message.side_effect = RuntimeError("simulated comment failure")
        with patch.object(main.STORE, "configured", return_value=True), \
             patch.object(main, "task_from_cache", return_value={"id":"1"}), \
             patch.object(main, "require_assignee"), \
             patch.object(main, "workspace_paths", return_value={"folder":"test","note":"test.md"}), \
             patch.object(main, "read_fields", return_value={"result":"Done"}), \
             patch.object(main, "readiness", return_value=100), \
             patch.object(main, "client", return_value=api):
            response = self.post(self.a,"/task/1/complete",{})
        self.assertEqual(response.status_code, 302)
        api.send_message.assert_called_once()
        api.complete_task.assert_not_called()

    def test_workspace_reassignment_never_overwrites_destination(self):
        from workspace import task_folder, move_workspace
        task = {"id":"81","title":"مهمة عربية"}
        source = task_folder(self.directory.name,"Project",task,"Old")
        target = task_folder(self.directory.name,"Project",task,"New")
        source.mkdir(parents=True)
        target.mkdir(parents=True)
        (source/"note.txt").write_text("source",encoding="utf-8")
        (target/"note.txt").write_text("target",encoding="utf-8")
        result = move_workspace(self.directory.name,"Project",task,"Old","New")
        self.assertEqual(result["reason"],"target_exists")
        self.assertEqual((source/"note.txt").read_text(),"source")
        self.assertEqual((target/"note.txt").read_text(),"target")


class ScheduledHistoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = ConfigStore(Path(self.directory.name) / "test.sqlite3")
        self.pid = "schedule-test"
        self.store.set("signed_profile_active", True, profile_id=self.pid)
        self.store.set("webhook_url", "https://bitrix.internal/rest/1/test/", profile_id=self.pid)
        self.store.replace_projects([{"id": "1", "name": "Test"}], profile_id=self.pid)
        self.history = History()
        self.clock = 1000
        self.scheduler = HistoryScheduler(self.store, MemoryVault(), self.history, lambda: self.clock)
        self.rows = [{"source": "bitrix", "id": "1", "title": "invoice review", "description": "supplier invoice reconciliation"}]
        self.producer = patch("history_scheduler.bitrix_pages", side_effect=lambda *args, **kwargs: iter([(1, self.rows)]))
        self.mock_pages = self.producer.start()
        self.addCleanup(self.producer.stop)

    def wait(self, job):
        for _ in range(200):
            state = self.history.job(self.pid, job)
            if state["status"] != "running":
                return state
            time.sleep(.005)
        self.fail("History job did not finish")

    def test_startup_and_exact_two_hour_interval(self):
        first = self.scheduler.refresh(self.pid, "bitrix")
        self.assertEqual(self.wait(first)["status"], "complete")
        self.assertIsNotNone(self.history.index(self.pid, "bitrix"))
        self.clock += 7199
        self.assertIsNone(self.scheduler.refresh(self.pid, "bitrix"))
        self.clock += 1
        second = self.scheduler.refresh(self.pid, "bitrix")
        self.assertNotEqual(first, second)
        self.assertEqual(self.wait(second)["status"], "complete")
        self.assertEqual(self.mock_pages.call_count, 2)
        self.assertEqual(self.scheduler.status(self.pid, "bitrix")["interval_seconds"], 7200)

    def test_no_overlap_manual_and_automatic(self):
        release = threading.Event()
        def slow(*args, **kwargs):
            release.wait(2)
            yield 1, self.rows
        self.mock_pages.side_effect = slow
        first = self.scheduler.refresh(self.pid, "bitrix")
        self.assertEqual(self.scheduler.refresh(self.pid, "bitrix", force=True), first)
        release.set()
        self.wait(first)
        self.assertEqual(self.mock_pages.call_count, 1)

    def test_failed_refresh_keeps_successful_index_and_retries(self):
        self.wait(self.scheduler.refresh(self.pid, "bitrix"))
        previous = self.history.index(self.pid, "bitrix")
        def failed(*args, **kwargs):
            yield 1, [{**self.rows[0], "id": "partial"}]
            raise RuntimeError("offline")
        self.mock_pages.side_effect = failed
        self.clock += 7200
        self.assertEqual(self.wait(self.scheduler.refresh(self.pid, "bitrix"))["status"], "failed")
        self.scheduler.refresh(self.pid, "bitrix")
        self.assertIs(self.history.index(self.pid, "bitrix"), previous)
        self.assertEqual(self.history.source(self.pid, "bitrix")["records"][0]["id"], "1")
        self.clock += 300
        self.mock_pages.side_effect = lambda *args, **kwargs: iter([(1, self.rows)])
        self.assertEqual(self.wait(self.scheduler.refresh(self.pid, "bitrix"))["status"], "complete")

    def test_changed_connection_clears_old_index(self):
        self.wait(self.scheduler.refresh(self.pid, "bitrix"))
        self.store.set("webhook_url", "", profile_id=self.pid)
        self.scheduler.refresh(self.pid, "bitrix")
        self.assertEqual(self.history.source(self.pid, "bitrix")["records"], [])
        self.assertIsNone(self.history.index(self.pid, "bitrix"))
        self.assertFalse(self.scheduler.status(self.pid, "bitrix")["enabled"])

    def test_profiles_and_filtered_diwan_are_separate(self):
        self.wait(self.scheduler.refresh(self.pid, "bitrix"))
        self.assertIsNone(self.history.index("another", "bitrix"))
        full = self.history.start(self.pid, "diwan_analysis", lambda _: iter([(1, [{**self.rows[0], "source": "diwan"}])]))
        self.wait(full)
        filtered = self.history.start(self.pid, "diwan", lambda _: iter([(1, [])]))
        self.wait(filtered)
        self.assertEqual(len(self.history.source(self.pid, "diwan_analysis")["records"]), 1)

    def test_discovered_employee_and_self_exclusion(self):
        from task_intelligence import TaskIndex
        records = [{**self.rows[0], "category": "invoice", "completed": True, "assignee_id": "11", "assignee_name": "Test Employee"},
                   {**self.rows[0], "id": "2", "category": "invoice", "completed": False, "assignee_id": "1"}]
        result = analyze(records, "invoice review", {}, [], "bitrix", index=TaskIndex(records), exclude=("bitrix", "2"))
        self.assertEqual([m["task"]["id"] for m in result["related"]], ["1"])
        self.assertEqual(result["recommendations"], [])


if __name__ == "__main__":
    unittest.main()
