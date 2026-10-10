"""Local indexed matching and explainable, advisory employee recommendations."""
from collections import Counter
from datetime import datetime
from similarity import normalize
from recommendation_matching import RelevanceIndex, MODEL, query_profile
from sla import estimate, parse, TZ, business_deadline


class TaskIndex(RelevanceIndex):
    def examples(self):
        pairs, seen = [], set()
        for row in self.records[:100]:
            for match in self.related(row.get("title", "") + " " + row.get("description", ""), exclude=(row["source"], row["id"]), limit=1):
                key = tuple(sorted(((row["source"], row["id"]), (match["task"]["source"], match["task"]["id"]))))
                if match["score"] >= 25 and key not in seen:
                    seen.add(key)
                    pairs.append({"task": row, "match": match})
        return sorted(pairs, key=lambda p: -p["match"]["score"])[:8]



def effective_priority(record, settings):
    tag_rules = settings.get("tag_priorities", {})
    return max([int(record.get("priority") or 0)] +
               [int(tag_rules.get(tag, 0)) for tag in record.get("tags", [])])


def analyze(records, text, settings, employees, source="diwan", category="", index=None, exclude=None):
    pool = [r for r in records if r["source"] == source]
    index = index or TaskIndex(pool)
    related = index.related(text, exclude=exclude)
    completed = [m["task"] for m in related if m["task"].get("completed")]
    votes = Counter(r["category"] for r in completed if r.get("category") and r.get("source") == source)
    selected_category = category or (votes.most_common(1)[0][0] if votes else "")
    comparable = [r for r in pool if r.get("completed") and selected_category and
                  normalize(r["category"]) == normalize(selected_category)]
    return {"related": related, "query_profile": query_profile(text, index), "model": index.model_summary(), "category": selected_category,
            "category_support": votes.get(selected_category, 0),
            "recommendations": [], "estimate": estimate(comparable),
            "scope": "accessible source records; counts are not effort estimates"}


def annotate(records, settings):
    rows = []
    for record in records:
        row = dict(record)
        row["effective_priority"] = effective_priority(row, settings)
        target = settings.get("sla_hours", {}).get(row.get("category"), 0)
        due = business_deadline(parse(row.get("created_at")), target, settings) if target else None
        row["sla_deadline"] = due.isoformat() if due else ""
        row["sla_late"] = bool(due and not row.get("completed") and due < datetime.now(TZ))
        rows.append(row)
    return rows


def data_quality(records):
    """Coverage diagnostics, not a declaration that source history is complete."""
    fingerprints=Counter((r["source"],normalize(r.get("title","")),normalize(r.get("description",""))) for r in records)
    closed=[r for r in records if r.get("completed")]
    invalid=[r for r in closed if not parse(r.get("created_at")) or not parse(r.get("completed_at")) or parse(r["completed_at"])<=parse(r["created_at"])]
    dates=[parse(r.get("created_at")) for r in records if parse(r.get("created_at"))]
    return {"records":len(records),"completed":len(closed),"invalid_completion_dates":len(invalid),
            "missing_description":sum(not r.get("description","").strip() for r in records),
            "missing_category":sum(not r.get("category","").strip() for r in records),
            "missing_executor":sum(not r.get("assignee_id") for r in records),
            "duplicate_content_groups":sum(n>1 for n in fingerprints.values()),
            "first_created":min(dates).isoformat() if dates else None,"last_created":max(dates).isoformat() if dates else None}
