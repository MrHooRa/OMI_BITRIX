"""Offline coverage for the full Diwany JSON column catalog and token preview."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_diwany as fixtures
import diwan_columns
from diwany import DiwanError, normalize, validate_config
from history import connection_scope
from storage import ConfigStore


# Keep this list independent of the implementation: it is the user's JSON schema.
REQUESTED_COLUMNS = [
    "id", "platform", "isOwner", "requestId", "serviceName", "assignee",
    "businessServiceName", "itRequestId", "isCompleted", "isRead", "status",
    "daysRequested", "createdDate", "requestPendingOn", "isImportant",
    "takenActionId", "actionCode", "dueDate", "numberOfDays", "action",
    "escalationDueDate", "escalationNumberOfDays", "escelationAction",
    "task_details", "detail_status", "detail_service_name", "detail_created_date",
    "detail_completed*date", "FORM*نوع الطلب", "FORM*الوكالة", "FORM*القطاع",
    "FORM*الإدارة", "FORM*التاريخ", "FORM*منطقة العمل", "FORM*وصف منطقة العمل",
    "FORM*سبب الطلب", "FORM*تفاصيل الطلب",
    "FORM*هل يحتوي الطلب على تفاصيل معلومات المكلف؟", "FORM*المرفقات",
    "employee.id", "employee.personId", "employee.name", "employee.photo",
    "employee.email", "employee.department", "employee.position", "employee.domain",
    "request.requestId", "request.platform", "request.employee", "request.serviceName",
    "request.serviceImage", "request.displayServiceName", "request.itRequestId",
    "request.isCompleted", "request.status.id", "request.status.name",
    "request.status.nameEn", "request.status.nameAr", "request.status.statusCode",
    "request.status.statusColor", "request.formCode", "request.daysRequested",
    "request.createdDate", "request.modifiedDate", "request.requestPendingOn.name",
    "request.requestPendingOn.nameAr", "request.requestPendingOn.nameEn",
    "request.requestPendingOn.pendingOnCode", "request.isRequestAgain",
    "request.pageCode", "request.leaveRequestId",
]


class DisplayExtractionTests(unittest.TestCase):
    def test_catalog_contains_every_requested_json_column_without_duplicates(self):
        self.assertEqual(set(diwan_columns.JSON_COLUMNS), set(REQUESTED_COLUMNS))
        self.assertEqual(len(diwan_columns.JSON_COLUMNS), len(set(diwan_columns.JSON_COLUMNS)))
        self.assertGreaterEqual(diwan_columns.MAX_COLUMNS, len(REQUESTED_COLUMNS))

    def test_nested_json_and_literal_form_labels_have_requested_paths(self):
        record = normalize({
            "id": 81,
            "employee": {"id": 9, "name": "مها", "department": "المالية"},
            "request": {"status": {"id": 3, "nameAr": "قيد المعالجة"},
                        "requestPendingOn": {"nameEn": "Supervisor"}},
            "FORM*نوع الطلب": "طلب جديد",
            "FORM*تفاصيل الطلب": "<b>Preserve this as text</b>",
        }, validate_config(fixtures.CONFIG))
        expected = {
            "employee.id": "9", "employee.name": "مها",
            "employee.department": "المالية", "request.status.id": "3",
            "request.status.nameAr": "قيد المعالجة",
            "request.requestPendingOn.nameEn": "Supervisor",
            "FORM*نوع الطلب": "طلب جديد",
            "FORM*تفاصيل الطلب": "<b>Preserve this as text</b>",
        }
        for key, value in expected.items():
            with self.subTest(key=key):
                self.assertEqual(diwan_columns.value(record, "json:" + key), value)

    def test_view_form_controls_are_available_by_their_labels(self):
        record = normalize({"id": 81, "viewForm": {"controls": [
            {"id": "type", "label": "نوع الطلب", "value": "تعديل"},
            {"id": "reason", "label": "سبب الطلب", "value": "مراجعة"},
            {"id": "count", "label": "تفاصيل الطلب", "value": 0},
            {"id": "details", "label": "هل يحتوي الطلب على تفاصيل معلومات المكلف؟", "value": False},
        ]}}, validate_config(fixtures.CONFIG))
        self.assertEqual(diwan_columns.value(record, "json:FORM*نوع الطلب"), "تعديل")
        self.assertEqual(diwan_columns.value(record, "json:FORM*سبب الطلب"), "مراجعة")
        self.assertEqual(diwan_columns.value(record, "json:FORM*تفاصيل الطلب"), "0")
        self.assertEqual(diwan_columns.value(record, "json:FORM*هل يحتوي الطلب على تفاصيل معلومات المكلف؟"), "false")

    def test_completed_date_alias_and_false_zero_missing_values(self):
        record = normalize({"id": 81, "isOwner": False, "daysRequested": 0,
                            "dueDate": None, "detail_completed_date": "2026-10-10"},
                           validate_config(fixtures.CONFIG))
        self.assertEqual(diwan_columns.value(record, "json:detail_completed*date"), "2026-10-10")
        self.assertEqual(diwan_columns.value(record, "json:isOwner"), "false")
        self.assertEqual(diwan_columns.value(record, "json:daysRequested"), "0")
        self.assertEqual(diwan_columns.value(record, "json:dueDate"), "")
        self.assertEqual(diwan_columns.value(record, "json:employee.photo"), "")
        self.assertIs(record["completed"], False)

    def test_compound_column_values_are_json_without_nested_credentials(self):
        raw = {
            "id": 81,
            "status": {"id": 2, "nameAr": "مفتوحة", "accessToken": "hidden-one",
                       "metadata": {"password": "hidden-two", "code": 0}},
            "request": {"employee": {"name": "منى", "authorization": "hidden-three"}},
            "task_details": [{"name": "مهمة", "isCompleted": False,
                              "credentials": {"apiKey": "hidden-four", "department": "Tax"}}],
        }
        record = normalize(raw, validate_config(fixtures.CONFIG))
        status = json.loads(diwan_columns.value(record, "json:status"))
        self.assertEqual(status, {"id": 2, "nameAr": "مفتوحة", "metadata": {"code": 0}})
        employee = json.loads(diwan_columns.value(record, "json:request.employee"))
        self.assertEqual(employee, {"name": "منى"})
        details = json.loads(diwan_columns.value(record, "json:task_details"))
        self.assertEqual(details, [{"name": "مهمة", "isCompleted": False,
                                    "credentials": {"department": "Tax"}}])
        self.assertNotIn("hidden-", json.dumps(record["display_fields"]))


class CatalogRouteTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post
    connect = fixtures.AppTests.connect

    def test_catalog_available_without_token_or_history_and_without_network(self):
        with patch("diwany.DiwanClient.list_page", side_effect=AssertionError("No token or fetch needed")):
            response = self.a.get("/api/diwany/columns")
        self.assertEqual(response.status_code, 200)
        available = [column["key"] for column in response.json["available"]]
        missing = sorted({"json:" + name for name in REQUESTED_COLUMNS} - set(available))
        self.assertEqual(missing, [])
        self.assertEqual(len(available), len(set(available)))
        self.assertTrue(all("task:" + name in available for name, _ in diwan_columns.BUILTINS))
        self.assertFalse(fixtures.main.app.extensions["diwan_vault"].present(self.pid(self.a)))

    def test_all_columns_can_be_selected_and_persisted_for_only_this_profile(self):
        selected = [{"key": "json:" + name, "label": name} for name in REQUESTED_COLUMNS]
        self.assertGreater(len(selected), 20)
        response = self.post(self.a, "/api/diwany/columns", {"columns": selected})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(self.a.get("/api/diwany/columns").json["selected"], selected)
        reopened = ConfigStore(Path(self.directory.name) / "test.sqlite3")
        self.assertEqual(reopened.get("diwan_columns", profile_id=self.pid(self.a)), selected)
        self.assertNotEqual(self.b.get("/api/diwany/columns").json["selected"], selected)
        self.assertIsNone(reopened.get("diwan_columns", profile_id=self.pid(self.b)))

    def test_task_list_renders_full_selection_in_order_with_blank_missing_values(self):
        self.connect(self.a)
        selected = [{"key": "json:" + name, "label": name} for name in REQUESTED_COLUMNS]
        self.assertEqual(self.post(self.a, "/api/diwany/columns", {"columns": selected}).status_code, 200)
        pid = self.pid(self.a)
        history = fixtures.main.app.extensions["diwan_history"]
        history.bind_scope(pid, "diwan", connection_scope(fixtures.main.STORE, pid, "diwan"))
        record = normalize({"id": 81, "isOwner": False, "daysRequested": 0,
                            "employee": {"name": "مها"}}, validate_config(fixtures.CONFIG))
        with history.lock:
            history._state(pid)["sources"]["diwan"] = {"records": [record], "complete": True}
        response = self.a.get("/api/diwany/tasks")
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json["columns"], selected)
        values = response.json["records"][0]["display_values"]
        self.assertEqual(len(values), len(REQUESTED_COLUMNS))
        by_name = dict(zip(REQUESTED_COLUMNS, values))
        self.assertEqual(by_name["id"], "81")
        self.assertEqual(by_name["isOwner"], "false")
        self.assertEqual(by_name["daysRequested"], "0")
        self.assertEqual(by_name["employee.name"], "مها")
        self.assertEqual(by_name["employee.email"], "")
        self.assertNotIn("display_fields", response.json["records"][0])

    def test_token_validation_discovers_only_column_names_without_saving_task_preview(self):
        self.assertEqual(self.post(self.a, "/api/diwany/config", fixtures.CONFIG).status_code, 200)
        preview = {"id": "private-task-81", "privateExtra": {"name": "private-task-description"},
                   "employee": {"name": "private-person-name"}, "token": "private-source-secret"}
        with patch("diwany.DiwanClient.list_page", return_value=[preview]) as fetch:
            response = self.post(self.a, "/api/diwany/token", {"token": "column-preview-token"})
            self.assertEqual(response.status_code, 200, response.json)
            catalog = self.a.get("/api/diwany/columns").json
        self.assertEqual(fetch.call_count, 1)
        fetch.assert_called_once_with(page_size=1)
        available = {column["key"] for column in catalog["available"]}
        self.assertIn("json:privateExtra.name", available)
        self.assertNotIn("json:token", available)
        metadata = fixtures.main.STORE.get("diwan_discovered_columns", [], profile_id=self.pid(self.a))
        self.assertIn("privateExtra.name", metadata)
        self.assertTrue(all(isinstance(name, str) for name in metadata))
        self.assertNotIn("private-task-description", json.dumps(metadata))
        self.assertNotIn("private-person-name", json.dumps(metadata))
        history = fixtures.main.app.extensions["diwan_history"]
        for source in ("diwan", "diwan_analysis"):
            self.assertEqual(history.source(self.pid(self.a), source)["records"], [])
        other = {column["key"] for column in self.b.get("/api/diwany/columns").json["available"]}
        self.assertNotIn("json:privateExtra.name", other)

    def test_replacement_token_replaces_preview_columns_and_retains_user_selection(self):
        self.assertEqual(self.post(self.a, "/api/diwany/config", fixtures.CONFIG).status_code, 200)
        selected = [{"key": "json:employee.name", "label": "Employee"}]
        self.assertEqual(self.post(self.a, "/api/diwany/columns", {"columns": selected}).status_code, 200)
        with patch("diwany.DiwanClient.list_page", return_value=[{"id": 1, "oldPrivateField": "value"}]):
            self.assertEqual(self.post(self.a, "/api/diwany/token", {"token": "first-token"}).status_code, 200)
        with patch("diwany.DiwanClient.list_page", return_value=[{"id": 2, "newPrivateField": "value"}]):
            self.assertEqual(self.post(self.a, "/api/diwany/token", {"token": "second-token"}).status_code, 200)
        result = self.a.get("/api/diwany/columns").json
        keys = {column["key"] for column in result["available"]}
        self.assertIn("json:newPrivateField", keys)
        self.assertNotIn("json:oldPrivateField", keys)
        self.assertEqual(result["selected"], selected)

    def test_failed_token_validation_preserves_previous_column_metadata_and_token(self):
        self.assertEqual(self.post(self.a, "/api/diwany/config", fixtures.CONFIG).status_code, 200)
        with patch("diwany.DiwanClient.list_page", return_value=[{"id": 1, "privateField": "value"}]):
            self.assertEqual(self.post(self.a, "/api/diwany/token", {"token": "good-token"}).status_code, 200)
        pid = self.pid(self.a)
        previous = fixtures.main.STORE.get("diwan_discovered_columns", [], profile_id=pid)
        with patch("diwany.DiwanClient.list_page", side_effect=DiwanError("token_invalid", 401)):
            response = self.post(self.a, "/api/diwany/token", {"token": "invalid-token"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(fixtures.main.app.extensions["diwan_vault"].get(pid), "good-token")
        self.assertEqual(fixtures.main.STORE.get("diwan_discovered_columns", [], profile_id=pid), previous)

    def test_configuration_change_discards_stale_preview_columns(self):
        self.assertEqual(self.post(self.a, "/api/diwany/config", fixtures.CONFIG).status_code, 200)
        with patch("diwany.DiwanClient.list_page", return_value=[{"id": 1, "privateField": "value"}]):
            self.assertEqual(self.post(self.a, "/api/diwany/token", {"token": "good-token"}).status_code, 200)
        candidate = {**fixtures.CONFIG, "detail_url": "https://diwan.internal/other/{task_id}"}
        self.assertEqual(self.post(self.a, "/api/diwany/config", candidate).status_code, 200)
        keys = {column["key"] for column in self.a.get("/api/diwany/columns").json["available"]}
        self.assertNotIn("json:privateField", keys)

    def test_credential_columns_rejected_without_replacing_valid_selection(self):
        selected = [{"key": "json:id", "label": "ID"}]
        self.assertEqual(self.post(self.a, "/api/diwany/columns", {"columns": selected}).status_code, 200)
        for key in ("json:employee.accessToken", "json:request.password", "json:authorization"):
            with self.subTest(key=key):
                response = self.post(self.a, "/api/diwany/columns", {"columns": [{"key": key}]})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.a.get("/api/diwany/columns").json["selected"], selected)


if __name__ == "__main__":
    unittest.main()
