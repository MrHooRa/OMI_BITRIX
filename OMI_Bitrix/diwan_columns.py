"""Selectable list columns from the caller's cached JSON; never evaluated as code."""
import json
import re
from diwany import DiwanError, field_value, form_fields

BUILTINS = [
    ("request_id", "d_request_id"), ("id", "d_task_id"), ("title", "d_category"),
    ("status_label", "d_status"), ("assignee_name", "d_column_assignee"),
    ("created_at", "d_created"), ("completed_at", "d_completed"), ("deadline", "d_due")]
DEFAULT_KEYS = ["task:" + key for key, _ in BUILTINS[:5]]
MAX_COLUMNS = 1000
JSON_COLUMNS = """
id
platform
isOwner
requestId
serviceName
assignee
businessServiceName
itRequestId
isCompleted
isRead
status
daysRequested
createdDate
requestPendingOn
isImportant
takenActionId
actionCode
dueDate
numberOfDays
action
escalationDueDate
escalationNumberOfDays
escelationAction
task_details
detail_status
detail_service_name
detail_created_date
detail_completed*date
FORM*نوع الطلب
FORM*الوكالة
FORM*القطاع
FORM*الإدارة
FORM*التاريخ
FORM*منطقة العمل
FORM*وصف منطقة العمل
FORM*سبب الطلب
FORM*تفاصيل الطلب
FORM*هل يحتوي الطلب على تفاصيل معلومات المكلف؟
FORM*المرفقات
employee.id
employee.personId
employee.name
employee.photo
employee.email
employee.department
employee.position
employee.domain
request.requestId
request.platform
request.employee
request.serviceName
request.serviceImage
request.displayServiceName
request.itRequestId
request.isCompleted
request.status.id
request.status.name
request.status.nameEn
request.status.nameAr
request.status.statusCode
request.status.statusColor
request.formCode
request.daysRequested
request.createdDate
request.modifiedDate
request.requestPendingOn.name
request.requestPendingOn.nameAr
request.requestPendingOn.nameEn
request.requestPendingOn.pendingOnCode
request.isRequestAgain
request.pageCode
request.leaveRequestId
""".strip().splitlines()
SECRET = re.compile(r"token|password|secret|authorization|cookie|webhook|api[_-]?key", re.I)


def safe_json(value, depth=0):
    if depth > 5:
        return None
    if isinstance(value, dict):
        return {str(key): safe_json(child, depth + 1) for key, child in list(value.items())[:100]
                if not SECRET.search(str(key)) and not any(ord(char) < 32 for char in str(key))}
    if isinstance(value, list):
        return [safe_json(child, depth + 1) for child in value[:100]]
    return value


def display_value(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list, bool)):
        return json.dumps(safe_json(value), ensure_ascii=False)[:4000]
    return str(value)[:4000]


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
            values[path] = display_value(value)
    visit(row)
    missing = object()
    for key in JSON_COLUMNS:
        value = field_value(row, key, missing)
        if value is missing and key == "detail_completed*date":
            value = row.get("detail_completed_date", missing)
        if value is missing and key.startswith("FORM*"):
            value = row.get("FORM_" + key[5:], missing)
        if value is not missing:
            values[key] = display_value(value)
    controls = {}
    for field in form_fields(row):
        key = "FORM*" + field["label"]
        if len(key) <= 250 and not SECRET.search(key):
            controls.setdefault(key, []).append(field["value"])
    for key, fields in controls.items():
        if len(values) < 350:
            values.setdefault(key, display_value(fields[0] if len(fields) == 1 else fields))
    return values


def detail_fields(row):
    """Display aliases for a verified details response, separate from analysis text."""
    values = display_fields(row)
    aliases = {
        "task_details": row,
        "detail_status": row.get("status"),
        "detail_service_name": row.get("serviceName") or field_value(row, "request.serviceName"),
        "detail_created_date": row.get("createdDate") or field_value(row, "request.createdDate"),
        "detail_completed*date": row.get("requestCompletedDate") or row.get("completedDate") or row.get("detail_completed_date"),
    }
    for key, value in aliases.items():
        if key not in values and value is not None:
            values[key] = display_value(value)
    return values


def columns(store, profile):
    return store.get("diwan_columns", None, profile_id=profile) or [{"key": key, "label": ""} for key in DEFAULT_KEYS]


def validate_columns(raw):
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_COLUMNS:
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
