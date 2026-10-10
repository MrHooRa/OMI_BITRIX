"""Profile-scoped Bitrix recommendations and explicit human assignment actions."""
from collections import defaultdict
from flask import Blueprint, current_app, g, jsonify, render_template, request, redirect, url_for
from bitrix import BitrixClient, BitrixError
from history import bitrix_record
from diwany import DiwanError
from recommendations import validate_policy, task_supervisors, pending_review

bp = Blueprint("recommendations", __name__)


def unified_directory():
    from employee_directory import EmployeeDirectory
    store = current_app.extensions["diwan_store"]
    directory = current_app.extensions.get("employee_directory")
    if directory is None or directory.store is not store:
        directory = EmployeeDirectory(store, current_app.extensions["diwan_history"],
            {s: current_app.extensions[k] for s, k in (("bitrix", "recommendations"), ("diwan", "diwan_recommendations"))})
        current_app.extensions["employee_directory"] = directory
    return directory


def service():
    unified_directory()
    return current_app.extensions["diwan_recommendations" if request.args.get("source") == "diwan" else "recommendations"]


def payload():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ValueError("Invalid request")
    return value


@bp.errorhandler(ValueError)
@bp.errorhandler(TypeError)
def bad_request(error):
    return jsonify(ok=False, error=str(error)), 400


@bp.errorhandler(PermissionError)
def forbidden(error):
    return jsonify(ok=False, error=str(error)), 403


@bp.errorhandler(DiwanError)
def diwan_error(error):
    return jsonify(ok=False,error=str(error)), error.status


@bp.errorhandler(BitrixError)
def source_error(error):
    return jsonify(ok=False, error="Bitrix could not verify or complete this action. Refresh and check permissions."), 502


@bp.get("/recommendations")
def page():
    return redirect(url_for("diwan.tasks", **{**request.args.to_dict(), "view": "assignments"}))


@bp.get("/api/recommendations")
def snapshot():
    data = service().snapshot(g.profile_id)
    if request.args.get("summary") == "1":
        notifications = [r for r in data.get("notifications", []) if data.get("user_id") not in r.get("read_by", [])]
        notifications.sort(key=lambda r: (-int(r.get("priority") or 0), r.get("deadline") or "9999", r["id"]))
        first = notifications[0] if notifications else None
        data = {"configured": data["configured"], "unread": data.get("unread", 0),
                "alert": {"id": first["id"], "title": first["title"], "suggestion": first.get("suggestion"),
                          "source": service().source_name} if first else None}
    return jsonify(ok=True, **data)


@bp.post("/api/recommendations/refresh")
def refresh():
    service().refresh(g.profile_id, force=True)
    return jsonify(ok=True, **service().snapshot(g.profile_id))


@bp.post("/api/recommendations/policy")
def save_policy():
    if service().source_name == "diwan":
        raise ValueError("Manage Diwan recipients in connection settings")
    clean = validate_policy(payload())
    context = service().context(g.profile_id)
    if not context:
        raise ValueError("Connect Diwan and configure its task roles first" if service().source_name == "diwan" else "Connect Bitrix first")
    projects = {p["id"] for p in context["projects"]}
    if any(set(e["projects"]) - projects for e in clean["employees"]):
        raise ValueError("Employee eligibility must use selected projects")
    service().store.set("recommendation_policy", clean, profile_id=g.profile_id)
    # Source field changes are picked up by the independent full-history scheduler.
    service().refresh(g.profile_id, force=True)
    return jsonify(ok=True)


@bp.post("/api/recommendations/rank")
def recommend():
    data = payload()
    text = str(data.get("text", "")).strip()[:4000]
    if not data.get("task_id") and not text:
        raise ValueError("Enter task text or select an open task")
    live_record = None
    if data.get("task_id"):
        _, _, live_record = live_task(str(data["task_id"]), require_edit=False)
    return jsonify(ok=True, result=service().recommend(g.profile_id, data.get("task_id"), text,
                    str(data.get("project_id", "")), str(data.get("category", ""))[:200],
                    exclude_id=str(data.get("exclude_id") or ""), live_record=live_record))


def live_task(task_id, require_edit=True):
    context = service().context(g.profile_id)
    if not context:
        raise ValueError("Connect Diwan and configure its task roles first" if service().source_name == "diwan" else "Connect Bitrix first")
    api, actor, task = source_task(context, task_id)
    if require_edit and context.get("source") == "diwan" and not context["config"].get("delegation_confirmed"):
        raise PermissionError("Confirm the Diwan delegation contract first")
    if task["project_id"] not in {p["id"] for p in context["projects"]}:
        raise PermissionError("Task is outside selected projects")
    if task["completed"] or pending_review(task):
        raise ValueError("Closed or pending-review tasks cannot enter the assignment queue")
    if actor not in task_supervisors(task):
        raise PermissionError("Only this task owner or observer may manage its assignment")
    if require_edit and context.get("source") != "diwan":
        access = api.task_access(task_id, actor)
        if not (access.get("EDIT") or access.get("DELEGATE")):
            raise PermissionError("Bitrix assignment permission is required")
    return api, actor, task


@bp.post("/api/recommendations/tasks/<task_id>/needs-assignment")
def needs_assignment(task_id):
    with service().lock:
        _, actor, task = live_task(task_id)
        assert_resolved(task_id)
        service().decision(g.profile_id, task, "needs_assignment", actor)
    return jsonify(ok=True)


def assert_resolved(task_id):
    if service().operation(g.profile_id, task_id).get("status") in {"pending", "uncertain"}:
        raise ValueError("Assignment outcome requires reconciliation")


@bp.post("/api/recommendations/tasks/<task_id>/self")
def self_assignment(task_id):
    with service().lock:
        _, actor, task = live_task(task_id, require_edit=False)
        assert_resolved(task_id)
        if task["assignee_id"] != actor:
            raise PermissionError("Only the current assignee can declare that they will do the work")
        service().decision(g.profile_id, task, "self", actor)
    return jsonify(ok=True)


@bp.post("/api/recommendations/tasks/<task_id>/assign")
def assign(task_id):
    body, status = execute_assignment(task_id, payload())
    return jsonify(**body), status


def execute_assignment(task_id, data):
    """The single transaction used by both assignment interfaces."""
    if data.get("confirmed") is not True:
        raise ValueError("Confirm the assignment")
    # Serialize local mutations; Bitrix is read again immediately before writing.
    with service().lock:
        api, actor, task = live_task(task_id)
        if str(data.get("expected_assignee", "")) != task["assignee_id"]:
            return {"ok": False, "error": "Assignee changed. Refresh the recommendation."}, 409
        assert_resolved(task_id)
        result = service().recommend(g.profile_id, task_id, live_record=task)
        target = str(data.get("employee_id", ""))
        if result["stale"] or target not in result["eligible_ids"]:
            raise ValueError("Refresh workload and choose an eligible employee")
        if target == task["assignee_id"] and target in task_supervisors(task) and target != actor:
            raise ValueError("Only the supervising employee can confirm their own execution; choose an executor or ask them to confirm")
        if target == task["assignee_id"] and target == actor:
            service().decision(g.profile_id, task, "self", actor, result, str(data.get("reason", "")))
            return {"ok": True}, 200
        if service().source_name == "diwan":
            from diwany_routes import operation_key
            legacy = service().store.get(operation_key(task_id), {}, profile_id=g.profile_id)
            if legacy.get("status") in {"pending", "uncertain"}:
                raise ValueError("Verify the outstanding Diwan delegation before another assignment")
        # Inference can take seconds. Verify roles, edit rights and task inputs again
        # immediately before writing, rather than relying on the pre-analysis read.
        api, latest_actor, latest = live_task(task_id)
        fields = ("assignee_id", "creator_id", "auditor_ids", "project_id", "title", "description", "status")
        if latest_actor != actor or any(latest.get(k) != task.get(k) for k in fields):
            return {"ok": False, "error": "Task changed during analysis. Refresh before assigning."}, 409
        task = latest
        metadata = {}
        if service().source_name == "bitrix":
            capture = current_app.extensions.get("assignment_workspace_context")
            if capture:
                metadata = capture(task, target)
        service().operation(g.profile_id, task_id, target, "pending", workspace=metadata,
                            reason=str(data.get("reason", ""))[:500], follow_up="pending")
        try:
            context = service().context(g.profile_id)
            if context.get("source") == "diwan":
                people = unified_directory().source_people(g.profile_id, "diwan")
                person = next(p for p in people if p["id"] == target and p["enabled"] and p["active"])
                person = {**person, "value": person["id"], "name_ar": person["name"], "name_en": person["name"]}
                api.delegate(task_id, task["request_id"], person)
            else:
                api.reassign_task(task_id, target)
            _, _, confirmed = source_task(context, task_id)
            if confirmed["assignee_id"] != target:
                raise ValueError("Assignment not confirmed")
        except Exception:
            service().operation(g.profile_id, task_id, target, "uncertain")
            return {"ok": False, "error": "Outcome uncertain. Use Verify assignment; do not retry blindly."}, 409
        service().decision(g.profile_id, confirmed, "self" if actor == target else "assigned", actor,
                           result, str(data.get("reason", "")))
        service().operation(g.profile_id, task_id, target, "confirmed")
        warnings = finish_assignment(task_id, api)
    return {"ok": True, "warnings": warnings}, 200


def finish_assignment(task_id, api):
    """Source success is final even if local files or the audit comment fail."""
    operation = service().operation(g.profile_id, task_id)
    if operation.get("follow_up") == "complete":
        return []
    callback = current_app.extensions.get("assignment_workspace_finish")
    if service().source_name != "bitrix" or not callback:
        return []
    # Record the attempt first: an ambiguous comment response must never be retried blindly.
    service().operation(g.profile_id, task_id, status="confirmed", follow_up="attempted")
    try:
        warnings = callback(api, task_id, operation)
    except Exception:
        warnings = ["Assignment confirmed; workspace follow-up could not be completed. Check the workspace before moving files manually."]
    service().operation(g.profile_id, task_id, status="confirmed",
                        follow_up="attention" if warnings else "complete", warnings=warnings)
    return warnings


def update_legacy_marker(task_id, status):
    if service().source_name != "diwan":
        return
    from diwany_routes import operation_key
    key = operation_key(task_id)
    marker = service().store.get(key, {}, profile_id=g.profile_id)
    if marker:
        service().store.set(key, {**marker, "status": status}, profile_id=g.profile_id)


@bp.post("/api/recommendations/tasks/<task_id>/verify")
def verify(task_id):
    with service().lock:
        api, actor, task = live_task(task_id)
        operation = service().operation(g.profile_id, task_id)
        if not operation or task["assignee_id"] != operation.get("target"):
            return jsonify(ok=False, error="Assignment is still unconfirmed. Check the task in its source."), 409
        if operation.get("status") != "confirmed":
            service().decision(g.profile_id, task, "self" if actor == task["assignee_id"] else "assigned", actor)
        service().operation(g.profile_id, task_id, status="confirmed")
        update_legacy_marker(task_id, "confirmed")
        warnings = finish_assignment(task_id, api) if operation.get("follow_up") == "pending" else operation.get("warnings", [])
    return jsonify(ok=True, warnings=warnings)


@bp.post("/api/recommendations/tasks/<task_id>/read")
def mark_read(task_id):
    service().mark_read(g.profile_id, task_id)
    return jsonify(ok=True)


@bp.get("/api/recommendations/evidence/<task_id>")
def evidence(task_id):
    # This read-only view neither creates workspaces nor assumes executor rights.
    context = service().context(g.profile_id)
    if not context:
        raise PermissionError("Connect Diwan first" if service().source_name == "diwan" else "Connect Bitrix first")
    _, _, row = source_task(context, task_id)
    if row["project_id"] not in {p["id"] for p in context["projects"]}:
        raise PermissionError("Task is outside selected projects")
    return jsonify(ok=True, task=row)


@bp.get("/api/recommendations/decisions")
def decisions():
    context = service().context(g.profile_id)
    if not context:
        return jsonify(ok=True, events=[])
    state = service()._state(context)
    allowed = {r["id"] for r in state["active"] if context["user"] in task_supervisors(r)}
    source = service().history.source(g.profile_id, "diwan_analysis" if service().source_name == "diwan" else "bitrix")
    allowed.update(r["id"] for r in source["records"] if context["user"] in task_supervisors(r))
    journal = service().journal.read(context["key"])
    events = [e for e in journal["audit"] if e.get("task_id") in allowed]
    return jsonify(ok=True, events=list(reversed(events))[:200])


@bp.post("/api/recommendations/tasks/<task_id>/release-uncertain")
def release_uncertain(task_id):
    if payload().get("confirmed") is not True:
        raise ValueError("Confirm reconciliation")
    with service().lock:
        _, actor, task = live_task(task_id)
        operation = service().operation(g.profile_id, task_id)
        if not operation or operation.get("status") != "uncertain":
            raise ValueError("No uncertain assignment to reconcile")
        if task["assignee_id"] == operation.get("target"):
            raise ValueError("Assignment succeeded; verify it instead")
        service().operation(g.profile_id, task_id, status="cancelled")
        update_legacy_marker(task_id, "cancelled")
    return jsonify(ok=True)


def source_task(context, task_id):
    if context.get("source") == "diwan":
        from diwany import normalize
        api = service().client(context)
        raw = api.details(task_id)
        raw.setdefault(context["config"]["task_id_field"], task_id)
        return api, context["user"], normalize(raw, context["config"])
    api = BitrixClient(context["url"])
    return api, str(api.current_user()["ID"]), bitrix_record(api.task_get(task_id), context["policy"].get("category_field", ""), context["policy"].get("data_fields", {}))


@bp.get("/api/recommendations/fields")
def source_fields():
    context=service().context(g.profile_id)
    if not context or service().source_name != "bitrix":
        return jsonify(ok=True,fields=[])
    fields=BitrixClient(context["url"]).get_task_fields()
    fields=fields.get("fields",fields)
    return jsonify(ok=True,fields=[{"id":key,"name":value.get("title") or key} for key,value in fields.items() if isinstance(value,dict)])


@bp.get("/api/recommendations/people")
def employee_profiles():
    from employee_insights import profiles
    with service().lock:
        context = service().context(g.profile_id)
        if not context:
            return jsonify(ok=True, configured=False, people=[], total=0)
        state = service()._state(context)
        service()._prepare(context, state)
        prepared, workload, _ = service().ranking_inputs(context, state)
        data = profiles(service().directory(context, state), prepared.records, [r for rows in workload.values() for r in rows], detail_id=request.args.get("employee", ""), classifier=prepared.classify)
        topics = {t["id"]: {k: v for k, v in t.items() if k != "count"} for p in data for t in p["topics"]}
        query = request.args.get("q", "").strip().casefold()[:200]
        topic = request.args.get("topic", "")
        ident = request.args.get("employee", "")
        evidence_text = defaultdict(str)
        for row in prepared.records:
            evidence_text[str(row.get("assignee_id") or "")] += " " + row.get("title", "") + " " + row.get("description", "")
        for person in data:
            if not ident:
                person.pop("tasks", None)
        if ident:
            data = [p for p in data if p["id"] == ident]
            if not data:
                return jsonify(ok=False, error="Employee unavailable in this source scope"), 404
        data = [p for p in data if (not topic or any(t["id"] == topic for t in p["topics"])) and
                (not query or query in (p["name"] + " " + " ".join(t["ar"] + " " + t["en"] for t in p["topics"]) + evidence_text[p["id"]]).casefold())]
        data.sort(key=lambda p: (-p["completed_count"], p["name"], p["id"]))
        page = max(1, int(request.args.get("page", 1)))
        total = len(data)
        if ident:
            person = data[0] if data else None
            if person:
                person["task_total"] = len(person["tasks"])
                person["tasks"] = person["tasks"][(page-1)*20:page*20]
        else:
            data = data[(page-1)*20:page*20]
        return jsonify(ok=True, configured=True, people=data, total=total, page=page,
                       history_ready=state.get("history_complete", False), checked_at=state["checked_at"],
                       stale=bool(state.get("error") or state.get("directory_error")) or service().clock()-state.get("checked_epoch", 0)>120,
                       topics=list(topics.values()), projects=context["projects"])


@bp.get("/api/employees")
def directory_snapshot():
    data = unified_directory().snapshot(g.profile_id)
    query = request.args.get("q", "").strip().casefold()[:200]
    if query:
        data["people"] = [p for p in data["people"] if query in (
            p["name"] + " " + p["team"] + " " + " ".join(a["id"] for a in p["accounts"])).casefold()]
    return jsonify(ok=True, **data)


@bp.post("/api/employees")
def directory_save():
    return jsonify(ok=True, **unified_directory().save(g.profile_id, payload().get("people")))


@bp.get("/api/intelligence/domains")
def domain_rules():
    selected = request.args.get("source", "bitrix")
    cache = "diwan_analysis" if selected == "diwan" else "bitrix"
    index = service().history.index(g.profile_id, cache)
    discovered = index.domain_model if index and hasattr(index.domain_model, "topics") else None
    return jsonify(ok=True, builtins=[{k:t[k] for k in ("id","ar","en","support")} for t in discovered.topics] if discovered else [],
        discovery=discovered.summary() if discovered else {"status":"insufficient_corpus","predefined_domains":False},
        domains=current_app.extensions["diwan_store"].get("task_domain_rules", [], profile_id=g.profile_id))


@bp.post("/api/intelligence/domains")
def save_domain_rules():
    from task_language import validate_domain_rules
    from employee_insights import TAXONOMY
    rows = validate_domain_rules(payload().get("domains"))
    if {r["id"] for r in rows} & {row[0] for row in TAXONOMY}:
        raise ValueError("Custom domains must use identifiers distinct from built-in labels")
    current_app.extensions["diwan_store"].set("task_domain_rules", rows, profile_id=g.profile_id)
    return jsonify(ok=True)
