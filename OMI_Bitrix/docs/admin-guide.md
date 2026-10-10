# Administration and Offline Deployment

## Supported environment

Current frozen semantic dependencies: Python 3.12+ on Windows. The bundled wheelhouse in this release was prepared for CPython 3.14 on Windows x64. PyTorch, NumPy and other native dependencies are version/platform specific; other targets require matching wheels.

Production entry point: serve.py using Waitress with eight threads and a 2 MiB request-body limit. python app.py remains a development entry point.

## Offline installation

The target requires Python, the project files, requirements-lock.txt, wheelhouse/, and both pinned model folders in models/.

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements-lock.txt
.\.venv\Scripts\python.exe serve.py
~~~

No package index is used by start.bat. Prepare a different target's wheels on an approved connected build machine using that target's Python, then transfer and verify them. wheelhouse/SHA256SUMS.txt records packaged artifact checksums.

## Local history cache

Historical task snapshots are held separately from configuration in `data/task-history.sqlite3` (SQLite WAL). Keep the entire private `data/` directory when upgrading or backing up, with the server stopped. Preserve the signing secret and protected credentials so profiles can reuse their cache. The cache is per profile/source connection; a changed service or token invalidates that source. Cached history does not replace the source's permissions or write verification. Restored indexes prepare in background workers, while saved tasks can be browsed immediately. Large-model cold starts and source refreshes can still take time.

## Local models (3.7)

The bundled model files total approximately 3.43 GB. `tools/prepare_models.py` verifies their SHA-256 manifest offline; `--download` is an explicit connected build step only. Runtime uses local paths, safetensors and `trust_remote_code=False`. No private task text is sent to a model provider. Preserve each model README and license metadata when packaging. `tools/package_release.py` includes models but excludes their `.cache`, application data, credentials and virtual environments.

`TASK_MODEL_MODE=lexical` explicitly disables semantic inference for diagnostics. `TASK_EMBEDDING_PATH` and `TASK_RERANKER_PATH` can identify prepared local copies. Missing embeddings yield a disclosed lexical-only result without restoring predefined business domains; missing pair verification is disclosed and uses a stricter semantic retrieval floor. RAM/inference load requires measurement on the target machine; the old lexical timing figures do not describe this release.

## Inference and training operation (3.8)

`TASK_TORCH_THREADS` overrides CPU inference threads (default 8 with at least 16 logical processors, otherwise up to 4). Measure the target; more threads are not universally faster. `TASK_RERANKER_PRECISION` defaults to `fp32`; `int8` uses pinned PyTorch dynamic Linear quantization as an experiment and is not accuracy-equivalent by assumption. This API is deprecated upstream, so retest it before upgrading the frozen dependencies. Model files are unchanged.

`tools/benchmark_models.py` records cold/warm timings on anonymous cases with outbound sockets blocked. Training preparation/reviews belong in `data/model-training`; candidates belong in `data/model-candidates`. They contain business-sensitive material or derivatives and are excluded from portable releases. Do not promote a candidate using only pair-level metrics; verify employee ranking and calibrate runtime acceptance thresholds separately. No candidate is auto-loaded or auto-published by the trainer. See [training operations](MODEL_EFFICIENCY_AND_TRAINING_AR.md).

## Environment settings

| Variable | Default | Purpose |
|---|---|---|
| HOST | 127.0.0.1 | Bind address; use an intended internal interface deliberately |
| PORT | 5055 | Listener port |
| OMI_DATA_DIR | project/data | Configuration, protected credentials, local signing material |
| WORK_COCKPIT_SECRET | generated persistent local secret | Cookie/session signing |
| OMI_HTTPS | 0 | Set 1 when users access the app through HTTPS |
| OMI_AUTO_SYNC | 1 | Set 0 to disable background workspace and history scheduling in serve.py (opening the analysis page can still trigger due history fetches) |

For shared hosting, use a protected network and an HTTPS reverse proxy. Configure Windows firewall access only for intended internal clients. Browser profiles are not corporate authentication; do not expose the application publicly.

The current implementation limits source traffic to user-configured connections by design and blocks Diwan redirects. Enforce organizational network allowlists at the host/network boundary; URL settings alone are not a firewall.

## Secrets and profiles

Diwan tokens are DPAPI-protected under the Windows account running the server, with profile-specific entropy. Protect data/ using NTFS access control for the service account and administrators. DPAPI protection does not replace host security.

Do not share data/cockpit.sqlite3, .session-secret, logs, or exports. Legacy Bitrix webhook settings remain sensitive data in the existing SQLite store and must be protected by filesystem permissions.

Do not casually change WORK_COCKPIT_SECRET or delete .session-secret: existing signed profile cookies will no longer resolve. Tokens may require re-entry after changing machine or Windows account.

The upgrade introduces wc_profile_v2 signed cookies. Existing unsigned browser profiles must reconnect. Their old configuration records remain in SQLite; do not delete them as part of an upgrade.

## Network shares

The server's Windows account must have share and NTFS permissions. Mapped drives are account/session-specific; a service may need a UNC path instead:

~~~text
\\server\department\Team Work
\\server\Shared Data\إدارة البيانات\المهام
~~~

Use Test folder under the deployment account. It checks read/write, Unicode, and a nested long path and removes its temporary contents. A successful local-path test does not validate your actual UNC share.

## Runtime data and capacity

Task histories and indexes are memory-only and expire after 12 hours of inactivity or restart. At most four ingestion jobs run simultaneously. Each source/profile keeps a bounded latest job; source histories are limited to 100,000 records.

Progress is per browser profile. A failed refresh preserves previous records where available and exposes an error. No restart recovery of partially ingested task history is promised.

## Backup and rollback

Back up the configuration database and signing material under protected storage, plus employee workspaces according to organizational policy. DPAPI ciphertext recovery depends on the Windows account/machine context. Never convert credentials to plaintext for portability.

Before upgrade, stop the server and keep a recoverable copy of the previous source and database. The implementation created data/pre-diwany-backup/ for affected source files; it is not a complete database backup.

Rollback requires restoring the compatible source/dependencies and, if needed, the separately backed-up database. Do not overwrite or merge employee task workspaces during rollback.

## Packaging

Use tools/package_release.py. It includes only explicit source, template, static, test, documentation, and wheel directories. It excludes data/, virtual environments, screenshots, browser session state, real exports, and employee workspaces. No live token or endpoint configuration belongs in the ZIP.

## Two-hour history scheduler

`history_scheduler.py` runs independently of workspace synchronization. Startup and connection changes trigger a full read-only history fetch; successful starts schedule the next run 7,200 seconds later. A source/profile can have only one history job running, including manual refreshes. Failures retain the last successful records/index and schedule a five-minute retry. Connection changes clear the old corpus before fetching the new source.

The `/tasks` page displays schedule status through `/api/intelligence`. The API refreshes only due sources; its 15-second UI polling is not a new upstream fetch every 15 seconds. The index and preview pairs are built once per successful ingestion. A server restart rebuilds memory automatically. Use one application process per deployment; a machine shutdown cannot run scheduled refreshes.

## Recommendation watcher and journal

`recommendation_service.py` starts with the existing server lifecycle. It fetches all accessible open selected-project tasks every 60 seconds, never overlapping itself; fetch failures retain the previous state and back off for five minutes. Do not confuse this operational snapshot with the independent two-hour full history job. Open-task polling updates queue state and queues automatic suggestions for the current task supervisor when task text, eligibility, history, linked evidence or workload changes. One worker per source computes the same ranking engine outside the service lock; unchanged inputs reuse the compact in-memory result. Manual ranking still runs on request; normal recommendation inference releases the service lock and rejects assignment use if its snapshot changes. Mutations remain serialized. Similarity examples run only when their section is opened, after the history snapshot is published. The assignment queue supports search and sorting; history is paginated in 50-record pages. Large supervisor queues are still transferred as one snapshot and need production-scale verification. Directory status refreshes every two hours. Failed directory reads keep the previous membership/status data, expose an error, block assignments and retry on the next open-task cycle. Permissions and source task inputs are rechecked after inference immediately before assignment.

`data/recommendations/<scope-hash>.json` stores minimal task/decision state using atomic replacement. The scope hash includes profile and connection/project scope, not plaintext credentials. The latest 1,000 audit entries remain in the state file; older entries are appended to `.audit.jsonl` in the same protected directory. Archives have no automatic deletion; include them in your organization's retention and backup policy. A crash around archive rotation may duplicate archived events; they are audit records and never trigger mutations. The state cap is 100,000 observed tasks per scope. Journal corruption/capacity or source errors are exposed as unavailable; no partial poll replaces the UI state silently.

Browser profiles remain separation rather than authentication. Use protected internal access and authenticated hosting for shared organizational deployment. Alerts are local and visible only in the recipient's connected profile with the relevant project scope; alerts do not send email or chat. An explicitly confirmed Bitrix reassignment adds a WORK_COCKPIT_REASSIGN source comment; ambiguous comment outcomes are reported and never resent automatically. Supervision comes from current task creator/observers, never project roles alone.


## Supervision, shared decisions and Diwan

Task creator and explicit observers can supervise Bitrix assignments; the source EDIT/DELEGATE permission remains mandatory. Executor identity alone does not grant management rights. A supervising holder must personally confirm execution. No maximum task count limits eligibility.

Self-execution decisions and operation markers are shared by source portal/task, independent of personal credentials. Source access and profile audit views remain separate. Run one server process: the in-process locks are not a distributed locking service. Reassignment uses read-check-write-readback; source atomic compare-and-swap is not available.

Diwan setup additionally requires verified supervisor/executor fields and current-user identity. That identity is configured, not independently authenticated; match it to the token with the service owner. Never infer task roles from request employee or isOwner. Legacy Diwany delegation also checks these roles and shares uncertain-operation markers with recommendations.

Diwan details are enriched in background history jobs. Sources without modification timestamps can require one detail request per open task each poll; tune/extend the adapter only against a verified vendor contract. No batch endpoint is invented. Validate API limits and latency at real scale.

Custom outcome fields remain raw evidence until their semantics are approved. Policy and availability are per-profile configuration, not a centrally governed HR directory. Protect the journal as business data. New queue entries store task metadata; new human decisions retain compact candidate/evidence IDs and scores. Workspace reconciliation retains the metadata required to finish a transfer. Existing journals and archives are preserved unchanged by this policy and may contain narratives and full recommendations from earlier releases. No automatic deletion or retention migration was applied. Earlier PDF and RAR exports have not been rebuilt; the 3.9 Markdown correction guide documents this update.


## Workspace follow-up and browser drafts (3.9)

Both Bitrix assignment entry points use the same transaction. A confirmed remote assignment is not rolled back or repeated because workspace transfer or a source comment failed. Existing destination folders are never overwritten or merged; inspect both folders manually when a collision is reported. If the process stops after recording a follow-up attempt, inspect the workspace/comment before taking manual action. Run one server process; there is no distributed transaction or source CAS.

The analysis composer keeps a per-profile/source draft in browser sessionStorage for this tab with a 30-minute validity period. It contains description/category/project only, never credentials or model responses. Reloading restores the draft, not a stale recommendation. Treat managed browser sessions as business data.


### Automatic alert suggestions (3.10)

`notification_suggestions.py` maintains a deduplicated task queue per service and compact profile-scoped RAM results. It never assigns tasks or sends external messages. A result names an employee only when that employee is eligible and has related, valid-dated completed evidence. Native/linked source failures, incomplete history and open snapshots older than 120 seconds hide cached candidates. Calculation/publication failures retry after five minutes; source polling retains its existing backoff. Recovered linked-source status is re-read rather than permanently cached as unavailable.

The notification API includes `suggestion.status` (`pending`, `ready`, `no_evidence`, `unavailable`, `failed`), and for `ready`, `employee` and a compact `reason` with counts, workload and one evidence reference. `?summary=1` returns the highest-priority unread task as `alert`, including its source for deep linking. Names and evidence descriptions are not written to the decision journal; only the suggested employee ID and existing read/alert metadata are persisted. A changed top candidate reopens the alert; unchanged refreshes preserve read state. Source-task rights are checked again through the existing human assignment flow.

The server must remain running. Automatic ranking has no runtime cloud dependency. Large queues, cold model startup and multi-user CPU contention still require deployment-scale measurement; this release does not assert a notification-latency SLA.
