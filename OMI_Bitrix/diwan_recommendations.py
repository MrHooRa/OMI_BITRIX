"""Diwan assignment adapter. Explicit field mappings, no guessed workflow roles."""
import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit
from recommendation_service import RecommendationService
from diwany import DiwanClient, normalize
from history import now


class DiwanRecommendationService(RecommendationService):
    source_name = "diwan"

    def __init__(self, store, history, root, vault, **kwargs):
        super().__init__(store, history, root, **kwargs)
        self.vault = vault

    def context(self, pid):
        config = self.store.get("diwan_config", {}, profile_id=pid)
        if not (self.store.get("signed_profile_active", False, profile_id=pid) and self.vault.present(pid)
                and config.get("roles_confirmed") and config.get("supervisor_field") and config.get("current_user_id")):
            return None
        origin=urlsplit(config["list_url"])
        scope=hashlib.sha256(json.dumps([config,self.store.get("diwan_token_protected","",profile_id=pid)],sort_keys=True).encode()).hexdigest()
        policy=self.store.get("recommendation_policy",{},profile_id=pid)
        return {"key":pid+":"+scope, "shared_key":"diwan:"+origin.scheme+"://"+origin.netloc+origin.path,
                "source":"diwan", "config":config,"pid":pid,"url":config["list_url"],
                "projects":[{"id":"diwan","name":"Diwan"}], "user":config["current_user_id"],
                "policy":{k:v for k,v in policy.items() if k in {"weights","top_n"}}}

    def client(self, context):
        return DiwanClient(context["config"], self.vault.get(context["pid"]))

    def source_directory(self, context, state):
        people=self.store.get("diwan_employees",[],profile_id=context["pid"])
        return [{"id":str(p["value"]),"name":p.get("name_ar") or p.get("name_en") or p["value"],
                 "enabled":True,"active":True,"projects":["diwan"],"categories":[],
                 "away_from":p.get("away_from",""),"away_to":p.get("away_to","")} for p in people if p.get("source","diwan")=="diwan"]

    def refresh(self,pid,force=False):
        with self.lock:
            context=self.context(pid)
            if not context:return
            state=self._state(context)
            if state["running"] or (not force and self.clock()<state["next"]):return
            state.update(running=True,next=self.clock()+60)
            generation=state.get("generation",0)
        try:
            verified_at=datetime.now(timezone.utc).isoformat()
            api=self.client(context)
            cached={r["id"]:r for r in state["active"]}
            active=[]
            for _,rows in api.iter_pages():
                for row in rows:
                    if row["completed"]:continue
                    previous=cached.get(row["id"])
                    # Enrich new/changed tasks; missing change stamps require a fresh detail read.
                    if context["config"].get("detail_url") and (not previous or not row.get("modified_at") or previous.get("modified_at")!=row["modified_at"]):
                        raw=api.details(row["id"]);raw.setdefault(context["config"]["task_id_field"],row["id"])
                        detail=normalize(raw,context["config"])
                        row={k:(v if v not in (None,"",[]) else row.get(k,v)) for k,v in detail.items()}
                    elif previous:
                        row={k:(v if v not in (None,"",[]) else previous.get(k,v)) for k,v in row.items()}
                    if not row["completed"]:active.append(row)
                    if len(active)>100000:raise ValueError("active_capacity")
            with self.lock:
                latest=self.context(pid)
                if not latest or latest["key"]!=context["key"] or generation!=state.get("generation",0):return
                state["active"]=active
                state.update(checked_at=now(),checked_epoch=self.clock(),error=None)
                self._prepare(context,state);self.process(context,state,verified_at=verified_at)
        except Exception:
            with self.lock:state.update(error="source_or_journal_unavailable",next=self.clock()+300)
        finally:
            with self.lock:state["running"]=False
