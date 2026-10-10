import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


SUBFOLDERS = ["01_Input", "02_Workflow", "03_Queries", "04_Output", "05_Evidence"]
FIELDS = ["objective", "work_done", "queries", "validation", "result", "next_step"]
ARTIFACT_INDEX_START = "<!-- ARTIFACT_INDEX -->"
ARTIFACT_INDEX_END = "<!-- /ARTIFACT_INDEX -->"


def safe_name(value, max_len=110):
    value = re.sub(r"[<>:\\|?*\"/]", "-", str(value or ""))
    value = re.sub(r"\s+", " ", value).strip().rstrip(".")
    return (value or "Untitled")[:max_len]


def project_name(project_id, projects):
    for p in projects:
        if str(p["id"]) == str(project_id):
            return p["name"]
    return f"Project {project_id}"


def task_folder(vault_root, project, task, employee_name="Employee"):
    """Return the task folder under a dedicated employee directory."""
    project_dir = Path(vault_root) / "Bitrix Work" / safe_name(employee_name) / safe_name(project)
    project_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{task['id']} - "
    for child in project_dir.iterdir():
        if child.is_dir() and child.name.startswith(prefix):
            return child
    return project_dir / safe_name(f"{task['id']} - {task.get('title', 'Task')}")


def note_path(folder):
    """Keep one deterministic task note beside the task artifact folders."""
    folder = Path(folder)
    return folder / f"{safe_name(folder.name)}.md"


def marker(field, content=""):
    return f"<!-- FIELD:{field} -->\n{content}\n<!-- /FIELD:{field} -->"


def artifact_index(folder, language="en"):
    """Build a relative-link index so work files are referenced from the Obsidian note."""
    folder = Path(folder)
    ar = str(language).lower().startswith("ar")
    lines = [ARTIFACT_INDEX_START]
    found_any = False
    for subfolder in SUBFOLDERS:
        base = folder / subfolder
        files = []
        if base.exists():
            files = sorted(
                p for p in base.rglob("*")
                if p.is_file() and not p.name.startswith(".deadline_justification")
            )
        lines.append(f"### {subfolder}")
        if not files:
            lines.append("_لا توجد ملفات حتى الآن._" if ar else "_No files yet._")
        else:
            found_any = True
            for file_path in files:
                rel = file_path.relative_to(folder).as_posix()
                href = quote(rel, safe="/._-~")
                lines.append(f"- [{file_path.name}]({href}) — `{rel}`")
        lines.append("")
    if not found_any:
        lines.append("> أضف ملفاتك إلى المجلدات أعلاه. يقوم OMI Bitrix بتحديث هذه القائمة عند المزامنة أو الفتح أو الحفظ." if ar else "> Add files to the folders above. OMI Bitrix refreshes this index during sync/open/save.")
        lines.append("")
    lines.append(ARTIFACT_INDEX_END)
    return "\n".join(lines)


def template(task, project, folder, language="en"):
    deadline = task.get("deadline") or ("بدون موعد نهائي" if str(language).lower().startswith("ar") else "No deadline")
    description = strip_bitrix(task.get("description") or "")
    ar = str(language).lower().startswith("ar")
    if ar:
        return f'''---
bitrix_task_id: "{task.get('id')}"
project: "{yaml_escape(project)}"
status: "{task.get('status', '')}"
deadline: "{yaml_escape(deadline)}"
workspace: "{yaml_escape(str(folder))}"
tags: [bitrix, work]
---

# {task.get('title', 'مهمة بدون عنوان')}

> **المشروع:** {project}  
> **مهمة Bitrix:** #{task.get('id')}  
> **الموعد النهائي:** {deadline}  
> **مجلد المهمة داخل المستودع:** `{folder}`

## ملخص المهمة
{description or '_لا يوجد وصف للمهمة في Bitrix24._'}

## الهدف
{marker('objective', '> اكتب النتيجة المطلوب الوصول إليها من هذه المهمة.')}

## ما تم إنجازه
{marker('work_done', '> وثّق الخطوات الأساسية، مثل Alteryx أو Power BI أو Python أو أي معالجة وتحليل تم تنفيذه.')}

## الاستعلامات ومنطق العمل
{marker('queries', '> سجّل ملفات SQL المهمة والجداول والربط والفلاتر والحسابات وقواعد العمل المستخدمة.')}

## التحقق والمطابقة
{marker('validation', '> وثّق المطابقات، أعداد السجلات، اختبارات التحقق، الحالات الخاصة، أو تأكيد أصحاب المصلحة.')}

## النتيجة والمخرجات
{marker('result', '> اكتب ما تم تسليمه وأشر إلى الملفات النهائية داخل 04_Output.')}

## الخطوة التالية / التسليم
{marker('next_step', '> اختياري: متابعة مطلوبة، اعتماد، عائق، أو ملاحظة للتسليم.')}

## خريطة مساحة العمل
- `01_Input/` — الملفات المصدرية، الاستخراجات، والمتطلبات
- `02_Workflow/` — Alteryx وPython وملفات سير العمل
- `03_Queries/` — SQL وملاحظات الاستعلامات
- `04_Output/` — المخرجات النهائية
- `05_Evidence/` — لقطات الشاشة، المطابقات، والاعتمادات

## ملفات العمل المرتبطة
{artifact_index(folder, language)}

## سجل النشاط
- {datetime.now().strftime('%Y-%m-%d %H:%M')} — تم إنشاء مساحة العمل وملف Obsidian بواسطة OMI Bitrix.
'''
    return f'''---
bitrix_task_id: "{task.get('id')}"
project: "{yaml_escape(project)}"
status: "{task.get('status', '')}"
deadline: "{yaml_escape(deadline)}"
workspace: "{yaml_escape(str(folder))}"
tags: [bitrix, work]
---

# {task.get('title', 'Untitled task')}

> **Project:** {project}  
> **Bitrix task:** #{task.get('id')}  
> **Deadline:** {deadline}  
> **Workspace / vault folder:** `{folder}`

## Task brief
{description or '_No description was provided in Bitrix24._'}

## Objective
{marker('objective', '> Replace this line with the outcome you need to deliver.')}

## Work performed
{marker('work_done', '> Record the main steps, Alteryx workflows, Power BI work, transformations, or analysis performed.')}

## Queries / logic
{marker('queries', '> List important SQL files, tables, joins, filters, calculations, or business rules.')}

## Validation
{marker('validation', '> Document reconciliations, row counts, checks, stakeholder confirmation, or edge cases.')}

## Result / deliverables
{marker('result', '> State what was delivered and point to files in 04_Output.')}

## Next step / handover
{marker('next_step', '> Optional: follow-up, dependency, blocker, or handover note.')}

## Workspace map
- `01_Input/` — source files, extracts, requirements
- `02_Workflow/` — Alteryx workflows, Python, process assets
- `03_Queries/` — SQL and query notes
- `04_Output/` — final deliverables
- `05_Evidence/` — screenshots, reconciliations, approvals

## Referenced work files
{artifact_index(folder, language)}

## Activity log
- {datetime.now().strftime('%Y-%m-%d %H:%M')} — unified Obsidian/workspace created by OMI Bitrix.
'''


def yaml_escape(value):
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def strip_bitrix(text):
    text = re.sub(r"\[/?[A-Z]+(?:=[^\]]+)?\]", "", str(text), flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def refresh_artifact_index(note, folder, language="en"):
    note = Path(note)
    if not note.exists():
        return
    text = note.read_text(encoding="utf-8")
    replacement = artifact_index(folder, language)
    pattern = rf"{re.escape(ARTIFACT_INDEX_START)}.*?{re.escape(ARTIFACT_INDEX_END)}"
    if re.search(pattern, text, flags=re.S):
        text = re.sub(pattern, lambda _m: replacement, text, flags=re.S)
    else:
        heading = "ملفات العمل المرتبطة" if str(language).lower().startswith("ar") else "Referenced work files"
        text += f"\n\n## {heading}\n{replacement}\n"
    note.write_text(text, encoding="utf-8")


def ensure_workspace(vault_root, project, task, language="en", employee_name="Employee"):
    """Create one unified vault/workspace inside the employee-specific folder."""
    folder = task_folder(vault_root, project, task, employee_name)
    folder.mkdir(parents=True, exist_ok=True)
    for name in SUBFOLDERS:
        (folder / name).mkdir(exist_ok=True)

    note = note_path(folder)
    if not note.exists():
        # Backward-friendly: if a legacy README was manually moved into the new task folder,
        # adopt its contents instead of discarding it.
        legacy = folder / "README.md"
        if legacy.exists():
            note.write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            note.write_text(template(task, project, folder, language), encoding="utf-8")

    refresh_artifact_index(note, folder, language)
    return {"folder": folder, "note": note, "vault_root": Path(vault_root)}


def read_fields(note):
    text = Path(note).read_text(encoding="utf-8") if note and Path(note).exists() else ""
    values = {}
    for field in FIELDS:
        m = re.search(
            rf"<!-- FIELD:{re.escape(field)} -->\s*(.*?)\s*<!-- /FIELD:{re.escape(field)} -->",
            text,
            flags=re.S,
        )
        values[field] = m.group(1).strip() if m else ""
    return values


def save_fields(note, values, folder=None, language="en"):
    note = Path(note)
    text = note.read_text(encoding="utf-8")
    for field in FIELDS:
        replacement = marker(field, values.get(field, "").strip())
        pattern = rf"<!-- FIELD:{re.escape(field)} -->.*?<!-- /FIELD:{re.escape(field)} -->"
        if re.search(pattern, text, flags=re.S):
            text = re.sub(pattern, lambda _m, r=replacement: r, text, flags=re.S)
    note.write_text(text, encoding="utf-8")
    if folder:
        refresh_artifact_index(note, folder, language)


def readiness(values):
    required = ["objective", "work_done", "validation", "result"]
    filled = 0
    for key in required:
        value = (values.get(key) or "").strip()
        if value and not value.startswith(("> Replace", "> Record", "> Document", "> State", "> اكتب", "> وثّق", "> سجّل")):
            filled += 1
    return round((filled / len(required)) * 100)


def count_artifacts(folder):
    counts = {}
    folder = Path(folder)
    for name in SUBFOLDERS:
        p = folder / name
        counts[name] = sum(1 for x in p.rglob("*") if x.is_file() and not x.name.startswith(".deadline_justification")) if p.exists() else 0
    return counts


def delay_justification_file(folder):
    return Path(folder) / "05_Evidence" / ".deadline_justification.json"


def read_delay_justification(folder, deadline=None):
    """Return the posted justification for the current deadline, if any."""
    path = delay_justification_file(folder)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if deadline is not None and str(data.get("deadline") or "") != str(deadline or ""):
        return None
    return data


def save_delay_justification(folder, task, justification):
    """Remember only that a justification was successfully posted to Bitrix."""
    path = delay_justification_file(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "task_id": str(task.get("id") or ""),
        "deadline": str(task.get("deadline") or ""),
        "justification": str(justification or "").strip(),
        "posted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def open_path(path):
    path = str(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: S606 - intentional local desktop action
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def obsidian_uri(vault_path, note):
    vault_path = Path(vault_path)
    vault = vault_path.name
    rel = Path(note).relative_to(vault_path).with_suffix("")
    return f"obsidian://open?vault={quote(vault)}&file={quote(rel.as_posix())}"


def move_workspace(vault_root, project, task, old_employee, new_employee, language="en"):
    """Move an existing task workspace to a newly assigned employee folder.

    The move is conservative: it only happens when the source exists and the
    target does not.  If both exist, no files are merged automatically.
    """
    import shutil

    source = task_folder(vault_root, project, task, old_employee)
    target = task_folder(vault_root, project, task, new_employee)
    if os.path.normcase(os.path.abspath(str(source))) == os.path.normcase(os.path.abspath(str(target))):
        return {"moved": False, "reason": "same", "folder": source, "note": note_path(source) if source.exists() else None}
    if not source.exists():
        return {"moved": False, "reason": "source_missing", "folder": target, "note": note_path(target) if target.exists() else None}
    if target.exists():
        return {"moved": False, "reason": "target_exists", "folder": target, "note": note_path(target)}

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    note = note_path(target)
    if note.exists():
        text = note.read_text(encoding="utf-8")
        # Refresh the visible workspace path in YAML/body where it exactly matched
        # the old location. Relative artifact links remain valid after the move.
        text = text.replace(str(source), str(target))
        note.write_text(text, encoding="utf-8")
        refresh_artifact_index(note, target, language)
    return {"moved": True, "reason": "moved", "folder": target, "note": note if note.exists() else None}
