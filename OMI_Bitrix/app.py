import atexit
import hashlib
import os
import re
import string
import threading
import time
import uuid
import secrets
import hmac
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import Flask, flash, g, jsonify, redirect, render_template, request, send_file, url_for, session

from itsdangerous import URLSafeTimedSerializer, BadSignature
from security import signing_secret
from diwany_routes import initialize as initialize_diwan
from bitrix import BitrixClient, BitrixError
from i18n import get_text, js_strings, normalize_language
from planner import LOCAL_TZ, build_today_plan, due_bucket, parse_deadline
from review import (
    DELIVERY_LABELS,
    RATING_LABELS,
    discover_review_fields,
    label_for_delivery,
    label_for_rating,
    read_review,
    save_review,
)
from similarity import attach_similarities, search_tasks
from storage import ConfigStore
from team_registry import folder_name as registry_folder_name, register as register_employee
from workspace import (
    count_artifacts,
    ensure_workspace,
    move_workspace,
    obsidian_uri,
    open_path,
    project_name,
    read_delay_justification,
    read_fields,
    readiness,
    save_delay_justification,
    save_fields,
    task_folder,
)
from xlsx_report import build_team_report

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("OMI_DATA_DIR", str(BASE_DIR / "data")))
STORE = ConfigStore(DATA_DIR / "cockpit.sqlite3")
PROFILE_COOKIE = "wc_profile_v2"

app = Flask(__name__)
app.secret_key = signing_secret(DATA_DIR)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("OMI_HTTPS", "0") == "1"
PROFILE_SIGNER = URLSafeTimedSerializer(app.secret_key, salt="omi-profile-v2")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
initialize_diwan(app, STORE)

TASK_CACHES = {}
CACHE_LOCK = threading.RLock()
STOP_EVENT = threading.Event()
NEXT_SYNC = {}


def profile_id():
    return getattr(g, "profile_id", None)


def setting(key, default=None, pid=None):
    return STORE.get(key, default, profile_id=pid or profile_id())


def client(pid=None):
    return BitrixClient(STORE.get("webhook_url", profile_id=pid or profile_id()))


def selected_projects(pid=None):
    return STORE.projects(profile_id=pid or profile_id())


def workspace_root(pid=None):
    return STORE.workspace_root(pid or profile_id())


def employee_name(pid=None):
    return STORE.get("employee_name", "Employee", profile_id=pid or profile_id()) or "Employee"


def current_language(pid=None):
    return normalize_language(STORE.get("ui_language", "en", profile_id=pid or profile_id()))


def tr(key, pid=None, **kwargs):
    return get_text(current_language(pid), key, **kwargs)


def display_user_name(user):
    return " ".join(filter(None, [user.get("NAME"), user.get("LAST_NAME")])).strip()


def empty_cache():
    return {
        "assigned": [],
        "supervised": [],
        "members": [],
        "review_fields": {},
        "related_pairs": [],
        "access": {},
        "messages": {},
        "error": None,
        "updated_at": None,
        "syncing": False,
    }


def cache_for(pid):
    with CACHE_LOCK:
        return TASK_CACHES.setdefault(pid, empty_cache())


def current_user_id(pid=None):
    user = setting("bitrix_user", {}, pid) or {}
    return str(user.get("ID") or user.get("id") or "")


def task_roles(task, pid=None):
    uid = current_user_id(pid)
    auditors = task.get("auditors") or []
    if not isinstance(auditors, (list, tuple, set)):
        auditors = [auditors]
    roles = []
    if str(task.get("responsibleId") or "") == uid:
        roles.append("assignee")
    if str(task.get("createdBy") or "") == uid:
        roles.append("creator")
    if uid and uid in {str(x) for x in auditors}:
        roles.append("observer")
    return roles


def employee_folder_for_task(task, pid=None):
    pid = pid or profile_id()
    uid = str(task.get("responsibleId") or "")
    if uid and uid == current_user_id(pid):
        return employee_name(pid)
    fallback = task.get("responsibleName") or f"Employee {uid or 'Unknown'}"
    root = workspace_root(pid)
    return registry_folder_name(root, uid, fallback) if root else fallback


def workspace_paths(task, pid=None, create=False):
    pid = pid or profile_id()
    root = workspace_root(pid)
    emp = task.get("workspaceEmployee") or employee_folder_for_task(task, pid)
    folder = task_folder(root, task["projectName"], task, emp)
    if create or folder.exists():
        return ensure_workspace(root, task["projectName"], task, current_language(pid), emp)
    return {"folder": folder, "note": None, "vault_root": Path(root)}


def delivery_state(task):
    """Compute an explainable delivery signal used as the supervisor default."""
    deadline = parse_deadline(task.get("deadline"))
    if not deadline:
        return "on_time"
    status = str(task.get("status") or "")
    candidate = None
    if status == "5":
        candidate = parse_deadline(task.get("closedDate") or task.get("closed"))
    elif status == "4":
        # Awaiting control means the participant already submitted the work.
        candidate = parse_deadline(task.get("statusChangedDate") or task.get("changedDate") or task.get("changed"))
    if candidate:
        return "late" if candidate > deadline else "on_time"
    return "late" if datetime.now(LOCAL_TZ) > deadline else "on_time"


def task_is_late(task):
    """Treat a task as late based on delivery, not merely because an old deadline passed.

    For completed / pending-review work we compare the actual submission/close time
    against the deadline. For still-open work, the current deadline bucket is enough.
    """
    status = str(task.get("status") or "")
    if status in {"4", "5"}:
        return task.get("deliveryComputed") == "late"
    return task.get("dueBucket") == "overdue"


def enrich_task(task, projects, names, pid, create_missing=False):
    task = dict(task)
    task["projectName"] = project_name(task.get("groupId"), projects)
    responsible_id = str(task.get("responsibleId") or "")
    task["responsibleName"] = names.get(responsible_id, f"Employee {responsible_id}")
    roles = task_roles(task, pid)
    task["roles"] = roles
    task["isAssignee"] = "assignee" in roles
    task["isCreator"] = "creator" in roles
    task["isObserver"] = "observer" in roles
    task["workspaceEmployee"] = employee_folder_for_task(task, pid)

    should_create = bool(
        create_missing
        and task["isAssignee"]
        and str(task.get("status")) != "5"
        and setting("auto_scaffold", True, pid)
    )
    paths = workspace_paths(task, pid, create=should_create)
    task["workspaceExists"] = Path(paths["folder"]).exists()
    task["folder"] = str(paths["folder"])
    task["note"] = str(paths["note"]) if paths.get("note") else ""
    task["readiness"] = readiness(read_fields(paths["note"])) if paths.get("note") else 0
    task["artifacts"] = count_artifacts(paths["folder"]) if task["workspaceExists"] else {}

    bucket, hours = due_bucket(task.get("deadline"))
    task["dueBucket"] = bucket
    task["hoursToDeadline"] = hours
    delay_note = read_delay_justification(paths["folder"], task.get("deadline")) if task["workspaceExists"] else None
    task["delayJustification"] = (delay_note or {}).get("justification", "")
    task["hasDelayJustification"] = bool(delay_note)
    task["justificationRequired"] = bucket == "overdue" and not delay_note
    task["deliveryComputed"] = delivery_state(task)
    task["isLate"] = task_is_late(task)
    return task


def _register_current_employee(pid, user, project_ids):
    try:
        register_employee(
            workspace_root(pid),
            user.get("ID") or user.get("id"),
            employee_name(pid),
            display_user_name(user),
            project_ids,
        )
    except Exception:
        # Registry improves shared-folder discovery but should never block Bitrix sync.
        pass


def sync_tasks(create_missing=True, pid=None):
    pid = pid or profile_id()
    if not pid or not STORE.configured(pid):
        return empty_cache()
    cache = cache_for(pid)
    with CACHE_LOCK:
        if cache["syncing"]:
            return cache
        cache["syncing"] = True
    try:
        bx = client(pid)
        user = STORE.get("bitrix_user", profile_id=pid) or bx.current_user()
        STORE.set("bitrix_user", user, profile_id=pid)
        projects = selected_projects(pid)
        project_ids = [p["id"] for p in projects]
        if not project_ids:
            raise BitrixError("Select at least one Bitrix24 project.")
        user_id = str(user.get("ID") or user.get("id"))
        _register_current_employee(pid, user, project_ids)

        assigned_raw = bx.assigned_tasks(user_id, project_ids)
        supervised_raw = bx.supervised_tasks(
            user_id,
            project_ids,
            completed_days=int(setting("report_days", 90, pid) or 90),
        )
        members = bx.project_members(project_ids)
        member_names = {str(m["id"]): m["name"] for m in members}
        all_ids = {
            str(t.get("responsibleId"))
            for t in assigned_raw + supervised_raw
            if t.get("responsibleId") not in (None, "")
        }
        missing = all_ids - set(member_names)
        member_names.update(bx.users_by_ids(missing))
        member_names[user_id] = display_user_name(user) or employee_name(pid)

        assigned = [enrich_task(t, projects, member_names, pid, create_missing=create_missing) for t in assigned_raw]
        supervised = [enrich_task(t, projects, member_names, pid, create_missing=False) for t in supervised_raw]

        upcoming = [t for t in assigned if t.get("dueBucket") in {"today", "soon", "later"}]
        related_pairs = attach_similarities(upcoming, upcoming, threshold=40, max_per_task=3)

        try:
            review_fields = discover_review_fields(bx.get_task_fields())
        except Exception:
            review_fields = {}

        updated = datetime.now(LOCAL_TZ).isoformat(timespec="seconds")
        with CACHE_LOCK:
            cache.update(
                assigned=assigned,
                supervised=supervised,
                members=members,
                review_fields=review_fields,
                related_pairs=related_pairs[:20],
                error=None,
                updated_at=updated,
                syncing=False,
            )
        return cache
    except Exception as exc:
        with CACHE_LOCK:
            cache.update(error=str(exc), updated_at=datetime.now(LOCAL_TZ).isoformat(timespec="seconds"), syncing=False)
        return cache


def sync_loop():
    while not STOP_EVENT.is_set():
        now = time.monotonic()
        for pid in STORE.configured_profiles():
            if not STORE.get("signed_profile_active", False, profile_id=pid):
                continue
            interval = max(30, int(STORE.get("sync_interval", 90, profile_id=pid) or 90))
            if now >= NEXT_SYNC.get(pid, 0):
                sync_tasks(create_missing=True, pid=pid)
                NEXT_SYNC[pid] = now + interval
        STOP_EVENT.wait(15)


def task_from_cache(task_id, refresh=False, include_supervised=True):
    pid = profile_id()
    cache = cache_for(pid)
    if refresh or not cache["updated_at"]:
        cache = sync_tasks(create_missing=False, pid=pid)
    pools = [cache.get("assigned", [])]
    if include_supervised:
        pools.append(cache.get("supervised", []))
    for pool in pools:
        for task in pool:
            if str(task.get("id")) == str(task_id):
                return task
    cache = sync_tasks(create_missing=False, pid=pid)
    for pool in [cache.get("assigned", []), cache.get("supervised", []) if include_supervised else []]:
        for task in pool:
            if str(task.get("id")) == str(task_id):
                return task
    raise KeyError(f"Task {task_id} not found in selected projects.")


def require_assignee(task):
    if not task.get("isAssignee"):
        raise PermissionError(tr("assignee_action_only"))


def can_pause_task(task):
    """Pause is for a future/no-deadline task the assignee is actively working on.

    We deliberately do not allow pausing work due today or already overdue. Those
    remain visible in today's delivery flow and overdue work keeps its justification
    requirement. A future started task can be paused back to Bitrix Waiting status,
    which naturally removes it from the 8-hour planner until it is started again.
    """
    if str(task.get("status") or "") != "3":
        return False
    deadline = parse_deadline(task.get("deadline"))
    if not deadline:
        return True
    return deadline.date() > datetime.now(LOCAL_TZ).date()


def cached_access(task, max_age=300):
    pid = profile_id()
    cache = cache_for(pid)
    tid = str(task.get("id"))
    now = time.monotonic()
    item = cache.get("access", {}).get(tid)
    if item and now - item.get("time", 0) < max_age:
        return item.get("actions", {})
    try:
        actions = client().task_access(tid, current_user_id())
    except Exception:
        # Conservative role-based fallback if the portal blocks getaccess.
        actions = {
            "APPROVE": bool(task.get("isCreator") and str(task.get("status")) == "4"),
            "DISAPPROVE": bool(task.get("isCreator") and str(task.get("status")) == "4"),
            "EDIT": bool(task.get("isCreator")),
            "CHANGE_DEADLINE": bool(task.get("isCreator")),
            "DELEGATE": bool(task.get("isCreator")),
            "RATE": bool(task.get("isCreator")),
        }
    with CACHE_LOCK:
        cache.setdefault("access", {})[tid] = {"time": now, "actions": actions}
    return actions


def cached_messages(task_id, max_age=120):
    pid = profile_id()
    cache = cache_for(pid)
    tid = str(task_id)
    now = time.monotonic()
    item = cache.get("messages", {}).get(tid)
    if item and now - item.get("time", 0) < max_age:
        return item.get("messages", [])
    messages = client().recent_task_messages(task_id, 50)
    with CACHE_LOCK:
        cache.setdefault("messages", {})[tid] = {"time": now, "messages": messages}
    return messages


def extract_justification(messages):
    for item in reversed(messages or []):
        text = str(item.get("text") or "")
        if "[WORK_COCKPIT_DELAY]" not in text and "Deadline justification" not in text and "توضيح سبب التأخير" not in text:
            continue
        m = re.search(r"(?:WC_JUSTIFICATION|Justification|سبب التأخير)\s*:\s*(.+)", text, flags=re.I)
        if m:
            return m.group(1).strip()
        return text.strip()
    return ""


def extract_review_from_messages(messages):
    for item in reversed(messages or []):
        text = str(item.get("text") or "")
        if "[WORK_COCKPIT_REVIEW]" not in text:
            continue
        out = {"raw": text}
        m = re.search(r"WC_RATING:(\d)", text)
        if m:
            out["rating"] = int(m.group(1))
        m = re.search(r"WC_DELIVERY:(on_time|late)", text)
        if m:
            out["delivery"] = m.group(1)
        m = re.search(r"WC_OUTCOME:(.+)", text)
        if m:
            out["outcome"] = m.group(1).strip()
        return out
    return None


def latest_justification(task):
    if task.get("delayJustification"):
        return task["delayJustification"]
    if task.get("dueBucket") != "overdue" and task.get("deliveryComputed") != "late":
        return ""
    try:
        return extract_justification(cached_messages(task["id"]))
    except Exception:
        return ""


def task_matches(task, query):
    q = (query or "").strip().lower()
    if not q:
        return True
    values = [
        task.get("id"), task.get("title"), task.get("description"), task.get("projectName"),
        task.get("responsibleName"), task.get("workspaceEmployee"), task.get("deadline"),
    ]
    hay = " ".join(str(v or "") for v in values).lower()
    return all(token in hay for token in q.split())


def planner_revision(tasks):
    """Revision key for every task that can influence today's planner."""
    today = datetime.now(LOCAL_TZ).date()
    values = []
    for task in tasks:
        deadline = parse_deadline(task.get("deadline"))
        due_today = bool(deadline and deadline.date() == today)
        started = str(task.get("status") or "") == "3"
        if str(task.get("status")) not in {"4", "5", "6", "7"} and (due_today or started or bool(deadline and deadline < datetime.now(LOCAL_TZ))):
            values.append(f"{task.get('id')}|{task.get('priority')}|{task.get('deadline')}|{task.get('status')}|{task.get('timeEstimate')}")
    return hashlib.sha1("\n".join(sorted(values)).encode("utf-8")).hexdigest()[:10]


@app.before_request
def attach_profile():
    raw = request.cookies.get(PROFILE_COOKIE, "")
    try:
        pid = PROFILE_SIGNER.loads(raw, max_age=60 * 60 * 24 * 365)
        if not isinstance(pid, str) or len(pid) != 32:
            raise BadSignature("Invalid profile")
    except BadSignature:
        pid = uuid.uuid4().hex
        g.new_profile_cookie = True
    g.profile_id = pid
    STORE.ensure_profile(pid)
    if not STORE.get("signed_profile_active", False, profile_id=pid):
        STORE.set("signed_profile_active", True, profile_id=pid)
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        submitted = request.headers.get("X-CSRF-Token") or request.form.get("_csrf", "")
        if not submitted or not hmac.compare_digest(submitted, session["csrf_token"]):
            return jsonify(ok=False, code="csrf", error=get_text(current_language(), "d_error_csrf")), 403

    allowed = {"setup", "api_test_bitrix", "api_projects", "api_folders",
               "set_language", "static", "health", "settings", "test_workspace", "favicon"}
    if request.endpoint and request.endpoint.startswith(("diwan.", "recommendations.")):
        return None
    if request.endpoint and request.endpoint not in allowed and not STORE.configured(pid):
        return redirect(url_for("diwan.page"))


@app.after_request
def persist_profile_cookie(response):
    if getattr(g, "new_profile_cookie", False):
        response.set_cookie(PROFILE_COOKIE, PROFILE_SIGNER.dumps(g.profile_id),
                            max_age=60 * 60 * 24 * 365, samesite="Lax", httponly=True,
                            secure=app.config["SESSION_COOKIE_SECURE"])
    if request.endpoint != "static":
        response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.context_processor
def inject_helpers():
    lang = current_language()
    return {
        "due_bucket": due_bucket,
        "app_name": "OMI Bitrix",
        "employee_name": employee_name(),
        "lang": lang,
        "dir": "rtl" if lang == "ar" else "ltr",
        "t": lambda key, **kwargs: get_text(lang, key, **kwargs),
        "js_i18n": js_strings(lang),
        "csrf_token": session.get("csrf_token", ""),
        "diwan_i18n": {k: v for k, v in __import__("i18n").TRANSLATIONS[lang].items() if k.startswith("d_")},
        "diwan_connected": app.extensions["diwan_vault"].present(profile_id()),
        "diwan_endpoint_ready": bool(setting("diwan_config", {})),
        "rating_labels": RATING_LABELS,
        "delivery_labels": DELIVERY_LABELS,
    }


def settings_model():
    return {
        "webhook_url": "",
        "vault_root": workspace_root() or "",
        "employee_name": setting("employee_name", ""),
        "sync_interval": setting("sync_interval", 90),
        "auto_scaffold": setting("auto_scaffold", True),
        "workday_start": setting("workday_start", "08:00"),
        "app_name": "OMI Bitrix",
        "ui_language": current_language(),
        "report_days": setting("report_days", 90),
        "storage_mode": setting("storage_mode", "Shared Folder"),
        "planner_minutes": setting("planner_minutes", 480),
    }


def save_configuration():
    webhook = request.form.get("webhook_url", "").strip() or setting("webhook_url", "")
    vault_root = request.form.get("vault_root", "").strip()
    emp_name = request.form.get("employee_name", "").strip()
    project_ids = request.form.getlist("project_id")
    project_ids.extend(x.strip() for x in request.form.get("manual_projects", "").split(",") if x.strip())
    if not all(str(x).isdigit() for x in project_ids):
        raise ValueError("Project IDs must be numeric.")
    project_ids = list(dict.fromkeys(project_ids))
    ui_language = normalize_language(request.form.get("ui_language") or current_language())

    planner_minutes = int(request.form.get("planner_minutes", 480))
    storage_mode = request.form.get("storage_mode", "Shared Folder")
    if not 15 <= planner_minutes <= 1440 or planner_minutes % 15:
        raise ValueError("Planner capacity must be 15–1440 minutes in 15-minute increments.")
    if storage_mode not in {"Shared Folder", "Local Folder", "Network Share", "Obsidian Vault"}:
        raise ValueError("Invalid storage mode.")
    bx = BitrixClient(webhook)
    user = bx.current_user()
    all_projects = bx.projects()
    project_map = {str(p["id"]): p["name"] for p in all_projects}
    chosen = [{"id": pid, "name": project_map.get(str(pid), f"Project {pid}")} for pid in project_ids]
    if not chosen:
        raise ValueError("اختر مشروعًا واحدًا على الأقل من Bitrix24." if ui_language == "ar" else "Select at least one Bitrix24 project.")
    if not vault_root:
        raise ValueError("حدد مسار مجلد العمل." if ui_language == "ar" else "Choose the workspace folder.")
    if not emp_name:
        emp_name = display_user_name(user)
    if not emp_name:
        raise ValueError("أدخل اسم الموظف لإنشاء مجلد مستقل له." if ui_language == "ar" else "Enter the employee name used for the dedicated workspace folder.")
    Path(vault_root).expanduser().mkdir(parents=True, exist_ok=True)

    STORE.set_many(
        {
            "webhook_url": bx.webhook_url,
            "vault_root": str(Path(vault_root).expanduser()),
            "shared_root": str(Path(vault_root).expanduser()),
            "obsidian_vault": str(Path(vault_root).expanduser()),
            "storage_mode": storage_mode,
            "planner_minutes": planner_minutes,
            "employee_name": emp_name,
            "bitrix_user": user,
            "sync_interval": int(request.form.get("sync_interval", 90)),
            "auto_scaffold": bool(request.form.get("auto_scaffold")),
            "workday_start": request.form.get("workday_start", "08:00") or "08:00",
            "ui_language": ui_language,
            "report_days": int(request.form.get("report_days", 90) or 90),
        },
        profile_id=profile_id(),
    )
    STORE.replace_projects(chosen, profile_id=profile_id())
    register_employee(
        str(Path(vault_root).expanduser()),
        user.get("ID") or user.get("id"),
        emp_name,
        display_user_name(user),
        project_ids,
    )
    sync_tasks(create_missing=True)
    return ui_language


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        try:
            lang = save_configuration()
            flash("تم حفظ الإعدادات بنجاح." if lang == "ar" else "OMI Bitrix configured successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as exc:
            flash(str(exc), "error")
    return render_template("setup.html", settings=settings_model(), selected=selected_projects())


@app.post("/api/test-bitrix")
def api_test_bitrix():
    data = request.get_json(silent=True) or {}
    try:
        bx = BitrixClient(data.get("webhook_url"))
        user = bx.current_user()
        return jsonify({"ok": True, "user": {"id": user.get("ID"), "name": display_user_name(user)}})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/projects")
def api_projects():
    data = request.get_json(silent=True) or {}
    try:
        projects = BitrixClient(data.get("webhook_url")).projects()
        return jsonify({"ok": True, "projects": projects})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


def folder_roots():
    roots = []
    if os.name == "nt":
        for letter in string.ascii_uppercase:
            p = Path(f"{letter}:\\")
            if p.exists():
                roots.append(str(p))
    else:
        roots.append("/")
    for extra in [Path.home(), Path.cwd(), Path(workspace_root() or Path.home())]:
        value = str(extra)
        if value not in roots and Path(value).exists():
            roots.append(value)
    return roots


@app.get("/api/folders")
def api_folders():
    raw = (request.args.get("path") or "").strip()
    if not raw:
        return jsonify({"ok": True, "roots": folder_roots(), "path": "", "parent": None, "folders": []})
    try:
        path = Path(raw).expanduser()
        path = path.resolve(strict=True)
        if not path.is_dir():
            raise ValueError("Not a folder")
        children = []
        try:
            iterator = path.iterdir()
            for child in iterator:
                try:
                    if child.is_dir() and child.name not in {"$Recycle.Bin", "System Volume Information"}:
                        children.append({"name": child.name, "path": str(child)})
                except OSError:
                    continue
        except PermissionError:
            raise ValueError("The OMI Bitrix server process cannot read this folder.")
        children.sort(key=lambda x: x["name"].casefold())
        parent = str(path.parent) if path.parent != path else None
        return jsonify({"ok": True, "roots": folder_roots(), "path": str(path), "parent": parent, "folders": children[:500]})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "roots": folder_roots()}), 400


@app.route("/")
def dashboard():
    cache = cache_for(profile_id())
    if not cache["updated_at"]:
        cache = sync_tasks(create_missing=True)
    with CACHE_LOCK:
        assigned = [dict(t) for t in cache.get("assigned", [])]
        related_pairs = list(cache.get("related_pairs", []))
        cache_view = dict(cache)
    q = request.args.get("q", "").strip()
    visible = [t for t in assigned if task_matches(t, q)]
    order = {"overdue": 0, "today": 1, "soon": 2, "later": 3, "no-deadline": 4}
    visible.sort(key=lambda t: (order.get(t["dueBucket"], 9), -int(t.get("priority") or 0), t.get("deadline") or "9999"))
    counts = {k: sum(1 for t in assigned if t["dueBucket"] == k) for k in order}
    today_plan = build_today_plan(assigned, setting("workday_start", "08:00"), setting("planner_minutes", 480))
    return render_template(
        "dashboard.html",
        tasks=visible,
        all_tasks=assigned,
        counts=counts,
        today_plan=today_plan,
        related_pairs=related_pairs,
        q=q,
        planner_date=datetime.now(LOCAL_TZ).date().isoformat(),
        planner_start=setting("workday_start", "08:00"),
        planner_revision=planner_revision(assigned),
        cache=cache_view,
        user=setting("bitrix_user", {}),
        projects=selected_projects(),
        supervisor_count=len(cache.get("supervised", [])),
    )


@app.route("/search")
def search_dashboard():
    cache = cache_for(profile_id())
    if not cache["updated_at"]:
        cache = sync_tasks(create_missing=False)
    scope = request.args.get("scope", "all")
    q = request.args.get("q", "").strip()
    assigned = [dict(t) for t in cache.get("assigned", [])]
    supervised = [dict(t) for t in cache.get("supervised", [])]
    if scope == "mine":
        pool = assigned
    elif scope == "supervisor":
        pool = supervised
    else:
        # Preserve per-task roles while avoiding a duplicate search result.
        merged = {}
        for t in assigned + supervised:
            tid = str(t.get("id"))
            if tid in merged:
                roles = list(dict.fromkeys((merged[tid].get("roles") or []) + (t.get("roles") or [])))
                merged[tid]["roles"] = roles
            else:
                merged[tid] = t
        pool = list(merged.values())
    results = search_tasks(pool, q) if q else pool
    results = results[:100]
    attach_similarities(results, pool, threshold=38, max_per_task=3)
    return render_template("search.html", tasks=results, q=q, scope=scope)


def _hydrate_supervisor_context(tasks, include_access=True):
    for task in tasks:
        if include_access and str(task.get("status")) != "5":
            task["access"] = cached_access(task)
        else:
            task["access"] = {}
        task["isLate"] = task_is_late(task)
        if task["isLate"]:
            task["supervisorJustification"] = latest_justification(task)
        else:
            task["supervisorJustification"] = task.get("delayJustification") or ""
        if task.get("workspaceExists"):
            task["savedReview"] = read_review(task["folder"])
        else:
            task["savedReview"] = None
    return tasks


@app.route("/supervisor")
def supervisor_dashboard():
    cache = cache_for(profile_id())
    if not cache["updated_at"]:
        cache = sync_tasks(create_missing=False)
    tasks = [dict(t) for t in cache.get("supervised", [])]
    q = request.args.get("q", "").strip()
    if q:
        tasks = search_tasks(tasks, q)
    # Keep the interactive dashboard bounded: each active row may require a
    # Bitrix per-task access check. Reports still cover the full supervised set.
    tasks = tasks[:80]
    _hydrate_supervisor_context(tasks)

    pending = [t for t in tasks if str(t.get("status")) == "4"]
    active = [t for t in tasks if str(t.get("status")) in {"2", "3", "6"}]
    completed = [t for t in tasks if str(t.get("status")) == "5"]
    active.sort(key=lambda t: (-int(t.get("priority") or 0), 0 if t.get("dueBucket") == "overdue" else 1, t.get("deadline") or "9999"))
    pending.sort(key=lambda t: (0 if t.get("deliveryComputed") == "late" else 1, t.get("deadline") or "9999"))
    completed.sort(key=lambda t: t.get("closedDate") or t.get("changedDate") or "", reverse=True)

    team = {}
    for task in tasks:
        name = task.get("responsibleName") or "Employee"
        stat = team.setdefault(
            name,
            {"name": name, "total": 0, "active": 0, "in_progress": 0, "review": 0, "overdue": 0, "justified": 0, "high": 0, "priority_load": 0, "completed": 0},
        )
        stat["total"] += 1
        stat["active"] += int(str(task.get("status")) in {"2", "3", "6"})
        stat["in_progress"] += int(str(task.get("status")) == "3")
        stat["review"] += int(str(task.get("status")) == "4")
        stat["completed"] += int(str(task.get("status")) == "5")
        stat["overdue"] += int(bool(task.get("isLate")))
        stat["justified"] += int(bool(task.get("isLate") and (task.get("supervisorJustification") or task.get("delayJustification"))))
        stat["high"] += int(str(task.get("priority")) == "2" and str(task.get("status")) != "5")
        stat["priority_load"] += {"2": 3, "1": 2, "0": 1}.get(str(task.get("priority")), 1) if str(task.get("status")) != "5" else 0

    # Put a small live workload hint beside each project member in the reassignment list.
    member_load, member_active, member_high = {}, {}, {}
    for item in active + pending:
        uid = str(item.get("responsibleId") or "")
        if not uid:
            continue
        member_load[uid] = member_load.get(uid, 0) + {"2": 3, "1": 2, "0": 1}.get(str(item.get("priority")), 1)
        member_active[uid] = member_active.get(uid, 0) + 1
        member_high[uid] = member_high.get(uid, 0) + int(str(item.get("priority")) == "2")
    members_view = []
    for member in cache.get("members", []):
        row = dict(member)
        uid = str(row.get("id") or "")
        row["load"] = member_load.get(uid, 0)
        row["active"] = member_active.get(uid, 0)
        row["high"] = member_high.get(uid, 0)
        members_view.append(row)
    members_view.sort(key=lambda m: (m.get("load", 0), m.get("name", "").casefold()))

    # Duplicate-work radar for supervisors. All similarity stays local in Python.
    team_upcoming = [item for item in active if item.get("dueBucket") in {"overdue", "today", "soon", "later"}][:100]
    team_related_pairs = attach_similarities(team_upcoming, team_upcoming, threshold=42, max_per_task=2)[:12]

    return render_template(
        "supervisor.html",
        tasks=tasks,
        pending=pending,
        active=active,
        completed=completed[:40],
        team=sorted(team.values(), key=lambda x: (-x["priority_load"], x["name"])),
        members=members_view,
        team_related_pairs=team_related_pairs,
        review_fields=cache.get("review_fields") or {},
        q=q,
        cache=cache,
        assigned_count=len(cache.get("assigned", [])),
    )


@app.post("/sync")
def manual_sync():
    cache = sync_tasks(create_missing=True)
    if cache["error"]:
        flash(cache["error"], "error")
    else:
        flash("تمت مزامنة المهام من Bitrix24." if current_language() == "ar" else "Tasks synced from Bitrix24.", "success")
    return redirect(request.referrer or url_for("dashboard"))


@app.route("/task/<task_id>")
def task_detail(task_id):
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        paths = workspace_paths(task, create=True)
        values = read_fields(paths["note"])
        task["readiness"] = readiness(values)
        task["artifacts"] = count_artifacts(paths["folder"])
        delay_note = read_delay_justification(paths["folder"], task.get("deadline"))
        task["hasDelayJustification"] = bool(delay_note)
        task["justificationRequired"] = task.get("dueBucket") == "overdue" and not delay_note
        return render_template("task.html", task=task, paths=paths, values=values)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("dashboard"))


@app.post("/task/<task_id>/workspace")
def create_workspace(task_id):
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        workspace_paths(task, create=True)
        flash("تم تجهيز مجلد المهمة وملف التوثيق داخل المستودع المشترك." if current_language() == "ar" else "Task folder and documentation note are ready.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("dashboard"))


@app.post("/task/<task_id>/documentation")
def update_documentation(task_id):
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        paths = workspace_paths(task, create=True)
        values = {k: request.form.get(k, "") for k in ["objective", "work_done", "queries", "validation", "result", "next_step"]}
        save_fields(paths["note"], values, paths["folder"], current_language())
        flash("تم حفظ التوثيق وتحديث روابط ملفات العمل." if current_language() == "ar" else "Documentation saved and work-file links refreshed.", "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("task_detail", task_id=task_id))


@app.post("/task/<task_id>/start")
def start_task(task_id):
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        client().start_task(task_id)
        flash("تم بدء المهمة في Bitrix24 وإضافتها إلى خطة اليوم." if current_language() == "ar" else "Task started in Bitrix24 and added to today's plan.", "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("dashboard"))


@app.post("/task/<task_id>/pause")
def pause_task(task_id):
    try:
        # Refresh before enforcing the rule so a deadline/status changed in Bitrix
        # cannot be paused using stale dashboard state.
        task = task_from_cache(task_id, refresh=True, include_supervised=False)
        require_assignee(task)
        if not can_pause_task(task):
            raise ValueError(tr("pause_future_only"))
        client().pause_task(task_id)
        flash(tr("task_paused_success"), "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("dashboard"))


@app.post("/task/<task_id>/message")
def task_message(task_id):
    message = request.form.get("message", "").strip()
    if not message:
        flash("اكتب التحديث قبل الإرسال." if current_language() == "ar" else "Write an update before posting.", "error")
        return redirect(request.referrer or url_for("dashboard"))
    try:
        task = task_from_cache(task_id)
        if not (task.get("isAssignee") or task.get("isCreator") or task.get("isObserver")):
            raise PermissionError("This task is outside your Bitrix role scope.")
        client().send_message(task_id, message)
        flash("تم إرسال التحديث إلى المهمة." if current_language() == "ar" else "Update posted to the task.", "success")
        cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("dashboard"))


@app.get("/api/task/<task_id>/comments")
def api_task_comments(task_id):
    """Lazy task discussion feed for both assignee and supervisor views."""
    try:
        task = task_from_cache(task_id)
        if not (task.get("isAssignee") or task.get("isCreator") or task.get("isObserver")):
            raise PermissionError("This task is outside your Bitrix role scope.")
        try:
            limit = int(request.args.get("limit", 12) or 12)
        except ValueError:
            limit = 12
        limit = max(1, min(50, limit))
        messages = cached_messages(task_id)
        author_ids = [str(m.get("author_id")) for m in messages if m.get("author_id") not in (None, "", 0, "0")]
        profile_cache = cache_for(profile_id())
        author_names = profile_cache.setdefault("user_names", {})
        missing_ids = [uid for uid in sorted(set(author_ids)) if uid not in author_names]
        if missing_ids:
            resolved = client().users_by_ids(missing_ids)
            author_names.update(resolved)
        items = []
        for m in messages[:limit]:
            aid = str(m.get("author_id") or "")
            items.append({
                "id": m.get("id"),
                "author_id": aid,
                "author": author_names.get(aid) or ("Bitrix24" if not aid else f"Employee {aid}"),
                "date": m.get("date") or "",
                "text": m.get("text") or "",
            })
        return jsonify({
            "ok": True,
            "task_id": str(task_id),
            "comments": items,
            "shown": len(items),
            "available": len(messages),
            "has_more": len(messages) > len(items),
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/task/<task_id>/justify-delay")
def justify_delay(task_id):
    justification = request.form.get("justification", "").strip()
    if len(justification) < 8:
        flash("اكتب سبب التأخير بشكل واضح قبل الإرسال." if current_language() == "ar" else "Add a clear justification before posting the deadline update.", "error")
        return redirect(request.referrer or url_for("task_detail", task_id=task_id))
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        paths = workspace_paths(task, create=True)
        deadline = parse_deadline(task.get("deadline"))
        deadline_text = deadline.strftime("%Y-%m-%d %H:%M Asia/Riyadh") if deadline else (task.get("deadline") or "No deadline")
        if current_language() == "ar":
            message = (
                "[WORK_COCKPIT_DELAY]\n"
                "توضيح سبب التأخير\n\n"
                f"الموعد النهائي الأصلي: {deadline_text}\n"
                f"سبب التأخير: {justification}\n"
                f"WC_JUSTIFICATION: {justification}\n\n"
                "الحالة: ستبقى المهمة مفتوحة لحين استكمال العمل.\n"
                f"الموظف: {employee_name()}\n"
                f"مجلد المهمة: {paths['folder']}\n"
                f"ملف التوثيق: {paths['note']}"
            )
        else:
            message = (
                "[WORK_COCKPIT_DELAY]\n"
                "Deadline justification\n\n"
                f"Original deadline: {deadline_text}\n"
                f"Justification: {justification}\n"
                f"WC_JUSTIFICATION: {justification}\n\n"
                "Status: The task remains open until the work is completed.\n"
                f"Employee: {employee_name()}\n"
                f"Task workspace: {paths['folder']}\n"
                f"Task documentation: {paths['note']}"
            )
        client().send_message(task_id, message)
        save_delay_justification(paths["folder"], task, justification)
        cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
        flash("تم نشر توضيح سبب التأخير في تعليقات المهمة على Bitrix24." if current_language() == "ar" else "Deadline justification posted to the Bitrix24 task comments.", "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("task_detail", task_id=task_id))


@app.post("/task/<task_id>/complete")
def complete_task(task_id):
    try:
        task = task_from_cache(task_id, include_supervised=False)
        require_assignee(task)
        paths = workspace_paths(task, create=True)
        values = read_fields(paths["note"])
        score = readiness(values)
        if score < 100:
            flash((f"التوثيق مكتمل بنسبة {score}%. أكمل الهدف، وما تم إنجازه، والتحقق والمطابقة، والنتيجة قبل إغلاق المهمة." if current_language() == "ar" else f"Documentation is {score}% ready. Fill Objective, Work performed, Validation and Result before closing."), "error")
            return redirect(url_for("task_detail", task_id=task_id))
        summary = values.get("result", "").strip()
        if current_language() == "ar":
            message = (
                "[WORK_COCKPIT_COMPLETE]\n"
                "تم إنجاز المهمة وإرسالها للمراجعة/الإغلاق.\n\n"
                f"الموظف: {employee_name()}\n"
                f"النتيجة: {summary}\n\n"
                f"مجلد العمل المشترك: {workspace_root()}\n"
                f"مجلد المهمة: {paths['folder']}\n"
                f"ملف توثيق المهمة: {paths['note']}"
            )
        else:
            message = (
                "[WORK_COCKPIT_COMPLETE]\n"
                "Work completed and submitted for review/closure.\n\n"
                f"Employee: {employee_name()}\n"
                f"Result: {summary}\n\n"
                f"Shared workspace: {workspace_root()}\n"
                f"Task workspace: {paths['folder']}\n"
                f"Task documentation: {paths['note']}"
            )
        # Comment is deliberately mandatory. A task should not close without its
        # documentation path being visible to the creator/supervisor.
        client().send_message(task_id, message)
        cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
        client().complete_task(task_id)
        flash("تم نشر مسارات العمل والتوثيق ثم إنهاء المهمة في Bitrix24." if current_language() == "ar" else "Workspace paths posted and task completed in Bitrix24.", "success")
        sync_tasks(create_missing=False)
        return redirect(url_for("dashboard"))
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("task_detail", task_id=task_id))


@app.post("/supervisor/task/<task_id>/replan")
def supervisor_replan(task_id):
    try:
        task = task_from_cache(task_id)
        if not (task.get("isCreator") or task.get("isObserver")):
            raise PermissionError(tr("supervisor_scope_only"))
        access = cached_access(task, max_age=0)
        deadline = request.form.get("deadline", "").strip()
        priority = request.form.get("priority", "").strip()
        reason = request.form.get("reason", "").strip()
        fields = {}
        if deadline:
            if not (access.get("CHANGE_DEADLINE") or access.get("EDIT")):
                raise PermissionError(tr("no_deadline_permission"))
            dt = datetime.fromisoformat(deadline)
            dt = dt.replace(tzinfo=LOCAL_TZ) if dt.tzinfo is None else dt.astimezone(LOCAL_TZ)
            fields["DEADLINE"] = dt.isoformat()
        if priority in {"0", "1", "2"}:
            if not access.get("EDIT"):
                raise PermissionError(tr("no_edit_permission"))
            fields["PRIORITY"] = priority
        if not fields:
            raise ValueError(tr("choose_replan_change"))
        client().update_task(task_id, fields)
        if current_language() == "ar":
            message = (
                "[WORK_COCKPIT_REPLAN]\n"
                "إعادة تخطيط من المشرف\n\n"
                f"الموعد السابق: {task.get('deadline') or 'غير محدد'}\n"
                f"الموعد الجديد: {fields.get('DEADLINE', 'بدون تغيير')}\n"
                f"الأولوية: {fields.get('PRIORITY', 'بدون تغيير')}\n"
                f"سبب التعديل: {reason or 'إعادة ترتيب الأولويات وخطة العمل'}"
            )
        else:
            message = (
                "[WORK_COCKPIT_REPLAN]\n"
                "Supervisor replan\n\n"
                f"Previous deadline: {task.get('deadline') or 'None'}\n"
                f"New deadline: {fields.get('DEADLINE', 'Unchanged')}\n"
                f"Priority: {fields.get('PRIORITY', 'Unchanged')}\n"
                f"Reason: {reason or 'Workload / priority replanning'}"
            )
        client().send_message(task_id, message)
        cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
        cache_for(profile_id()).get("access", {}).pop(str(task_id), None)
        flash("تم تحديث الموعد/الأولوية، وسيُعاد بناء خطة الموظف بعد المزامنة." if current_language() == "ar" else "Deadline/priority updated; the employee plan will rebuild on sync.", "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("supervisor_dashboard"))


@app.post("/supervisor/task/<task_id>/reassign")
def supervisor_reassign(task_id):
    try:
        if request.args.get("source", "bitrix") != "bitrix":
            raise ValueError("This action is for Bitrix tasks")
        from recommendation_routes import execute_assignment
        result, code = execute_assignment(task_id, {
            "confirmed": True, "employee_id": request.form.get("responsible_id", "").strip(),
            "expected_assignee": request.form.get("expected_assignee", ""),
            "reason": request.form.get("reason", "").strip()})
        if not result["ok"]:
            raise ValueError(result["error"])
        flash("تم تأكيد الإسناد." if current_language() == "ar" else "Assignment confirmed.", "success")
        for warning in result.get("warnings", []):
            flash(warning, "error")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("supervisor_dashboard"))


def assignment_workspace_context(task, target):
    root = workspace_root()
    if not root:
        return {}
    cache = cache_for(profile_id())
    cached = next((t for t in cache["assigned"] + cache["supervised"]
                   if str(t["id"]) == task["id"] and str(t.get("responsibleId")) == task["assignee_id"]), {})
    service = app.extensions["recommendations"]
    context = service.context(profile_id())
    people = service.directory(context, service._state(context))
    names = {p["id"]: p["name"] for p in people}
    old_task = {"id": task["id"], "title": task["title"], "responsibleId": task["assignee_id"],
                "responsibleName": names.get(task["assignee_id"], task.get("assignee_name"))}
    return {"root": str(root), "task": {"id": task["id"], "title": task["title"]},
            "project": next(p["name"] for p in context["projects"] if p["id"] == task["project_id"]),
            "old_employee": cached.get("workspaceEmployee") or employee_folder_for_task(old_task),
            "new_employee": registry_folder_name(root, target, names.get(target, target)),
            "language": current_language()}


def assignment_workspace_finish(api, task_id, operation):
    warnings = []
    metadata = operation.get("workspace") or {}
    move_text = "No local workspace configured."
    if metadata:
        try:
            result = move_workspace(metadata["root"], metadata["project"], metadata["task"],
                                    metadata["old_employee"], metadata["new_employee"], metadata["language"])
            move_text = result["reason"]
            if result["reason"] == "target_exists":
                warnings.append("Assignment confirmed; both workspace folders exist. Files were preserved without merging.")
        except Exception:
            move_text = "workspace_follow_up_failed"
            warnings.append("Assignment confirmed; workspace transfer failed. Check the source and destination folders.")
    # An attempted/uncertain comment must not be automatically resent on Verify.
    if operation.get("follow_up") == "pending":
        try:
            api.send_message(task_id, "[WORK_COCKPIT_REASSIGN]\nAssignment confirmed\n"
                             + "Employee ID: " + operation["target"] + "\nReason: "
                             + operation.get("reason", "") + "\nWorkspace: " + move_text)
        except Exception:
            warnings.append("Assignment confirmed; the source comment was not confirmed. Check it in Bitrix before posting again.")
    cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
    return warnings


app.extensions["assignment_workspace_context"] = assignment_workspace_context
app.extensions["assignment_workspace_finish"] = assignment_workspace_finish


@app.post("/supervisor/task/<task_id>/review")
def supervisor_review(task_id):
    try:
        task = task_from_cache(task_id)
        access = cached_access(task, max_age=0)
        if str(task.get("status")) != "4":
            raise BitrixError(tr("not_pending_review"))
        decision = request.form.get("decision", "approve")
        required_action = "APPROVE" if decision == "approve" else "DISAPPROVE"
        if not access.get(required_action):
            raise PermissionError(tr("no_review_permission"))

        try:
            rating = int(request.form.get("rating", "3"))
        except ValueError:
            rating = 3
        rating = min(5, max(1, rating))
        delivery = request.form.get("delivery", task.get("deliveryComputed") or "on_time")
        if delivery not in {"on_time", "late"}:
            delivery = task.get("deliveryComputed") or "on_time"
        feedback = request.form.get("feedback", "").strip()
        if decision == "return" and len(feedback) < 5:
            raise ValueError(tr("feedback_required_return"))

        bx = client()
        discovered = cache_for(profile_id()).get("review_fields") or {}
        fields = {}
        custom_written = []
        rating_field = discovered.get("rating_field")
        rating_values = discovered.get("rating_values") or {}
        delivery_field = discovered.get("delivery_field")
        delivery_values = discovered.get("delivery_values") or {}
        if rating_field and str(rating) in rating_values:
            fields[rating_field] = rating_values[str(rating)]
            custom_written.append(rating_field)
        if delivery_field and delivery in delivery_values:
            fields[delivery_field] = delivery_values[delivery]
            custom_written.append(delivery_field)

        # Bitrix's standard MARK is only positive / negative / unrated. The exact
        # 1-5 company assessment is always retained in the structured task comment.
        if access.get("RATE") or access.get("EDIT"):
            fields["MARK"] = "P" if rating >= 4 else "N" if rating <= 2 else None

        field_write_error = ""
        if fields:
            try:
                bx.update_task(task_id, fields)
            except BitrixError as exc:
                # Do not block the actual approve/return action because a portal-
                # specific custom field or native MARK is not writable. The exact
                # assessment remains in the Bitrix task comment and Excel report.
                field_write_error = str(exc)
                custom_written = []

        outcome_label = label_for_rating(rating, current_language())
        delivery_label = label_for_delivery(delivery, current_language())
        reviewer = display_user_name(setting("bitrix_user", {})) or employee_name()
        if current_language() == "ar":
            message = (
                "[WORK_COCKPIT_REVIEW]\n"
                f"WC_RATING:{rating}\nWC_DELIVERY:{delivery}\nWC_OUTCOME:{RATING_LABELS[rating]['en']}\n"
                "مراجعة المشرف\n\n"
                f"التسليم: {delivery_label}\n"
                f"التقييم: {rating}/5 — {outcome_label}\n"
                f"ملاحظة المشرف: {feedback or 'لا توجد ملاحظة إضافية.'}\n"
                f"القرار: {'اعتماد وإغلاق المهمة' if decision == 'approve' else 'إعادة المهمة للاستكمال'}"
                + (f"\nملاحظة تكامل: تعذر تحديث حقل التقييم في Bitrix ({field_write_error})." if field_write_error else "")
            )
        else:
            message = (
                "[WORK_COCKPIT_REVIEW]\n"
                f"WC_RATING:{rating}\nWC_DELIVERY:{delivery}\nWC_OUTCOME:{RATING_LABELS[rating]['en']}\n"
                "Supervisor review\n\n"
                f"Delivery: {delivery_label}\n"
                f"Rating: {rating}/5 — {outcome_label}\n"
                f"Supervisor comment: {feedback or 'No additional note.'}\n"
                f"Decision: {'Approve and close' if decision == 'approve' else 'Return for revision'}"
                + (f"\nIntegration note: the Bitrix review field could not be updated ({field_write_error})." if field_write_error else "")
            )
        bx.send_message(task_id, message)
        if decision == "approve":
            bx.approve_task(task_id)
        else:
            bx.disapprove_task(task_id)

        if task.get("workspaceExists"):
            save_review(
                task["folder"],
                task_id=task_id,
                rating=rating,
                delivery=delivery,
                feedback=feedback,
                action=decision,
                reviewer=reviewer,
                bitrix_field_status={"detected": bool(discovered), "fields": custom_written, "error": field_write_error},
            )
        cache_for(profile_id()).get("messages", {}).pop(str(task_id), None)
        flash("تم حفظ التقييم وتحديث حالة المهمة في Bitrix24." if current_language() == "ar" else "Review saved and Bitrix24 task status updated.", "success")
        sync_tasks(create_missing=False)
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(url_for("supervisor_dashboard"))


def _task_report_review(task):
    if task.get("workspaceExists"):
        saved = read_review(task["folder"])
        if saved:
            return saved
    try:
        parsed = extract_review_from_messages(cached_messages(task["id"], max_age=0))
        return parsed or {}
    except Exception:
        return {}


@app.get("/supervisor/report.xlsx")
def supervisor_report():
    cache = cache_for(profile_id())
    if not cache["updated_at"]:
        cache = sync_tasks(create_missing=False)
    tasks = [dict(t) for t in cache.get("supervised", [])]
    _hydrate_supervisor_context(tasks, include_access=False)

    generated = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    team = {}
    task_rows = [[
        "Employee", "Task ID", "Task", "Project", "Status", "Priority", "Deadline", "Delivery",
        "Rating", "Outcome", "Supervisor feedback", "Late justification", "Roles", "Workspace",
    ]]
    late_rows = [["Employee", "Task ID", "Task", "Project", "Deadline", "Justification", "Workspace"]]

    status_names = {"2": "Waiting", "3": "In progress", "4": "Pending review", "5": "Completed", "6": "Deferred"}
    priority_names = {"2": "High", "1": "Medium", "0": "Low"}
    for task in tasks:
        name = task.get("responsibleName") or "Employee"
        review_data = _task_report_review(task)
        rating = review_data.get("rating", "") if review_data else ""
        outcome = review_data.get("outcome", "") if review_data else ""
        if rating and not outcome:
            try:
                outcome = RATING_LABELS[int(rating)]["en"]
            except Exception:
                pass
        justification = task.get("supervisorJustification") or latest_justification(task)
        delivery = "Late" if task.get("deliveryComputed") == "late" else "On time"
        roles = ", ".join(task.get("roles") or [])
        feedback = review_data.get("feedback", "") if review_data else ""
        task_rows.append([
            name, task.get("id"), task.get("title"), task.get("projectName"), status_names.get(str(task.get("status")), task.get("status")),
            priority_names.get(str(task.get("priority")), task.get("priority")), task.get("deadline") or "", delivery,
            rating, outcome, feedback, justification, roles, task.get("folder") or "",
        ])
        if task_is_late(task):
            late_rows.append([name, task.get("id"), task.get("title"), task.get("projectName"), task.get("deadline") or "", justification or "No justification found", task.get("folder") or ""])

        s = team.setdefault(name, {"total": 0, "active": 0, "completed": 0, "review": 0, "overdue": 0, "justified": 0, "high": 0, "ratings": []})
        s["total"] += 1
        s["active"] += int(str(task.get("status")) in {"2", "3", "6"})
        s["completed"] += int(str(task.get("status")) == "5")
        s["review"] += int(str(task.get("status")) == "4")
        is_late = task_is_late(task)
        s["overdue"] += int(is_late)
        s["justified"] += int(bool(is_late and justification))
        s["high"] += int(str(task.get("priority")) == "2" and str(task.get("status")) != "5")
        if rating:
            try:
                s["ratings"].append(int(rating))
            except Exception:
                pass

    summary_rows = [["Employee", "Total", "Active", "Pending review", "Completed", "Late", "Late justified", "High priority", "Average rating", "Generated"]]
    for name, s in sorted(team.items()):
        avg = round(sum(s["ratings"]) / len(s["ratings"]), 2) if s["ratings"] else ""
        summary_rows.append([name, s["total"], s["active"], s["review"], s["completed"], s["overdue"], s["justified"], s["high"], avg, generated])

    xlsx = build_team_report(summary_rows, task_rows, late_rows)
    stamp = datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M")
    return send_file(
        BytesIO(xlsx),
        as_attachment=True,
        download_name=f"work_cockpit_team_report_{stamp}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.post("/task/<task_id>/open-workspace")
def open_workspace(task_id):
    try:
        task = task_from_cache(task_id)
        paths = workspace_paths(task, create=bool(task.get("isAssignee")))
        if not Path(paths["folder"]).exists():
            raise FileNotFoundError(tr("employee_workspace_missing"))
        open_path(paths["folder"])
        flash("تم فتح مجلد المهمة على الجهاز الذي يشغّل OMI Bitrix." if current_language() == "ar" else "Workspace opened on the machine running OMI Bitrix.", "success")
    except Exception as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("dashboard"))


@app.get("/task/<task_id>/obsidian")
def open_obsidian(task_id):
    try:
        task = task_from_cache(task_id)
        paths = workspace_paths(task, create=bool(task.get("isAssignee")))
        if not paths.get("note") or not Path(paths["note"]).exists():
            raise FileNotFoundError(tr("employee_note_missing"))
        return redirect(obsidian_uri(workspace_root(), paths["note"]))
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(request.referrer or url_for("dashboard"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        try:
            lang = save_configuration()
            flash("تم حفظ الإعدادات." if lang == "ar" else "Settings saved.", "success")
            return redirect(url_for("settings"))
        except Exception as exc:
            flash(str(exc), "error")
    return render_template("settings.html", settings=settings_model(), selected=selected_projects())


@app.get("/language/<lang>")
def set_language(lang):
    lang = normalize_language(lang)
    STORE.set("ui_language", lang, profile_id=profile_id())
    return redirect(request.referrer or (url_for("dashboard") if STORE.configured(profile_id()) else url_for("setup")))


@app.get("/favicon.ico")
def favicon():
    return "", 204


@app.post("/api/workspace/test")
def test_workspace():
    import tempfile
    payload = request.get_json(silent=True) or {}
    selected = str(payload.get("path") or "").strip()
    if not selected:
        return jsonify(ok=False, error="Choose a folder."), 400
    root = Path(selected).expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="omi-folder-check-", dir=root) as temp:
            test_file = Path(temp) / "اختبار القراءة والكتابة.txt"
            test_file.write_text("OMI ✓", encoding="utf-8")
            if test_file.read_text(encoding="utf-8") != "OMI ✓":
                raise OSError("Read verification failed")
            long_dir = Path(temp) / ("long-path-" + "a" * 110) / ("unicode-" + "ب" * 110)
            long_dir.mkdir(parents=True)
            (long_dir / "اختبار.txt").write_text("OK", encoding="utf-8")
        return jsonify(ok=True, read=True, write=True, unicode=True, long_path=True)
    except OSError:
        return jsonify(ok=False, error="Folder read/write or long-path test failed. Check Windows permissions and path support."), 400


@app.get("/health")
def health():
    cache = cache_for(profile_id()) if profile_id() else empty_cache()
    return jsonify({"ok": True, "configured": STORE.configured(profile_id()), "cache": {"updated_at": cache.get("updated_at"), "error": cache.get("error")}})


def start_background_sync():
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        app.extensions["history_scheduler"].start(STOP_EVENT)
        app.extensions["recommendations"].start(STOP_EVENT)
        app.extensions["diwan_recommendations"].start(STOP_EVENT)
        thread = threading.Thread(target=sync_loop, name="bitrix-sync", daemon=True)
        thread.start()
        return thread


atexit.register(STOP_EVENT.set)

if __name__ == "__main__":
    app.debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    start_background_sync()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5055")), threaded=True)
