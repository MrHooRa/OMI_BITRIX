"""Offline ranking evaluation using explicit, time-stamped candidate judgments.

No historical assignee is silently converted to an optimal-employee label.
Run: python recommendation_evaluation.py --input verified-cases.json --k 3
"""
import argparse
import json
from collections import Counter
from datetime import datetime
from math import log2
from time import perf_counter
from recommendations import rank
from sla import parse


def metrics(order, judgments, k):
    selected=order[:k]
    relevant={key for key,value in judgments.items() if value>0}
    hits=sum(key in relevant for key in selected)
    dcg=sum((2**judgments.get(key,0)-1)/log2(i+2) for i,key in enumerate(selected))
    ideal=sum((2**value-1)/log2(i+2) for i,value in enumerate(sorted(judgments.values(),reverse=True)[:k]))
    return {"precision_at_k":hits/k,"recall_at_k":hits/len(relevant) if relevant else None,
            "ndcg_at_k":dcg/ideal if ideal else None,
            "mrr":next((1/(i+1) for i,key in enumerate(selected) if key in relevant),0)}


def evaluate_cases(cases,k=3):
    if not 1<=k<=10:raise ValueError("K must be 1..10")
    totals={name:[] for name in ("model","least_loaded","experience_only")}
    concentration=Counter();latencies=[];abstentions=0
    for case in sorted(cases,key=lambda c:c["at"]):
        at=parse(case["at"])
        if not at or parse(case.get("snapshot_at"))!=at:
            raise ValueError("Each case needs an actual as-of snapshot matching decision time")
        judgments=case.get("judgments",{})
        if not case.get("judgment_source") or not judgments:
            raise ValueError("Explicit suitability judgments and their source are required")
        if any(not isinstance(v,(int,float)) or not 0<=v<=3 for v in judgments.values()):
            raise ValueError("Judgments must be graded 0..3")
        rows=case.get("records",[])
        if any(not parse(r.get("observed_at")) or parse(r["observed_at"])>at for r in rows):
            raise ValueError("Future or undated observations cannot enter a replay")
        if any(parse(r.get("created_at")) and parse(r["created_at"])>at for r in rows):
            raise ValueError("Future tasks cannot enter a replay")
        start=perf_counter()
        result=rank(case["task"],rows,case["employees"],{**case.get("policy",{}),"top_n":max(1,len(case["employees"]))},at=at)
        latencies.append((perf_counter()-start)*1000)
        eligible=set(result["eligible_ids"])
        if not eligible <= judgments.keys():
            raise ValueError("All eligible candidates must have explicit judgments; missing is not failure")
        judgments={key:value for key,value in judgments.items() if key in eligible}
        pool=result["candidates"]+result["provisional"]+result["available"]
        orders={"model":[p["id"] for p in result["candidates"]],
                "least_loaded":[p["id"] for p in sorted(pool,key=lambda p:(p["priority_load"],p["id"]))],
                "experience_only":[p["id"] for p in sorted(pool,key=lambda p:(-p["similar_completed"],p["id"]))]}
        if not orders["model"]:abstentions+=1
        concentration.update(orders["model"][:k])
        for name,order in orders.items():totals[name].append(metrics(order,judgments,k))
    def average(rows):
        return {key:round(sum(v)/len(v),4) if v else None for key in ("precision_at_k","recall_at_k","ndcg_at_k","mrr")
                for v in [[row[key] for row in rows if row[key] is not None]]}
    return {"cases":len(cases),"k":k,"results":{key:average(value) for key,value in totals.items()},
            "abstentions":abstentions,"recommendation_counts":dict(concentration),
            "mean_latency_ms":round(sum(latencies)/len(latencies),3) if latencies else None,
            "note":"Only supplied judgments are evaluated; source snapshot correctness requires independent verification."}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--input",required=True);parser.add_argument("--k",type=int,default=3)
    args=parser.parse_args()
    with open(args.input,encoding="utf-8") as stream:cases=json.load(stream)
    print(json.dumps(evaluate_cases(cases,args.k),ensure_ascii=False,indent=2))
