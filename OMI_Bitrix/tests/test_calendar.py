"""Calendar tests use fake Bitrix data and never contact a portal."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_TEMP = tempfile.TemporaryDirectory()
os.environ["OMI_DATA_DIR"] = _TEMP.name
import app as application
from bitrix import BitrixClient

EN_PROFILE = "1" * 32
AR_PROFILE = "2" * 32


def cookie(profile):
    return application.PROFILE_SIGNER.dumps(profile)


TASKS = [
    {"id": "101", "title": "Reconcile VAT <sample>", "groupId": "7", "status": "2",
     "priority": "2", "deadline": "2026-10-10T22:30:00Z"},
    {"id": "102", "title": "Prepare monthly report", "groupId": "7", "status": "3", "deadline": ""},
    {"id": "103", "title": "Completed validation", "groupId": "8", "status": "5", "deadline": "2026-10-09T10:00:00+03:00"},
]


def fixture_store():
    store = MagicMock()
    store.configured.return_value = True
    store.projects.return_value = [{"id": "7", "name": "VAT"}, {"id": "8", "name": "Reporting"}]
    def get(key, default=None, profile_id=None):
        return {"webhook_url": "https://example.invalid/rest/1/secret/",
                "bitrix_user": {"ID": "1"}, "employee_name": "Employee",
                "ui_language": "ar" if profile_id == AR_PROFILE else "en"}.get(key, default)
    store.get.side_effect = get
    return store


def fixture_client():
    bx = MagicMock()
    bx.assigned_tasks.return_value = TASKS
    bx.project_members.return_value = [{"id": "1", "name": "Me"}, {"id": "2", "name": "Ahmed"}]
    return bx


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.store = fixture_store()
        self.bx = fixture_client()
        self.patches = [patch.object(application, "STORE", self.store),
                        patch.object(application, "client", return_value=self.bx)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        self.http = application.app.test_client()
        self.http.set_cookie(application.PROFILE_COOKIE, cookie(EN_PROFILE))

    def test_calendar_reads_all_assigned_tasks_and_riyadh_deadlines(self):
        response = self.http.get("/api/calendar")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.bx.assigned_tasks.assert_called_once_with("1", ["7", "8"], include_completed=True)
        self.assertEqual(len(data["tasks"]), 3)
        self.assertEqual(data["tasks"][0]["deadline"], "2026-10-11T01:30:00+03:00")
        self.assertEqual(data["tasks"][2]["status"], "5")
        self.assertEqual(data["members"], [{"id": "2", "name": "Ahmed"}])
        self.assertNotIn("secret", response.get_data(as_text=True))
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual([call[0] for call in self.bx.mock_calls], ["assigned_tasks", "project_members"])

    def test_page_renders_both_languages_and_isolates_browser_storage(self):
        english = self.http.get("/calendar").get_data(as_text=True)
        self.assertIn("Your tasks, your plan", english)
        self.assertNotIn("secret", english)
        self.http.set_cookie(application.PROFILE_COOKIE, cookie(AR_PROFILE))
        arabic = self.http.get("/calendar").get_data(as_text=True)
        self.assertIn('dir="rtl"', arabic)
        self.assertIn("مهامك وخطتك", arabic)
        import re
        self.assertNotEqual(re.search('data-scope="([^"]+)"', english)[1],
                            re.search('data-scope="([^"]+)"', arabic)[1])

    def test_no_projects_does_not_fetch_tasks(self):
        self.store.projects.return_value = []
        self.assertEqual(self.http.get("/api/calendar").get_json(), {"tasks": [], "members": []})
        self.bx.assigned_tasks.assert_not_called()

    def test_failure_redacts_webhook_and_does_not_return_partial_data(self):
        self.bx.project_members.side_effect = RuntimeError("https://portal/rest/1/secret/")
        response = self.http.get("/api/calendar")
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("secret", response.get_data(as_text=True))
        self.assertNotIn("tasks", response.get_json())

    def test_unconfigured_profile_uses_existing_connection_flow(self):
        self.store.configured.return_value = False
        response = self.http.get("/calendar")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Connect Bitrix to see your tasks", page)
        self.assertIn('href="/settings#bitrixIdentity"', page)
        self.assertNotIn('id="taskCalendar"', page)
        response = self.http.get("/api/calendar")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/settings#bitrixIdentity"))
        self.bx.assigned_tasks.assert_not_called()

    def test_no_calendar_write_endpoint(self):
        self.http.get("/calendar")
        with self.http.session_transaction() as session:
            csrf = session["csrf_token"]
        self.assertEqual(self.http.post("/api/calendar", json={"deadline": "2030-01-01"},
                                       headers={"X-CSRF-Token": csrf}).status_code, 405)
        self.bx.update_task.assert_not_called()

    def test_navigation_preserves_friend_features_and_security(self):
        page = self.http.get("/calendar").get_data(as_text=True)
        for path in ('href="/diwany"', 'href="/tasks"', 'href="/connections"', 'href="/calendar"'):
            self.assertIn(path, page)
        self.assertIn('name="csrf-token"', page)
        self.assertIn("/static/security.js", page)
        self.assertEqual(self.http.post("/api/calendar", json={}).status_code, 403)

    def test_scope_changes_when_profile_connection_or_employee_changes(self):
        import re
        def scope():
            return re.search('data-scope="([^"]+)"', self.http.get("/calendar").get_data(as_text=True))[1]
        original = scope()
        with patch.object(application, "current_user_id", return_value="9"):
            self.assertNotEqual(original, scope())
        original_get = self.store.get.side_effect
        self.store.get.side_effect = lambda key, default=None, profile_id=None: (
            "https://other.invalid/rest/1/private/" if key == "webhook_url" else original_get(key, default, profile_id))
        self.assertNotEqual(original, scope())

    def test_assigned_task_default_preserves_dashboard_scope(self):
        bx = BitrixClient("https://example.invalid/rest/1/secret/")
        with patch.object(bx, "_task_list_for_filter", return_value=[]) as listing:
            bx.assigned_tasks("1", ["7"])
            listing.assert_called_once_with(["7"], {"RESPONSIBLE_ID": 1}, include_completed=False)
            listing.reset_mock()
            bx.assigned_tasks("1", ["7"], include_completed=True)
            listing.assert_called_once_with(["7"], {"RESPONSIBLE_ID": 1}, include_completed=True)


if __name__ == "__main__":
    if "--export" in sys.argv:
        output = Path(sys.argv[sys.argv.index("--export") + 1])
        output.mkdir(parents=True, exist_ok=True)
        application.STORE = fixture_store()
        application.client = fixture_client
        with application.app.test_client() as http:
            import json
            (output / "cookies.json").write_text(json.dumps({"name": application.PROFILE_COOKIE,
                "en": cookie(EN_PROFILE), "ar": cookie(AR_PROFILE)}), encoding="utf-8")
            for profile, name in ((EN_PROFILE, "en"), (AR_PROFILE, "ar")):
                http.set_cookie(application.PROFILE_COOKIE, cookie(profile))
                (output / f"{name}.html").write_text(http.get("/calendar").get_data(as_text=True), encoding="utf-8")
            (output / "tasks.json").write_text(http.get("/api/calendar").get_data(as_text=True), encoding="utf-8")
    elif "--serve" in sys.argv:
        application.STORE = fixture_store()
        application.client = fixture_client
        application.app.run(host="127.0.0.1", port=5066, use_reloader=False)
    else:
        unittest.main()
