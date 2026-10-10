"""Small shared employee-folder registry stored inside the vault.

This is intentionally not a task database.  It only lets different browser
profiles agree on which configured employee folder belongs to which Bitrix user
ID, so supervisors can open the same workspace employees are using.
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.RLock()


def _path(vault_root):
    return Path(vault_root) / ".work-cockpit" / "team.json"


def _load(vault_root):
    path = _path(vault_root)
    if not path.exists():
        return {"version": 1, "employees": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        data.setdefault("version", 1)
        data.setdefault("employees", {})
        return data
    except Exception:
        return {"version": 1, "employees": {}}


def register(vault_root, user_id, employee_name, bitrix_name="", project_ids=None):
    if not vault_root or not user_id or not employee_name:
        return
    with _LOCK:
        data = _load(vault_root)
        uid = str(user_id)
        data["employees"][uid] = {
            "folder_name": str(employee_name).strip(),
            "bitrix_name": str(bitrix_name or employee_name).strip(),
            "projects": sorted({str(x) for x in (project_ids or [])}),
            "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        path = _path(vault_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)


def folder_name(vault_root, user_id, fallback="Employee"):
    with _LOCK:
        data = _load(vault_root)
        item = data.get("employees", {}).get(str(user_id)) or {}
        return item.get("folder_name") or fallback


def all_employees(vault_root):
    with _LOCK:
        return dict(_load(vault_root).get("employees", {}))
