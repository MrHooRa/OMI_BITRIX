"""Explainable, offline employee ranking. Scores are not probabilities."""
from collections import defaultdict
from datetime import datetime
from math import log1p

from sla import parse, TZ, estimate
from similarity import normalize
from recommendation_matching import RelevanceIndex, MODEL, query_profile, group_related, term_counts
from employee_insights import task_labels, coverage, complementary_team
from task_affinity import summarize_open, sort_open, mentioned_periods

VERSION = "task-scoped-3.10"
def pending_review(task):
    return bool(task.get("pending_review", task.get("source", "bitrix") == "bitrix" and task.get("status") == "4"))


DEFAULT_WEIGHTS = {"similarity": 50, "experience": 20, "capacity": 30}


def rank(task, records, employees, policy=None, at=None, prepared=None, workload=None, open_index=None):
    policy = policy or {}
    at = at or datetime.now(TZ)
    weights = policy.get("weights", DEFAULT_WEIGHTS)
    # Reuse only a time-valid index which could not have learned from the target.
    target_key = (task.get("source","bitrix"),task.get("id"))
    invalid_index = prepared is not None and (not prepared.completed_valid or
        (prepared.latest_completion and prepared.latest_completion >= at) or target_key in prepared.identities)
    pool = prepared.records if prepared is not None else records
    if prepared is None or invalid_index:
        completed = [r for r in pool if r.get("completed") and
            (r.get("source","bitrix"),r.get("id")) != target_key and parse(r.get("completed_at")) and
            parse(r["completed_at"]) < at and parse(r.get("created_at")) and
            parse(r["created_at"]) < parse(r["completed_at"])]
        index = RelevanceIndex(completed, domain_rules=prepared.domain_rules if prepared else None, at=at)
    else:
        completed, index = prepared.records, prepared
    requested_labels = index.classify(task.get("title", "") + " " + task.get("description", ""))
    matches = index.related(task.get("title", "") + " " + task.get("description", ""), exclude=(task.get("source", "bitrix"), task.get("id")), limit=300)
    evidence = defaultdict(list)
    for item in matches:
        if item["score"] >= 16 and parse(item["task"].get("completed_at")) and parse(item["task"]["completed_at"]) < at:
            evidence[item["task"].get("assignee_id", "")].append(item)
    active = defaultdict(list) if workload is None else workload
    for record in (records if workload is None else []):
        if (not parse(record.get("created_at")) or parse(record["created_at"]) <= at) and not record.get("completed") and not record.get("awaiting_executor") and not pending_review(record) and (record.get("source", "bitrix"), record.get("id")) != (task.get("source", "bitrix"), task.get("id")):
            active[record.get("assignee_id", "")].append(record)
    open_rows = [r for r in records if not r.get("completed") and not r.get("awaiting_executor")
                 and not pending_review(r) and (not parse(r.get("created_at")) or parse(r["created_at"]) <= at)]
    if open_index is not None and open_index.domain_model is not index.domain_model:
        open_index = RelevanceIndex(open_index.records,domain_rules=index.domain_rules,domain_model=index.domain_model)
    open_matches = (open_index or RelevanceIndex(open_rows, domain_rules=index.domain_rules, domain_model=index.domain_model)).related(
        task.get("title", "") + " " + task.get("description", ""), exclude=(task.get("source", "bitrix"), task.get("id")))
    exposure = defaultdict(list)
    for match in open_matches:
        row = match["task"]
        created = parse(row.get("created_at"))
        if row.get("completed") or row.get("awaiting_executor") or pending_review(row) or (created and created > at):
            continue
        exposure[row.get("assignee_id", "")].append(match)
    candidates, provisional, available, excluded, related_excluded = [], [], [], [], []
    open_affinity = []
    today = at.date().isoformat()
    for employee in employees:
        ident = str(employee["id"])
        reasons = []
        if not employee.get("enabled"):
            reasons.append("eligibility_unconfirmed")
        if not employee.get("active", True):
            reasons.append("inactive")
        projects = employee.get("projects", [])
        if str(task.get("project_id", "")) not in projects:
            reasons.append("project_not_allowed")
        categories = employee.get("categories", [])
        if categories and normalize(task.get("category", "")) not in {normalize(c) for c in categories}:
            reasons.append("category_not_allowed")
        if employee.get("away_from") and employee["away_from"] <= today <= employee.get("away_to", ""):
            reasons.append("unavailable")
        tasks = [r for r in active.get(ident, []) if (not parse(r.get("created_at")) or parse(r["created_at"]) <= at) and (r.get("source", "bitrix"), r.get("id")) != (task.get("source", "bitrix"), task.get("id"))]
        if reasons:
            excluded.append({"id": ident, "name": employee["name"], "reasons": reasons})
            related = evidence[ident] or exposure[ident]
            if related:
                related_excluded.append({"id": ident, "name": employee["name"], "reasons": reasons,
                    "evidence_level": "eligibility_blocked", "similar_completed": len(evidence[ident]),
                    "similar_open": len(exposure[ident]), "active_tasks": len(tasks),
                    "examples": [{"id": m["task"]["id"], "source": m["task"].get("source", "bitrix"), "title": m["task"]["title"], "similarity": m["score"],
                                  "shared_terms": m["shared_terms"]} for m in related[:5]]})
            continue
        if exposure[ident]:
            open_affinity.append(summarize_open(exposure[ident], employee, len(evidence[ident]), len(tasks)))
        examples = sorted(evidence[ident], key=lambda m: -m["score"])
        # Copies cannot buy ranking credit; explicit periods retain real recurring cycles.
        patterns = {}
        for match in examples:
            item = match["task"]
            key = (tuple(sorted(term_counts(item.get("title","")))), tuple(sorted(term_counts(item.get("description","")))),
                tuple(sorted(t["id"] for t in match.get("labels",[]) if t["type"]=="TASK_TYPE")),tuple(mentioned_periods(item)))
            patterns.setdefault(key,match)
        independent = list(patterns.values())
        similarity = sum(m["score"] for m in independent[:3]) / max(1, min(3, len(independent))) / 100
        coverage_info = coverage(requested_labels, [m["task"] for m in examples])
        observed = {t["id"] for m in examples for t in m.get("labels", [])}
        coverage_info["matched"] = [t for t in coverage_info["requested"] if t["id"] in observed]
        coverage_info["missing"] = [t for t in coverage_info["requested"] if t["id"] not in observed]
        coverage_info["ratio"] = len(coverage_info["matched"]) / len(coverage_info["requested"]) if coverage_info["requested"] else None
        lexical_similarity = similarity
        if examples and coverage_info["ratio"] is not None:
            similarity = .75 * similarity + .25 * coverage_info["ratio"]
        experience = min(1, log1p(len(independent)) / log1p(10))
        priority_load = sum(1.5 if max([int(r.get("priority") or 0)] + [int(policy.get("tag_priorities", {}).get(tag, 0)) for tag in r.get("tags", [])]) >= 2 else 1 for r in tasks)
        spare = 1 / (1 + priority_load)
        components = {"similarity": round(similarity * weights["similarity"], 2),
                      "experience": round(experience * weights["experience"], 2),
                      "capacity": round(spare * weights["capacity"], 2)}
        valid_deadlines = [m["task"] for m in examples if parse(m["task"].get("deadline"))]
        on_time = sum(parse(r["completed_at"]) <= parse(r["deadline"]) for r in valid_deadlines)
        primary_ids = {(m["task"].get("source","bitrix"),m["task"]["id"]) for m in independent}
        display_examples = independent + [m for m in examples if (m["task"].get("source","bitrix"),m["task"]["id"]) not in primary_ids]
        candidate = {"id": ident, "name": employee["name"],
            "person_id": employee.get("person_id"), "linked_sources": employee.get("linked_sources", []),
            "score": round(sum(components.values()), 2), "components": components,
            "coverage": coverage_info, "retrieval_similarity": round(100 * lexical_similarity, 2),
            "lexical_similarity": round(100 * lexical_similarity, 2),
            "topics": index.classify(" ".join(m["task"].get("title", "") + " " + m["task"].get("description", "") for m in examples[:20])),
            "evidence_patterns": len(independent),
            "evidence_level": "historical" if len(independent) >= 3 else "repeated" if len(examples) >= 3 else "limited" if examples else "cold_start",
            "similar_completed": len(examples), "active_tasks": len(tasks),
            "priority_load": priority_load,
            "duration": estimate([m["task"] for m in examples]),
            "observed_deadline_results": {"samples": len(valid_deadlines), "on_time": on_time},
            "examples": [{"id": m["task"]["id"], "source": m["task"].get("source", "bitrix"), "title": m["task"]["title"], "similarity": m["score"], "shared_terms": m["shared_terms"], "lexical_score": m.get("lexical_score"), "bm25_score": m.get("bm25_score"), "action_coverage": m.get("action_coverage"), "concept_score": m.get("concept_score"), "method": m.get("method"), "semantic_cosine": m.get("semantic_cosine"), "labels": m.get("labels", [])} for m in display_examples[:5]]}
        if examples:
            candidates.append(candidate)
        elif exposure[ident]:
            related = exposure[ident]
            candidate.update(evidence_level="open_only", score=None, similar_open=len(related),
                relevance=related[0]["score"],
                examples=[{"id": m["task"]["id"], "source": m["task"].get("source", "bitrix"), "title": m["task"]["title"], "similarity": m["score"],
                           "shared_terms": m["shared_terms"]} for m in related[:5]])
            provisional.append(candidate)
        else:
            candidate.update(score=None, evidence_level="no_relevance", examples=[])
            available.append(candidate)
    candidates.sort(key=lambda c: (-c["score"], c["active_tasks"], c["id"]))
    provisional.sort(key=lambda c: (-c["relevance"], c["active_tasks"], c["id"]))
    available.sort(key=lambda c: (c["active_tasks"], c["id"]))
    eligible = candidates + provisional + available
    return {"version": VERSION, "model": {**index.model_summary(), "learned_terms": len(index.domain_model.associations)},
            "query_profile": query_profile(task.get("title", "") + " " + task.get("description", ""), index), "task_labels": requested_labels,
            "open_affinity": sort_open(open_affinity), "team": complementary_team(candidates, requested_labels), "at": at.isoformat(), "candidates": candidates[:policy.get("top_n", 3)],
            "provisional": provisional[:policy.get("top_n", 3)], "available": available, "related_excluded": related_excluded,
            "eligible_count": len(eligible), "eligible_ids": [c["id"] for c in eligible],
            "outcome": "recommended" if candidates else "provisional_only" if provisional else "insufficient_evidence", "excluded": excluded, "weights": weights,
            "completed_records": len(completed), "scope": "accessible selected projects",
            "limitations": ["assignee_at_completion_unverified", "deadline_history_unverified",
                            "quality_not_used", "score_not_probability"]}


def task_supervisors(task):
    """Task owner and explicitly listed observers, never global project roles."""
    return {str(value) for value in [task.get("creator_id"), *task.get("auditor_ids", [])]
            if value not in (None, "", 0, "0")}


def assignment_state(task, policy, previous=None):
    if task.get("completed") or pending_review(task):
        return "closed" if task.get("completed") else "pending_review"
    executor = str(task.get("assignee_id") or "")
    supervisors = task_supervisors(task)
    decision = (previous or {}).get("decision") or {}
    if decision.get("expected_assignee") == executor and decision.get("expected_creator") == task.get("creator_id"):
        if decision.get("kind") == "self" and decision.get("actor") == executor:
            return "self_assigned"
        if decision.get("kind") == "assigned" and executor not in supervisors:
            return "assigned"
        if decision.get("kind") == "needs_assignment":
            return "needs_assignment"
    if not executor or executor == "0" or executor in supervisors:
        return "needs_assignment"
    return "assigned"


def validate_policy(raw):
    if not isinstance(raw, dict):
        raise ValueError("Invalid policy")
    clean = {"employees": [], "weights": {}, "intake_ids": [], "supervisor_ids": [],
             "data_fields": {}, "top_n": int(raw.get("top_n", 3)), "category_field": str(raw.get("category_field", "")).strip()}
    if not 1 <= clean["top_n"] <= 10:
        raise ValueError("Top N must be between 1 and 10")
    import re
    if clean["category_field"] and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", clean["category_field"]):
        raise ValueError("Invalid field code")
    mapping = raw.get("data_fields", {})
    if not isinstance(mapping,dict):raise ValueError("Invalid data field mapping")
    for key,code in mapping.items():
        if key not in {"quality","delivery","team","department","task_type","effort","reopened"} or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,99}", str(code)):
            raise ValueError("Invalid data field mapping")
        clean["data_fields"][key]=str(code)
    for key in ("intake_ids", "supervisor_ids"):
        values = raw.get(key, [])
        if not isinstance(values, list) or len(values) > 500 or any(not str(v).isdigit() or int(v) < 1 for v in values):
            raise ValueError("Invalid user IDs")
        clean[key] = sorted(set(str(int(v)) for v in values))
    if not isinstance(raw.get("weights", {}), dict):
        raise ValueError("Invalid weights")
    for key, default in DEFAULT_WEIGHTS.items():
        value = float(raw.get("weights", {}).get(key, default))
        if not 0 <= value <= 100:
            raise ValueError("Invalid weight")
        clean["weights"][key] = value
    if abs(sum(clean["weights"].values()) - 100) > .01:
        raise ValueError("Weights must sum to 100")
    entries = raw.get("employees", [])
    if not isinstance(entries, list) or len(entries) > 500:
        raise ValueError("Invalid directory")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("projects", []), list) or not isinstance(entry.get("categories", []), list):
            raise ValueError("Invalid employee eligibility lists")
        ident = str(entry.get("id", ""))
        if not ident.isdigit() or int(ident) < 1 or ident in seen:
            raise ValueError("Invalid or duplicate employee")
        seen.add(ident)
        row = {"id": ident, "name": str(entry.get("name") or ident)[:200],
               "enabled": entry.get("enabled") is True, "active": entry.get("active") is not False,
               "projects": [str(p) for p in entry.get("projects", [])],
               "categories": [str(c)[:200] for c in entry.get("categories", [])],
               "away_from": str(entry.get("away_from") or ""), "away_to": str(entry.get("away_to") or "")}
        if len(row["projects"]) > 500 or any(not p.isdigit() for p in row["projects"]) or len(row["categories"]) > 100:
            raise ValueError("Invalid eligibility")
        if bool(row["away_from"]) != bool(row["away_to"]):
            raise ValueError("Specify both absence dates")
        if row["away_from"]:
            from datetime import date
            if date.fromisoformat(row["away_from"]) > date.fromisoformat(row["away_to"]):
                raise ValueError("Invalid absence interval")
        clean["employees"].append(row)
    return clean
