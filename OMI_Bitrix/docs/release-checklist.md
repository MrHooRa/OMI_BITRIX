# Release checklist — task-scoped-3.7

Current model preparation and validation: [automatic topics](AUTOMATIC_DOMAINS_AR.md), [testing](testing.md). The 3.1 verification entries below are historical evidence, not a fresh production certification.

## Implemented and locally verified

- [x] Unified source-specific analysis, assignment, decision log and history workspace; existing colors/fonts retained.
- [x] Task-scoped supervision, supervising-holder self declaration, executor-only denial and fresh source permission checks.
- [x] Shared portal/task decisions and uncertain-operation markers, including legacy Diwany delegation; source-role changes invalidate old decisions.
- [x] No maximum task-count eligibility rule. Workload balances ranking without establishing suitability on its own.
- [x] Conservative ID/boilerplate cleanup, small bilingual aliases and technical-term allowlist; target excluded from both matching and ranking.
- [x] Completed evidence, open related work and manual-only choices separated; exact-content display groups retain IDs.
- [x] Diwan configurable role mappings, individual protected tokens, paged history/detail enrichment and minute operational watcher.
- [x] Independent two-hour history scheduler, complete-index publication, controlled-clock interval tests and retry behavior.
- [x] Optional custom-field evidence mapping, data-quality diagnostics, queue search/sort, history pagination and read-only evidence dialog.
- [x] Offline ranking evaluation tool with explicit as-of judgments and least-load/experience baselines.
- [x] 103 mocked/offline regressions, compilation and JavaScript syntax checks passed.
- [x] Read-only live Bitrix and browser checks documented in testing.md; no live assignment submitted.
- [x] Bounded synthetic index/rank timing recorded with scope limits.

## Required external acceptance — still open

- [ ] Verify Diwan status, supervisor/executor and token-identity semantics inside the internal environment. No sample upload is necessary.
- [ ] Controlled live delegation and independent permission/read-back verification for deployed source contracts.
- [ ] Verify actual outcome/quality/reopen/SLA fields before incorporating performance into scores.
- [ ] Representative, independently judged, time-stamped evaluation cases; compare model to baselines on untouched later cases.
- [ ] Production concurrency, history volume, API rate limits and 6 GB memory budgets, including journals and per-profile duplication.
- [ ] Corporate UNC/service-account deployment, internal HTTPS/firewall and clean target-machine installation.
- [ ] Complete keyboard/screen-reader/zoom and user acceptance with populated production-sized queues.

## Deployment limits

Run one application process. Browser profiles separate data but are not corporate authentication. Diwan identity and availability require verified configuration. Source compare-and-swap is unavailable, so external changes between read/write remain possible. History is memory-only; journals contain business data and need retention/ACL/backup policies. Policy remains per profile, not a central HR administration system.

The offline wheel bundle targets CPython 3.14 Windows x64. `tools/package_release.py` builds a clean 3.7 ZIP, excludes runtime data/browser sessions/workspaces, emits a SHA-256 inventory and validates archive integrity. Existing older ZIP/PDF files are historical and are not the current specification. Current discovery documentation is `AUTOMATIC_DOMAINS_AR.md` and `DELIVERY_STATUS_AR.md`.
