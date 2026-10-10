"""Subject relevance and statistical representation regressions, fully offline."""
import unittest
from recommendation_matching import RelevanceIndex, query_profile, terms
from recommendations import rank
from test_recommendations import record, employee


def task(ident, title, description="", executor="1", completed=True):
    return {**record(ident, executor, completed), "title": title, "description": description}


class StatisticalModelTests(unittest.TestCase):
    def test_known_subject_rejects_unclassified_tool_only_history(self):
        rows = [task(1, "مراجعة الرواتب بالأكسل"), task(2, "Excel report", "generic spreadsheet formatting")]
        matches = RelevanceIndex(rows).related("payroll review Excel")
        self.assertEqual([m["task"]["id"] for m in matches], ["1"])

    def test_arabic_english_tools_and_domains_retrieve_same_evidence(self):
        rows = [task(1, "tax review Python"), task(2, "network Excel report")]
        index = RelevanceIndex(rows)
        self.assertEqual([m["task"]["id"] for m in index.related("تحليل الضرائب باستخدام بايثون")], ["1"])
        self.assertEqual([m["task"]["id"] for m in index.related("tax review Python")], ["1"])

    def test_multiword_tool_aliases_share_features(self):
        self.assertEqual(terms("Power BI"), terms("باور بي آي"))
        self.assertIn("bi", terms("Power BI IPv6"))
        self.assertEqual([m["task"]["id"] for m in RelevanceIndex([task(1,"payroll Power BI")]).related("رواتب باور بي اي")], ["1"])

    def test_title_is_more_informative_than_incidental_description(self):
        rows = [task(1,"payroll Excel","meeting schedule"),task(2,"meeting schedule","payroll Excel")]
        matches = RelevanceIndex(rows).related("payroll Excel")
        self.assertEqual(matches[0]["task"]["id"], "1")
        self.assertGreater(matches[0]["score"], matches[1]["score"])

    def test_duplicate_content_does_not_change_idf_similarity(self):
        first = task(1,"payroll Excel","allowances deductions")
        other = task(2,"network Python","routing")
        base = RelevanceIndex([first, other])
        repeated = RelevanceIndex([first, other] + [{**first,"id":str(i)} for i in range(3,45)])
        expected = base.related("payroll Excel")[0]["score"]
        self.assertEqual(repeated.document_count, 2)
        self.assertTrue(all(m["score"] == expected for m in repeated.related("payroll Excel")))

    def test_query_unknown_terms_are_not_silently_removed_from_norm(self):
        index = RelevanceIndex([task(1,"payroll Excel")])
        specific = index.related("payroll Excel")[0]["score"]
        broader = index.related("payroll Excel astronomy telescope")[0]["score"]
        self.assertGreater(specific, broader)

    def test_generic_connectors_and_ticket_never_establish_similarity(self):
        index = RelevanceIndex([task(1,"مراجعة الرواتب على Excel [REQ-4444]"),task(2,"فحص الشبكة على Python [REQ-4444]")])
        self.assertEqual(index.related("تحليل تقرير على الموظفين [REQ-4444]"), [])
        self.assertEqual(query_profile("تحليل تقرير على الموظفين")["status"], "no_subject")

    def test_unknown_subject_remains_supported_by_exact_text(self):
        index = RelevanceIndex([task(1,"astronomy telescope calibration")])
        self.assertEqual(len(index.related("astronomy telescope calibration")), 1)
        self.assertFalse(query_profile("astronomy telescope calibration")["domain_known"])

    def test_query_profile_distinguishes_tool_only_and_subject(self):
        self.assertEqual(query_profile("Excel report")["status"], "tool_only")
        result = query_profile("مراجعة رواتب باستخدام بايثون وإعداد تقرير")
        self.assertEqual(result["status"], "specific")
        self.assertEqual(result["domains"], [])  # Standalone text has no fitted discovery corpus.
        self.assertEqual(result["tools"][0]["id"], "python")
        self.assertEqual(result["deliverables"][0]["id"], "report")

    def test_repeated_evidence_is_explicit_and_not_called_varied(self):
        rows = [task(i,"payroll Excel") for i in range(1,5)]
        result = rank(task(99,"payroll Excel"), rows, [employee()])
        candidate = result["candidates"][0]
        self.assertEqual(candidate["similar_completed"], 4)
        self.assertEqual(candidate["evidence_patterns"], 1)
        self.assertEqual(candidate["evidence_level"], "repeated")
        self.assertFalse(result["model"]["organization_fine_tuned"])
        self.assertFalse(result["model"]["topic_discovery_supervised"])
        self.assertEqual(result["model"]["fitted_documents"], 1)

    def test_unrelated_idle_person_cannot_beat_subject_evidence(self):
        rows = [task(1,"payroll Excel",executor="1"), task(2,"Excel report",executor="2")]
        rows += [task(100+i,"network support",executor="1",completed=False) for i in range(200)]
        result = rank(task(999,"payroll Excel"),rows,[employee(),employee("2")])
        self.assertEqual([c["id"] for c in result["candidates"]],["1"])
        self.assertIn("1",result["eligible_ids"])
        self.assertEqual(result["candidates"][0]["active_tasks"],200)

    def test_distinct_sources_and_exclusion_are_preserved(self):
        rows = [task(1,"payroll"),{**task(1,"payroll"),"source":"diwan"}]
        matches = RelevanceIndex(rows).related("payroll",exclude=("bitrix","1"))
        self.assertEqual([m["task"]["source"] for m in matches],["diwan"])

    def test_new_local_domains_are_bilingual(self):
        index = RelevanceIndex([task(1,"procurement Python"),task(2,"recruitment Python")])
        self.assertEqual([m["task"]["id"] for m in index.related("مراجعة المشتريات باستخدام بايثون")],["1"])

    def test_attached_arabic_prepositions_on_tools_are_conservative(self):
        query = query_profile("تحليل الرواتب ببايثون وبالاكسل")
        self.assertEqual({t["id"] for t in query["tools"]}, {"python", "excel"})
        self.assertTrue({"python", "excel"} <= terms("بالPython وبالاكسل"))
        self.assertEqual([m["task"]["id"] for m in RelevanceIndex([task(1,"AI requirements")]).related("متطلبات ذكاء الاصطناعي")], ["1"])

    def test_sublinear_tf_limits_repetition_without_unbounded_scores(self):
        index = RelevanceIndex([task(1,"payroll", "salary "*100 + "allowances"),task(2,"payroll","deductions")])
        matches = index.related("payroll")
        self.assertTrue(all(16 <= m["score"] <= 100 for m in matches))
        self.assertLess(index.vectors[0]["رواتب"], 10 * index.idf["رواتب"])


if __name__ == "__main__":
    unittest.main()
