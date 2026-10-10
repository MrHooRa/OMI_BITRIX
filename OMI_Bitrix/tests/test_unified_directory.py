"""Offline acceptance cases for unified identities and task understanding."""
import time
import unittest
from unittest.mock import Mock, patch
import test_diwany as fixtures
from test_recommendations import record, employee
from diwany import validate_config, normalize
from history import now, connection_scope
from recommendations import validate_policy, rank
from recommendation_matching import RelevanceIndex, query_profile
from employee_directory import EmployeeDirectory


def task(ident, title, source="bitrix", worker="1", completed=True):
    return {**record(ident, worker, completed), "title": title, "description": "",
            "source": source, "project_id": "diwan" if source == "diwan" else "1"}


class TaskUnderstandingTests(unittest.TestCase):
    def test_payroll_paraphrases_bilingual_and_subject_guard(self):
        rows = [task(1,"employee remuneration Excel"), task(2,"network Excel")]
        result = rank(task(99,"مطابقة مسيرات الأجور"), rows, [employee()])
        self.assertEqual([r["id"] for r in result["candidates"]], ["1"])
        self.assertEqual([r["id"] for r in result["candidates"][0]["examples"]], ["1"])
        self.assertTrue(all(t["id"].startswith("topic_") for t in result["task_labels"] if t["type"]=="BUSINESS_DOMAIN"))

    def test_sparse_history_does_not_invent_manual_domain(self):
        rows=[task(1,"payroll garnishment deductions"),task(2,"payroll garnishment allowances"),task(3,"network routing")]
        index=RelevanceIndex(rows)
        profile=query_profile("garnishment review",index)
        self.assertEqual(profile["domains"],[])
        self.assertFalse(profile["needs_clarification"])
        self.assertEqual({r["task"]["id"] for r in index.related("garnishment review")},{"1","2"})

    def test_open_future_and_tools_do_not_teach_domain(self):
        rows=[task(1,"payroll garnishment allowances",completed=False),
              task(2,"payroll garnishment deductions",completed=False),
              {**task(3,"payroll garnishment payments"),"completed_at":"2099-01-01"}]
        self.assertFalse(query_profile("garnishment",RelevanceIndex(rows))["domain_known"])
        done=[task(1,"payroll Excel deductions"),task(2,"payroll Excel allowances")]
        self.assertEqual(query_profile("Excel report",RelevanceIndex(done))["domains"],[])

    def test_ambiguous_corpus_word_is_not_promoted(self):
        rows=[task(1,"payroll adjustment deductions"),task(2,"payroll adjustment allowances"),
              task(3,"network adjustment firewall")]
        self.assertFalse(query_profile("adjustment",RelevanceIndex(rows))["domain_known"])

    def test_explicit_exclusion_does_not_retrieve_excluded_domain(self):
        index=RelevanceIndex([task(1,"payroll Excel"),task(2,"tax Excel")])
        profile=query_profile("payroll review excluding tax",index)
        self.assertEqual(profile["domains"],[])
        self.assertEqual(profile["excluded_labels"],[])  # Raw exclusion still removes tax before both models.
        self.assertEqual([m["task"]["id"] for m in index.related("payroll excluding tax")],["1"])

    def test_custom_domain_handles_no_shared_surface_words(self):
        rule={"id":"licensing","ar":"التراخيص","en":"Licensing",
              "aliases":["تجديد رخص التشغيل","operating licence renewal"]}
        index=RelevanceIndex([task(1,"operating licence renewal")],domain_rules=[rule])
        result=index.related("تجديد رخص التشغيل")
        self.assertEqual([r["task"]["id"] for r in result],["1"])
        self.assertEqual(result[0]["shared_terms"],[])
        self.assertEqual(result[0]["lexical_score"],0)
        self.assertEqual(result[0]["concept_score"],100)
        self.assertFalse(index.related("payroll"))

    def test_flat_diwan_fields_and_explicit_executor_metadata(self):
        config=validate_config({**fixtures.CONFIG,"assignee_field":"executor.email","supervisor_field":"owner"})
        row=normalize({"id":"4","owner":"boss","executor":{"email":"staff@internal.example",
            "name":"Staff","department":"Finance","position":"Analyst"},
            "employee":{"name":"Requester"},"FORM*تفاصيل الطلب":"مطابقة مسيرات الأجور",
            "isCompleted":True,"detail_created_date":"2025-01-01",
            "detail_completed*date":"2025-01-02"},config)
        self.assertEqual(row["assignee_name"],"Staff")
        self.assertEqual(row["assignee_department"],"Finance")
        self.assertIn("مسيرات",row["description"])
        self.assertEqual(row["completed_at"],"2025-01-02")


class DirectoryFlowTests(unittest.TestCase):
    setUp=fixtures.AppTests.setUp
    pid=fixtures.AppTests.pid
    post=fixtures.AppTests.post

    def prepare(self):
        self.profile=self.pid(self.a)
        store=fixtures.main.STORE
        store.set_many({"webhook_url":"https://bitrix.internal/rest/1/test/",
            "bitrix_user":{"ID":"boss"},"recommendation_policy":validate_policy({
                "employees":[employee("1",name="Same Name"),employee("2",name="Same Name")]})},profile_id=self.profile)
        store.replace_projects([{"id":"1","name":"Finance"}],profile_id=self.profile)
        self.config=validate_config({**fixtures.CONFIG,"supervisor_field":"supervisor",
            "roles_confirmed":True,"current_user_id":"boss"})
        store.set("diwan_config",self.config,profile_id=self.profile)
        store.set("diwan_employees",[{"source":"diwan","value":"staff@internal.example","name_en":"Same Name"}],profile_id=self.profile)
        services={s:fixtures.main.app.extensions[k] for s,k in
                  (("bitrix","recommendations"),("diwan","diwan_recommendations"))}
        services["diwan"].vault.save(self.profile,"test-token")
        self.directory=EmployeeDirectory(store,fixtures.main.app.extensions["diwan_history"],services)
        fixtures.main.app.extensions["employee_directory"]=self.directory
        self.services=services
        self.query=task(99,"مطابقة مسيرات الأجور","diwan","boss",False)
        self.query.update(creator_id="boss",auditor_ids=[],awaiting_executor=True)
        for source,service in services.items():
            cache="diwan_analysis" if source=="diwan" else "bitrix"
            self.directory.history.bind_scope(self.profile,cache,connection_scope(store,self.profile,source))
            rows=[task(99,"payroll review Excel"),task(2,"payroll deductions")] if source=="bitrix" else []
            with self.directory.history.lock:
                self.directory.history._state(self.profile)["sources"][cache]={
                    "records":rows,"revision":source+"-1","complete":True,"updated_at":now(),"error":None}
            state=service._state(service.context(self.profile))
            state.update(active=[self.query] if source=="diwan" else [],checked_at=now(),checked_epoch=time.time(),error=None)
            service._prepare(service.context(self.profile),state)

    def link(self):
        data=self.directory.snapshot(self.profile)
        left=next(p for p in data["people"] if p["accounts"][0]["source"]=="bitrix" and p["accounts"][0]["id"]=="1")
        right=next(p for p in data["people"] if p["accounts"][0]["source"]=="diwan" and p["accounts"][0]["id"]=="staff@internal.example")
        linked={**left,"accounts":left["accounts"]+right["accounts"],"name":"Linked Employee"}
        self.directory.save(self.profile,[linked])
        return linked

    def test_same_names_do_not_merge_or_create_completed_experience(self):
        self.prepare()
        self.assertEqual(len(self.directory.snapshot(self.profile)["people"]),4)
        result=self.services["diwan"].recommend(self.profile,text=self.query["title"],project_id="diwan")
        self.assertEqual(result["candidates"],[])

    def test_bitrix_completion_supports_new_diwan_task_with_native_recipient(self):
        self.prepare();self.link()
        result=self.services["diwan"].recommend(self.profile,live_record=self.query,text="payroll")
        self.assertEqual(result["candidates"][0]["id"],"staff@internal.example")
        self.assertEqual({r["source"] for r in result["candidates"][0]["examples"]},{"bitrix"})
        # Equal task IDs in different sources must not exclude real evidence.
        self.assertIn("99",[r["id"] for r in result["candidates"][0]["examples"]])
        self.assertFalse(result["stale"])

    def test_linking_does_not_grant_bitrix_eligibility_or_source_activity(self):
        self.prepare();linked=self.link()
        policy=fixtures.main.STORE.get("recommendation_policy",profile_id=self.profile)
        policy["employees"][0]["enabled"]=False;policy["employees"][0]["active"]=False
        fixtures.main.STORE.set("recommendation_policy",policy,profile_id=self.profile)
        person=self.directory.source_people(self.profile,"bitrix")[0]
        self.assertFalse(person["enabled"]);self.assertFalse(person["active"])

    def test_local_switch_can_be_reenabled_without_changing_source_approval(self):
        self.prepare();self.link()
        data=self.directory.snapshot(self.profile)
        person=next(p for p in data["people"] if p["linked"])
        account=next(a for a in person["accounts"] if a["source"]=="bitrix")
        account["enabled"]=False
        saved=self.directory.save(self.profile,[person])
        person=next(p for p in saved["people"] if p["linked"])
        account=next(a for a in person["accounts"] if a["source"]=="bitrix")
        self.assertFalse(account["enabled"])
        self.assertTrue(account["source_enabled"])
        account["enabled"]=True
        self.directory.save(self.profile,[person])
        self.assertTrue(next(p for p in self.directory.source_people(self.profile,"bitrix") if p["id"]=="1")["enabled"])

    def test_unlink_removes_cross_source_evidence_immediately(self):
        self.prepare();self.link()
        self.directory.save(self.profile,[])
        result=self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")
        self.assertEqual(result["candidates"],[])

    def test_wrong_scope_duplicate_account_and_profile_are_rejected(self):
        self.prepare();linked=self.link()
        self.assertEqual(self.b.get("/api/employees").json["people"],[])
        self.assertEqual(self.post(self.b,"/api/employees",{"people":[linked]}).status_code,400)
        with self.assertRaises(ValueError):self.directory.save(self.profile,[linked,linked])
        linked["accounts"][0]["scope"]="wrong"
        with self.assertRaises(ValueError):self.directory.save(self.profile,[linked])

    def test_portal_switch_never_reuses_old_link_for_same_id(self):
        self.prepare();self.link()
        fixtures.main.STORE.set("webhook_url","https://other.internal/rest/1/test/",profile_id=self.profile)
        result=self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")
        self.assertEqual(result["candidates"],[])
        self.assertFalse(any(p["linked"] for p in self.directory.snapshot(self.profile)["people"]))

    def test_absence_and_disabled_person_apply_across_sources(self):
        self.prepare();linked=self.link()
        linked.update(active=False)
        self.directory.save(self.profile,[linked])
        result=self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")
        self.assertEqual(result["eligible_ids"],[])
        linked.update(active=True,away_from="2020-01-01",away_to="2099-01-01")
        self.directory.save(self.profile,[linked])
        self.assertEqual(self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")["eligible_ids"],[])

    def test_stale_peer_workload_prevents_assignment(self):
        self.prepare();self.link()
        service=self.services["bitrix"]
        service._state(service.context(self.profile))["checked_epoch"]=0
        self.assertTrue(self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")["stale"])

    def test_observed_new_diwan_employee_requires_explicit_enable(self):
        self.prepare()
        state=self.services["diwan"]._state(self.services["diwan"].context(self.profile))
        state["active"].append(task(55,"network","diwan","new@internal.example",False))
        person=next(p for p in self.directory.snapshot(self.profile)["people"] if p["accounts"][0]["id"]=="new@internal.example")
        self.assertFalse(person["accounts"][0]["enabled"])
        person["accounts"][0]["enabled"]=True
        self.directory.save(self.profile,[person])
        found=next(p for p in self.directory.source_people(self.profile,"diwan") if p["id"]=="new@internal.example")
        self.assertTrue(found["enabled"])

    def test_saving_connected_half_preserves_disconnected_identity(self):
        self.prepare();linked=self.link()
        store=fixtures.main.STORE
        old=store.get("webhook_url",profile_id=self.profile)
        store.set("webhook_url","",profile_id=self.profile)
        person=next(p for p in self.directory.snapshot(self.profile)["people"] if p["person_id"]==linked["person_id"])
        self.assertEqual(len(person["accounts"]),1)
        self.directory.save(self.profile,[person])
        stored=store.get("employee_directory",profile_id=self.profile)
        self.assertEqual(len(stored[0]["accounts"]),2)
        store.set("webhook_url",old,profile_id=self.profile)
        self.assertTrue(any(p["linked"] for p in self.directory.snapshot(self.profile)["people"]))

    def test_cross_source_open_work_balances_pressure_without_fake_completion(self):
        self.prepare();self.link()
        service=self.services["bitrix"]
        state=service._state(service.context(self.profile))
        execution=task(80,"payroll review","bitrix","1",False)
        execution["creator_id"]="supervisor"
        waiting=task(81,"payroll review","bitrix","1",False)
        waiting["creator_id"]="1"
        state["active"]=[execution,waiting]
        result=self.services["diwan"].recommend(self.profile,text="payroll",project_id="diwan")
        candidate=result["candidates"][0]
        self.assertEqual(candidate["similar_completed"],2)
        self.assertEqual(candidate["active_tasks"],1)
        self.assertEqual(candidate["components"]["capacity"],15)
        self.assertEqual(result["open_affinity"][0]["similar_open"],1)
        self.assertEqual(result["open_affinity"][0]["examples"][0]["source"],"bitrix")

    def test_human_diwan_assignment_uses_linked_recipient_and_readback(self):
        self.prepare();self.link()
        raw={"id":"99","serviceName":"payroll","supervisor":"boss","assignTo":"boss"}
        api=Mock()
        api.details.side_effect=lambda _:dict(raw)
        api.delegate.side_effect=lambda tid,rid,p:raw.update(assignTo=p["value"])
        with patch.object(self.services["diwan"],"client",return_value=api):
            response=self.post(self.a,"/api/recommendations/tasks/99/assign?source=diwan",
                {"confirmed":True,"employee_id":"staff@internal.example","expected_assignee":"boss"})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(api.delegate.call_args.args[2]["value"],"staff@internal.example")

    def test_domain_settings_are_validated_profile_scoped_and_used_by_rank(self):
        self.prepare()
        rule={"id":"licensing","ar":"التراخيص","en":"Licensing","aliases":["تجديد رخص التشغيل"]}
        self.assertEqual(self.post(self.a,"/api/intelligence/domains",{"domains":[rule]}).status_code,200)
        self.assertEqual(self.b.get("/api/intelligence/domains").json["domains"],[])
        rule["id"]="python"
        self.assertEqual(self.post(self.a,"/api/intelligence/domains",{"domains":[rule]}).status_code,400)
        result=self.services["diwan"].recommend(self.profile,text="تجديد رخص التشغيل",project_id="diwan")
        self.assertEqual(result["task_labels"][0]["id"],"licensing")

    def test_similarity_and_recommendations_share_cross_source_evidence(self):
        self.prepare();self.link()
        with patch.object(fixtures.main.app.extensions["history_scheduler"],"tick"):
            response=self.post(self.a,"/api/intelligence/analyze",{
                "source":"diwan","text":"مطابقة مسيرات الأجور"})
        self.assertEqual(response.status_code,200,response.json)
        related=response.json["result"]["related"]
        self.assertEqual({m["task"]["source"] for m in related},{"bitrix"})
        self.assertEqual({m["task"]["id"] for m in related},{"99","2"})

    def test_employee_profile_contains_linked_sources_and_native_action_id(self):
        self.prepare();self.link()
        data=self.a.get("/api/recommendations/people?source=diwan&employee=staff@internal.example").json
        self.assertEqual(data["people"][0]["completed_count"],2)
        self.assertEqual({r["source"] for r in data["people"][0]["tasks"]},{"bitrix"})
        self.assertEqual(data["people"][0]["id"],"staff@internal.example")


if __name__=="__main__":
    unittest.main()

