# Repository Guidelines

## Project Structure & Module Organization

The application lives in `OMI_Bitrix/`. Read its `README.md` for workflows and root `AGENT.MD` and `PROMPT.txt` for requirements.

- `app.py`: Flask routes, profiles, caching, and synchronization.
- `bitrix.py` and `storage.py`: Bitrix24 client and SQLite configuration.
- `workspace.py` and `team_registry.py`: employee folders and documentation.
- `planner.py`, `similarity.py`, `review.py`, `xlsx_report.py`: planning, search, assessments, and exports.
- `templates/`: Jinja HTML; `static/`: JavaScript/CSS; `i18n.py`: translations.
- `data/`: generated, Git-ignored state. Offline regression tests live in tests/.

## Build, Test, and Development Commands

Use Python 3.10+; run commands from `OMI_Bitrix/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe serve.py
```

The server defaults to `http://127.0.0.1:5055`. Alternatively, `.\start.bat` creates the environment and installs dependencies from the offline wheelhouse when needed. There is no frontend build step.

Run `python -m compileall -q . -x "[.]venv"` for Python syntax validation. If Node is available, `node --check static/app.js` checks JavaScript syntax.

## Coding Style & Naming Conventions

Follow existing formatting: four-space Python indentation, two-space JavaScript/CSS indentation, and surrounding Jinja conventions. Use `snake_case` for Python functions/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants, and `camelCase` for JavaScript functions. No formatter or linter is configured.

Prefer the standard library; Flask, tzdata, and Waitress are declared runtime dependencies; keep additions minimal. Keep frontend assets local and framework-free. Add English/Arabic strings through `i18n.py`; preserve RTL layouts and readable LTR paths.

## Testing Guidelines

Use the existing standard-library `unittest`, use `tests/test_*.py`, and run `python -m unittest discover -s tests`. Mock Bitrix requests and use temporary workspaces.

Manually verify affected workflows, both languages, themes, and narrow screens. Prioritize planner allocation, UNC/Unicode paths, documentation preservation, and completion blocked when its prerequisite comment fails. Distinguish live Bitrix checks from offline validation.

## Commit & Pull Request Guidelines

Use concise imperative subjects, such as `Fix planner allocation`. PRs should describe behavior changes, link relevant issues, list validation and limitations, and include screenshots for UI changes.

## Security & Configuration

Never commit webhook URLs or `data/`. Configuration lives in `cockpit.sqlite3`; historical task snapshots live in `task-history.sqlite3`, scoped to profile and source connection. Sources remain authoritative. Set `WORK_COCKPIT_SECRET` for deployment; configure `HOST` and `PORT` deliberately. Browser profiles are not authentication. Respect per-task permissions and never overwrite existing workspaces.
