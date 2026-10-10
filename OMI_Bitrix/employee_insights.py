"""Local typed evidence inspired by the reference discovery workflow.

Labels describe observed tasks, never certified skills or personal performance.
"""
import re
from collections import Counter, defaultdict
from functools import lru_cache
from similarity import normalize
from task_language import language_text, scope_text

# Stable IDs, bilingual display names, explicit locally maintained phrases.
TAXONOMY = [
    ("reconciliation", "TASK_TYPE", "المطابقة والتسوية", "Reconciliation", "مطابقه|تسويه|reconcile|reconciliation|reconciling"),
    ("extraction", "TASK_TYPE", "استخراج البيانات", "Data extraction", "استخراج|استخراح|extract|extraction"),
    ("analytics", "TASK_TYPE", "تحليل البيانات", "Data analysis", "تحليل|analysis|analytics|analyze|analyse"),
    ("review", "TASK_TYPE", "المراجعة", "Review", "مراجعه|review|audit|تدقيق"),
    ("requirements", "TASK_TYPE", "المتطلبات", "Requirements", "متطلبات|requirements"),
    ("integration", "TASK_TYPE", "التكامل", "Integration", "تكامل|integration|etl"),
    ("troubleshooting", "TASK_TYPE", "تشخيص الأعطال وإصلاحها", "Troubleshooting", "تشخيص|اصلاح|صيانة|diagnose|diagnosis|repair|troubleshooting|failure|outage"),
    ("configuration", "TASK_TYPE", "التهيئة والإعداد", "Configuration", "تهيئه|configuration|configure|setup|تهيئة"),
    ("documentation", "TASK_TYPE", "التوثيق", "Documentation", "توثيق|documentation"),
    ("power_bi", "SYSTEM_OR_TOOL", "Power BI", "Power BI", "power bi|powerbi|باور بي اي|باور بي آي"),
    ("excel", "SYSTEM_OR_TOOL", "Excel", "Excel", "excel|اكسل|اكسيل"),
    ("python", "SYSTEM_OR_TOOL", "Python", "Python", "python|بايثون"),
    ("sql", "SYSTEM_OR_TOOL", "SQL", "SQL", "sql|اس كيو ال"),
    ("sap", "SYSTEM_OR_TOOL", "SAP", "SAP", "sap|ساب"),
    ("api", "SYSTEM_OR_TOOL", "API", "API", "api|واجهه برمجه"),
    ("report", "DELIVERABLE_TYPE", "تقرير", "Report", "تقرير|تقارير|report|reports"),
    ("dashboard", "DELIVERABLE_TYPE", "لوحة مؤشرات", "Dashboard", "لوحه مؤشرات|لوحه معلومات|dashboard"),
    ("data_quality", "CONCEPT", "جودة البيانات", "Data quality", "جوده بيانات|جوده البيانات|data quality"),
    ("governance", "CONCEPT", "حوكمة البيانات", "Data governance", "حوكمه|governance"),
]
TOPIC_TYPES = {"BUSINESS_DOMAIN", "SYSTEM_OR_TOOL", "CONCEPT"}
CLITIC_ANCHORS = {normalize(alias) for _, _, _, _, aliases in TAXONOMY
                  for alias in aliases.split("|") if " " not in alias}


def _words(text):
    text = re.sub(r"\[OMI[^\]]*\]|https?://\S+", " ", str(text or ""), flags=re.I)
    text = re.sub(r"(?<!\w)[\w-]*\d[\w-]*(?!\w)", " ", text)
    words = language_text(text).split()
    cleaned = []
    for word in words:
        for prefix in ("وبال", "وال", "بال", "لل", "ال"):
            if word.startswith(prefix) and len(word) - len(prefix) >= 3:
                word = word[len(prefix):]
                break
        if word[:1] in {"ب", "و", "ف", "ل"} and word[1:] in CLITIC_ANCHORS:
            word = word[1:]
        cleaned.append(word)
    return " " + " ".join(cleaned) + " "


_TAXONOMY_PHRASES = [(ident, tuple(_words(alias) for alias in aliases.split("|")))
                     for ident, _, _, _, aliases in TAXONOMY]


@lru_cache(maxsize=2048)
def _classify(text):
    clean = _words(text)
    return tuple(ident for ident, phrases in _TAXONOMY_PHRASES
                 if any(phrase in clean for phrase in phrases))


def classify(text):
    scoped, _ = scope_text(text)
    ids = set(_classify(scoped[:12000]))
    return [{"id": ident, "type": kind, "ar": ar, "en": en, "basis": "local_rule"}
            for ident, kind, ar, en, _ in TAXONOMY if ident in ids]


def task_labels(row):
    return classify(str(row.get("title") or "") + " " + str(row.get("description") or ""))


def coverage(requested, rows):
    # Tools/general work types cannot manufacture completed domain experience.
    requested = [tag for tag in requested if tag["type"] in TOPIC_TYPES]
    observed = {tag["id"] for row in rows for tag in task_labels(row)}
    matched = [tag for tag in requested if tag["id"] in observed]
    return {"requested": requested, "matched": matched,
            "missing": [tag for tag in requested if tag["id"] not in observed],
            "ratio": len(matched) / len(requested) if requested else None}


def profiles(employees, completed, active, detail_id=None, classifier=None):
    labels_for = (lambda r: classifier(r.get("title", "") + " " + r.get("description", ""))) if classifier else task_labels
    done = defaultdict(list)
    opened = defaultdict(list)
    for row in completed:
        done[str(row.get("assignee_id") or "")].append(row)
    for row in active:
        if not row.get("completed") and not row.get("awaiting_executor") and not row.get("pending_review") and not (row.get("source", "bitrix") == "bitrix" and row.get("status") == "4"):
            opened[str(row.get("assignee_id") or "")].append(row)
    result = []
    for employee in employees:
        ident = str(employee["id"])
        counts = Counter(); labels = {}
        unique = {(r.get("source"), r["id"]): r for r in done[ident]}
        for row in unique.values():
            for label in labels_for(row):
                labels[label["id"]] = label
                counts[label["id"]] += 1
        topics = [{**labels[key], "count": count} for key, count in counts.most_common()]
        detail_rows = sorted(unique.values(), key=lambda r: r.get("completed_at") or "", reverse=True) if detail_id is None or ident == detail_id else []
        result.append({**employee, "completed_count": len(unique), "active_count": len(opened[ident]),
                       "topics": topics, "evidence_basis": "observed_completed_tasks",
                       "tasks": [{"id": r["id"], "title": r.get("title", ""), "source": r.get("source"),
                                  "completed_at": r.get("completed_at"), "source_assignee_id": r.get("source_assignee_id", r.get("assignee_id")), "labels": labels_for(r)}
                                 for r in detail_rows]})
    return result


def complementary_team(candidates, requested, limit=3):
    """Advisory complementary completed evidence; no group mutation or lead inference."""
    needed = {tag["id"] for tag in requested if tag["type"] in TOPIC_TYPES}
    remaining = set(needed); chosen = []; pool = list(candidates)
    while remaining and pool and len(chosen) < limit:
        best = max(pool, key=lambda c: (len({t["id"] for t in c["coverage"]["matched"]} & remaining), c["score"]))
        gain = {t["id"] for t in best["coverage"]["matched"]} & remaining
        if not gain:
            break
        chosen.append({"id": best["id"], "name": best["name"], "contributes": sorted(gain)})
        remaining -= gain
        pool.remove(best)
    return {"members": chosen if len(chosen) > 1 else [],
            "missing": [tag for tag in requested if tag["id"] in remaining], "advisory_only": True}
