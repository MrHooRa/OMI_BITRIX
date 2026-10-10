# OMI Bitrix and Diwany — Implementation Plan

**Document date:** 3 October 2026  
**Status:** Implementation authorized by the owner on 3 October 2026. See OMI_Bitrix/docs/release-checklist.md for delivered behavior and pending external acceptance.  
**Audience:** Implementers, reviewers, and the project owner.  
**Primary reference:** `current_strcuture.py`, the supplied OMI Bitrix brief, and the supplied feature diagram.

## 1. Purpose and scope

Extend OMI Bitrix with two primary pages:

1. **ديواني — Diwany:** retrieve an employee's accessible requests, inspect task details, and delegate an eligible task to an eligible employee.
2. **مهام — Tasks:** inspect related historical work, suggest categories and responsible employees, examine workload, apply local tag-priority rules, and estimate completion times.

Preserve the original OMI Bitrix workflows: personal tasks, supervision, planning, documentation, shared folders, comments, approvals, reports, bilingual presentation, and diagnostics.

The application must remain practical for a Windows PC or a protected corporate Windows server. Keep dependencies small and responsibilities clear.

### 1.1 Confirmed owner decisions

- Internal Diwan and Bitrix connections are allowed.
- Assets and analysis must remain local, without public-internet dependencies.
- Each employee has an individual Diwan token.
- A popup must collect and manage that token for the current employee's browser profile.
- Follow the request structure and field mappings in `current_strcuture.py`.
- The owner subsequently authorized implementation and requested per-profile URL fields and HTTP-method dropdowns in Settings.

### 1.2 Working assumptions and unresolved decisions

| Decision | Proposed approach | Implementation consequence |
|---|---|---|
| Extend or rebuild | Extend the existing app. | Implemented following the owner's approval of this plan. |
| Historical persistence | Process authorized task history in memory initially. | Persistent task snapshots or task-level indexes require an explicit policy decision. |
| Credential persistence | Save protected tokens server-side per profile. | Confirm the Windows account and backup/recovery process used by deployment. |
| Meaning of مهام | A task-analysis workspace alongside the existing personal-task dashboard. | Avoid duplicating the current execution queue. |
| Diwan-to-Bitrix relationship | Keep sources distinct, with optional explicit links. | Do not automatically create Bitrix tasks or synchronize mutations between systems. |
| Availability | Manual absence periods or an approved local import. | An HR integration is optional future work. |
| SLA policy | Owner-configured targets and working calendar. | Historical estimates cannot define contractual SLA commitments automatically. |

For a clean rebuild, retain the same functional milestones in a separate project directory, use the existing application only as behavioral evidence, and do not copy its implementation. Define migration and cutover before replacing the running app.

## 2. Evidence and current implementation gaps

These observations come from the repository and script already reviewed during planning. They are not a new production acceptance audit.

| Area | Observed state | Required work |
|---|---|---|
| Diwan listing | The script requests page 1 with page size 50. | Implement verified all-page retrieval. |
| Diwan details | Uses a details URL with an internal task identifier. | Confirm identifier fields and normalize responses. |
| Delegation | A sample payload exists; no delegation function or endpoint is supplied. | Obtain the contract before implementing a real mutation. |
| API configuration | Token and endpoint values are placeholders in the script. | Replace with validated server configuration and per-profile token handling. |
| Record extraction | Calls dictionary methods before handling top-level lists. | Handle actual response types, nulls, and malformed responses safely. |
| Form fields | Labels become `FORM_...` keys. | Preserve Arabic fields and prevent duplicate labels from overwriting values. |
| Script execution | Requests run at module import time. | Extract reusable functions with no import-time network calls. |
| Export | The final column selection omits internal IDs and several enriched fields. | Preserve identifiers, useful details, and explicit export choices. |
| Bitrix history | Assigned tasks are active; supervised completed history defaults to 90 days. | Add an independent historical ingestion path. |
| Similarity | Local Arabic/English normalization and pairwise comparisons exist. | Add candidate indexing, classification, and employee recommendations. |
| Setup | Existing setup requires Bitrix configuration and a workspace. | Allow Diwany-only setup and independent connector readiness. |
| Planner | Prior-day overdue tasks are excluded unless already started. | Reconcile eligibility with the original brief. |
| Workspace | Existing configuration is Obsidian-oriented; movement uses `.resolve()`. | Support generic folders and audit UNC/long-path behavior. |
| Deployment | Windows previously required an additional timezone-data installation. | Declare and package runtime dependencies reproducibly. |

The previously successful local startup is not proof of live source integration, historical completeness, delegation, or multi-user production readiness.

## 3. Operating model and boundaries

### 3.1 Network and offline behavior

The browser talks to the local Flask application. The server communicates only with the configured internal Diwan and Bitrix services needed by the requested workflow.

- No CDN assets, external fonts, telemetry, cloud AI, or runtime package downloads.
- Keep HTML, CSS, JavaScript, translations, and analysis logic local.
- Use server-side source clients; never expose bearer tokens to frontend API calls.
- Validate configured endpoint schemes and hosts. Do not let a submitted token choose an arbitrary request destination.
- Preserve TLS verification and document corporate certificate configuration where needed.
- Do not follow redirects to another host while forwarding credentials.

When an internal service is unavailable:

- Keep the application and local navigation usable.
- Show the last successful synchronization time and a clear stale/partial-data state.
- Permit analysis of data already held in the authorized session cache.
- Disable operations that require source confirmation.
- On a cold start without source access or an approved historical input, show an empty state rather than inventing data.
- Do not queue delegation or completion for silent execution later.

### 3.2 Storage boundaries

| Information | Proposed location |
|---|---|
| Profile preferences, connection settings, priority rules, calendar settings | SQLite configuration/application state |
| Protected credentials | Server-side profile-scoped credential storage |
| Current source tasks and historical task records | Profile-scoped memory in the first release |
| Search indexes and analysis features | Rebuildable memory structures in the first release |
| Task documentation and existing workflow markers | Authorized employee workspace folders |
| Minimal action audit metadata | Protected local audit files with rotation and retention |
| User-requested exports | Explicit download/output destination |

Diwan and Bitrix remain systems of record. Moving complete task copies into JSON does not avoid the restriction on duplicate task storage. Persisting raw records, task-level feature indexes, or historical snapshots is a separate decision.

Do not store raw tokens, complete API responses, or unnecessary personal/task content in audit logs.

## 4. Diwan API contract and normalization

### 4.1 Required sanitized fixtures

Obtain these without including real credentials:

- First, middle, and final list-page responses.
- Empty results and any total-count, next-page, or page-count metadata.
- A detail response with form controls and previous actions.
- Missing/null fields and duplicate form-control labels.
- Pending, completed, returned, canceled, and other relevant status values.
- Eligible-recipient records and permission failures.
- Delegation endpoint, HTTP method, request body, and success/error responses.
- Token rejection, expired-token, rate-limit, and service-unavailable responses.
- Historical records showing reassignment, completion, and reopen behavior.

Do not infer endpoint URLs or numeric status codes from display text.

### 4.2 Script mappings to preserve

| Script input | Application use |
|---|---|
| `Authorization: Bearer ...` | Credential supplied by the current profile |
| `pageNumber`, `pageSize` | Source pagination |
| `filter`, `orderByValue` | Supported source-side filtering and ordering |
| `result.data.viewForm.controls` | Structured request form fields |
| `result.data.previousActions` | Structured workflow history and display summary |
| `serviceNameEn` / `serviceName` | Service display name |
| `createdDate`, `requestCompletedDate` | Source timestamps with explicit semantics |
| `taskId` / verified internal ID | Details and delegation identity |
| `requestId` | Business request/ticket number |

Keep the Arabic fields represented by the script, including request type, agency, sector, department, date, work region, region description, request reason, and request details. Preserve source field IDs and original labels alongside normalized display labels.

### 4.3 Canonical identity

Use a small normalized record shared by display and analysis:

```text
source, source_task_id, request_id
title, description, service, category
source_status, normalized_status
assignee_source_id, assignee_email
project_or_group_id, tags, source_priority
created_at, started_at, completed_at, deadline
form_fields, workflow_actions
fetched_at, completeness, source_link
```

Optional values must remain unknown when absent.

- `source_task_id` and `request_id` are different concepts.
- Verify the script's `id → taskId → bpmTaskId` fallback against actual fixtures.
- Names and ticket numbers are not safe identity keys.
- Use source-qualified keys such as `diwan:5810314` and `bitrix:5810314`.
- Map employees across systems using verified source IDs or email, not fuzzy name matching.
- A linked task may represent one unit of work; only verified links justify deduplication.

### 4.4 Client interface

```python
list_tasks_page(filters, page_number, page_size)
iter_all_tasks(filters)
get_task_details(task_id)
delegate_task(task_id, request_id, employee)
```

Keep timeouts, JSON parsing, error classification, and credential redaction centralized. Prefer the existing standard-library HTTP approach; do not add pandas or requests solely because the reference script uses them.

Retry read-only requests only when safe and bounded. A POST used for listing may be read-only, but delegation is a mutation and needs different retry rules.

## 5. Per-employee Diwan token popup

This is a required feature, not an optional settings enhancement.

### 5.1 Entry points

Open the modal:

1. On first access to ديواني when the profile has no token.
2. When the employee selects **Connect Diwan** or **Replace Token**.
3. After a source response specifically confirms invalid or expired authentication.

Do not reopen it for every timeout, server error, or task-level permission denial.

### 5.2 Modal content

- Title: **ربط حساب ديواني / Connect Diwan**.
- Brief text explaining that the employee should use their own token.
- Masked token input with accessible Show/Hide.
- **Validate & Save**, **Cancel**, and a help explanation.
- Pending, valid, invalid, and temporarily unavailable states.
- Keyboard focus management, Escape/cancel behavior, and screen-reader labels.
- Natural Arabic text and an LTR token field.

Use a verified harmless identity or listing request for token validation. Do not invent a validation endpoint.

### 5.3 Save and replacement flow

```text
Open modal
→ Enter token
→ Submit to local server with CSRF protection
→ Validate with configured Diwan endpoint
→ Save only after successful validation
→ Rotate profile credential generation
→ Invalidate old credential-scoped data
→ Refresh the Diwan page
```

If replacement validation fails, retain the previous credential until the user explicitly removes it. Never redisplay the saved token.

Settings must show connection status and provide **Replace Token** and **Remove Token**. Removing a token clears associated caches and cancels that profile's Diwan jobs. Keep Bitrix configuration independent.

### 5.4 Isolation and protection

- No global/shared Diwan token.
- Resolve the active profile server-side; do not accept a client-selected profile ID in operation payloads.
- Partition caches and jobs by profile, source, and credential generation.
- Prevent late results from an old job from repopulating a cache after token replacement/removal.
- Store secrets encrypted/protected at rest using an appropriate Windows mechanism, such as DPAPI under the service account, with restrictive file permissions.
- Never place tokens in URLs, localStorage, HTML attributes, logs, exports, or generated notes.
- Protect credential and mutation routes against CSRF.
- Sign or otherwise protect profile-cookie integrity; cookies still do not constitute employee authentication.
- Preserve the requirement for protected internal hosting without introducing another application username/password system.

Document that credentials protected under a Windows account may require re-entry when moving to a different account or machine.

**Acceptance:** two browsers with different tokens cannot read, replace, use, or invalidate each other's credentials or cached source data.

## 6. ديواني page and delegation

### 6.1 List and details

Use dense rows with request number, internal task ID, service/type, agency/sector/department, status, creation date, and assignee where available.

Provide:

- Source-supported filters and local search over fetched data.
- Explicit refresh with page/record progress and cancellation.
- Last-successful-sync and completeness indicators.
- Lazy detail drawers containing form fields and workflow history.
- Clear distinction between a failed detail fetch and an empty detail record.
- Export using the existing XLSX facility or a small isolated extension.
- Safe handling of spreadsheet values beginning with formula characters.

Fetch all pages in a background job, not in the initial page-render request. Use verified pagination metadata; guard against repeated pages, duplicated records, and unbounded loops. A safety limit must produce a partial-result status, never a false complete status.

Where supported, use stable ordering with a unique tie-breaker or a snapshot boundary. If the source cannot provide a consistent snapshot, document reconciliation behavior and expose concurrent-change limitations.

### 6.2 Delegation workflow

```text
Choose task
→ Fetch current details
→ Obtain eligible recipients
→ Select recipient
→ Review task ID, ticket, and recipient
→ Confirm
→ Validate current state/permissions
→ Submit source mutation
→ Re-fetch affected task
→ Show confirmed outcome
```

Map the sample payload only after verifying its fields:

```json
{
  "taskId": "<verified internal task ID>",
  "requestId": "<business request number>",
  "assignTo": "<verified recipient identifier>",
  "assignToNameEn": "<verified English name>",
  "assignToNameAr": "<verified Arabic name>"
}
```

The diagram mentions employee email, but the sample does not prove that `assignTo` accepts email. Confirm this before implementation.

- Validate permissions and eligible recipients server-side.
- Prevent duplicate submissions for the same profile/task/action.
- Use a source idempotency mechanism if supported.
- After a timeout with uncertain outcome, reconcile before retrying.
- Refresh only affected task and workload data where practical.
- Log minimal outcome metadata with no token or full payload.
- Do not automatically create, delegate, or update a corresponding Bitrix task.
- Keep source delegation success separate from any later local filesystem failure.

**Acceptance:** failures are actionable, ambiguous outcomes are visible, and task ownership is never reported changed without source evidence.

## 7. Historical ingestion and مهام

### 7.1 Historical coverage

Create a separate job for all accessible history within selected source/project boundaries. Pending Diwan listings alone cannot supply a completed-work training/evidence set.

The job must:

- Page through accessible records with progress, cancellation, and bounded resource use.
- Record coverage dates, source scope, counts, failures, and inaccessible subsets.
- Resume interrupted work where the selected storage policy permits.
- Support incremental changed-record refresh when the API provides suitable fields.
- Preserve the last successful complete state when a later synchronization fails.
- Avoid claiming team-wide completeness when the token only exposes part of the team.
- Treat access changes and credential replacement as cache invalidation events.

Bitrix API versions use different response and pagination contracts. Pin the adapter to the deployed portal's verified behavior rather than mixing legacy and REST 3.0 fields.

### 7.2 Page content

The مهام page should offer compact sections or tabs for:

- Current tasks and workload.
- Related historical tasks.
- Suggested categories/tags.
- Suggested responsible employees.
- Tag-priority settings and effective priorities.
- Completion estimates and SLA risk.
- History coverage and data-quality diagnostics.

Keep the existing personal-task execution workflow available. Analysis must not accidentally invoke Start, Complete, Approve, or Delegate.

## 8. Local similarity and task classification

### 8.1 Processing pipeline

```text
Authorized source records
→ Normalize text and structured fields
→ Tokenize Arabic/English
→ Build an inverted index
→ Retrieve candidate historical tasks
→ Rank candidates
→ Suggest categories and supporting examples
```

Reuse verified normalization behavior conceptually, including Unicode handling, whitespace, Arabic variants, and punctuation. Keep original text for display.

Avoid comparing every task with every historical record. Use indexed candidate retrieval, then bounded similarity scoring. Standard-library token overlap, sequence comparison, and locally calculated term weights are sufficient for an initial implementation.

### 8.2 Classification behavior

- Learn suggestions from actual categories/tags, not invented taxonomy.
- Allow owner-defined category aliases where sources differ.
- Exclude the task itself and linked duplicate copies from supporting evidence.
- Show similar task titles, source references, relevance scores, and category support.
- Return **insufficient evidence** for weak or contradictory matches.
- Label relevance scores accurately; they are not calibrated confidence probabilities.
- Keep weights and thresholds configurable and versioned.

**Acceptance:** Arabic and English examples retrieve relevant evidence without external services, and large-history processing is bounded and measurable.

## 9. Employee recommendations and workload

### 9.1 Candidate eligibility

Filter candidates before ranking:

- Current source eligibility to receive the task.
- Relevant project/team membership where required.
- Active employment/account status when reliably available.
- Known availability constraints.
- Verified cross-system identity mapping.

Unknown availability must remain unknown. Do not infer vacation from inactivity.

### 9.2 Ranking signals

Consider relevant completed work, category experience, current assignments, due/overdue commitments, source priority, and available capacity.

Show each recommendation with:

- Relevant historical examples and sample count.
- Current workload and data freshness.
- Matching skills/categories derived from task evidence.
- Known availability and any missing information.
- A plain explanation of why the employee appears in the list.

Keep count-based workload distinct from effort-based workload. Do not add elapsed cycle time as if it were remaining working hours. Only deduplicate cross-system workload when tasks have verified links.

Do not attribute all success or elapsed time to the final assignee after reassignment. Use assignment history where available; label uncertain attribution.

The user chooses the recipient. No automatic delegation is enabled by a recommendation.

## 10. Tag priorities, duration estimates, and SLA rules

### 10.1 Tag priorities

Fetch actual Bitrix tags and let the user map them to local priorities.

Define deterministic combination rules, such as selecting the highest matching configured priority. Show source priority separately from effective local priority. Store configuration in SQLite.

Changing a local rule does not silently write a new priority to Bitrix. A source update remains an explicit, permission-checked action.

### 10.2 Historical duration estimates

Use a documented fallback hierarchy:

1. Employee and similar completed work.
2. Team and matching category/service.
3. Broader comparable-work baseline.
4. Insufficient evidence.

Exclude invalid timestamps, canceled tasks, and unresolved reopen cycles according to documented rules. Retain visibility into exclusions and sparse samples.

Display a typical duration, an uncertainty range, sample size, evidence period, and whether the measurement represents elapsed time or recorded effort.

If only creation/completion timestamps exist, present an elapsed completion estimate. Do not claim active working hours or derive employee productivity from that difference alone.

### 10.3 SLA policy

SLA targets are owner-defined commitments. Historical estimates are predictions. Show them separately.

Configure timezone, working days, holidays, workday hours, and any formally defined pause/resume rules. Determine whether each SLA measures calendar time or business time.

When generating an ETA, avoid counting waiting time twice: a historical end-to-end cycle estimate already contains historical queue/wait effects. Only add explicit queue/capacity calculations when the underlying effort model supports them.

Evaluate predictions with a chronological holdout and compare against a simple category baseline. Record error, interval coverage, sample size, and sparse-group behavior. Agree release thresholds after measuring representative data; do not invent accuracy guarantees.

### 10.4 Optional availability

Start with manually entered date ranges or a validated local import, including source and last-update time. Define who may edit team availability within the deployment's access model.

An HR API integration remains outside the initial critical path.

## 11. Original OMI Bitrix requirements to preserve and close

| Area | Required behavior and acceptance |
|---|---|
| Setup | Per-profile settings; fetched projects and ordinary workgroups; manual multiple project/group IDs; independent connector readiness. |
| Storage modes | Shared Folder, Local Folder, Network Share, optional Obsidian linking; one physical workspace root. |
| Folder browser | Server-side drives/directories and manually entered UNC paths; no browser folder upload. |
| Folder test | Check access, read/write, Unicode and long-path handling; clean up test files. |
| Workspace creation | Employee/project/task separation; five standard subfolders; collision-safe creation and reassignment. |
| Documentation | Preserve user-authored content; maintain generated artifact links; verify required completion sections. |
| Start/Pause | Real source actions; future started work enters today; eligible future paused work leaves; no future-task justification. |
| Planner | Include unfinished due-today and overdue active work plus future started work; exclude completed and future queued work. |
| Planner capacity | Fifteen-minute increments; exact configured capacity when eligible work exists; define empty-day and excess-task overflow behavior; reject incompatible capacities. |
| Delay justification | Require only after the actual deadline; post the comment before marking success; repeat for a newly missed changed deadline. |
| Completion | Validate documentation; post result/workspace/documentation comment first; never complete after comment failure. |
| Partial completion failure | If comment succeeds but completion fails, report both states and avoid duplicating the comment on a blind retry. |
| Discussion | Lazy multiline history, author/time, pagination, refresh, and invalidation after posting. |
| Supervision | Per-task roles; permission-aware approval, return, priority/deadline change, and reassignment. |
| Assessment | Separate delivery and five-point performance; discover actual custom fields; structured-comment/report fallback. |
| Reports | Valid XLSX with Team Summary, Task Detail, and Late Justifications; documented source coverage. |
| Presentation | Natural Arabic/English, full RTL, LTR technical identifiers, blue-based design, both themes, system fonts, compact responsive rows. |
| Focus messages | Local bilingual rotation with a manual next action; no network dependency. |
| Diagnostics | Connector health, sync freshness, accessible scope, folder tests, and actionable errors without secrets. |
| Reliability | Centralized request/path/configuration handling, bounded caching, lazy loading, and targeted refreshes. |

Automatic validation cannot prove behavior on a real corporate share or portal. Keep those acceptance gates separate.

## 12. Proposed module organization

Use small modules and the existing Flask/Jinja structure. Avoid introducing a framework layer for every function.

```text
OMI_Bitrix/
  app.py                    # application assembly and existing routes
  bitrix.py                 # Bitrix adapter and history/tag capabilities
  diwany.py                 # Diwan transport and response normalization
  diwany_routes.py          # list, detail, token and delegation endpoints
  task_intelligence.py      # categories, recommendations, workload
  history.py                # ingestion jobs, coverage, memory indexes
  sla.py                    # durations and business-calendar policy
  similarity.py             # normalization and candidate scoring
  storage.py                # profile/configuration access
  credentials.py            # protected per-profile credential handling
  workspace.py
  planner.py
  review.py
  xlsx_report.py
  i18n.py
  templates/
    diwany.html
    tasks.html
    _diwany_token_dialog.html
  static/
    app.css
    app.js
  tests/
    fixtures/               # sanitized, synthetic source responses
    test_diwany.py
    test_profile_isolation.py
    test_history.py
    test_task_intelligence.py
    test_sla.py
    test_existing_workflows.py
```

Move existing routes into smaller modules only when needed by the change. Keep the first slice reviewable instead of refactoring the entire app at once.

### 12.1 Proposed application routes

These are local application routes, not claims about source API paths.

| Method and route | Purpose |
|---|---|
| `GET /diwany` | Render Diwan page and connection state |
| `POST /api/diwany/token` | Validate and save/replace this profile's token |
| `DELETE /api/diwany/token` | Remove token and invalidate profile Diwan state |
| `POST /api/diwany/sync` | Start bounded listing refresh |
| `GET /api/diwany/jobs/<job_id>` | Read progress for a profile-owned job |
| `GET /api/diwany/tasks/<task_id>` | Fetch/display authorized details |
| `POST /api/diwany/tasks/<task_id>/delegate` | Explicit validated delegation |
| `GET /tasks` | Render task intelligence page |
| `POST /api/history/sync` | Start authorized historical ingestion |
| `GET /api/tasks/<source>/<task_id>/recommendations` | Read suggestions for an accessible task |

Apply profile ownership checks to every job and cached record lookup. Use existing settings routes for priority/calendar preferences where practical.

## 13. Delivery milestones and exit gates

### Milestone 0 — Resolve contracts and scope

Deliver: scope decision, sanitized fixtures, ID/status mapping, endpoint contracts, network policy, history-storage decision, and working-calendar definitions.

Exit gate: no invented source endpoint, mutation payload, or authorization assumption remains in the next implementation slice.

### Milestone 1 — Token popup and read-only Diwan integration

Deliver: independent Diwan setup, protected per-profile tokens, pagination, lazy details, progress, errors, and export.

Exit gate: complete multi-page fixture retrieval, profile isolation, correct IDs, token lifecycle, and bilingual modal behavior pass offline tests.

### Milestone 2 — Delegation

Deliver: verified recipient selection, current-state validation, confirmation, source mutation, reconciliation, audit metadata, and affected-data refresh.

Exit gate: success, permission denial, stale task, duplicate click, and ambiguous timeout scenarios pass; then verify one explicitly approved controlled live case.

### Milestone 3 — History and task analysis

Deliver: background historical ingestion, scope/coverage reporting, source-aware identity, indexed similarity, category suggestions, and the مهام page.

Exit gate: representative history loads without blocking page rendering; missing/partial history is visible; Arabic/English evidence is reviewable.

### Milestone 4 — Employee recommendations and tag rules

Deliver: eligible-candidate filtering, verified employee mapping, workload aggregation, explainable suggestions, and local priority configuration.

Exit gate: no cross-profile leakage, no unlinked double-counting, deterministic priority rules, and understandable sparse-history behavior.

### Milestone 5 — Estimates, SLA, and optional availability

Deliver: duration baselines, intervals, policy-based SLA calculations, calendar settings, and optional absence input.

Exit gate: time-boundary tests and chronological evaluation report pass agreed thresholds; effort and elapsed time remain clearly distinguished.

### Milestone 6 — Baseline compliance and packaging

Deliver: original-brief gap fixes, regression results, offline installation materials, deployment documentation, and clean distributable ZIP.

Exit gate: all required local checks pass and live/hardware/manual gates are recorded honestly as passed, failed, or pending.

## 14. Validation strategy

Prefer standard-library `unittest`, Flask's test client, mocked HTTP, temporary directories, and sanitized fixtures. No tests may silently contact production or mutate real tasks.

### 14.1 Automated checks

- Python compilation, Flask route registration, Jinja parsing, JavaScript syntax, and translation-key coverage.
- Page 1 through final-page retrieval, empty history, duplicates, repeated pages, malformed/null responses, and mid-sync errors.
- Task ID versus request ID correctness and approved delegation schema.
- Token validation, replacement, removal, expiry, CSRF, secret redaction, and two-profile isolation.
- Concurrent job ownership, cancellation, and rejection of results from old credentials.
- Safe mutation retry/reconciliation and task permission changes.
- Arabic/English normalization, duplicate labels, indexed candidates, unknown categories, and insufficient evidence.
- Linked-task workload deduplication, identity mapping, attribution after reassignment, and unknown availability.
- Calendar boundaries, timezone conversion, missing/invalid timestamps, holidays, reopen rules, and uncertainty calculations.
- Planner total 480 minutes at default capacity, due/overdue inclusion, future queued exclusion, started inclusion, paused exclusion, and overflow/empty-day behavior.
- No justification for eligible future Start/Pause; overdue justification tied to the actual deadline.
- Arabic/spaced folder names, UNC normalization, employee separation, collision safety, user-note preservation, and completion/comment ordering.
- Comment pagination/cache invalidation, XLSX validity, spreadsheet injection protection, and ZIP/package integrity.

Run offline tests from the app directory with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\python.exe -m compileall -q . -x "[.]venv"
```

JavaScript syntax can be checked with developer tooling when available; Node is not a deployed application dependency.

### 14.2 Manual and external gates

- Token flow and permitted operations against actual internal Diwan/Bitrix deployments.
- Real Windows UNC shares, mapped drives, account permissions, long paths, and recovery after disconnection.
- Two independent browsers/profiles under concurrent use.
- Keyboard navigation, screen-reader modal announcements, both themes, and Arabic RTL.
- Viewports near 320, 375, 430, 768, 1024, 1366, and 1920 pixels, plus 125% and 150% zoom.
- Startup/install with public internet blocked; separately test internal-service outage and recovery.
- Representative historical volume with measured ingestion time, memory use, request counts, and cached-page responsiveness.

Set concrete performance budgets using the owner's target PC and representative volume before performance sign-off. A mocked HTTP test is not evidence of live portal compatibility.

## 15. Documentation and deployment deliverables

### 15.1 Documentation set

| Document | Required content |
|---|---|
| `README.md` | Purpose, installation, first run, local URL, architecture summary, and links to detailed guides |
| `docs/diwany-integration.md` | Verified API shapes, identifier mapping, paging, error semantics, recipient lookup, and delegation |
| `docs/user-guide.md` | Token popup, replacement/removal, task details, delegation, recommendations, priorities, and estimates |
| `docs/admin-guide.md` | Internal hosting, network access, certificates, Windows account, shares, secrets, configuration, and retention |
| `docs/data-and-analysis.md` | Historical scope, storage policy, employee/task mapping, scoring, missing data, SLA definitions, and evaluation |
| `docs/testing.md` | Offline commands, fixtures, manual procedures, and evidence matrix |
| `docs/troubleshooting.md` | Expired token, permission denial, partial sync, source outage, timezone data, paths, and ambiguous mutations |
| `docs/release-checklist.md` | Acceptance results, deployment steps, backup/restore, rollback, limitations, and package inventory |

Document operational behavior in plain language. Include realistic sanitized examples, never usable credentials or confidential task dumps.

### 15.2 Offline Windows installation

- Declare actual runtime dependencies, including timezone data where required.
- Prepare a wheel bundle on an approved connected build machine, with versions and checksums.
- Install from local artifacts on the target host; do not invoke public package indexes at runtime.
- Keep `start.bat` usable for local-PC operation and document stop/restart behavior.
- For shared production hosting, select and package a Windows-compatible WSGI server rather than treating the Flask development server as production deployment.
- Document `HOST`, `PORT`, and `WORK_COCKPIT_SECRET`; generate deployment secrets locally.
- Bind to localhost by default and expose an internal interface deliberately.
- Test from a clean Windows environment using the packaged dependencies.

### 15.3 Backup, upgrade, and rollback

Back up configuration, required local secret material, and authorized workspace documentation according to the protection mechanism in use. Do not export credentials into a plaintext backup.

Version schema/configuration changes and document migrations. For an extension, retain a recoverable pre-upgrade package and configuration backup. For a rebuild, define a separate cutover and rollback procedure.

Exclude live databases, credentials, logs, real task exports, employee documents, virtual environments, and private fixtures from the distributable ZIP.

## 16. Definition of done

The feature is complete only when:

1. The approved scope and unresolved policy decisions are documented.
2. Diwan token setup works independently for each employee profile.
3. All-page retrieval, details, and verified delegation use correct source identities.
4. Historical coverage and authorization limits are visible.
5. Similarity, categories, recommendations, and estimates run locally with explainable evidence.
6. Priority rules and SLA policy are explicit and do not silently mutate source tasks.
7. Original OMI Bitrix workflow requirements pass the applicable regression gates.
8. Offline installation, internal connectivity, failure recovery, and multi-profile behavior are demonstrated.
9. Documentation, a clean package, and an acceptance evidence matrix are delivered.
10. Any unverified live, hardware, or manual gate remains explicitly pending; it is not reported as passed.

## 17. Reference notes

- `current_strcuture.py`: Diwan request, field extraction, workflow summary, and sample delegation payload.
- `PROMPT.MD` and the attached brief: original OMI Bitrix requirements; their text matched in the earlier review.
- Supplied diagram: two new pages, local analysis, historical recommendations, tag priorities, SLA estimates, and optional availability.
- Owner clarifications: internal-source connections are permitted; credentials must be individual and collected through a popup.
- [Bitrix task listing documentation](https://apidocs.bitrix24.com/api-reference/tasks/tasks-task-list.html): permission-scoped records and legacy pagination.
- [Bitrix REST 3.0 task listing documentation](https://apidocs.bitrix24.com/api-reference/tasks/tasks-task-list-rest-v3.html): separate version-specific request/pagination contract.

The actual Diwan API contract and deployed Bitrix behavior must be confirmed before implementing their dependent operations.

## 18. Implemented release notes

The owner requested configurable endpoints and method dropdowns instead of supplying fixed URLs. These are now per-profile Settings fields. The new pages, token popup, local analysis, offline package, and tests are implemented. The source-specific API adapter is configurable but still requires validation against the actual internal services. See OMI_Bitrix/docs/release-checklist.md for remaining external/manual gates and documented limitations.
