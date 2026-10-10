import unittest
from datetime import datetime
from unittest.mock import Mock,patch
import test_diwany as fixtures
from test_recommendations import record,employee
from diwany import DiwanClient,validate_config,normalize
from recommendation_evaluation import evaluate_cases,metrics


class DataPipelineTests(unittest.TestCase):
    def test_diwan_enriches_all_pages_and_preserves_narrative(self):
        config=validate_config({**fixtures.CONFIG,"supervisor_field":"supervisor.id","assignee_field":"executor.email"})
        def transport(url,method,data):
            if url.endswith("/list"):
                return [{"id":"7","serviceName":"Finance"}] if data["pageNumber"]==1 else []
            return {"id":"7","supervisor":{"id":"owner"},"executor":{"email":"employee@internal"},
                    "dueDate":"2026-01-01","viewForm":{"controls":[{"label":"تفاصيل الطلب","value":"رواتب"}]}}
        rows=[r for _,page in DiwanClient(config,"test",transport).iter_analysis_pages() for r in page]
        self.assertEqual(rows[0]["title"],"Finance")
        self.assertEqual(rows[0]["creator_id"],"owner")
        self.assertEqual(rows[0]["assignee_id"],"employee@internal")
        self.assertIn("رواتب",rows[0]["description"])
        self.assertEqual(rows[0]["deadline"],"2026-01-01")

    def test_diwan_status_four_is_not_bitrix_review(self):
        from recommendations import assignment_state
        row={"source":"diwan","id":"1","status":"4","creator_id":"a","assignee_id":"a"}
        self.assertEqual(assignment_state(row,{}),"needs_assignment")

    def test_field_roles_are_not_guessed_from_request_employee(self):
        row=normalize({"id":"1","employee":{"id":"7"},"isOwner":True},validate_config(fixtures.CONFIG))
        self.assertEqual(row["creator_id"],"")
        self.assertEqual(row["assignee_id"],"")

    def test_source_metadata_is_preserved_without_fabricated_scores(self):
        from history import bitrix_record
        from recommendations import validate_policy
        policy=validate_policy({"data_fields":{"quality":"UF_QUALITY","team":"UF_TEAM"}})
        from bitrix import BitrixClient
        row=bitrix_record({"id":"1",BitrixClient._camel("UF_QUALITY"):"approved",BitrixClient._camel("UF_TEAM"):"Finance"},data_fields=policy["data_fields"])
        self.assertEqual(row["attributes"]["quality"],"approved")
        with self.assertRaises(ValueError):validate_policy({"data_fields":{"secret":"PASSWORD"}})

    def test_rank_metrics_require_real_explicit_judgments(self):
        at="2026-01-01T08:00:00+03:00"
        case={"at":at,"snapshot_at":at,"task":record(99),"employees":[employee()],
              "records":[{**record(1,completed=True),"observed_at":at}],"judgments":{"1":3},"judgment_source":"reviewed fixture"}
        result=evaluate_cases([case],1)
        self.assertEqual(result["results"]["model"]["ndcg_at_k"],1)
        case["records"][0]["observed_at"]="2030-01-01T00:00:00+03:00"
        with self.assertRaises(ValueError):evaluate_cases([case])
        case["records"]=[];case["judgments"]={}
        with self.assertRaises(ValueError):evaluate_cases([case])


class DiwanRecommendationTests(unittest.TestCase):
    setUp=fixtures.AppTests.setUp
    pid=fixtures.AppTests.pid
    post=fixtures.AppTests.post

    def prepare(self):
        self.profile=self.pid(self.a)
        self.config=validate_config({**fixtures.CONFIG,"supervisor_field":"supervisor","current_user_id":"owner","roles_confirmed":True})
        fixtures.main.STORE.set("diwan_config",self.config,profile_id=self.profile)
        fixtures.main.STORE.set("diwan_employees",[{"source":"diwan","value":"worker","name_en":"Worker"}],profile_id=self.profile)
        self.service=fixtures.main.app.extensions["diwan_recommendations"]
        self.service.vault=Mock();self.service.vault.present.return_value=True;self.service.vault.get.return_value="test"
        self.raw={"id":"7","supervisor":"owner","assignTo":"owner","serviceName":"payroll"}
        self.api=Mock();self.api.iter_pages.side_effect=lambda:iter([(1,[normalize(self.raw,self.config)])])
        self.api.details.side_effect=lambda _:dict(self.raw)
        def delegate(tid,rid,person):self.raw["assignTo"]=person["value"]
        self.api.delegate.side_effect=delegate
        mocked=patch.object(self.service,"client",return_value=self.api);mocked.start();self.addCleanup(mocked.stop)
        self.service.refresh(self.profile,force=True)

    def test_diwan_queue_self_and_manual_assignment(self):
        self.prepare()
        self.assertEqual(self.a.get("/api/recommendations?source=diwan").json["notifications"][0]["id"],"7")
        self.assertEqual(self.post(self.a,"/api/recommendations/tasks/7/self?source=diwan",{}).status_code,200)
        self.assertEqual(self.a.get("/api/recommendations?source=diwan").json["notifications"],[])
        response=self.post(self.a,"/api/recommendations/tasks/7/assign?source=diwan",{"confirmed":True,"employee_id":"worker","expected_assignee":"owner"})
        self.assertEqual(response.status_code,200,response.json)
        self.api.delegate.assert_called_once()
        self.assertEqual(self.raw["assignTo"],"worker")

    def test_diwan_executor_without_supervision_is_denied(self):
        self.prepare();self.raw["supervisor"]="someone-else"
        response=self.post(self.a,"/api/recommendations/tasks/7/assign?source=diwan",{"confirmed":True,"employee_id":"worker","expected_assignee":"owner"})
        self.assertEqual(response.status_code,403)
        self.api.delegate.assert_not_called()

    def test_diwan_credential_change_invalidates_scope(self):
        self.prepare()
        first=self.service.context(self.profile)
        fixtures.main.STORE.set("diwan_token_protected","changed-test-ciphertext",profile_id=self.profile)
        second=self.service.context(self.profile)
        self.assertNotEqual(first["key"],second["key"])
        self.assertEqual(first["shared_key"],second["shared_key"])
        self.assertEqual(self.service.snapshot(self.profile)["tasks"],[])

    def test_diwan_role_acknowledgement_required(self):
        self.prepare()
        fixtures.main.STORE.set("diwan_config",{**self.config,"roles_confirmed":False},profile_id=self.profile)
        self.assertFalse(self.a.get("/api/recommendations?source=diwan").json["configured"])

    def test_legacy_diwan_delegation_cannot_bypass_supervision(self):
        self.prepare()
        history=fixtures.main.app.extensions["diwan_history"]
        with history.lock:history._state(self.profile)["sources"]["diwan"]={"records":[normalize(self.raw,self.config)]}
        self.raw["supervisor"]="other"
        with patch("diwany_routes.client",return_value=self.api):
            result=self.post(self.a,"/api/diwany/tasks/7/delegate",{"confirmed":True,"recipient":"worker"})
        self.assertEqual(result.status_code,403,result.json)
        self.api.delegate.assert_not_called()

    def test_legacy_diwan_delegation_respects_shared_uncertain_marker(self):
        self.prepare()
        history=fixtures.main.app.extensions["diwan_history"]
        with history.lock:history._state(self.profile)["sources"]["diwan"]={"records":[normalize(self.raw,self.config)]}
        self.service.operation(self.profile,"7","worker","uncertain")
        result=self.post(self.a,"/api/diwany/tasks/7/delegate",{"confirmed":True,"recipient":"worker"})
        self.assertEqual(result.status_code,409,result.json)
        self.api.delegate.assert_not_called()

    def test_verify_clears_legacy_and_shared_uncertainty(self):
        import hashlib
        self.prepare()
        self.service.operation(self.profile,"7","worker","uncertain")
        key="diwan_operation_"+hashlib.sha256((self.config["list_url"]+"|7").encode()).hexdigest()
        fixtures.main.STORE.set(key,{"status":"uncertain","recipient":"worker"},profile_id=self.profile)
        self.raw["assignTo"]="worker"
        response=self.post(self.a,"/api/recommendations/tasks/7/verify?source=diwan",{})
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(fixtures.main.STORE.get(key,profile_id=self.profile)["status"],"confirmed")
        self.assertEqual(self.service.operation(self.profile,"7")["status"],"confirmed")
