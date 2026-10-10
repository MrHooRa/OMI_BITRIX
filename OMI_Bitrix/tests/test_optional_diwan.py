"""Optional Diwany credentials must never gate the Bitrix workspace."""
import unittest
from unittest.mock import patch

import test_diwany as fixtures
from i18n import get_text


class OptionalDiwanTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post

    def configure_bitrix(self):
        pid = self.pid(self.a)
        fixtures.main.STORE.set_many({
            "webhook_url": "https://bitrix.internal/rest/1/test/",
            "vault_root": self.directory.name,
            "employee_name": "Employee",
            "bitrix_user": {"ID": "1", "NAME": "Employee"},
        }, profile_id=pid)
        fixtures.main.STORE.replace_projects([{"id": "1", "name": "Project"}], profile_id=pid)
        self.addCleanup(fixtures.main.TASK_CACHES.pop, pid, None)
        return pid

    def test_fresh_my_tasks_stays_accessible_without_either_connection(self):
        with patch.object(fixtures.main, "sync_tasks", side_effect=AssertionError("No Bitrix sync before setup")):
            response = self.a.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn(get_text("en", "my_work"), page)
        self.assertIn(get_text("en", "cal_connect"), page)
        self.assertIn('href="/settings#bitrixIdentity"', page)
        self.assertNotIn('id="todayPlanner"', page)
        self.assertNotIn('action="/sync"', page)
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(self.pid(self.a)))

    def test_incomplete_configuration_does_not_display_previous_cached_tasks(self):
        pid = self.pid(self.a)
        cached = fixtures.main.empty_cache()
        cached.update(updated_at="2026-10-10T09:00:00+03:00", assigned=[{"title": "Stale private task"}])
        fixtures.main.TASK_CACHES[pid] = cached
        self.addCleanup(fixtures.main.TASK_CACHES.pop, pid, None)
        with patch.object(fixtures.main, "sync_tasks", side_effect=AssertionError("No sync")):
            page = self.a.get("/").get_data(as_text=True)
        self.assertNotIn("Stale private task", page)
        self.assertNotIn('id="todayPlanner"', page)

    def test_configured_bitrix_my_tasks_works_without_diwan_token(self):
        pid = self.configure_bitrix()
        task = {"id": "81", "title": "Bitrix-only task", "projectName": "Project",
                "status": "2", "priority": "0", "deadline": "", "dueBucket": "no-deadline",
                "workspaceEmployee": "Employee", "readiness": 0,
                "hasDelayJustification": False, "justificationRequired": False}
        cache = fixtures.main.empty_cache()
        cache.update(updated_at="2026-10-10T09:00:00+03:00", assigned=[task])
        fixtures.main.TASK_CACHES[pid] = cache
        with patch.object(fixtures.main, "sync_tasks", side_effect=AssertionError("Reuse current cache")), \
             patch("diwany.DiwanClient.list_page", side_effect=AssertionError("No Diwany request")):
            response = self.a.get("/")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("Bitrix-only task", page)
        self.assertIn('id="todayPlanner"', page)
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(pid))

    def test_configured_bitrix_can_sync_without_diwan_token(self):
        pid = self.configure_bitrix()
        cache = fixtures.main.empty_cache()
        cache["updated_at"] = "2026-10-10T09:00:00+03:00"
        with patch.object(fixtures.main, "sync_tasks", return_value=cache) as sync:
            response = self.a.get("/")
        self.assertEqual(response.status_code, 200)
        sync.assert_called_once_with(create_missing=True)
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(pid))

    def test_bitrix_protected_api_routes_point_to_bitrix_settings(self):
        for url in ("/api/calendar", "/api/task/81/comments", "/supervisor/report.xlsx"):
            with self.subTest(url=url):
                response = self.a.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.location.endswith("/settings#bitrixIdentity"))
                self.assertNotIn("diwany", response.location)

    def test_all_navigation_pages_are_accessible_without_any_connection(self):
        with patch.object(fixtures.main, "sync_tasks", side_effect=AssertionError("No Bitrix sync before setup")), \
             patch.object(fixtures.main, "client", side_effect=AssertionError("No live Bitrix client before setup")):
            for url in ("/", "/supervisor", "/search", "/calendar", "/tasks", "/diwany", "/connections", "/settings", "/task/81"):
                with self.subTest(url=url):
                    response = self.a.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('href="/"', response.get_data(as_text=True))
        for url in ("/supervisor", "/search", "/task/81"):
            with self.subTest(url=url):
                page = self.a.get(url).get_data(as_text=True)
                self.assertIn(get_text("en", "cal_connect"), page)
                self.assertIn('href="/settings#bitrixIdentity"', page)

    def test_configured_bitrix_navigation_works_without_diwan_token(self):
        pid = self.configure_bitrix()
        cache = fixtures.main.empty_cache()
        cache["updated_at"] = "2026-10-10T09:00:00+03:00"
        fixtures.main.TASK_CACHES[pid] = cache
        with patch.object(fixtures.main, "sync_tasks", side_effect=AssertionError("Reuse current cache")), \
             patch("diwany.DiwanClient.list_page", side_effect=AssertionError("No Diwany request")):
            for url in ("/", "/supervisor", "/search", "/calendar", "/tasks", "/diwany", "/connections", "/settings"):
                with self.subTest(url=url):
                    self.assertEqual(self.a.get(url).status_code, 200)
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(pid))

    def test_unconfigured_bitrix_mutations_still_require_configuration_and_csrf(self):
        self.assertEqual(self.a.post("/sync").status_code, 403)
        response = self.post(self.a, "/sync", {})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/settings#bitrixIdentity"))
        response = self.post(self.a, "/task/81/start", {})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/settings#bitrixIdentity"))

    def test_diwan_and_similarity_pages_remain_accessible_without_token(self):
        for url in ("/diwany", "/tasks", "/connections"):
            with self.subTest(url=url):
                self.assertEqual(self.a.get(url).status_code, 200)
        page = self.a.get("/diwany").get_data(as_text=True)
        self.assertIn(get_text("en", "d_diwan_optional_help"), page)
        self.assertIn('href="/"', page)
        self.assertEqual(self.a.get("/api/diwany/tasks").get_json()["total"], 0)
        response = self.post(self.a, "/api/diwany/sync", {})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["code"], "token_required")


if __name__ == "__main__":
    unittest.main()
