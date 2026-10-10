"""Elapsed-duration evidence and separately configured business-hour SLA."""
from datetime import datetime, timedelta
from statistics import median
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Riyadh")


def parse(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result.replace(tzinfo=TZ) if result.tzinfo is None else result.astimezone(TZ)
    except (ValueError, TypeError):
        return None


def estimate(records, minimum=3):
    durations = []
    for record in records:
        start, end = parse(record.get("created_at")), parse(record.get("completed_at"))
        if record.get("completed") and start and end and end > start:
            durations.append((end - start).total_seconds() / 3600)
    durations.sort()
    if len(durations) < minimum:
        return {"available": False, "samples": len(durations), "basis": "elapsed_hours"}
    return {"available": True, "samples": len(durations), "basis": "elapsed_hours",
            "median": round(median(durations), 1),
            "low": round(durations[int((len(durations) - 1) * .1)], 1),
            "high": round(durations[int((len(durations) - 1) * .9)], 1)}


def business_deadline(start, hours, settings):
    if not start or not 0 < hours <= 2000:
        return None
    days = set(settings.get("working_days", [6, 0, 1, 2, 3]))
    holidays = set(settings.get("holidays", []))
    begin, end = settings.get("start_hour", 8), settings.get("end_hour", 16)
    if not days or not all(isinstance(d, int) and 0 <= d <= 6 for d in days) or not 0 <= begin < end <= 24:
        raise ValueError("Invalid work calendar")
    cursor = start.astimezone(TZ)
    remaining = hours * 3600
    for _ in range(3660):
        midnight = cursor.replace(hour=0, minute=0, second=0, microsecond=0)
        opening, closing = midnight + timedelta(hours=begin), midnight + timedelta(hours=end)
        if cursor.weekday() not in days or cursor.date().isoformat() in holidays or cursor >= closing:
            cursor = midnight + timedelta(days=1)
            continue
        cursor = max(cursor, opening)
        available = (closing - cursor).total_seconds()
        if remaining <= available:
            return cursor + timedelta(seconds=remaining)
        remaining -= available
        cursor = midnight + timedelta(days=1)
    raise ValueError("Calendar horizon exceeded")


def evaluate(records):
    """Chronological event sweep; training never includes future completions."""
    from bisect import insort
    from collections import defaultdict
    events = []
    for index, record in enumerate(records):
        created, closed = parse(record.get("created_at")), parse(record.get("completed_at"))
        if record.get("completed") and created and closed and closed > created:
            key = (record["source"], record.get("category", ""))
            duration = (closed - created).total_seconds() / 3600
            events.extend([(created, 0, index, key, duration), (closed, 1, index, key, duration)])
    baselines, predictions = defaultdict(list), {}
    errors, covered = [], 0
    for timestamp, kind, index, key, duration in sorted(events):
        values = baselines[key]
        if kind == 0:
            if len(values) >= 3:
                predictions[index] = (median(values), values[int((len(values)-1)*.1)], values[int((len(values)-1)*.9)])
        else:
            if index in predictions:
                typical, low, high = predictions.pop(index)
                errors.append(abs(duration-typical))
                covered += low <= duration <= high
            insort(values, duration)
    return {"samples": len(errors), "mae_hours": round(sum(errors)/len(errors), 1) if errors else None,
            "interval_coverage": round(covered/len(errors), 2) if errors else None}
