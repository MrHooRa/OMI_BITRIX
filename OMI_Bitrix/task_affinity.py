"""Describe observed open-work proximity without inventing completed experience."""
import re
from recommendation_matching import group_related
from similarity import normalize

MONTHS = (
    ("january", "يناير"), ("february", "فبراير"), ("march", "مارس"),
    ("april", "ابريل"), ("may", "مايو"), ("june", "يونيو"),
    ("july", "يوليو"), ("august", "اغسطس"), ("september", "سبتمبر"),
    ("october", "اكتوبر"), ("november", "نوفمبر"), ("december", "ديسمبر"),
)


def mentioned_periods(row):
    # Titles specify the work period. Creation/deadline dates and generic
    # descriptions must never be mistaken for independently performed cycles.
    title = re.sub(r"\[OMI[^\]]*\]|https?://\S+", " ", row.get("title", ""), flags=re.I)
    clean = normalize(title)
    result = set()
    for month, names in enumerate(MONTHS, 1):
        for name in names:
            for match in re.finditer(r"(?<!\w)" + re.escape(name) + r"(?!\w)(?:\s+(?:عام\s+|سنه\s+)?(20[0-9]{2}))?", clean):
                year = match.group(1)
                result.add(f"{year or 'unspecified'}-{month:02d}")
    return sorted(result)


def summarize_open(matches, person, completed_count, active_tasks):
    groups = group_related(matches)
    periods = sorted({period for item in groups for period in mentioned_periods(item["task"])})
    return {"id": person["id"], "name": person["name"], "basis": "open_work_only",
            "text_similarity": max(item["score"] for item in matches),
            "similar_open": len(matches), "content_patterns": len(groups),
            "mentioned_periods": periods, "similar_completed": completed_count,
            "active_tasks": active_tasks, "examples": [
                {"id": item["task"]["id"], "source": item["task"].get("source", "bitrix"), "title": item["task"]["title"],
                 "similarity": item["score"], "status": item["task"].get("status"),
                 "created_at": item["task"].get("created_at"),
                 "completed_at": item["task"].get("completed_at"),
                 "mentioned_periods": mentioned_periods(item["task"]),
                 "duplicate_tasks": item["duplicate_tasks"]} for item in groups[:5]]}


def sort_open(rows):
    # Recurrence breaks equal text matches only. Neither frequency nor spare
    # capacity can make unrelated work relevant or manufacture success evidence.
    return sorted(rows, key=lambda row: (-row["text_similarity"],
        -len(row["mentioned_periods"]), -row["content_patterns"], row["active_tasks"], row["id"]))
