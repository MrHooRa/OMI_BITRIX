"""Independent Diwan and task-intelligence pages; mutations are profile-scoped."""
import hashlib
import json
import re
import threading
from datetime import date
from io import BytesIO

from flask import Blueprint, current_app, g, jsonify, render_template, request, send_file
from bitrix import BitrixClient
from diwany import DiwanClient, DiwanError, validate_config, normalize, field_value
from history import History, bitrix_pages, now, connection_scope
from history_scheduler import HistoryScheduler
from recommendation_service import RecommendationService
from recommendations import task_supervisors
from recommendation_routes import bp as recommendation_bp
from i18n import get_text
from security import CredentialVault
from sla import evaluate
from task_intelligence import data_quality, analyze, annotate
from recommendation_matching import group_related
from xlsx_report import build_workbook
from diwan_columns import BUILTINS, columns, validate_columns, value as column_value
from urllib.parse import urlsplit

bp = Blueprint("diwan", __name__)


def initialize(app, store):
    from diwan_recommendations import DiwanRecommendationService
    app.extensions["diwan_store"] = store
    app.extensions["diwan_vault"] = CredentialVault(store)
    app.extensions["diwan_history"] = History(store.db_path.parent / "task-history.sqlite3")
    app.extensions["history_scheduler"] = HistoryScheduler(store, app.extensions["diwan_vault"], app.extensions["diwan_history"])
    app.extensions["diwan_locks"] = {}
    app.extensions["diwan_locks_guard"] = threading.Lock()
    app.extensions["recommendations"] = RecommendationService(store, app.extensions["diwan_history"], store.db_path.parent / "recommendations")
    app.extensions["diwan_recommendations"] = DiwanRecommendationService(store, app.extensions["diwan_history"], store.db_path.parent / "recommendations", app.extensions["diwan_vault"])
    from employee_directory import EmployeeDirectory
    app.extensions["employee_directory"] = EmployeeDirectory(store, app.extensions["diwan_history"],
        {s: app.extensions[k] for s, k in (("bitrix", "recommendations"), ("diwan", "diwan_recommendations"))})
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(bp)


def store():
    return current_app.extensions["diwan_store"]


def history():
    cache = current_app.extensions["diwan_history"]
    for source, key in (("bitrix", "bitrix"), ("diwan", "diwan_analysis"), ("diwan", "diwan")):
        cache.bind_scope(profile(), key, connection_scope(store(), profile(), source))
    return cache


def scheduler():
    return current_app.extensions["history_scheduler"]


def vault():
    return current_app.extensions["diwan_vault"]


def profile():
    return g.profile_id


def profile_lock():
    with current_app.extensions["diwan_locks_guard"]:
        return current_app.extensions["diwan_locks"].setdefault(profile(), threading.RLock())


def config():
    return store().get("diwan_config", {}, profile_id=profile())


def settings():
    return store().get("intelligence_settings", {}, profile_id=profile())


def employees():
    return store().get("diwan_employees", [], profile_id=profile())


def client():
    token = vault().get(profile())
    if not token:
        raise DiwanError("token_required", 401)
    if not config():
        raise DiwanError("missing_endpoint", 409)
    return DiwanClient(config(), token)


def body():
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise DiwanError("invalid_input", 400)
    return value


def json_error(code, status=400):
    lang = store().get("ui_language", "en", profile_id=profile())
    return jsonify(ok=False, code=code, error=get_text(lang, "d_error_" + code)), status


@bp.errorhandler(DiwanError)
def handle_error(exc):
    return json_error(exc.code, exc.status)


@bp.errorhandler(ValueError)
@bp.errorhandler(TypeError)
def handle_input_error(exc):
    return json_error("invalid_input", 400)


@bp.errorhandler(RuntimeError)
def handle_runtime_error(exc):
    return json_error("credential_protection", 500)


@bp.get("/diwany")
def page():
    return render_template("diwany.html", connected=vault().present(profile()),
                           endpoint_ready=bool(config()), recipients=employees(),
                           delegate_ready=bool(config().get("delegate_url") and config().get("delegation_confirmed")))


@bp.get("/tasks")
def tasks():
    return render_template("tasks.html", analysis_settings=settings(), recipients=employees(),
                           default_source="bitrix" if store().get("webhook_url", profile_id=profile()) else "diwan")


@bp.get("/connections")
def connections():
    return render_template("connections.html", connection=config(), connected=vault().present(profile()),
                           recipients=employees(), analysis_settings=settings())


@bp.post("/api/diwany/config")
def save_config():
    raw = body()
    candidate = validate_config(raw)
    with profile_lock():
        if candidate != config():
            old_origins = {urlsplit(config()[name + "_url"]).netloc.casefold() for name in ("list", "detail", "delegate") if config().get(name + "_url")}
            new_origins = {urlsplit(candidate[name + "_url"]).netloc.casefold() for name in ("list", "detail", "delegate") if candidate.get(name + "_url")}
            if new_origins != old_origins:
                vault().remove(profile())
            history().invalidate(profile())
            history().invalidate(profile(), "diwan_analysis")
            store().set("diwan_config", candidate, profile_id=profile())
    return jsonify(ok=True)


@bp.post("/api/diwany/token")
def save_token():
    token = str(body().get("token", "")).strip()
    if not token or len(token) > 16384 or any(c.isspace() for c in token):
        raise DiwanError("invalid_token", 400)
    with profile_lock():
        current = config()
        if not current:
            raise DiwanError("missing_endpoint", 409)
        # Listing is read-only even for APIs that use POST.
        DiwanClient(current, token).list_page(page_size=1)
        if vault().get(profile()) != token:
            vault().save(profile(), token)
            history().invalidate(profile())
            history().invalidate(profile(), "diwan_analysis")
    return jsonify(ok=True)


@bp.delete("/api/diwany/token")
def remove_token():
    with profile_lock():
        vault().remove(profile())
        history().invalidate(profile())
        history().invalidate(profile(), "diwan_analysis")
    return jsonify(ok=True)


@bp.post("/api/diwany/sync")
def sync():
    data = body()
    filters = {}
    for key in ("requestId", "employeeName", "from", "to"):
        if data.get(key):
            filters[key] = str(data[key])[:200]
    if data.get("statusId") not in (None, ""):
        filters["statusId"] = int(data["statusId"])
    with profile_lock():
        bx = client()
        job = history().start(profile(), "diwan",
                              lambda cancelled: bx.iter_pages(filters, cancelled))
    return jsonify(ok=True, job_id=job), 202


@bp.route("/api/diwany/jobs/<job_id>", methods=["GET", "DELETE"])
def job_status(job_id):
    return jsonify(ok=True, job=history().job(profile(), job_id, request.method == "DELETE"))


@bp.get("/api/diwany/tasks")
def task_list():
    snapshot = history().metadata(profile(), "diwan")
    query = request.args.get("q", "").casefold()
    page_number = max(1, int(request.args.get("page", 1)))
    rows, total = history().page(profile(), "diwan", page_number, query)
    selected = columns(store(), profile())
    labels = dict(BUILTINS)
    lang = store().get("ui_language", "en", profile_id=profile())
    selected = [{**column, "label": column["label"] or (get_text(lang, labels[column["key"][5:]])
                if column["key"].startswith("task:") else column["key"][5:])} for column in selected]
    rendered = [{**{key: val for key, val in row.items() if key != "display_fields"},
                 "display_values": [column_value(row, column["key"]) for column in selected]} for row in rows]
    return jsonify(ok=True, records=rendered, columns=selected, total=total, page=page_number, coverage=snapshot)


@bp.route("/api/diwany/columns", methods=["GET", "POST"])
def list_columns():
    if request.method == "POST":
        selected = validate_columns(body().get("columns"))
        store().set("diwan_columns", selected, profile_id=profile())
        return jsonify(ok=True)
    lang = store().get("ui_language", "en", profile_id=profile())
    available = [{"key": "task:" + name, "label": get_text(lang, label)} for name, label in BUILTINS]
    keys = set()
    for cache in ("diwan", "diwan_analysis"):
        for record in history().source(profile(), cache, copy_records=False)["records"]:
            keys.update(record.get("display_fields", {}))
    available.extend({"key": "json:" + key, "label": key} for key in sorted(keys)[:1000])
    return jsonify(ok=True, available=available, selected=columns(store(), profile()), has_json_fields=bool(keys))


def accessible_task(task_id):
    for record in history().source(profile(), "diwan", copy_records=False)["records"]:
        if record["id"] == task_id:
            return record
    raise DiwanError("not_found", 404)


@bp.get("/api/diwany/tasks/<task_id>")
def details(task_id):
    with profile_lock():
        original = accessible_task(task_id)
        generation = history().generation(profile())
        data = client().details(task_id)
        data.setdefault(config()["task_id_field"], task_id)
        row = normalize(data, config())
        row["request_id"] = row["request_id"] or original["request_id"]
        history().update_record(profile(), "diwan", row, generation)
    return jsonify(ok=True, task=row)


def operation_key(task_id):
    value = config().get("list_url", "") + "|" + task_id
    return "diwan_operation_" + hashlib.sha256(value.encode()).hexdigest()


@bp.post("/api/diwany/tasks/<task_id>/delegate")
def delegate(task_id):
    payload = body()
    if payload.get("confirmed") is not True:
        raise DiwanError("confirmation_required", 400)
    with profile_lock(), current_app.extensions["diwan_recommendations"].lock:
        task = accessible_task(task_id)
        service = current_app.extensions["diwan_recommendations"]
        context = service.context(profile())
        if not context:
            raise DiwanError("roles_required", 409)
        shared = service.operation(profile(), task_id)
        if shared and shared.get("status") in {"pending", "uncertain"}:
            raise DiwanError("delegation_uncertain", 409)
        person = next((p for p in employees() if p["value"] == payload.get("recipient") and p.get("source", "diwan") == "diwan"), None)
        if person is None:
            raise DiwanError("invalid_recipient", 400)
        if person.get("away_from") and person["away_from"] <= date.today().isoformat() <= person.get("away_to", ""):
            raise DiwanError("recipient_unavailable", 409)
        key = operation_key(task_id)
        previous = store().get(key, {}, profile_id=profile())
        if previous.get("status") in {"pending", "uncertain"}:
            raise DiwanError("delegation_uncertain", 409)
        api = client()
        current = api.details(task_id)
        if str(field_value(current,config()["assignee_field"],"") or "") == person["value"]:
            raise DiwanError("already_assigned", 409)
        current.setdefault(config()["task_id_field"], task_id)
        live = normalize(current, config())
        if context["user"] not in task_supervisors(live):
            raise DiwanError("permission_denied", 403)
        if live["completed"]:
            raise DiwanError("task_completed", 409)
        marker = {"status": "pending", "recipient": person["value"], "time": now()}
        store().set(key, marker, profile_id=profile())
        service.operation(profile(), task_id, person["value"], "pending")
        try:
            after = api.delegate(task_id, live["request_id"] or task["request_id"], person)
        except DiwanError as exc:
            marker["status"] = "failed" if exc.code in {
                "token_invalid", "permission_denied", "source_rejected", "delegation_disabled"} else "uncertain"
            store().set(key, marker, profile_id=profile())
            service.operation(profile(), task_id, person["value"], marker["status"])
            raise
        except Exception:
            marker["status"] = "uncertain"
            store().set(key, marker, profile_id=profile())
            service.operation(profile(), task_id, person["value"], marker["status"])
            raise DiwanError("delegation_uncertain", 409) from None
        marker["status"] = "confirmed"
        store().set(key, marker, profile_id=profile())
        service.operation(profile(), task_id, person["value"], "confirmed")
        after.setdefault(config()["task_id_field"], task_id)
        service.decision(profile(), normalize(after, config()), "assigned", context["user"])
        history().update_record(profile(), "diwan", normalize(after, config()),
                                history().generation(profile()))
    return jsonify(ok=True)


@bp.post("/api/diwany/tasks/<task_id>/reconcile")
def reconcile(task_id):
    with profile_lock(), current_app.extensions["diwan_recommendations"].lock:
        accessible_task(task_id)
        key = operation_key(task_id)
        marker = store().get(key, {}, profile_id=profile())
        if marker.get("status") not in {"pending", "uncertain"}:
            raise DiwanError("not_found", 404)
        current = client().details(task_id)
        if str(field_value(current,config()["assignee_field"],"") or "") != marker["recipient"]:
            raise DiwanError("delegation_uncertain", 409)
        service = current_app.extensions["diwan_recommendations"]
        context = service.context(profile())
        current.setdefault(config()["task_id_field"], task_id)
        live = normalize(current, config())
        if not context or context["user"] not in task_supervisors(live):
            raise DiwanError("permission_denied", 403)
        service.operation(profile(), task_id, marker["recipient"], "confirmed")
        service.decision(profile(), live, "assigned", context["user"])
        marker.update(status="confirmed", time=now())
        store().set(key, marker, profile_id=profile())
    return jsonify(ok=True)


@bp.post("/api/diwany/employees")
def save_employees():
    rows = body().get("employees")
    if not isinstance(rows, list) or len(rows) > 500:
        raise DiwanError("invalid_input", 400)
    normalized, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            raise DiwanError("invalid_input", 400)
        value = str(row.get("value", "")).strip()
        source = "bitrix" if row.get("source") == "bitrix" else "diwan"
        if not value or len(value) > 200 or (source, value) in seen:
            raise DiwanError("invalid_recipient", 400)
        if source == "diwan" and config().get("recipient_kind") == "email" and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise DiwanError("invalid_recipient", 400)
        entry = {k: str(row.get(k, "")).strip()[:200] for k in
                 ("name_en", "name_ar", "away_from", "away_to")}
        if bool(entry["away_from"]) != bool(entry["away_to"]):
            raise DiwanError("invalid_input", 400)
        if entry["away_from"] and date.fromisoformat(entry["away_from"]) > date.fromisoformat(entry["away_to"]):
            raise DiwanError("invalid_input", 400)
        entry.update(value=value, source=source)
        seen.add((source, value))
        normalized.append(entry)
    with profile_lock():
        store().set("diwan_employees", normalized, profile_id=profile())
    return jsonify(ok=True)


@bp.post("/api/history/sync")
def history_sync():
    source = str(body().get("source", "bitrix"))
    job = scheduler().refresh(profile(), source, force=True)
    if not job:
        raise DiwanError("bitrix_required" if source == "bitrix" else "token_required", 409)
    return jsonify(ok=True, job_id=job), 202


def all_records(selected=""):
    if selected:
        scheduler().refresh(profile(), selected)
    else:
        scheduler().tick(profile())
    records, coverage = [], {}
    for source in ("diwan", "bitrix"):
        if selected and source != selected:
            continue
        state = history().source(profile(), scheduler().cache_key(source), copy_records=False)
        state["count"] = len(state["records"])
        state.update({key: value for key, value in history().metadata(profile(), scheduler().cache_key(source)).items()
                      if key in {"index_ready", "index_error"}})
        state["schedule"] = scheduler().status(profile(), source)
        records.extend(state.pop("records"))
        coverage[source] = state
    return records, coverage


@bp.get("/api/intelligence/tags")
def available_tags():
    records, _ = all_records("bitrix")
    return jsonify(ok=True, tags=sorted({tag for r in records if r["source"] == "bitrix" for tag in r.get("tags", [])}))


@bp.get("/api/intelligence")
def intelligence():
    selected = request.args.get("source", "")
    if selected not in {"", "bitrix", "diwan"}:
        raise DiwanError("invalid_input", 400)
    records, coverage = all_records(selected)
    pairs = []
    selected = request.args.get("source", "")
    for source in ("bitrix", "diwan"):
        if selected and source != selected:
            continue
        index = history().index(profile(), scheduler().cache_key(source))
        coverage[source].update({key: value for key, value in history().metadata(profile(), scheduler().cache_key(source)).items()
                                if key in {"index_ready", "index_error"}})
        if index and request.args.get("pairs") == "1":
            if index.preview is None:
                index.preview = index.examples()
            pairs.extend(index.preview)
    pairs.sort(key=lambda p: -p["match"]["score"])
    selected=request.args.get("source","")
    query=request.args.get("q","").strip().casefold()
    filtered = [] if selected else [r for r in records if not query or query in (r["id"]+" "+r["title"]+" "+r.get("assignee_name","")).casefold()]
    page_number=max(1,int(request.args.get("page",1)))
    page_rows, total = history().page(profile(), scheduler().cache_key(selected), page_number, query, selected) if selected else (filtered[(page_number-1)*50:page_number*50], len(filtered))
    quality = current_app.extensions.setdefault("history_quality", {})
    diagnostics = {}
    for source in coverage:
        key = (profile(), source)
        revision = coverage[source].get("revision")
        cached = quality.get(key)
        if not cached or cached[0] != revision:
            cached = (revision, data_quality([record for record in records if record["source"] == source]))
            quality[key] = cached
        diagnostics[source] = cached[1]
    return jsonify(ok=True, pairs=pairs[:8], records=annotate(page_rows, settings()),
                   filtered_total=total,page=page_number,quality=diagnostics,
                   total=len(records), coverage=coverage,
                   evaluation=evaluate(records) if request.args.get("evaluate") == "1" else None)


@bp.post("/api/intelligence/analyze")
def analyze_task():
    data = body()
    text = str(data.get("text", "")).strip()[:4000]
    source = str(data.get("source", "diwan"))
    if source not in {"diwan", "bitrix"} or (not text and not data.get("task_id")):
        raise DiwanError("invalid_input", 400)
    records, coverage = all_records(source)
    exclude = None
    if data.get("task_id"):
        row = next((r for r in records if r["source"] == source and r["id"] == str(data["task_id"])), None)
        if row is None:
            raise DiwanError("not_found", 404)
        text = row["title"] + " " + row["description"]
        exclude = (source, row["id"])
    # Similarity and assignment share the linked, profile-visible evidence pool.
    from recommendation_routes import unified_directory
    directory = unified_directory()
    recommendation_service = directory.services[source]
    recommendation_context = recommendation_service.context(profile())
    linked_completed = []
    if recommendation_context:
        recommendation_state = recommendation_service._state(recommendation_context)
        recommendation_service._prepare(recommendation_context, recommendation_state)
        prepared, _, _ = recommendation_service.ranking_inputs(recommendation_context, recommendation_state)
        linked_completed = [r for r in prepared.records if r["source"] != source]
    custom_rules = store().get("task_domain_rules", [], profile_id=profile())
    local_index = history().index(profile(), scheduler().cache_key(source))
    if local_index is None and any(record["source"] == source for record in records):
        raise DiwanError(history().metadata(profile(), scheduler().cache_key(source)).get("index_error") or "index_building", 409)
    if custom_rules or linked_completed:
        from task_intelligence import TaskIndex
        scoped_rows = [r for r in records if r["source"] == source] + linked_completed
        signature = hashlib.sha256(json.dumps([scoped_rows, custom_rules], sort_keys=True).encode()).hexdigest()
        if recommendation_context:
            if recommendation_state.get("analysis_revision") != signature:
                recommendation_state["analysis_index"] = TaskIndex(scoped_rows, domain_rules=custom_rules)
                recommendation_state["analysis_revision"] = signature
            local_index = recommendation_state["analysis_index"]
        else:
            local_index = TaskIndex(scoped_rows, domain_rules=custom_rules)
    result = analyze(records, text, settings(), employees(), source,
                     str(data.get("category", ""))[:200],
                     index=local_index, exclude=exclude)
    result["related_groups"] = group_related(result["related"])
    result["evidence_sources"] = recommendation_state.get("evidence_sources", []) if recommendation_context else []
    result.update(exclude_id=exclude[1] if exclude else None, query_text=text, project_id=row.get("project_id", "") if exclude else "")
    # Bitrix employee ranking is provided by the unified recommendation service.
    result["recommendations"] = []
    return jsonify(ok=True, result=result, coverage=coverage)


@bp.post("/api/intelligence/settings")
def save_analysis_settings():
    data = body()
    clean = {"tag_priorities": {}, "sla_hours": {}, "working_days": data.get("working_days", [6, 0, 1, 2, 3]),
             "start_hour": int(data.get("start_hour", 8)), "end_hour": int(data.get("end_hour", 16)),
             "holidays": data.get("holidays", [])}
    if not isinstance(clean["working_days"], list) or not clean["working_days"] or not all(type(d) is int and 0 <= d <= 6 for d in clean["working_days"]):
        raise DiwanError("invalid_input", 400)
    if not 0 <= clean["start_hour"] < clean["end_hour"] <= 24:
        raise DiwanError("invalid_input", 400)
    if not isinstance(clean["holidays"], list) or len(clean["holidays"]) > 500:
        raise DiwanError("invalid_input", 400)
    clean["holidays"] = [date.fromisoformat(d).isoformat() for d in clean["holidays"]]
    for name, maximum in (("tag_priorities", 3), ("sla_hours", 2000)):
        values = data.get(name, {})
        if not isinstance(values, dict) or len(values) > 500:
            raise DiwanError("invalid_input", 400)
        for key, value in values.items():
            number = float(value)
            if not 0 <= number <= maximum or (name == "tag_priorities" and number != int(number)):
                raise DiwanError("invalid_input", 400)
            clean[name][str(key)[:200]] = number
    store().set("intelligence_settings", clean, profile_id=profile())
    return jsonify(ok=True)


@bp.get("/diwany/export.xlsx")
def export():
    state = history().source(profile(), "diwan")
    rows = [["Task ID", "Request ID", "Title", "Status", "Employee", "Created", "Completed"]]
    fields, actions = [["Task ID", "Field ID", "Label", "Value"]], [["Task ID", "Workflow action"]]
    for r in state["records"]:
        rows.append([r["id"], r["request_id"], r["title"], r["status_label"], r["assignee_name"],
                     r["created_at"], r["completed_at"]])
        for field in r["fields"]:
            fields.append([r["id"], field["id"], field["label"], json.dumps(field["value"], ensure_ascii=False)])
        for action in r["actions"]:
            actions.append([r["id"], json.dumps(action, ensure_ascii=False)])
    content = build_workbook([("Requests", rows, [18, 20, 40, 24, 30, 25, 25]), ("Form Fields", fields, [18, 18, 30, 60]), ("Workflow", actions, [18, 80])])
    return send_file(BytesIO(content), as_attachment=True, download_name="diwany.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
