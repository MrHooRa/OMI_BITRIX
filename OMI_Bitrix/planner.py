from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("Asia/Riyadh")


def parse_deadline(deadline):
    if not deadline:
        return None
    try:
        dt = datetime.fromisoformat(str(deadline).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=LOCAL_TZ)
        return dt.astimezone(LOCAL_TZ)
    except Exception:
        return None


def due_bucket(deadline):
    if not deadline:
        return "no-deadline", None
    dt = parse_deadline(deadline)
    if not dt:
        return "later", None
    now = datetime.now(LOCAL_TZ)
    hours = (dt - now).total_seconds() / 3600
    if hours < 0:
        return "overdue", hours
    if dt.date() == now.date():
        return "today", hours
    if (dt.date() - now.date()).days <= 2:
        return "soon", hours
    return "later", hours


def planner_weight(task):
    """Explainable focus weight; planner edits are kept in browser localStorage."""
    weight = 1.0
    if str(task.get("priority")) == "2":
        weight += 0.8
    if str(task.get("status")) == "3":
        weight += 0.35
    deadline = parse_deadline(task.get("deadline"))
    if deadline:
        now = datetime.now(LOCAL_TZ)
        if deadline < now:
            weight += 0.9
        elif deadline.date() == now.date():
            weight += 0.65
    try:
        estimate = float(task.get("timeEstimate") or 0)
        if estimate > 0:
            # Bitrix commonly returns TIME_ESTIMATE in seconds. Blend it instead of
            # trusting it completely because many teams do not maintain this field.
            hours = estimate / 3600.0
            weight += min(2.0, max(0.0, hours / 2.0))
    except (TypeError, ValueError):
        pass
    return weight


def build_today_plan(tasks, workday_start="08:00", total_minutes=480):
    """Allocate today's 8-hour focus plan.

    Eligibility is intentionally broader than just deadlines: a task belongs in the
    daily plan when it is due today OR when the assignee has explicitly started it
    in Bitrix (status 3 / in progress). This lets someone pull a future queued task
    into today's focus plan simply by pressing Start, without changing its deadline.
    Delay justification remains a deadline rule elsewhere in the app, not a planner
    rule, so a future started task never becomes 'late' just because it is planned.
    """
    if not isinstance(total_minutes, int) or total_minutes <= 0 or total_minutes % 15:
        raise ValueError("Planner capacity must be a positive multiple of 15 minutes.")
    now = datetime.now(LOCAL_TZ)
    today_tasks = []
    seen = set()
    for task in tasks:
        deadline = parse_deadline(task.get("deadline"))
        due_today = bool(deadline and deadline.date() == now.date())
        started = str(task.get("status") or "") == "3"
        overdue = bool(deadline and deadline < now)
        if str(task.get("status")) in {"4", "5", "6", "7"}:
            continue
        if due_today or started or overdue:
            task_id = str(task.get("id") or "")
            if task_id in seen:
                continue
            seen.add(task_id)
            item = dict(task)
            item["deadlineLocal"] = deadline.isoformat() if deadline else ""
            item["plannerWeight"] = planner_weight(task)
            item["plannerReason"] = "overdue" if overdue else ("due_today" if due_today else "started")
            today_tasks.append(item)

    def plan_sort_key(t):
        deadline = parse_deadline(t.get("deadline"))
        if deadline and deadline < now:
            urgency = 0
        elif deadline and deadline.date() == now.date():
            urgency = 1
        else:
            urgency = 2
        return (
            0 if str(t.get("priority")) == "2" else 1,
            urgency,
            t.get("deadlineLocal") or "9999",
        )

    today_tasks.sort(key=plan_sort_key)
    if not today_tasks:
        return []

    slot = 15
    total_slots = total_minutes // slot
    n = len(today_tasks)
    base = [1 if n <= total_slots else 0 for _ in today_tasks]
    remaining = total_slots - sum(base)
    weights = [max(0.1, t["plannerWeight"]) for t in today_tasks]
    weight_sum = sum(weights) or 1.0
    raw = [remaining * (w / weight_sum) for w in weights]
    added = [int(x) for x in raw]
    left = remaining - sum(added)
    order = sorted(range(n), key=lambda i: raw[i] - added[i], reverse=True)
    for i in order[:left]:
        added[i] += 1

    try:
        start_hour, start_minute = [int(x) for x in (workday_start or "08:00").split(":", 1)]
    except Exception:
        start_hour, start_minute = 8, 0
    cursor = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    plan = []
    for task, b, a in zip(today_tasks, base, added):
        minutes = (b + a) * slot
        end = datetime.fromtimestamp(cursor.timestamp() + minutes * 60, LOCAL_TZ)
        plan.append(
            {
                "task": task,
                "minutes": minutes,
                "start": cursor.strftime("%H:%M"),
                "end": end.strftime("%H:%M"),
            }
        )
        cursor = end
    return plan
