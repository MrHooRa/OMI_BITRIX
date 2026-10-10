"""Selectable list columns from the caller's cached JSON; never evaluated as code."""
import re
from diwany import DiwanError

BUILTINS = [
    ("request_id", "d_request_id"), ("id", "d_task_id"), ("title", "d_category"),
    ("status_label", "d_status"), ("assignee_name", "d_column_assignee"),
    ("created_at", "d_created"), ("completed_at", "d_completed"), ("deadline", "d_due")]
DEFAULT_KEYS = ["task:" + key for key, _ in BUILTINS[:5]]
SECRET = re.compile(r"token|password|secret|authorization|cookie|webhook|api[_-]?key", re.I)


def display_fields(row):
    values = {}
    def visit(value, path="", depth=0):
        if len(values) >= 250 or depth > 5:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                if not SECRET.search(str(key)) and not any(ord(char) < 32 for char in str(key)):
                    visit(child, path + "." + str(key) if path else str(key), depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value[:10]):
                visit(child, path + "." + str(index), depth + 1)
        elif path and len(path) <= 250:
            values[path] = str(value)[:4000] if value is not None else ""
    visit(row)
    return values


def columns(store, profile):
    return store.get("diwan_columns", None, profile_id=profile) or [{"key": key, "label": ""} for key in DEFAULT_KEYS]


def validate_columns(raw):
    if not isinstance(raw, list) or not 1 <= len(raw) <= 20:
        raise DiwanError("invalid_input", 400)
    result, seen = [], set()
    for column in raw:
        if not isinstance(column, dict):
            raise DiwanError("invalid_input", 400)
        key, label = str(column.get("key", "")), str(column.get("label", "")).strip()
        valid = key in {"task:" + name for name, _ in BUILTINS} or (
            key.startswith("json:") and 5 < len(key) <= 255 and not SECRET.search(key))
        if not valid or key in seen or len(label) > 80 or any(ord(char) < 32 for char in key):
            raise DiwanError("invalid_input", 400)
        result.append({"key": key, "label": label})
        seen.add(key)
    return result


def value(record, key):
    if key.startswith("json:"):
        return record.get("display_fields", {}).get(key[5:], "")
    name = key[5:]
    return record.get(name) or (record.get("assignee_id", "") if name == "assignee_name" else "")
