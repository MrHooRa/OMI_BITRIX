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


def filesystem_path(path, recursive=False):
    """Use extended Windows paths for IO without changing stored/displayed paths."""
    path = Path(path)
    absolute = os.path.abspath(path)
    if os.name == "nt" and not absolute.startswith("\\\\?\\") and (recursive or len(absolute.encode("utf-16-le")) // 2 >= 240):
        absolute = "\\\\?\\UNC\\" + absolute[2:] if absolute.startswith("\\\\") else "\\\\?\\" + absolute
        return Path(absolute)
    return path


def display_path(path):
    value = str(path)
    if value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    return value[4:] if value.startswith("\\\\?\\") else value


def project_name(project_id, projects):
    for p in projects:
        if str(p["id"]) == str(project_id):
            return p["name"]
    return f"Project {project_id}"


def task_folder(vault_root, project, task, employee_name="Employee", directory_cache=None):
    """Return the task folder under a dedicated employee directory."""
    project_dir = Path(vault_root) / "Bitrix Work" / safe_name(employee_name) / safe_name(project)
    filesystem_path(project_dir).mkdir(parents=True, exist_ok=True)
    cache_key = str(project_dir)
    if directory_cache is None or cache_key not in directory_cache:
        folders = {}
        for child in filesystem_path(project_dir, recursive=True).iterdir():
            if child.is_dir() and " - " in child.name:
                folders.setdefault(child.name.split(" - ", 1)[0], Path(display_path(child)))
        if directory_cache is not None:
            directory_cache[cache_key] = folders
    else:
        folders = directory_cache[cache_key]
    task_id = str(task["id"])
    if task_id not in folders:
        folders[task_id] = project_dir / safe_name(f"{task_id} - {task.get('title', 'Task')}", max_len=64)
    return folders[task_id]


def note_path(folder):
    """Keep one deterministic task note beside the task artifact folders."""
    folder = Path(folder)
    legacy = folder / f"{safe_name(folder.name)}.md"
    if filesystem_path(legacy).exists():
        return legacy
    if not filesystem_path(folder / "Task.md").exists() and filesystem_path(folder / "README.md").exists():
        return folder / "README.md"
    return folder / "Task.md"


def marker(field, content=""):
    return f"<!-- FIELD:{field} -->\n{content}\n<!-- /FIELD:{field} -->"


def artifact_index(folder, language="en"):
    """Build a relative-link index so work files are referenced from the Obsidian note."""
    folder = filesystem_path(folder, recursive=True)
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
    note = filesystem_path(note)
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


def ensure_workspace(vault_root, project, task, language="en", employee_name="Employee", folder=None):
    """Create one unified vault/workspace inside the employee-specific folder."""
    folder = Path(folder) if folder is not None else task_folder(vault_root, project, task, employee_name)
    filesystem_path(folder).mkdir(parents=True, exist_ok=True)
    for name in SUBFOLDERS:
        filesystem_path(folder / name).mkdir(exist_ok=True)

    note = note_path(folder)
    if not filesystem_path(note).exists():
        # Backward-friendly: if a legacy README was manually moved into the new task folder,
        # adopt its contents instead of discarding it.
        legacy = filesystem_path(folder / "README.md")
        if legacy.exists():
            filesystem_path(note).write_text(legacy.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            filesystem_path(note).write_text(template(task, project, folder, language), encoding="utf-8")

    refresh_artifact_index(note, folder, language)
    return {"folder": folder, "note": note, "vault_root": Path(vault_root)}


def read_fields(note):
    text = filesystem_path(note).read_text(encoding="utf-8") if note and filesystem_path(note).exists() else ""
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
    note = filesystem_path(note)
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
    folder = filesystem_path(folder, recursive=True)
    for name in SUBFOLDERS:
        p = folder / name
        counts[name] = sum(1 for x in p.rglob("*") if x.is_file() and not x.name.startswith(".deadline_justification")) if p.exists() else 0
    return counts


def delay_justification_file(folder):
    return filesystem_path(Path(folder) / "05_Evidence" / ".deadline_justification.json")


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
        os.startfile(str(filesystem_path(path)))  # noqa: S606 - intentional local desktop action
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
        return {"moved": False, "reason": "same", "folder": source, "note": note_path(source) if filesystem_path(source).exists() else None}
    if not filesystem_path(source).exists():
        return {"moved": False, "reason": "source_missing", "folder": target, "note": note_path(target) if filesystem_path(target).exists() else None}
    if filesystem_path(target).exists():
        return {"moved": False, "reason": "target_exists", "folder": target, "note": note_path(target)}

    # Retain legacy folder/note names when moving documentation between employees.
    target = target.parent / source.name
    filesystem_path(target.parent).mkdir(parents=True, exist_ok=True)
    shutil.move(str(filesystem_path(source)), str(filesystem_path(target)))
    note = note_path(target)
    if filesystem_path(note).exists():
        text = filesystem_path(note).read_text(encoding="utf-8")
        # Refresh the visible workspace path in YAML/body where it exactly matched
        # the old location. Relative artifact links remain valid after the move.
        text = text.replace(str(source), str(target))
        filesystem_path(note).write_text(text, encoding="utf-8")
        refresh_artifact_index(note, target, language)
    return {"moved": True, "reason": "moved", "folder": target, "note": note if filesystem_path(note).exists() else None}
