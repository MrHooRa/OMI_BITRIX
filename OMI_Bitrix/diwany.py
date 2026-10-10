"""Diwan adapter following current_strcuture.py; no import-time requests."""
import copy
import json
import re
import urllib.error
import urllib.request
from urllib.parse import quote, urlencode, urlsplit

DEFAULT_FILTER = {key: "" for key in (
    "requestId", "serviceId", "from", "to", "groupCode", "employeeName",
    "nameEn", "nameAr", "name", "requestTypeCode", "taxpayer", "TIN", "TaxRegNumber")}
DEFAULT_FILTER.update(statusId=0, statusIds=[], userEmails=[])


class DiwanError(RuntimeError):
    def __init__(self, code, status=502):
        super().__init__(code)
        self.code, self.status = code, status


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise DiwanError("redirect_blocked")


def validate_config(raw):
    result = {}
    for name, methods in (("list", {"GET", "POST"}), ("detail", {"GET", "POST"}),
                          ("delegate", {"POST", "PUT", "PATCH"})):
        url = str(raw.get(name + "_url", "")).strip()
        method = str(raw.get(name + "_method", "GET" if name == "detail" else "POST")).upper()
        if method not in methods:
            raise DiwanError("invalid_method", 400)
        if url:
            parsed = urlsplit(url.replace("{task_id}", "1"))
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username
                    or parsed.password or parsed.query or parsed.fragment
                    or any(c.isspace() for c in url)):
                raise DiwanError("invalid_endpoint", 400)
            if "{" in url.replace("{task_id}", "") or "}" in url.replace("{task_id}", ""):
                raise DiwanError("invalid_endpoint", 400)
        result[name + "_url"], result[name + "_method"] = url, method
    if not result["list_url"] or "{task_id}" in result["list_url"]:
        raise DiwanError("missing_endpoint", 400)
    task_field = str(raw.get("task_id_field", "id"))
    if task_field not in {"id", "taskId", "bpmTaskId"}:
        raise DiwanError("invalid_id_field", 400)
    result["task_id_field"] = task_field
    result["assignee_field"] = str(raw.get("assignee_field", "assignTo")).strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", result["assignee_field"]):
        raise DiwanError("invalid_assignee_field", 400)
    result["supervisor_field"] = str(raw.get("supervisor_field", "")).strip()
    if result["supervisor_field"] and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", result["supervisor_field"]):
        raise DiwanError("invalid_assignee_field", 400)
    result["current_user_id"] = str(raw.get("current_user_id", "")).strip()[:200]
    result["roles_confirmed"] = raw.get("roles_confirmed") is True
    result["recipient_kind"] = "id" if raw.get("recipient_kind") == "id" else "email"
    result["delegation_confirmed"] = raw.get("delegation_confirmed") is True
    result["completed_statuses"] = [s.strip() for s in str(raw.get("completed_statuses", "")).split(",") if s.strip()]
    return result


def envelope(payload):
    if isinstance(payload, dict) and payload.get("success") is False:
        raise DiwanError("source_rejected", 400)
    if isinstance(payload, dict) and payload.get("error"):
        raise DiwanError("source_rejected", 400)
    return payload


def records_from(payload):
    envelope(payload)
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        raise DiwanError("invalid_response")
    result = payload.get("result")
    candidates = [payload.get("data"), payload.get("items"), result]
    if isinstance(result, dict):
        candidates.insert(0, result.get("data"))
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
        if isinstance(candidate, dict):
            for key in ("items", "records", "tasks"):
                if isinstance(candidate.get(key), list):
                    return candidate[key]
    raise DiwanError("invalid_response")


def detail_data(payload):
    envelope(payload)
    if not isinstance(payload, dict):
        raise DiwanError("invalid_response")
    node = payload.get("result", payload)
    if isinstance(node, dict):
        node = node.get("data", node)
    if not isinstance(node, dict):
        raise DiwanError("invalid_response")
    return node


def form_fields(data):
    form = data.get("viewForm")
    controls = form.get("controls", []) if isinstance(form, dict) else []
    fields = []
    for control in controls if isinstance(controls, list) else []:
        if not isinstance(control, dict):
            continue
        label = control.get("label") or control.get("name") or control.get("id")
        if label:
            fields.append({"id": str(control.get("id") or ""), "label": str(label),
                           "value": control.get("value")})
    return fields


def field_value(row, path, default=None):
    if path in row:
        return row[path]
    value = row
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def normalize(row, config):
    if not isinstance(row, dict) or row.get(config["task_id_field"]) in (None, ""):
        raise DiwanError("missing_task_id")
    request_data = row.get("request") if isinstance(row.get("request"), dict) else {}
    status = row.get("status") or request_data.get("status") or {}
    status_id = str(status.get("id", row.get("statusId", ""))) if isinstance(status, dict) else str(status)
    fields = form_fields(row)
    narrative = [str(row.get("description") or "")]
    # Only task narrative controls enter similarity; personal/form identity data is excluded.
    for item in fields:
        if any(label in item["label"] for label in ("سبب الطلب", "تفاصيل الطلب", "تفاصيل  الطلب", "وصف الطلب")):
            narrative.append(str(item["value"]) if not isinstance(item["value"], (dict,list)) else json.dumps(item["value"],ensure_ascii=False))
    for label in ("سبب الطلب", "تفاصيل الطلب", "وصف الطلب"):
        for prefix in ("FORM_", "FORM*"):
            value = row.get(prefix + label)
            if value:
                narrative.append(str(value))
    owner = field_value(row, config.get("supervisor_field", ""), "")
    owners = [str(v) for v in owner] if isinstance(owner,list) else ([str(owner)] if isinstance(owner,(str,int)) and owner else [])
    assignee = field_value(row, config["assignee_field"], "")
    assignee = str(assignee) if isinstance(assignee,(str,int)) else ""
    parent_path = config["assignee_field"].rsplit(".", 1)[0] if "." in config["assignee_field"] else ""
    executor = field_value(row, parent_path, {}) if parent_path else {}
    executor = executor if isinstance(executor, dict) else {}
    completed = row.get("isCompleted",request_data.get("isCompleted")) is True or status_id in config.get("completed_statuses", [])
    return {
        "source":"diwan", "id":str(row[config["task_id_field"]]), "project_id":"diwan",
        "request_id":str(row.get("requestId") or request_data.get("requestId") or ""),
        "title":str(row.get("title") or row.get("serviceNameEn") or row.get("serviceName") or request_data.get("serviceName") or row.get("requestId") or ""),
        "description":"\n".join(v for v in narrative if v),
        "category":str(row.get("serviceNameEn") or row.get("serviceName") or request_data.get("serviceName") or ""),
        "creator_id":owners[0] if owners else "", "auditor_ids":owners[1:],
        "status":status_id, "status_label":str(status.get("nameAr") or status.get("nameEn") or status_id) if isinstance(status,dict) else str(status),
        "completed":completed, "assignee_id":assignee,
        "assignee_name":str(row.get("assignToNameAr") or row.get("assignToNameEn") or executor.get("name") or ""),
        "assignee_email":str(executor.get("email") or (assignee if "@" in assignee else "")),
        "assignee_department":str(executor.get("department") or ""),
        "assignee_position":str(executor.get("position") or ""),
        "created_at":row.get("createdDate") or row.get("detail_created_date") or request_data.get("createdDate"),
        "completed_at":row.get("requestCompletedDate") or row.get("detail_completed_date") or row.get("detail_completed*date"),
        "modified_at":row.get("modifiedDate") or request_data.get("modifiedDate"),
        "deadline":row.get("dueDate") or row.get("deadline"), "priority":2 if row.get("isImportant") else 0,
        "tags":[], "fields":fields, "actions":row.get("previousActions") if isinstance(row.get("previousActions"),list) else [],
    }


class DiwanClient:
    def __init__(self, config, token, transport=None):
        self.config, self.token = config, token
        self.transport = transport

    def _request(self, url, method, payload=None):
        if not url:
            raise DiwanError("missing_endpoint", 409)
        if self.transport:
            return envelope(self.transport(url, method, payload))
        headers = {"Authorization": "Bearer " + self.token,
                   "Accept": "application/json", "Content-Type": "application/json"}
        body = None
        if method == "GET" and payload is not None:
            params = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                      for k, v in payload.items()}
            url += "?" + urlencode(params)
        elif payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode()
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=25) as response:
                data = response.read(8 * 1024 * 1024 + 1)
                if len(data) > 8 * 1024 * 1024:
                    raise DiwanError("response_too_large")
                return envelope(json.loads(data.decode("utf-8-sig")))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise DiwanError("token_invalid", 401) from None
            if exc.code == 403:
                raise DiwanError("permission_denied", 403) from None
            raise DiwanError("source_unavailable") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise DiwanError("source_unavailable") from None
        except (ValueError, UnicodeError):
            raise DiwanError("invalid_response") from None

    def list_page(self, filters=None, page=1, page_size=50):
        payload = {"pageNumber": page, "pageSize": page_size,
                   "filter": {**copy.deepcopy(DEFAULT_FILTER), **(filters or {})},
                   "orderByValue": [{"colId": "createdDate", "sort": "desc"}]}
        result = self._request(self.config["list_url"], self.config["list_method"], payload)
        return records_from(result)

    def iter_pages(self, filters=None, cancelled=lambda: False, max_pages=2000):
        seen, fingerprints = set(), set()
        for number in range(1, max_pages + 1):
            if cancelled():
                raise DiwanError("cancelled", 409)
            records = self.list_page(filters, number)
            if not records:
                return
            items = [normalize(row, self.config) for row in records]
            fingerprint = tuple(sorted(item["id"] for item in items))
            if fingerprint in fingerprints:
                raise DiwanError("pagination_stalled", 409)
            fingerprints.add(fingerprint)
            fresh = [item for item in items if item["id"] not in seen]
            if not fresh:
                raise DiwanError("pagination_stalled", 409)
            seen.update(item["id"] for item in fresh)
            yield number, fresh
        raise DiwanError("page_limit", 409)

    def iter_analysis_pages(self, filters=None, cancelled=lambda: False):
        for page, rows in self.iter_pages(filters or {}, cancelled):
            enriched=[]
            for row in rows:
                if cancelled():
                    raise DiwanError("cancelled",409)
                if self.config.get("detail_url"):
                    raw=self.details(row["id"])
                    raw.setdefault(self.config["task_id_field"],row["id"])
                    detail=normalize(raw,self.config)
                    # Preserve nonempty list metadata if the details endpoint omits it.
                    detail={k:(v if v not in (None,"",[]) else row.get(k,v)) for k,v in detail.items()}
                    detail["completed"]=row["completed"] or detail["completed"]
                    enriched.append(detail)
                else:
                    enriched.append(row)
            yield page,enriched

    def details(self, task_id):
        url = self.config["detail_url"]
        if not url:
            raise DiwanError("missing_endpoint", 409)
        if self.config["detail_method"] == "GET":
            url = url.replace("{task_id}", quote(task_id, safe="")) if "{task_id}" in url else url.rstrip("/") + "/" + quote(task_id, safe="")
            payload = None
        else:
            url = url.replace("{task_id}", quote(task_id, safe=""))
            payload = {"taskId": task_id}
        data = detail_data(self._request(url, self.config["detail_method"], payload))
        returned_id = data.get(self.config["task_id_field"])
        if returned_id is not None and str(returned_id) != task_id:
            raise DiwanError("task_id_mismatch")
        return data

    def delegate(self, task_id, request_id, employee):
        if not self.config.get("delegation_confirmed") or not self.config.get("delegate_url"):
            raise DiwanError("delegation_disabled", 409)
        payload = {"taskId": task_id, "requestId": request_id, "assignTo": employee["value"],
                   "assignToNameEn": employee.get("name_en", ""),
                   "assignToNameAr": employee.get("name_ar", "")}
        url = self.config["delegate_url"].replace("{task_id}", quote(task_id, safe=""))
        self._request(url, self.config["delegate_method"], payload)
        after = self.details(task_id)
        if str(field_value(after,self.config["assignee_field"],"") or "") != employee["value"]:
            raise DiwanError("delegation_uncertain", 409)
        return after
