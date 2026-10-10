"""Kernel regressions and fixed anonymous before/after relevance cases."""
import unittest
from datetime import datetime
from recommendations import rank
from recommendation_matching import RelevanceIndex, query_profile
from task_language import scope_text
from employee_insights import classify
from model_quality_cases import cases,holdout_cases,row,person,AT
from sla import TZ


class ModelQualityTests(unittest.TestCase):
    def check_cases(self, samples):
        for case in samples:
            with self.subTest(case=case["name"]):
                result=rank(row(999,case["query"],completed=False),case["records"],
                    [person(i) for i in ("1","2","3")],at=AT)
                ids=[p["id"] for p in result["candidates"]]
                self.assertEqual(ids[0] if ids else None,case["employee"])
                self.assertFalse(set(ids)&case["forbidden"])

    def test_fixed_relevance_cases(self):
        self.check_cases(cases())

    def test_separate_domain_probes(self):
        self.check_cases(holdout_cases())

    def test_copying_completed_records_cannot_buy_score(self):
        query=row(999,"payroll deductions",completed=False)
        history=[row(1,"payroll deductions"),row(2,"network","2")]
        base=rank(query,history,[person("1"),person("2")],at=AT)["candidates"][0]
        repeats=history+[dict(history[0],id=str(100+i)) for i in range(50)]
        duplicate=rank(query,repeats,[person("1"),person("2")],at=AT)["candidates"][0]
        self.assertEqual(duplicate["score"],base["score"])
        self.assertEqual(duplicate["components"]["experience"],base["components"]["experience"])
        self.assertEqual(duplicate["similar_completed"],51)
        self.assertEqual(duplicate["evidence_patterns"],1)

    def test_copies_across_linked_sources_do_not_buy_experience(self):
        data=[row(1,"payroll deductions"),row(2,"payroll deductions",source="diwan")]
        result=rank(row(999,"payroll",completed=False),data,[person("1")],at=AT)["candidates"][0]
        single=rank(row(999,"payroll",completed=False),data[:1],[person("1")],at=AT)["candidates"][0]
        self.assertEqual(result["components"]["experience"],single["components"]["experience"])
        self.assertEqual(len(result["examples"]),2)  # source IDs remain available

    def test_explicit_completed_periods_retain_recurrence_credit(self):
        data=[row(1,"payroll September 2025"),row(2,"payroll October 2025")]
        result=rank(row(999,"payroll",completed=False),data,[person("1")],at=AT)["candidates"][0]
        single=rank(row(999,"payroll",completed=False),data[:1],[person("1")],at=AT)["candidates"][0]
        self.assertEqual(result["evidence_patterns"],2)
        self.assertGreater(result["components"]["experience"],single["components"]["experience"])

    def test_prepared_future_index_cannot_teach_past_decision(self):
        past=row(1,"payroll garnishment allowances")
        future=dict(row(2,"payroll garnishment deductions"),completed_at="2025-12-01")
        result=rank(row(999,"garnishment",completed=False),[past,future],[person("1")],
            at=datetime(2025,6,1,tzinfo=TZ),prepared=RelevanceIndex([past,future]))
        self.assertEqual(result["completed_records"],1)
        self.assertFalse(result["query_profile"]["domain_known"])

    def test_target_cannot_teach_its_own_unknown_term(self):
        data=[row(999,"payroll garnishment deductions"),row(1,"payroll garnishment allowances")]
        result=rank(row(999,"garnishment",completed=False),data,[person("1")],at=AT,
                    prepared=RelevanceIndex(data))
        self.assertEqual(result["completed_records"],1)
        self.assertFalse(result["query_profile"]["domain_known"])
        self.assertNotIn("999",[m["id"] for c in result["candidates"] for m in c["examples"]])

    def test_prepared_open_records_are_not_completed_evidence(self):
        data=[row(1,"payroll",completed=False)]
        result=rank(row(999,"payroll",completed=False),data,[person("1")],at=AT,prepared=RelevanceIndex(data))
        self.assertEqual(result["candidates"],[])
        self.assertEqual(result["completed_records"],0)

    def test_future_execution_does_not_inflate_pressure(self):
        data=[row(1,"payroll"),dict(row(2,"payroll",completed=False),created_at="2027-01-01")]
        for workload in (None,{"1":[data[1]]}):
            result=rank(row(999,"payroll",completed=False),data,[person("1")],at=AT,workload=workload)
            self.assertEqual(result["candidates"][0]["active_tasks"],0)
            self.assertEqual(result["open_affinity"],[])

    def test_ambiguous_spelling_is_not_guessed(self):
        index=RelevanceIndex([row(1,"tiger"),row(2,"timer")])
        self.assertEqual(set(index.query_counts("titer")),{"titer"})
        # No lexical correction; a semantic comparison may still retrieve a spelling variant.
        self.assertFalse(any(m["shared_terms"] for m in index.related("titer")))

    def test_exact_unknown_words_are_preserved(self):
        index=RelevanceIndex([row(1,"tiger timer")])
        self.assertEqual(set(index.query_counts("timer")),{"timer"})

    def test_two_edits_and_short_acronyms_are_not_corrected(self):
        index=RelevanceIndex([row(1,"payroll Python")])
        self.assertEqual(set(index.query_counts("pxyroxl")),{"pxyroxl"})
        self.assertEqual(set(index.query_counts("UI")),{"ui"})
        self.assertFalse(query_profile("UI",index)["domain_known"])

    def test_global_alias_spelling_also_handles_source_typo(self):
        index=RelevanceIndex([row(1,"payrol")])
        self.assertEqual([m["task"]["id"] for m in index.related("payroll")],["1"])

    def test_scope_keeps_positive_clause_and_tools_after_parenthesis(self):
        positive, excluded=scope_text("لا تشمل الضرائب ولكن تشمل الرواتب")
        self.assertIn("الرواتب",positive)
        self.assertEqual(excluded,["الضرائب"])
        index=RelevanceIndex([row(1,"payroll Excel")])
        query=query_profile("الرواتب (باستثناء الضرائب) باستخدام Excel",index)
        self.assertEqual([t["id"] for t in query["tools"]],["excel"])

    def test_backup_alone_cannot_establish_database_expertise(self):
        self.assertNotIn("database",{t["id"] for t in classify("annual leave backup coverage")})
        self.assertFalse(any(t["type"]=="BUSINESS_DOMAIN" for t in classify("database backup")))

    def test_match_components_are_bounded_and_work_type_changes_order(self):
        index=RelevanceIndex([row(1,"payroll review"),row(2,"payroll extraction")])
        matches=index.related("payroll extraction")
        self.assertEqual(matches[0]["task"]["id"],"2")
        self.assertTrue(all(0<=m["bm25_score"]<=100 and 0<=m["lexical_score"]<=100
                            and 16<=m["score"]<=100 for m in matches))

    def test_copies_do_not_hide_another_executor_at_retrieval_limit(self):
        data=[row(i,"payroll") for i in range(1,401)]+[row(99999,"payroll","2")]
        result=rank(row(999,"payroll",completed=False),data,[person("1"),person("2")],at=AT)
        self.assertEqual({c["id"] for c in result["candidates"]},{"1","2"})
        self.assertEqual(result["candidates"][0]["score"],result["candidates"][1]["score"])
