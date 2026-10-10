import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, urlunparse


class BitrixError(RuntimeError):
    pass


class BitrixClient:
    """Small Bitrix24 incoming-webhook client using only the standard library."""

    def __init__(self, webhook_url, timeout=20):
        self.webhook_url = self.normalize_webhook(webhook_url)
        self.timeout = timeout

    @staticmethod
    def normalize_webhook(url):
        url = (url or "").strip()
        if not url:
            raise BitrixError("Webhook URL is empty.")
        if not url.startswith("https://"):
            raise BitrixError("Bitrix24 webhook must use HTTPS.")
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p]
        try:
            rest_index = parts.index("rest")
        except ValueError as exc:
            raise BitrixError("Expected a Bitrix24 incoming webhook URL containing /rest/.") from exc
        tail = parts[rest_index + 1 :]
        if tail and tail[0] == "api":
            tail = tail[1:]
        if len(tail) < 2:
            raise BitrixError("Webhook URL must include the Bitrix user id and webhook token.")
        user_id, token = tail[0], tail[1]
        root_path = "/" + "/".join(parts[: rest_index + 1] + [user_id, token]) + "/"
        return urlunparse((parsed.scheme, parsed.netloc, root_path, "", "", ""))

    def _v3_root(self):
        parsed = urlparse(self.webhook_url)
        parts = [p for p in parsed.path.split("/") if p]
        rest_index = parts.index("rest")
        path = "/" + "/".join(parts[: rest_index + 1] + ["api"] + parts[rest_index + 1 :]) + "/"
        return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))

    def _call_raw(self, method, params=None, v3=False):
        root = self._v3_root() if v3 else self.webhook_url
        url = root + method
        data = json.dumps(params or {}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
                err = parsed.get("error")
                detail = parsed.get("error_description")
                if isinstance(err, dict):
                    detail = detail or err.get("message") or err.get("code")
                detail = detail or str(err) or body
            except Exception:
                detail = body or str(exc)
            raise BitrixError(f"Bitrix24 HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BitrixError(f"Cannot reach Bitrix24: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise BitrixError("Bitrix24 returned a non-JSON response.") from exc

        if isinstance(payload, dict) and payload.get("error"):
            err = payload["error"]
            detail = payload.get("error_description")
            if isinstance(err, dict):
                detail = detail or err.get("message") or err.get("code") or str(err)
            raise BitrixError(str(detail or err))
        return payload

    def call(self, method, params=None, v3=False):
        payload = self._call_raw(method, params, v3=v3)
        return payload.get("result", payload)

    def current_user(self):
        return self.call("user.current")

    def projects(self):
        items, start = [], 0
        while True:
            payload = self._call_raw(
                "sonet_group.get",
                {"ORDER": {"NAME": "ASC"}, "FILTER": {"ACTIVE": "Y", "CLOSED": "N"}, "start": start},
            )
            result = payload.get("result", [])
            items.extend(result)
            next_start = payload.get("next")
            if next_start is None:
                break
            start = int(next_start)
        projects = [g for g in items if str(g.get("PROJECT", "Y")).upper() == "Y"]
        return [
            {
                "id": str(g.get("ID")),
                "name": g.get("NAME") or f"Project {g.get('ID')}",
                "members": g.get("NUMBER_OF_MEMBERS"),
                "description": g.get("DESCRIPTION") or "",
            }
            for g in projects
        ]

    def project_members(self, project_ids):
        """Return distinct active users across selected projects.

        Group membership comes from sonet_group.user.get; names are resolved with
        user.get. Project roles are kept because they are useful context for a
        supervisor reassigning work.
        """
        membership = {}
        for project_id in [str(x) for x in project_ids]:
            try:
                rows = self.call("sonet_group.user.get", {"ID": int(project_id)}) or []
            except BitrixError:
                continue
            for row in rows:
                uid = str(row.get("USER_ID") or row.get("userId") or "")
                if not uid:
                    continue
                item = membership.setdefault(uid, {"id": uid, "roles": {}, "projects": []})
                item["roles"][project_id] = row.get("ROLE") or row.get("role") or "K"
                if project_id not in item["projects"]:
                    item["projects"].append(project_id)

        names = self.users_by_ids(membership.keys())
        result = []
        for uid, item in membership.items():
            item["name"] = names.get(uid, f"Employee {uid}")
            result.append(item)
        result.sort(key=lambda x: x["name"].casefold())
        return result

    @staticmethod
    def _camel(name):
        if not name:
            return name
        if "_" not in name:
            return name[0].lower() + name[1:] if name[0].isupper() else name
        parts = name.lower().split("_")
        return parts[0] + "".join(p.title() for p in parts[1:])

    @classmethod
    def _normalize_task(cls, task):
        return {cls._camel(k): v for k, v in (task or {}).items()}

    def _task_list_for_filter(self, project_ids, extra_filter, include_completed=False):
        by_id = {}
        select = [
            "ID", "TITLE", "DESCRIPTION", "STATUS", "subStatus", "DEADLINE", "CREATED_DATE",
            "CHANGED_DATE", "STATUS_CHANGED_DATE", "DATE_START", "CLOSED_DATE", "RESPONSIBLE_ID",
            "CREATED_BY", "GROUP_ID", "PRIORITY", "TIME_ESTIMATE", "ALLOW_TIME_TRACKING", "MARK",
            "AUDITORS", "ACCOMPLICES", "TASK_CONTROL", "ADD_IN_REPORT", "TAGS", "CHAT_ID",
        ]
        for project_id in [str(x) for x in project_ids]:
            start = 0
            while True:
                task_filter = {"GROUP_ID": int(project_id), **extra_filter}
                if not include_completed:
                    task_filter["!STATUS"] = 5
                payload = self._call_raw(
                    "tasks.task.list",
                    {
                        "order": {"DEADLINE": "asc", "PRIORITY": "desc", "ID": "desc"},
                        "filter": task_filter,
                        "select": select,
                        "params": {"WITH_RESULT_INFO": True},
                        "start": start,
                    },
                )
                raw_result = payload.get("result", {})
                tasks = raw_result.get("tasks") if isinstance(raw_result, dict) else raw_result
                for task in tasks or []:
                    normalized = self._normalize_task(task)
                    by_id[str(normalized.get("id"))] = normalized
                next_start = payload.get("next")
                if next_start is None:
                    break
                start = int(next_start)
        return list(by_id.values())

    def assigned_tasks(self, user_id, project_ids):
        return self._task_list_for_filter(project_ids, {"RESPONSIBLE_ID": int(user_id)}, include_completed=False)

    def supervised_tasks(self, user_id, project_ids, completed_days=90):
        """Tasks where current user is creator and/or observer.

        Active tasks are always included. Recent completed tasks are also included
        for supervisor statistics/reporting. A person may simultaneously be an
        assignee on other tasks; role separation is done per task in app.py.
        """
        by_id = {}

        def merge(tasks, source):
            for task in tasks:
                tid = str(task.get("id"))
                existing = by_id.get(tid)
                if existing:
                    sources = set(str(existing.get("supervisionSource") or "").split("+"))
                    sources.add(source)
                    existing["supervisionSource"] = "+".join(sorted(x for x in sources if x))
                else:
                    task["supervisionSource"] = source
                    by_id[tid] = task

        merge(self._task_list_for_filter(project_ids, {"CREATED_BY": int(user_id)}, include_completed=False), "creator")
        merge(self._task_list_for_filter(project_ids, {"AUDITOR": int(user_id)}, include_completed=False), "observer")

        if int(completed_days or 0) > 0:
            since = (datetime.now(timezone.utc) - timedelta(days=int(completed_days))).date().isoformat()
            for field, source in (("CREATED_BY", "creator"), ("AUDITOR", "observer")):
                try:
                    merge(
                        self._task_list_for_filter(
                            project_ids,
                            {field: int(user_id), "STATUS": 5, ">=CLOSED_DATE": since},
                            include_completed=True,
                        ),
                        source,
                    )
                except BitrixError:
                    # Some portals reject operator/date combinations. Reporting
                    # remains useful with the active/current cache in that case.
                    pass
        return list(by_id.values())

    def users_by_ids(self, user_ids):
        result = {}
        for user_id in sorted({str(x) for x in user_ids if x not in (None, "", 0, "0")}):
            try:
                users = self.call("user.get", {"FILTER": {"ID": int(user_id)}})
                if isinstance(users, list) and users:
                    u = users[0]
                    name = " ".join(filter(None, [u.get("NAME"), u.get("LAST_NAME")])).strip()
                    result[user_id] = name or f"Employee {user_id}"
            except BitrixError:
                result[user_id] = f"Employee {user_id}"
        return result

    def task_get(self, task_id):
        result = self.call(
            "tasks.task.get",
            {"taskId": int(task_id), "select": ["*", "DESCRIPTION", "GROUP_ID", "CHAT_ID", "AUDITORS", "TASK_CONTROL"]},
        )
        task = result.get("task", result) if isinstance(result, dict) else result
        return self._normalize_task(task)

    def task_access(self, task_id, user_id=None):
        params = {"taskId": int(task_id)}
        if user_id:
            params["users"] = [int(user_id)]
        result = self.call("tasks.task.getaccess", params) or {}
        actions = result.get("allowedActions", result.get("allowed_actions", {})) if isinstance(result, dict) else {}
        if not isinstance(actions, dict):
            return {}
        if user_id:
            raw = actions.get(str(user_id)) or actions.get(int(user_id)) or {}
        else:
            raw = next(iter(actions.values()), {}) if actions else {}
        return {str(k).upper(): v is True or v == 1 or str(v).upper() in {"Y", "TRUE"} for k, v in (raw or {}).items()}

    def get_task_fields(self):
        return self.call("tasks.task.getFields", {})

    def update_task(self, task_id, fields):
        if not fields:
            raise ValueError("At least one task field is required.")
        return self.call("tasks.task.update", {"taskId": int(task_id), "fields": fields})

    def reassign_task(self, task_id, responsible_id):
        return self.update_task(task_id, {"RESPONSIBLE_ID": int(responsible_id)})

    def start_task(self, task_id):
        return self.call("tasks.task.start", {"taskId": int(task_id)})

    def pause_task(self, task_id):
        """Pause active execution and return the Bitrix task to Waiting for Execution."""
        return self.call("tasks.task.pause", {"taskId": int(task_id)})

    def complete_task(self, task_id):
        return self.call("tasks.task.complete", {"taskId": int(task_id)})

    def approve_task(self, task_id):
        return self.call("tasks.task.approve", {"taskId": int(task_id)})

    def disapprove_task(self, task_id):
        return self.call("tasks.task.disapprove", {"taskId": int(task_id)})

    def set_mark(self, task_id, mark):
        if mark not in ("P", "N", None):
            raise ValueError("Bitrix mark must be P, N or None")
        return self.update_task(task_id, {"MARK": mark})

    def recent_task_messages(self, task_id, limit=50):
        """Read task discussion messages with new-card support and legacy fallback."""
        limit = max(1, min(50, int(limit or 50)))
        new_card_error = None
        try:
            task = self.task_get(task_id)
            chat_id = task.get("chatId")
            if chat_id:
                result = self.call(
                    "im.dialog.messages.get",
                    {"DIALOG_ID": f"chat{chat_id}", "LIMIT": limit},
                ) or {}
                messages = result.get("messages", []) if isinstance(result, dict) else []
                return [
                    {
                        "id": m.get("id"),
                        "author_id": m.get("author_id"),
                        "date": m.get("date"),
                        "text": m.get("text") or "",
                    }
                    for m in messages
                ]
        except BitrixError as exc:
            new_card_error = exc

        try:
            result = self.call(
                "task.commentitem.getlist",
                {"TASKID": int(task_id), "ORDER": {"POST_DATE": "desc"}, "FILTER": {}},
            ) or []
            return [
                {
                    "id": m.get("ID"),
                    "author_id": m.get("AUTHOR_ID"),
                    "date": m.get("POST_DATE"),
                    "text": m.get("POST_MESSAGE") or "",
                }
                for m in result[:limit]
            ]
        except BitrixError:
            if new_card_error:
                raise new_card_error
            raise

    def send_message(self, task_id, text):
        # REST 3.0 task chat is preferred for the new task card. Legacy comments
        # remain as a compatibility fallback for older portals/cards.
        try:
            return self.call(
                "tasks.task.chat.message.send",
                {"fields": {"taskId": int(task_id), "text": text}},
                v3=True,
            )
        except BitrixError as v3_error:
            try:
                return self.call(
                    "task.commentitem.add",
                    {"TASKID": int(task_id), "FIELDS": {"POST_MESSAGE": text}},
                )
            except BitrixError:
                raise v3_error
