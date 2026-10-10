"""Offline regression cases for typed evidence, coverage and scoped profiles."""
import unittest
from employee_insights import classify, coverage, profiles, complementary_team
from recommendation_matching import RelevanceIndex
from recommendations import rank
from test_recommendations import record, employee
import test_recommendations as ranking_fixtures
import test_diwany as fixtures


def task(ident, title, assignee="1", completed=True):
    return {**record(ident, assignee, completed), "title": title, "description": ""}


class EvidenceTests(unittest.TestCase):
    def test_bilingual_labels_and_types(self):
        tags = {t["id"]: t for t in classify("مراجعة الرواتب بالأكسل وإعداد تقرير")}
        self.assertNotIn("payroll", tags)  # No predefined domain labels.
        self.assertEqual(tags["excel"]["type"], "SYSTEM_OR_TOOL")
        self.assertIn("report", tags)
        self.assertEqual({t["id"] for t in classify("payroll review Excel report")}, set(tags))

    def test_labels_ignore_identifiers_and_word_substrings(self):
        self.assertEqual(classify("[OMI-AI-20261003] REQ-123 https://example.test/payroll email waiting"), [])
        self.assertEqual(classify("تحليل الرواتب")[0]["basis"], "local_rule")

    def test_conflicting_domains_cannot_match_only_through_a_tool(self):
        rows = [task(1,"payroll Excel report"),task(2,"network Excel report")]
        self.assertEqual([m["task"]["id"] for m in RelevanceIndex(rows).related("payroll Excel report")], ["1"])

    def test_unknown_domain_still_uses_text_evidence(self):
        self.assertEqual(len(RelevanceIndex([task(1,"astronomy telescope")]).related("astronomy telescope")),1)

    def test_multi_domain_query_can_retrieve_complementary_work(self):
        rows = [task(1,"payroll Excel"), task(2,"network Python")]
        self.assertEqual({m["task"]["id"] for m in RelevanceIndex(rows).related("payroll Excel network Python")}, {"1","2"})

    def test_coverage_is_explicit_and_general_work_does_not_inflate_it(self):
        result=coverage(classify("payroll Python report review"),[task(1,"payroll Excel report")])
        self.assertEqual(result["ratio"],0)
        self.assertEqual([t["id"] for t in result["missing"]],["python"])
        self.assertIsNone(coverage(classify("review report"),[])["ratio"])

    def test_profile_uses_executor_and_separates_waiting_and_open_work(self):
        done=task(1,"payroll Excel")
        rows=profiles([employee(),employee("2")],[done,done],[task(2,"network","2",False),{**task(3,"network","2",False),"awaiting_executor":True}])
        self.assertEqual(rows[0]["completed_count"],1)
        self.assertEqual(rows[0]["topics"][0]["count"],1)
        self.assertEqual(rows[1]["topics"],[])
        self.assertEqual(rows[1]["active_count"],1)

    def test_distinct_sources_keep_separate_records(self):
        row=task(1,"payroll")
        self.assertEqual(profiles([employee()],[row,{**row,"source":"diwan"}],[])[0]["completed_count"],2)

    def test_identity_cannot_change_ranking(self):
        rows=[task(1,"payroll Excel"),task(2,"network Excel","2")]
        query=task(99,"payroll Excel")
        a=rank(query,rows,[employee(name="Network"),employee("2",name="Payroll Expert")])
        b=rank(query,rows,[employee(name="Another name"),employee("2",name="Another name")])
        self.assertEqual([(r["id"],r["score"]) for r in a["candidates"]],[(r["id"],r["score"]) for r in b["candidates"]])
        self.assertEqual([r["id"] for r in a["candidates"]],["1"])

    def test_coverage_equation_is_auditable(self):
        result=rank(task(99,"payroll Python"),[task(1,"payroll Excel")],[employee()])["candidates"][0]
        self.assertEqual(result["coverage"]["ratio"],0)  # Python is requested, Excel is observed; no manual payroll label.
        expected=50*(.75*result["lexical_similarity"]/100+.25*0)
        self.assertAlmostEqual(result["components"]["similarity"],expected,places=2)
        self.assertAlmostEqual(result["score"],sum(result["components"].values()),places=2)

    def test_complementary_advice_adds_unique_coverage_only(self):
        tags=classify("payroll Python Excel")
        def candidate(ident,title,score):
            return {"id":ident,"name":ident,"score":score,"coverage":coverage(tags,[task(1,title)])}
        a=candidate("1","payroll Excel",80)
        b=candidate("2","Python",70)
        duplicate=candidate("3","payroll Excel",60)
        result=complementary_team([a,b,duplicate],tags)
        self.assertEqual([p["id"] for p in result["members"]],["1","2"])
        self.assertEqual(result["missing"],[])
        self.assertTrue(result["advisory_only"])
        self.assertEqual(complementary_team([candidate("1","payroll Python Excel",90),b],tags)["members"],[])

    def test_open_only_never_enters_team_or_completed_profile(self):
        result=rank(task(99,"payroll Python"),[task(1,"payroll",completed=False)],[employee()])
        self.assertEqual(result["team"]["members"],[])
        self.assertEqual(result["candidates"],[])
        self.assertEqual(result["provisional"][0]["coverage"]["matched"],[])


class ProfileEndpointTests(unittest.TestCase):
    setUp=fixtures.AppTests.setUp
    pid=fixtures.AppTests.pid
    prepare=ranking_fixtures.RecommendationFlowTests.prepare

    def test_profile_scope_search_and_absence_of_writes(self):
        self.prepare()
        response=self.a.get("/api/recommendations/people?q=invoice")
        self.assertEqual(response.status_code,200)
        data=response.get_json()
        self.assertEqual(data["total"],1)
        self.assertNotIn("tasks",data["people"][0])
        profile=self.a.get("/api/recommendations/people?employee=1").get_json()["people"][0]
        self.assertEqual(profile["task_total"],3)
        self.assertEqual(profile["active_count"],0)  # Supervisor intake, not execution.
        self.assertEqual(self.a.get("/api/recommendations/people?employee=999").status_code,404)
        self.assertEqual(self.b.get("/api/recommendations/people").get_json()["people"],[])
        self.assertEqual(self.a.get("/api/recommendations/people?source=diwan").get_json()["people"],[])
        self.api.reassign_task.assert_not_called()

    def test_profile_pagination_and_bad_page(self):
        self.prepare()
        state=self.service._state(self.service.context(self.profile))
        state["prepared"]=RelevanceIndex([task(i,"payroll") for i in range(25)])
        first=self.a.get("/api/recommendations/people?employee=1").get_json()["people"][0]
        second=self.a.get("/api/recommendations/people?employee=1&page=2").get_json()["people"][0]
        self.assertEqual(len(first["tasks"]),20)
        self.assertEqual(len(second["tasks"]),5)
        self.assertFalse({t["id"] for t in first["tasks"]}&{t["id"] for t in second["tasks"]})
        self.assertEqual(self.a.get("/api/recommendations/people?page=invalid").status_code,400)

    def test_switching_connection_does_not_expose_old_profile_history(self):
        self.prepare()
        fixtures.main.STORE.set("webhook_url","https://other.internal/rest/1/test/",profile_id=self.profile)
        data=self.a.get("/api/recommendations/people?employee=1").get_json()
        self.assertEqual(data["people"][0]["completed_count"],0)
        self.assertFalse(data["history_ready"])

    def test_new_revision_rebuilds_even_with_identical_display_timestamp(self):
        self.prepare()
        state=self.service._state(self.service.context(self.profile))
        history=self.service.history
        with history.lock:
            source=history._state(self.profile)["sources"]["bitrix"]
            source["records"]=[task(65,"network Python")]
            source["revision"]="new-revision-same-display-time"
        data=self.a.get("/api/recommendations/people?employee=1").get_json()["people"][0]
        self.assertEqual(data["completed_count"],1)
        self.assertEqual(data["tasks"][0]["id"],"65")
