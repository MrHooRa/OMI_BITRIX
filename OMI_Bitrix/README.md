> **GitHub source checkout:** model weights and offline wheels are distributed in [Release v3.10](https://github.com/MrHooRa/OMI_BITRIX/releases/tag/v3.10). See the [repository download guide](../README.md) before using the offline launcher.

# OMI Bitrix + Diwany

A Windows-hosted Flask application for Bitrix task execution, shared workspaces, Diwan requests, and local task analysis. Arabic/English, RTL, light/dark themes, and local assets are included.

## Start on this PC

Double-click **start.bat**, then open [http://127.0.0.1:5055](http://127.0.0.1:5055).

The launcher creates a virtual environment if needed and installs missing packages from the bundled wheelhouse, with public package indexes disabled. The included native wheel targets **CPython 3.14, Windows x64**. Other Python versions need a matching wheelhouse prepared on a connected build machine.

For a prepared environment:

~~~powershell
.\.venv\Scripts\python.exe serve.py
~~~

Use Ctrl+C in the server window to stop it. A server started in the background by an agent must be stopped by its recorded process ID before starting another instance on the same port.

## Personal task calendar

Open **Calendar** in the workspace navigation after configuring your Bitrix connection and selected projects. It shows your assigned tasks, including completed tasks, with project, status and text filters.

- Drag a task onto a day, or open its card and choose a personal plan date. Bitrix deadlines stay unchanged.
- Drag a task into the unscheduled area to remove its personal date. **Use Bitrix deadline** restores its original placement; **Undo last change** reverses your most recent edit.
- Open a card to add a colleague's name, reminder date and note. Names appear on the card; outstanding reminders appear under **Due follow-ups** when due. Mark them done, reopen or remove them from the task.

Dates and reminders belong to the current employee/connection/browser profile and are saved in this browser only. They do not sync across devices or send messages to colleagues. Arabic/RTL, light/dark themes and a mobile agenda are supported. Existing Diwany, analysis and assignment pages remain available.

Calendar checks use fake tasks and never contact Bitrix:

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_calendar.py -v
# Optional browser checks with Playwright installed:
.\.venv\Scripts\python.exe tests\test_calendar.py --export output\calendar-fixtures
$env:CALENDAR_FIXTURES=(Resolve-Path output\calendar-fixtures).Path
$env:BROWSER_CHANNEL='msedge'
node tests\calendar_browser.cjs
~~~

## Automatic assignment alerts (3.10)

New tasks needing an executor now receive a background recommendation in both Bitrix and Diwan. The alert names the top eligible employee, explains the related completed-work evidence and current workload, and links to a historical example. Pending work alone cannot produce a named recommendation. Changed ranking inputs invalidate the result; unchanged polling reuses it. The supervisor reviews and confirms any assignment. See [the Arabic notification guide](docs/AUTOMATIC_NOTIFICATIONS_AR.md) and [validation](docs/testing.md).

## Workflow corrections (3.9)

Both Bitrix assignment interfaces share live permission checks, uncertain-outcome protection, read-back confirmation and conservative workspace transfer. Failed employee-directory refreshes retain the last successful directory and block assignment until verified. Similarity uses one relevance engine across the old and unified views; routine task polling no longer reranks every task. Source-specific history, visible errors, draft retention and candidate-first results improve the existing interface without changing its palette. See [the Arabic correction guide](docs/WORKFLOW_FIXES_AR.md) and [validation](docs/testing.md).

## Configure Diwan

1. Open **Settings → Connections & analysis settings**.
2. Enter the internal HTTPS list, details, and optional delegation URLs.
3. Choose each HTTP method from its dropdown.
4. Select the actual internal task-ID field and assignee field.
5. Save; then select **Connect Diwan**.
6. Enter your own token in the popup and select **Validate & save**.
7. Open **ديواني** and select **Fetch all pages**.

Each browser profile has independent endpoints and a Windows-protected token. Tokens are never returned to HTML or stored in browser localStorage. Changing endpoint configuration removes that profile's saved token and Diwan cache. A failed token replacement preserves the old token.

No Diwan URL or token is shipped with the project. Enter the actual endpoints; placeholder examples are not a working connection.

## Interface structure

The task workspace starts with analysis, assignment decisions, and employee evidence. History, decisions, and eligibility are under **Workspace tools**. Settings are split into focused sections; mobile navigation opens from **Menu**. The existing OMI colors and fonts are preserved. See [the interface guide (Arabic)](docs/UI_STRUCTURE_AR.md) for the Rab6 structure mapping and validation.

## Model efficiency and reviewed training (3.8)

Inference now buckets pairs by token length, caches exact model inputs, reuses snapshot topic labels, and verifies selected evidence windows in long descriptions. FP32 remains the default. The 8-thread CPU setting on the development PC reduced the eight-query engineering run from 18.29 to 11.47 seconds while preserving its top-three evidence IDs; this is a bounded timing check, not production accuracy.

`model_training.py` prepares **unlabelled** review pairs from accessible history and fine-tunes the BGE classification head only after explicit human relevance review and chronological, family-separated splits. Historical assignments are never treated as suitability labels. No organisational fine-tuning or model replacement occurred: the available data currently contains history, not reviewed judgments. Training candidates and reports stay under ignored `data/`, with no automatic deployment.

See [the Arabic efficiency, training and evaluation guide](docs/MODEL_EFFICIENCY_AND_TRAINING_AR.md). Reproduce local timing with `tools/benchmark_models.py`; use `TASK_TORCH_THREADS` to measure the target machine. `TASK_RERANKER_PRECISION=int8` is experimental and changed some evidence ordering in the fixture, so it is not the default.

## Automatic topic discovery and local semantic models (3.7)

Task topics are now discovered from accessible task titles/descriptions using local multilingual E5 embeddings, HDBSCAN density clustering, and extracted class TF-IDF phrases. No predefined business-domain list or fixed topic count is used. A local BGE pair model verifies retrieved task subjects. Fewer than six distinct texts or inadequate structure produces no discovered topic; an unknown topic does not block text retrieval.

Arabic and English are compared in one embedding space. Extracted names stay in the source language when no English phrase is available. Tool/action rules and a small explicit bilingual lexical dictionary remain inspectable supporting rules, not automatically learned domains. User domain annotations do not seed clustering. See [the complete Arabic algorithm and model guide](docs/AUTOMATIC_DOMAINS_AR.md).

Completed, dated evidence supports employee recommendations; pending-work proximity stays independent. Account linking is explicit and retains source eligibility and per-task assignment rights. Workload is a soft balancing term with no maximum task-count exclusion. History/topic snapshots rebuild every two hours while the server runs.

Both pinned pretrained models are bundled in `models/` (about 3.43 GB of weights and configuration). Runtime loading is local-only; no cloud inference or model download occurs. The frozen dependencies require Python 3.12+, and the included wheels target **CPython 3.14 Windows x64**. No representative production accuracy or small-memory deployment is certified.

## New features

- Paginated Diwan retrieval, progress/cancellation, local search, lazy details, and XLSX export.
- Explicit delegation with configured recipients, read-back confirmation, and uncertain-outcome protection.
- **مهام** for local Arabic/English similarity, category suggestions, employee recommendations, and historical duration estimates.
- Full accessible Bitrix history ingestion by selected project, independent of the existing 90-day supervisor view.
- Tag-priority rules, business-hour SLA deadlines, working calendars, holidays, and optional employee absence periods.
- Signed profiles, CSRF protection, encrypted Diwan credentials, and per-profile in-memory jobs/caches.
- Existing Bitrix personal tasks, supervision, documentation, comments, planner, and reports remain available.

Analysis is advisory. Similarity is a relevance score. Historical elapsed durations include waiting and are not employee working hours or SLA promises.

## Bitrix and workspaces

Select **Bitrix24 / Settings** from the connection page to configure the webhook, employee name, project/group IDs, and workspace. Existing webhook values are not rendered back into the page; a blank field preserves a saved value.

Shared Folder, Local Folder, Network Share, and Obsidian Vault use the same filesystem layout:

~~~text
Workspace Root/
  Bitrix Work/
    Employee/
      Project/
        ID - Task/
          Task documentation.md
          01_Input/
          02_Workflow/
          03_Queries/
          04_Output/
          05_Evidence/
~~~

The folder browser runs on the server. **Test folder** checks read/write, Arabic filenames, and a long nested path, then removes its temporary files. Test your actual corporate share under the account running the server.

The planner includes unfinished overdue work, due-today work, and future tasks already started. Capacity is configurable in 15-minute increments. An empty eligible queue produces an empty plan. When tasks exceed available slots, some tasks receive zero minutes.

Completion still requires documentation and a successfully posted Bitrix comment before the Complete action. Task reassignment never overwrites an existing destination workspace.

## Offline and multi-user operation

No CDN, external fonts, cloud AI, or runtime package downloads are required. Internal Diwan/Bitrix connectivity is necessary for fetching and mutations.

History and its similarity index stay in memory. They rebuild automatically on startup and refresh every two hours while the server runs. During an outage, previously fetched data may remain visible with its timestamp/error state; it is not guaranteed current. No mutations are queued for later replay.

Profile cookies provide separation, not employee authentication. Use a protected internal host/network and HTTPS for shared deployment. The move from legacy unsigned profile cookies requires existing browsers to reconnect; old database records are preserved.

## Documentation

- [User guide](docs/user-guide.md)
- [Diwan API mapping](docs/diwany-integration.md)
- [Administration and offline deployment](docs/admin-guide.md)
- [Data and analysis](docs/data-and-analysis.md)
- [Testing and evidence](docs/testing.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Release checklist](docs/release-checklist.md)

## Validation

~~~powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q -x ".venv|data" .
node --check static/app.js
node --check static/security.js
node --check static/diwany.js
# Include real local-model tests (outbound TCP blocked in that test class):
$env:RUN_SEMANTIC_INTEGRATION="1"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
~~~

Node is development-only. See the release checklist for measured checks and the live-source, hardware, and manual gates that remain pending.

## Find similar tasks

Open **Tasks & similarity / مهام وتشابه** at `/tasks`. Similar pairs appear automatically after the first history fetch. Use **Find similar** beside any task or enter new task text in the analysis form. Bitrix is selected by default when connected. The page shows indexed counts, last successful refresh, next refresh, and errors. **Refresh selected source now** performs an immediate read-only refresh.

The scheduler fetches all accessible statuses in selected Bitrix projects and unfiltered Diwan history for each connected, signed profile. It runs without an open browser, refreshes every 7,200 seconds, and retries failures after five minutes. Keep the PC and server running. Restart rebuilds the in-memory index immediately; no duplicate task database is stored. Partial/failed refreshes never replace the last successful index. Diwan listing filters do not change the analysis corpus.

Bitrix recommendation candidates include assignees discovered in task history; configured absence/name values take precedence. Suggestions and duration estimates still require sufficient completed history. The local multilingual model supports cross-language retrieval; lexical normalization and explicit translations supply exact-match support. It does not generate translations or task answers.

## Employee recommendations (Bitrix and Diwan)

Open **Tasks, similarity & assignment** at `/tasks`. One workspace contains task analysis, supervised assignment decisions, and history/update monitoring. `/recommendations` redirects to its assignment tab. See [the step-by-step Arabic algorithm guide](docs/ALGORITHM_AR.md) for data sources, cleaning, formulas, limits and Diwan contract mapping.

Task roles come from CREATED_BY and AUDITORS, never project management alone. An owner assigned their own task receives an assignment prompt until explicitly claiming personal execution. An assignee without task supervision cannot use assignment actions, even when broad Bitrix permissions allow editing. Live permissions and expected-assignee checks remain mandatory.

There is no maximum task count for recommendation eligibility. Workload is a soft balancing term: `1 / (1 + priority-weighted open execution tasks)`. Legacy employee capacity limits are ignored. Pending supervisor assignments and tasks awaiting review do not count as execution workload. Eligibility, project/category and absence restrictions remain in effect.

Text matching shares one local index between similarity and recommendations. Ticket identifiers, URLs and synthetic boilerplate do not establish relevance. Identical content is grouped for display with all original IDs preserved. Completed evidence, open-work exposure and manual choices remain distinct. Ranking combines pretrained local semantic models with inspectable scoring rules; it is not calibrated as a probability of success or trained on organisational outcomes.


## Recommendation release 3.1

- Unified source selector, assignment queue search/sort, task brief, candidate selection, read-only evidence dialog and decision log. Colors, typography and local assets remain unchanged.
- Shared portal/task self-execution decisions and uncertain-write protection across browser profiles. Fresh source roles and permissions gate mutations, including legacy assignment routes.
- Diwan recommendations require verified supervisor/executor/current-user field mappings and a personal token. Configure these in Connections; test the real source contract before enabling delegation.
- Optional Bitrix field mapping preserves outcome metadata without inventing performance scores. Eligibility settings remain per profile.
- [Algorithm guide](docs/ALGORITHM_AR.md), [evaluation guide](docs/ranking-evaluation.md), [delivery status](docs/DELIVERY_STATUS_AR.md) and [validation evidence](docs/testing.md).


## Evidence discovery (3.2)

In **Tasks, similarity & assignment**, use **Employee evidence** to search observed topics and inspect each employee's completed-work profile. Task analysis shows typed labels, coverage gaps, expandable evidence and optional complementary experience. Existing colors, local assets and task-level assignment permissions are preserved.

See [Rab6 adoption review](docs/RAB6_ADOPTION_AR.md) and the updated [Arabic algorithm guide](docs/ALGORITHM_AR.md). This is local rule-based classification plus lexical retrieval, not a downloaded semantic model or a performance rating.


## Analysis and settings clarity (3.3)

Analysis now separates subject, tools, work type and deliverable before showing candidates. Shared field-weighted sublinear TF-IDF rejects tool-only overlap when a known subject is requested, supports explicit Arabic/English aliases, and protects IDF statistics from repeated term patterns. Recurring completed text is disclosed as such; its source IDs remain distinct. This remains an explainable offline statistical baseline, not a trained suitability model.

Settings navigation follows the same groups across Connections and Workspace, supports section links and browser Back, and preserves unsaved fields during local section changes. Current identity and assignment permissions remain in place. See [Arabic improvement report](docs/INTELLIGENCE_IMPROVEMENTS_AR.md), [formulas and sources](docs/ALGORITHM_AR.md) and [validation](docs/testing.md).


## Separate pending-work comparison (3.4)

Task analysis now offers **Related pending work** alongside completed-evidence candidates and related tasks. This independent view ranks eligible employees by open-work text proximity, then explicit title-period/content variety to break ties. It shows source status and creation dates; pending assignments never become completed experience. The same employee can appear in both contexts. Exact copies cannot strengthen proximity. See [Arabic case review](docs/RANKING_REVIEW_AR.md) and [formulas](docs/ALGORITHM_AR.md#19-قرب-الأعمال-المعلقة--مستقل-عن-ترشيح-الإسناد).
