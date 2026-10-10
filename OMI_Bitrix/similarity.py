import re
import unicodedata
from difflib import SequenceMatcher


AR_DIACRITICS = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]")
NON_WORD = re.compile(r"[^0-9a-zA-Z\u0600-\u06FF]+")
SPACE = re.compile(r"\s+")

STOPWORDS = {
    "the", "and", "for", "from", "with", "into", "task", "report", "data", "new",
    "في", "من", "على", "الى", "إلى", "عن", "مع", "هذا", "هذه", "مهمة", "مهام", "بيانات",
}


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text or "")).lower()
    text = AR_DIACRITICS.sub("", text).replace("ـ", "")
    for src, dst in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي"), ("ة", "ه")):
        text = text.replace(src, dst)
    text = NON_WORD.sub(" ", text)
    return SPACE.sub(" ", text).strip()


def tokens(text):
    return {x for x in normalize(text).split() if len(x) > 1 and x not in STOPWORDS}


def _matching_record(task):
    return {"source": task.get("source", "bitrix"), "id": str(task.get("id", "")),
            "title": task.get("title", ""), "description": task.get("description", ""),
            "assignee_id": str(task.get("assignee_id", task.get("responsibleId", ""))),
            "project_id": str(task.get("project_id", task.get("groupId", "")))}


# Bounded RAM-only cache: the exact visible pool is part of every cache key.
from functools import lru_cache
import json


@lru_cache(maxsize=4)
def _matching_index(key):
    from recommendation_matching import RelevanceIndex
    return RelevanceIndex(json.loads(key))


@lru_cache(maxsize=128)
def _matches(key, text, source, ident, limit):
    return _matching_index(key).related(text, exclude=(source, ident), limit=limit)


def task_similarity(a, b):
    """Use the same cleaned relevance model as the assignment workspace."""
    rows = [_matching_record(a), _matching_record(b)]
    rows[0]["id"], rows[1]["id"] = "left", "right"
    key = json.dumps(rows, sort_keys=True)
    matches = _matches(key, rows[0]["title"] + " " + rows[0]["description"], rows[0]["source"], "left", 1)
    return matches[0]["score"] if matches else 0


def attach_similarities(tasks, comparison_tasks=None, threshold=40, max_per_task=3):
    comparison_tasks = tasks if comparison_tasks is None else comparison_tasks
    rows = [_matching_record(t) for t in comparison_tasks]
    key = json.dumps(rows, sort_keys=True)
    by_id = {(r["source"], r["id"]): t for r, t in zip(rows, comparison_tasks)}
    unique = {}
    for task in tasks:
        current = _matching_record(task)
        matches = _matches(key, current["title"] + " " + current["description"],
                           current["source"], current["id"], max_per_task)
        task["similarTasks"] = []
        for match in matches:
            if match["score"] < threshold:
                continue
            other = by_id[(match["task"]["source"], match["task"]["id"])]
            task["similarTasks"].append({"id": other.get("id"), "title": other.get("title"),
                "projectName": other.get("projectName"), "responsibleName": other.get("responsibleName", ""),
                "score": match["score"]})
            pair_key = tuple(sorted(((current["source"], current["id"]),
                                     (match["task"]["source"], match["task"]["id"]))))
            if pair_key not in unique or match["score"] > unique[pair_key]["score"]:
                unique[pair_key] = {"a": task, "b": other, "score": match["score"]}
    return sorted(unique.values(), key=lambda p: -p["score"])


def search_score(task, query):
    """Return a simple local relevance score for task search."""
    q = normalize(query)
    if not q:
        return 1
    title = normalize(task.get("title"))
    description = normalize(task.get("description"))
    meta = normalize(" ".join(str(task.get(k) or "") for k in ("id", "projectName", "responsibleName")))
    hay = " ".join(x for x in (title, description, meta) if x)
    q_tokens = tokens(q)
    hay_tokens = tokens(hay)
    if q in hay:
        contains = 1.0
    else:
        contains = 0.0
    token_overlap = len(q_tokens & hay_tokens) / max(1, len(q_tokens))
    title_ratio = SequenceMatcher(None, q, title).ratio() if title else 0.0
    meta_ratio = SequenceMatcher(None, q, meta).ratio() if meta else 0.0
    return int(round(100 * min(1.0, 0.42 * contains + 0.32 * token_overlap + 0.20 * title_ratio + 0.06 * meta_ratio)))


def search_tasks(tasks, query, minimum=18):
    q = normalize(query)
    if not q:
        return list(tasks)
    scored = []
    for task in tasks:
        score = search_score(task, q)
        if score >= minimum:
            row = dict(task)
            row["searchScore"] = score
            scored.append(row)
    scored.sort(key=lambda t: (-t.get("searchScore", 0), str(t.get("deadline") or "9999")))
    return scored
