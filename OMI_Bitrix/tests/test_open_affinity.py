"""Independent open-work proximity; completion and suitability stay separate."""
import unittest
from datetime import datetime
from recommendations import rank
from recommendation_matching import RelevanceIndex
from task_affinity import mentioned_periods
from test_recommendations import record, employee
from sla import TZ


def payroll(ident, executor, title="payroll review", completed=False):
    return {**record(ident, executor, completed), "title": title, "description": "payroll allowances deductions"}


class OpenAffinityTests(unittest.TestCase):
    def test_recurring_pending_work_visible_but_not_completed_experience(self):
        rows=[payroll(i,"2","payroll review "+month) for i,month in enumerate(("September","October","November","December"),1)]
        rows.append(payroll(10,"1","payroll review October",True))
        result=rank(payroll(99,"1"),rows,[employee(),employee("2")])
        self.assertEqual([p["id"] for p in result["candidates"]],["1"])
        self.assertEqual(result["open_affinity"][0]["id"],"2")
        self.assertEqual(result["open_affinity"][0]["similar_completed"],0)
        self.assertEqual(len(result["open_affinity"][0]["mentioned_periods"]),4)
        self.assertEqual(result["provisional"][0]["score"],None)

    def test_periods_break_equal_text_match_ties_not_workload(self):
        rows=[payroll(1,"1","payroll September"),payroll(2,"2","payroll October"),payroll(3,"2","payroll November")]
        result=rank(payroll(99,"1"),rows,[employee(),employee("2")])
        self.assertEqual(result["open_affinity"][0]["id"],"2")
        self.assertEqual(result["open_affinity"][0]["active_tasks"],2)
        self.assertEqual(result["candidates"],[])

    def test_exact_copies_do_not_strengthen_affinity_order(self):
        rows=[payroll(1,"1","payroll September"),payroll(2,"2","payroll September")]
        base=rank(payroll(99,"1"),rows,[employee(),employee("2")])
        repeated=rank(payroll(99,"1"),rows+[{**rows[0],"id":str(i)} for i in range(3,25)],[employee(),employee("2")])
        first=next(p for p in repeated["open_affinity"] if p["id"]=="1")
        self.assertEqual(first["text_similarity"],base["open_affinity"][0]["text_similarity"])
        self.assertEqual(first["content_patterns"],1)
        self.assertEqual(len(first["mentioned_periods"]),1)
        self.assertEqual(repeated["open_affinity"][0]["id"],"2")
        self.assertEqual(len(first["examples"][0]["duplicate_tasks"]),23)

    def test_employee_with_completed_and_open_work_in_both_views(self):
        result=rank(payroll(99,"1"),[payroll(1,"1",completed=True),payroll(2,"1")],[employee()])
        self.assertEqual(len(result["open_affinity"]),1)
        self.assertEqual(result["open_affinity"][0]["similar_completed"],1)
        self.assertEqual(result["provisional"],[])

    def test_ineligible_and_unrelated_people_never_enter_open_affinity(self):
        rows=[payroll(1,"1"),{**record(2,"2"),"title":"network review","description":"network"}]
        result=rank(payroll(99,"1"),rows,[employee(enabled=False),employee("2"),employee("3")])
        self.assertEqual(result["open_affinity"],[])

    def test_target_future_supervisor_and_review_work_excluded(self):
        at=datetime(2026,1,1,tzinfo=TZ)
        rows=[payroll(99,"1"),{**payroll(1,"1"),"created_at":"2027-01-01"},
              {**payroll(2,"1"),"awaiting_executor":True},{**payroll(3,"1"),"status":"4"}]
        result=rank(payroll(99,"1"),rows,[employee()],at=at,open_index=RelevanceIndex(rows))
        self.assertEqual(result["open_affinity"],[])

    def test_named_periods_do_not_come_from_creation_or_boilerplate(self):
        row={"title":"مراجعة الرواتب [OMI-SIM-20261003]","description":"payroll review October 2026","created_at":"2026-10-03"}
        self.assertEqual(mentioned_periods(row),[])
        self.assertEqual(mentioned_periods({"title":"رواتب أكتوبر 2026"}),["2026-10"])
        self.assertEqual(mentioned_periods({"title":"payroll October 2026"}),["2026-10"])
        self.assertEqual(mentioned_periods({"title":"رواتب أكتوبر"}),["unspecified-10"])

    def test_renaming_people_cannot_change_evidence_order(self):
        rows=[payroll(1,"1","payroll September"),payroll(2,"2","payroll October"),payroll(3,"2","payroll November")]
        one=rank(payroll(99,"1"),rows,[employee(),employee("2")])
        two=rank(payroll(99,"1"),rows,[employee(name="Different"),employee("2",name="Another")])
        self.assertEqual([p["id"] for p in one["open_affinity"]],[p["id"] for p in two["open_affinity"]])


if __name__=="__main__":unittest.main()
