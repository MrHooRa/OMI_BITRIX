import json
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path


RATING_LABELS = {
    5: {"en": "Significantly exceeds expectations", "ar": "يتجاوز التوقعات بشكل ملحوظ"},
    4: {"en": "Completed task successfully", "ar": "تم إنجاز المهمة بنجاح"},
    3: {"en": "Meets minimal requirements", "ar": "يحقق الحد الأدنى من المتطلبات"},
    2: {"en": "Needs more supervision", "ar": "يحتاج إلى إشراف أكبر"},
    1: {"en": "Task not completed", "ar": "لم يتم إنجاز المهمة"},
}

DELIVERY_LABELS = {
    "on_time": {"en": "On-time delivery", "ar": "تم التسليم في الوقت المحدد"},
    "late": {"en": "Late delivery", "ar": "تم التسليم متأخرًا"},
}

RATING_ALIASES = {
    5: ["significantly exceeds expectations", "significantly exceed expectations", "far exceeds expectations"],
    4: ["completed task successfully", "completed successfully", "task completed successfully", "successful completion"],
    3: ["meets minimal requirements", "meet minimal requirements", "minimal requirements", "meets minimum requirements", "minimum requirements"],
    2: ["needs more supervision", "need more supervision", "requires more supervision", "more supervision"],
    1: ["task not completed", "not complete task", "not completed", "incomplete task"],
}
DELIVERY_ALIASES = {
    "on_time": ["on time", "on-time", "on time delivery", "on-time delivery", "timely delivery"],
    "late": ["late", "late delivery", "delayed delivery", "delivered late"],
}


def _norm(text):
    text = unicodedata.normalize("NFKC", str(text or "")).casefold()
    text = re.sub(r"[^0-9a-z\u0600-\u06ff]+", " ", text)
    return " ".join(text.split())


def _score(label, aliases):
    label = _norm(label)
    if not label:
        return 0.0
    best = 0.0
    for alias in aliases:
        alias = _norm(alias)
        if label == alias:
            return 1.0
        if alias in label or label in alias:
            best = max(best, 0.92)
        best = max(best, SequenceMatcher(None, label, alias).ratio())
    return best


def _field_values(field):
    values = (field or {}).get("values") or {}
    if isinstance(values, dict):
        return {str(k): str(v) for k, v in values.items()}
    if isinstance(values, list):
        return {str(i): str(v) for i, v in enumerate(values)}
    return {}


def discover_review_fields(fields):
    """Discover company-specific assessment fields from the live Bitrix field schema.

    tasks.task.getFields returns standard + custom task fields and enum values.  We do
    not assume field codes: we match the portal's enum captions and retain their exact
    internal values for later tasks.task.update calls.
    """
    result = {
        "rating_field": None,
        "rating_values": {},
        "delivery_field": None,
        "delivery_values": {},
        "confidence": 0,
    }
    candidates = fields or {}
    if isinstance(candidates, dict) and "fields" in candidates and isinstance(candidates["fields"], dict):
        candidates = candidates["fields"]

    best_rating = (0.0, None, {})
    best_delivery = (0.0, None, {})
    for code, desc in (candidates or {}).items():
        values = _field_values(desc)
        if not values:
            continue

        rating_map = {}
        rating_scores = []
        used_keys = set()
        for rating, aliases in RATING_ALIASES.items():
            matches = sorted(
                ((_score(label, aliases), key) for key, label in values.items() if key not in used_keys),
                reverse=True,
            )
            if matches and matches[0][0] >= 0.70:
                rating_scores.append(matches[0][0])
                rating_map[str(rating)] = matches[0][1]
                used_keys.add(matches[0][1])
        rating_conf = (sum(rating_scores) / 5.0) if rating_scores else 0.0
        # Field title is a useful tie-breaker for generic enum captions.
        title = _norm((desc or {}).get("title"))
        if any(x in title for x in ("rating", "evaluation", "assessment", "performance", "تقييم")):
            rating_conf += 0.08
        if len(rating_map) >= 3 and rating_conf > best_rating[0]:
            best_rating = (rating_conf, str(code), rating_map)

        delivery_map = {}
        delivery_scores = []
        used_keys = set()
        for key_name, aliases in DELIVERY_ALIASES.items():
            matches = sorted(
                ((_score(label, aliases), key) for key, label in values.items() if key not in used_keys),
                reverse=True,
            )
            if matches and matches[0][0] >= 0.72:
                delivery_scores.append(matches[0][0])
                delivery_map[key_name] = matches[0][1]
                used_keys.add(matches[0][1])
        delivery_conf = (sum(delivery_scores) / 2.0) if delivery_scores else 0.0
        if any(x in title for x in ("delivery", "timeliness", "deadline", "التسليم", "الموعد")):
            delivery_conf += 0.08
        if len(delivery_map) == 2 and delivery_conf > best_delivery[0]:
            best_delivery = (delivery_conf, str(code), delivery_map)

    if best_rating[1]:
        result["rating_field"] = best_rating[1]
        result["rating_values"] = best_rating[2]
    if best_delivery[1]:
        result["delivery_field"] = best_delivery[1]
        result["delivery_values"] = best_delivery[2]
    result["confidence"] = round(max(best_rating[0], best_delivery[0]), 3)
    return result


def label_for_rating(rating, lang="en"):
    lang = "ar" if str(lang).lower().startswith("ar") else "en"
    return RATING_LABELS.get(int(rating), RATING_LABELS[3])[lang]


def label_for_delivery(value, lang="en"):
    lang = "ar" if str(lang).lower().startswith("ar") else "en"
    return DELIVERY_LABELS.get(value, DELIVERY_LABELS["on_time"])[lang]


def review_file(folder):
    return Path(folder) / "05_Evidence" / ".supervisor_review.json"


def read_review(folder):
    path = review_file(folder)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_review(folder, *, task_id, rating, delivery, feedback, action, reviewer, bitrix_field_status=None):
    path = review_file(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": str(task_id),
        "rating": int(rating),
        "delivery": str(delivery),
        "feedback": str(feedback or "").strip(),
        "action": str(action),
        "reviewer": str(reviewer or ""),
        "reviewed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "bitrix_field_status": bitrix_field_status or {},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
