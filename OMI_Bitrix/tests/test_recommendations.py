import copy
import tempfile
import time
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

import test_diwany as fixtures
main = fixtures.main
from history import History, bitrix_record
from recommendation_service import RecommendationService, DecisionJournal
from recommendations import rank, assignment_state, validate_policy
from sla import TZ


def record(ident, employee="1", completed=False):
    return {"source": "bitrix", "id": str(ident), "title": "supplier invoice reconciliation",
            "description": "supplier invoice VAT purchase reconciliation", "project_id": "1",
            "category": "Finance", "assignee_id": employee, "assignee_name": "Employee " + employee,
            "creator_id": "1", "completed": completed, "status": "5" if completed else "2",
            "created_at": "2025-01-01T08:00:00+03:00", "completed_at": "2025-01-02T08:00:00+03:00" if completed else None,
            "deadline": "2025-01-03T08:00:00+03:00", "priority": 0}


def employee(ident="1", **kwargs):
    return {"id": ident, "name": "Employee " + ident, "enabled": True, "active": True,
            "projects": ["1"], "categories": [], "capacity": 10, **kwargs}


class RankingTests(unittest.TestCase):
    def test_normal_priority_does_not_inflate_workload(self):
        rows = [{**record(1), "priority": 1}, {**record(2), "priority": 2}]
        result = rank(record(99), rows, [employee()])
        self.assertEqual(result["provisional"][0]["priority_load"], 2.5)
        self.assertEqual(result["provisional"][0]["components"]["capacity"], 8.57)

    def test_cold_start_does_not_invent_experience(self):
        result = rank(record(99), [], [employee()])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["provisional"], [])
        self.assertEqual(result["outcome"], "insufficient_evidence")
        self.assertIsNone(result["available"][0]["score"])
        self.assertEqual(result["available"][0]["components"]["experience"], 0)

    def test_relevant_history_and_workload_explain_score(self):
        rows = [record(i, completed=True) for i in range(3)] + [record(20, "2")]
        result = rank(record(99), rows, [employee(), employee("2")])
        best = result["candidates"][0]
        self.assertEqual(best["id"], "1")
        self.assertEqual(best["similar_completed"], 3)
        self.assertAlmostEqual(best["score"], sum(best["components"].values()), places=2)
        self.assertEqual(len(best["examples"]), 3)

    def test_eligibility_absence_capacity_and_inactive_are_hard_filters(self):
        people = [employee("1", enabled=False), employee("2", active=False), employee("3", projects=["2"]),
                  employee("4", categories=["Network"]), employee("5", away_from="2020-01-01", away_to="2099-01-01"), employee("6", capacity=1)]
        result = rank(record(99), [record(10, "6")], people)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(len(result["excluded"]), 5)
        self.assertIn("6", result["eligible_ids"])

    def test_only_past_completions_and_not_target_count(self):
        future = record(1, completed=True); future["completed_at"] = "2030-01-02T08:00:00+03:00"
        target = record(99, completed=True)
        result = rank(target, [target, future], [employee()], at=datetime(2026, 1, 1, tzinfo=TZ))
        self.assertEqual(result["completed_records"], 0)
        self.assertEqual(result["available"][0]["similar_completed"], 0)

    def test_creator_and_waiting_status_do_not_mean_unassigned(self):
        task = record(1)
        self.assertEqual(assignment_state(task, {}), "needs_assignment")
        self.assertEqual(assignment_state(task, {"intake_ids": ["1"]}), "needs_assignment")
        previous = {"decision": {"kind": "self", "actor": "1", "expected_assignee": "1", "expected_creator": "1"}}
        self.assertEqual(assignment_state(task, {"intake_ids": ["1"]}, previous), "self_assigned")
        self.assertEqual(assignment_state({**task, "assignee_id": "2"}, {"intake_ids": ["2"]}, previous), "assigned")

    def test_payroll_query_uses_related_open_work_not_free_unrelated_employees(self):
        query = {**record(99), "title": "تحليل واستخراح تقرير لمراجعة رواتب الموظفين لأخر 3 شهور", "description": ""}
        payroll = {**record(1, "2"), "title": "مراجعة رواتب الموظفين لشهر سبتمبر [OMI-SIM-20261003]",
                   "description": "مراجعة رواتب الموظفين والبدلات والاستقطاعات ومطابقة كشف الرواتب لشهر أكتوبر.\nSynthetic similarity test only; no real work required."}
        network = {**record(2, "1"), "title": "مراجعة تقرير شبكة الموظفين", "description": ""}
        result = rank(query, [payroll, network], [employee(), employee("2"), employee("3")])
        self.assertEqual(result["candidates"], [])
        self.assertEqual([r["id"] for r in result["provisional"]], ["2"])
        self.assertIn("رواتب", result["provisional"][0]["examples"][0]["shared_terms"])
        self.assertIsNone(result["provisional"][0]["score"])
        self.assertEqual({r["id"] for r in result["available"]}, {"1", "3"})

    def test_completed_payroll_evidence_beats_unrelated_spare_capacity(self):
        query = {**record(99), "title": "تحليل واستخراج تقرير لمراجعة رواتب الموظفين لآخر 3 شهور", "description": ""}
        payroll = {**record(1, "2", True), "title": "مراجعة الرواتب", "description": ""}
        network = {**record(2, "1", True), "title": "مراجعة تقرير الشبكة", "description": ""}
        result = rank(query, [payroll, network], [employee(), employee("2"), employee("3")])
        self.assertEqual([r["id"] for r in result["candidates"]], ["2"])
        self.assertEqual(result["candidates"][0]["similar_completed"], 1)

    def test_shared_synthetic_note_cannot_create_relevance(self):
        note = "Synthetic similarity test only; no real work required."
        query = {**record(99), "title": "مراجعة رواتب الموظفين", "description": note}
        unrelated = {**record(1), "description": note}
        result = rank(query, [unrelated], [employee()])
        self.assertEqual(result["provisional"], [])

    def test_matching_unconfirmed_employee_is_explained_but_not_assignable(self):
        result = rank(record(99), [record(1)], [employee(enabled=False)])
        self.assertEqual(result["eligible_ids"], [])
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["provisional"], [])
        self.assertEqual(result["related_excluded"][0]["id"], "1")
        self.assertIn("eligibility_unconfirmed", result["related_excluded"][0]["reasons"])

    def test_unrelated_and_generic_queries_abstain(self):
        for text in ("تحليل واستخراج تقرير", "دراسة الزراعة والري", "astronomy telescope orbit"):
            query = {**record(99), "title": text, "description": ""}
            result = rank(query, [record(1, completed=True), record(2)], [employee()])
            self.assertEqual(result["candidates"], [], text)
            self.assertEqual(result["provisional"], [], text)

    def test_awaiting_supervisor_task_is_not_employee_exposure(self):
        result = rank(record(99), [{**record(1), "awaiting_executor": True}], [employee()])
        self.assertEqual(result["provisional"], [])
        self.assertEqual(result["available"][0]["active_tasks"], 0)

    def test_open_target_does_not_recommend_its_own_assignee(self):
        result = rank(record(99), [record(99)], [employee()])
        self.assertEqual(result["provisional"], [])

    def test_assigning_another_supervisor_requires_their_self_claim(self):
        task = record(1)
        previous = {"decision": {"kind": "assigned", "actor": "2", "expected_assignee": "1"}}
        self.assertEqual(assignment_state(task, {"intake_ids": ["1"]}, previous), "needs_assignment")

    def test_no_task_limit_and_pressure_is_soft(self):
        records = [record(1000+i, "1") for i in range(150)] + [record(2, "1", True), record(3, "2", True)]
        result = rank(record(99), records, [employee("1", capacity=1), employee("2")])
        self.assertIn("1", result["eligible_ids"])
        self.assertEqual(result["candidates"][0]["id"], "2")
        self.assertNotIn("capacity", result["candidates"][0])
        self.assertEqual(result["excluded"], [])

    def test_shared_ticket_cannot_make_unrelated_work_similar(self):
        from task_intelligence import TaskIndex
        rows = [{**record(1), "title":"مراجعة الرواتب [REQ-445566]", "description":"Synthetic similarity test only; no real work required."},
                {**record(2), "title":"اصلاح الشبكة [REQ-445566]", "description":"Synthetic similarity test only; no real work required."}]
        index = TaskIndex(rows)
        self.assertEqual([m["task"]["id"] for m in index.related('مراجعة الرواتب [REQ-445566]')], ["1"])
        self.assertEqual(index.related('[REQ-445566]'), [])

    def test_duplicate_content_retains_distinct_ids_and_assignees(self):
        from recommendation_matching import group_related
        rows = [{"task":record(13,"1"),"score":90}, {"task":record(31,"2"),"score":90}]
        groups = group_related(rows)
        self.assertEqual(len(groups), 1)
        self.assertEqual([r["id"] for r in groups[0]["duplicate_tasks"]], ["13","31"])

    def test_invalid_weight_and_duplicate_directory_rejected(self):
        with self.assertRaises(ValueError): validate_policy({"weights": {"similarity": 99}})
        with self.assertRaises(ValueError): validate_policy({"employees": [employee(), employee()]})

    def test_absent_deadlines_are_not_scored_as_failure(self):
        row = record(1, completed=True); row["deadline"] = None
        result = rank(record(99), [row], [employee()])
        self.assertEqual(result["candidates"][0]["observed_deadline_results"]["samples"], 0)


class RecommendationFlowTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    post = fixtures.AppTests.post
    pid = fixtures.AppTests.pid

    def prepare(self, needs=False):
        self.profile = self.pid(self.a)
        main.STORE.set_many({"webhook_url": "https://bitrix.internal/rest/1/test/", "bitrix_user": {"ID": "1"},
                            "recommendation_policy": validate_policy({"employees": [employee(), employee("11")],
                              "intake_ids": ["1"] if needs else [], "supervisor_ids": ["1"]})}, profile_id=self.profile)
        main.STORE.replace_projects([{"id": "1", "name": "Test"}], profile_id=self.profile)
        self.service = main.app.extensions["recommendations"]
        self.api = Mock()
        self.api.project_members.return_value = [{"id": "1", "name": "Employee 1", "projects": ["1"], "roles": {"1": "A"}}]
        self.api._call_raw.return_value = {"result": [{"ID": "1", "ACTIVE": True}]}
        self.api.current_user.return_value = {"ID": "1"}
        self.api.task_access.return_value = {"EDIT": True}
        self.raw = {"id": "99", "title": "supplier invoice reconciliation", "description": "supplier invoice VAT purchase reconciliation",
                    "responsibleId": "1", "createdBy": "1", "groupId": "1", "status": "2", "tags": ["Finance"]}
        self.api.task_get.side_effect = lambda *args: dict(self.raw)
        self.api.reassign_task.side_effect = lambda ident, target: self.raw.update(responsibleId=target)
        for location in ("recommendation_service.BitrixClient", "recommendation_routes.BitrixClient"):
            mocked = patch(location, return_value=self.api); mocked.start(); self.addCleanup(mocked.stop)
        pages = patch("recommendation_service.bitrix_pages", side_effect=lambda *args, **kwargs: iter([(1, [bitrix_record(self.raw)])]))
        pages.start(); self.addCleanup(pages.stop)
        history = main.app.extensions["diwan_history"]
        job = history.start(self.profile, "bitrix", lambda _: iter([(1, [record(i, completed=True) for i in range(3)])]))
        for _ in range(200):
            if history.job(self.profile, job)["status"] != "running": break
            time.sleep(.005)
        self.service.refresh(self.profile, force=True)

    def test_project_supervisor_is_detected_without_manual_intake_configuration(self):
        self.prepare(needs=False)
        data = self.service.snapshot(self.profile)
        self.assertEqual(data["policy"]["intake_ids"], [])
        self.assertEqual(data["tasks"][0]["state"], "needs_assignment")
        self.assertEqual(data["unread"], 1)
        self.assertEqual(data["detected_supervisors"][0]["id"], "1")
        self.api.reassign_task.assert_not_called()

    def test_supervisor_roles_are_project_scoped_and_moderators_count(self):
        self.prepare()
        context = self.service.context(self.profile)
        state = self.service._state(context)
        state["members"] = [{"id": "11", "name": "Moderator", "roles": {"2": "E"}, "projects": ["2"]}]
        self.assertEqual(self.service.task_policy(context, state, {"project_id": "1"})["intake_ids"], [])
        self.assertEqual(assignment_state({**record(53), "creator_id": "15", "assignee_id": "11"}, {}), "assigned")

    def test_creator_assignee_is_queued_without_project_manager_role(self):
        self.prepare()
        self.raw.update(createdBy="11", responsibleId="11")
        self.api.current_user.return_value = {"ID": "11"}
        main.STORE.set("bitrix_user", {"ID": "11"}, profile_id=self.profile)
        self.service.refresh(self.profile, force=True)
        data = self.service.snapshot(self.profile)
        self.assertEqual(data["unread"], 1)
        self.assertEqual(data["tasks"][0]["state"], "needs_assignment")

    def test_assignee_only_cannot_see_queue_or_mutate_even_with_source_edit_right(self):
        self.prepare()
        self.raw.update(createdBy="11", responsibleId="1", auditors=[])
        self.service.refresh(self.profile, force=True)
        data = self.service.snapshot(self.profile)
        self.assertEqual(data["tasks"], [])
        self.assertEqual(data["notifications"], [])
        for route, payload in [("rank", {"task_id": "99"}), ("tasks/99/assign", {"confirmed": True, "employee_id": "11", "expected_assignee": "1"}),
                               ("tasks/99/needs-assignment", {}), ("tasks/99/self", {}), ("tasks/99/verify", {})]:
            response = self.post(self.a, "/api/recommendations/" + route, payload)
            self.assertEqual(response.status_code, 403, route)
        self.api.reassign_task.assert_not_called()

    def test_live_owner_change_blocks_cached_owner_before_next_poll(self):
        self.prepare()
        self.raw.update(createdBy="11", responsibleId="1")
        response = self.post(self.a, "/api/recommendations/tasks/99/assign", {"confirmed":True,"employee_id":"11","expected_assignee":"1"})
        self.assertEqual(response.status_code, 403)
        self.api.reassign_task.assert_not_called()

    def test_owner_change_invalidates_previous_self_claim(self):
        self.prepare()
        self.post(self.a, "/api/recommendations/tasks/99/self", {})
        self.raw.update(createdBy="11", responsibleId="11")
        main.STORE.set("bitrix_user", {"ID":"11"}, profile_id=self.profile)
        self.service.refresh(self.profile, force=True)
        self.assertEqual(self.service.snapshot(self.profile)["tasks"][0]["state"], "needs_assignment")

    def test_legacy_page_redirects_to_unified_assignment_tab(self):
        response = self.a.get('/recommendations?task=53')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/tasks?', response.location)
        self.assertIn('view=assignments', response.location)
        self.assertIn('task=53', response.location)

    def test_known_inactive_user_cannot_be_enabled_by_policy(self):
        self.prepare()
        context = self.service.context(self.profile)
        state = self.service._state(context)
        state["user_status"] = {"11": False}
        result = self.service.recommend(self.profile, "99")
        excluded = next(row for row in result["excluded"] if row["id"] == "11")
        self.assertIn("inactive", excluded["reasons"])

    def test_open_task_poll_interval_is_one_minute(self):
        self.prepare()
        state = self.service._state(self.service.context(self.profile))
        clock = [1000]
        self.service.clock = lambda: clock[0]
        state["next"] = 0
        self.service.refresh(self.profile)
        calls = self.api.project_members.call_count
        checked = state["checked_epoch"]
        clock[0] += 59
        self.service.refresh(self.profile)
        self.assertEqual(state["checked_epoch"], checked)
        clock[0] += 1
        self.service.refresh(self.profile)
        self.assertEqual(state["checked_epoch"], 1060)

    def test_rank_and_inbox_are_profile_scoped(self):
        self.prepare(needs=True)
        a = self.a.get("/api/recommendations").get_json()
        self.assertEqual(a["unread"], 1)
        self.assertEqual(self.b.get("/api/recommendations").get_json()["notifications"], [])
        result = self.post(self.a, "/api/recommendations/rank", {"task_id": "99"}).get_json()
        self.assertEqual(result["result"]["candidates"][0]["id"], "1")
        self.assertEqual(result["result"]["candidates"][0]["similar_completed"], 3)

    def test_read_deduplicates_and_survives_service_restart(self):
        self.prepare(needs=True)
        self.post(self.a, "/api/recommendations/tasks/99/read", {})
        self.service.refresh(self.profile, force=True)
        self.assertEqual(self.service.snapshot(self.profile)["unread"], 0)
        replacement = RecommendationService(main.STORE, main.app.extensions["diwan_history"], self.service.journal.root, automatic_suggestions=False)
        replacement.refresh(self.profile, force=True)
        self.assertEqual(replacement.snapshot(self.profile)["unread"], 0)

    def test_supervisor_self_claim_stops_notifications(self):
        self.prepare(needs=True)
        response = self.post(self.a, "/api/recommendations/tasks/99/self", {})
        self.assertEqual(response.status_code, 200)
        self.service.refresh(self.profile, force=True)
        self.assertEqual(self.service.snapshot(self.profile)["notifications"], [])
        self.api.reassign_task.assert_not_called()

    def test_mark_needs_assignment_creates_alert_without_remote_mutation(self):
        self.prepare()
        response = self.post(self.a, "/api/recommendations/tasks/99/needs-assignment", {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.service.snapshot(self.profile)["unread"], 1)
        self.api.reassign_task.assert_not_called()

    def test_explicit_assignment_records_decision_and_readback(self):
        self.prepare(needs=True)
        response = self.post(self.a, "/api/recommendations/tasks/99/assign", {"confirmed": True, "employee_id": "11", "expected_assignee": "1", "reason": "capacity"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.raw["responsibleId"], "11")
        self.assertEqual(self.service.snapshot(self.profile)["unread"], 0)
        journal = self.service.journal.read(self.service.context(self.profile)["key"])
        self.assertEqual(journal["tasks"]["99"]["decision"]["kind"], "assigned")
        self.assertEqual(self.service.operation(self.profile, "99")["status"], "confirmed")

    def test_permission_and_assignee_change_block_mutation(self):
        self.prepare()
        self.api.task_access.return_value = {"EDIT": False}
        response = self.post(self.a, "/api/recommendations/tasks/99/assign", {"confirmed": True, "employee_id": "11", "expected_assignee": "1"})
        self.assertEqual(response.status_code, 403)
        self.api.task_access.return_value = {"EDIT": True}
        response = self.post(self.a, "/api/recommendations/tasks/99/assign", {"confirmed": True, "employee_id": "11", "expected_assignee": "7"})
        self.assertEqual(response.status_code, 409)
        self.api.reassign_task.assert_not_called()

    def test_uncertain_outcome_blocks_retry_until_verified(self):
        self.prepare()
        self.api.reassign_task.side_effect = TimeoutError("timeout")
        payload = {"confirmed": True, "employee_id": "11", "expected_assignee": "1"}
        self.assertEqual(self.post(self.a, "/api/recommendations/tasks/99/assign", payload).status_code, 409)
        self.assertEqual(self.post(self.a, "/api/recommendations/tasks/99/assign", payload).status_code, 400)
        self.assertEqual(self.api.reassign_task.call_count, 1)
        self.raw["responsibleId"] = "11"
        self.assertEqual(self.post(self.a, "/api/recommendations/tasks/99/verify", {}).status_code, 200)

    def test_source_switch_does_not_show_old_journal(self):
        self.prepare(needs=True)
        main.STORE.set("webhook_url", "https://other.internal/rest/1/test/", profile_id=self.profile)
        self.assertEqual(self.service.snapshot(self.profile)["notifications"], [])

    def test_workload_older_than_two_minutes_blocks_assignment(self):
        self.prepare()
        state = self.service._state(self.service.context(self.profile))
        state["checked_epoch"] = self.service.clock() - 121
        response = self.post(self.a, "/api/recommendations/tasks/99/assign", {"confirmed": True, "employee_id": "11", "expected_assignee": "1"})
        self.assertEqual(response.status_code, 400)
        self.api.reassign_task.assert_not_called()


class CorrectnessRegressionTests(unittest.TestCase):
    def test_preview_preserves_target_exclusion(self):
        row = record(31, completed=True)
        result = rank({**row, "description": "", "title": row["title"]}, [row], [employee()])
        self.assertEqual(result["candidates"], [])

    def test_technical_terms_survive_and_payroll_aliases_match(self):
        from recommendation_matching import terms
        self.assertTrue({"ai", "bi", "ipv6"} <= terms("AI Power BI IPv6 [OMI-SIM-20261003]"))
        self.assertTrue(terms("رواتب") & terms("الأجور") & terms("payroll"))
        self.assertNotIn("20261003", terms("[OMI-SIM-20261003]"))


class SharedDecisionTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post
    prepare = RecommendationFlowTests.prepare
    def test_self_claim_visible_across_profiles_same_portal(self):
        self.prepare()
        other = self.pid(self.b)
        main.STORE.set_many({"webhook_url":"https://bitrix.internal/rest/11/other/", "bitrix_user":{"ID":"11"}},profile_id=other)
        main.STORE.replace_projects([{"id":"1","name":"Test"}],profile_id=other)
        self.raw["auditors"] = ["11"]
        self.service.refresh(self.profile,force=True)
        self.service.refresh(other,force=True)
        self.assertEqual(self.service.snapshot(other)["tasks"][0]["state"],"needs_assignment")
        self.service.decision(self.profile,bitrix_record(self.raw),"self","1")
        self.assertEqual(self.service.snapshot(other)["tasks"][0]["state"],"self_assigned")
        self.assertEqual(self.service.snapshot(other)["notifications"],[])

    def test_source_portals_do_not_share_decisions(self):
        self.prepare()
        before=self.service.context(self.profile)["shared_key"]
        main.STORE.set("webhook_url","https://another.internal/rest/1/test/",profile_id=self.profile)
        self.assertNotEqual(before,self.service.context(self.profile)["shared_key"])

    def test_evidence_route_does_not_require_executor_or_create_workspace(self):
        self.prepare()
        self.raw.update(responsibleId="11",status="5")
        with patch("app.workspace_paths") as workspace:
            result=self.a.get("/api/recommendations/evidence/99")
        self.assertEqual(result.status_code,200)
        workspace.assert_not_called()

    def test_self_claim_does_not_resurrect_after_source_role_changes(self):
        self.prepare()
        self.service.decision(self.profile,bitrix_record(self.raw),"self","1")
        self.raw["createdBy"]="11"
        self.service.refresh(self.profile,force=True)
        self.raw["createdBy"]="1"
        self.service.refresh(self.profile,force=True)
        self.assertEqual(self.service.snapshot(self.profile)["tasks"][0]["state"],"needs_assignment")
        shared=self.service.journal.read(self.service.context(self.profile)["shared_key"])
        self.assertIsNone(shared["tasks"]["99"]["decision"])

    def test_same_holder_self_assignment_is_local(self):
        self.prepare()
        response=self.post(self.a,"/api/recommendations/tasks/99/assign",{"confirmed":True,"employee_id":"1","expected_assignee":"1"})
        self.assertEqual(response.status_code,200,response.json)
        self.api.reassign_task.assert_not_called()
        self.assertEqual(self.service.snapshot(self.profile)["tasks"][0]["state"],"self_assigned")

    def test_current_source_project_overrides_stale_ranking(self):
        self.prepare()
        self.raw["groupId"]="2"
        response=self.post(self.a,"/api/recommendations/rank",{"task_id":"99"})
        self.assertEqual(response.status_code,403)

    def test_pending_operation_shared_across_same_portal_profiles(self):
        self.prepare()
        other=self.pid(self.b)
        main.STORE.set_many({"webhook_url":"https://bitrix.internal/rest/11/other/","bitrix_user":{"ID":"11"}},profile_id=other)
        main.STORE.replace_projects([{"id":"1","name":"Test"}],profile_id=other)
        self.service.operation(self.profile,"99","11","uncertain")
        self.assertEqual(self.service.operation(other,"99")["status"],"uncertain")
        with self.assertRaises(ValueError):self.service.operation(other,"99","11","pending")
