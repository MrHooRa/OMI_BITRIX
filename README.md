# OMI Bitrix + Diwany — 3.10

Internal task analysis, similarity and supervised employee assignment with local multilingual models. Arabic/English, RTL and the existing OMI interface are included.

## Personal calendar in source

The current source adds a personal Bitrix task calendar alongside Diwany and task analysis. Drag tasks to plan days without changing Bitrix deadlines, and keep private colleague follow-up reminders with names visible on task cards. The published v3.10 release remains the original snapshot; use the current source for the calendar. See [calendar usage and checks](OMI_Bitrix/README.md#personal-task-calendar).

## Download the complete runnable version

Use [Release v3.10](https://github.com/MrHooRa/OMI_BITRIX/releases/tag/v3.10) for the clean **Windows x64 / CPython 3.14** distribution, including both pinned models and offline Python wheels.

1. Download both `OMI_Bitrix_3.10_Clean_2026-10-10.zip.001` and `.zip.002`, plus `Join-OMI-Release.ps1`, into one folder.
2. From that folder, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\Join-OMI-Release.ps1`. It verifies the parts, reconstructs the ZIP and checks its SHA-256.
3. Extract the resulting ZIP. Open `OMI_Bitrix` and run `start.bat` with CPython 3.14 x64 installed. Open http://127.0.0.1:5055.
4. Configure your own internal Bitrix/Diwan connections and Diwan token. No employee records, tasks, credentials or local configuration are included.

**Git clone / GitHub Source code ZIP contains source and model metadata only.** Model weights and offline wheels are supplied through the complete release; they are not Git objects. The application itself loads models locally and does not download them at runtime.

## Source development

```powershell
cd OMI_Bitrix
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe tools\prepare_models.py --download
.\.venv\Scripts\python.exe serve.py
```

These explicit dependency/model preparation commands require public internet on a build machine. To prepare offline, copy `models/` and `wheelhouse/` from the complete release into the source checkout instead. Runtime analysis and assets remain local; fetching and assignment require access to the configured internal systems.

## Validation and documentation

```powershell
cd OMI_Bitrix
.\.venv\Scripts\python.exe -m unittest discover -s tests
# With both local models available:
$env:RUN_SEMANTIC_INTEGRATION='1'
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Read [application workflows](OMI_Bitrix/README.md), [Arabic algorithm and formulas](OMI_Bitrix/docs/ALGORITHM_AR.md), [automatic domains and models](OMI_Bitrix/docs/AUTOMATIC_DOMAINS_AR.md), [deployment](OMI_Bitrix/docs/admin-guide.md) and [validation limits](OMI_Bitrix/docs/testing.md).

`CHECK_OMI_SERVER.bat` is a read-only Windows diagnostic: it compares current source files and identifies the server listening on ports 5055/5056. It does not stop processes or change settings.

The source preserves the 3.10 workflows and adds the personal task calendar. Personal examples in shared documentation are anonymised. Live Diwan acceptance, independently reviewed ranking accuracy and target-machine capacity measurements remain deployment checks.
