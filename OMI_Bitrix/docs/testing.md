# Testing and Distribution Verification

## Regression coverage

Run from OMI_Bitrix with the prepared environment:

    $env:RUN_SEMANTIC_INTEGRATION='1'
    .\.venv\Scripts\python.exe -m unittest discover -s tests

The latest local audit on 9 October 2026 passed 246 tests with the bundled semantic models. Source clients are mocked and configuration isolated. This does not establish live Diwan correctness or representative employee suitability accuracy.

Coverage includes completed versus pending evidence, multilingual retrieval, automatic topic discovery, temporal eligibility, per-task authorization, uncertain assignment outcomes, personal-token isolation, history scheduling, directory linking, automatic suggestions and reviewed-only training.

## Personal calendar verification

Run `python -m unittest discover -s tests -p test_calendar.py -v` for nine isolated server checks. Optional Playwright fixture commands are in the application README. Browser coverage includes dragging, date selection, persistence, unchanged deadlines, undo, colleague names, reminder completion/reopening, filters, profile isolation, Arabic/RTL, mobile and dark themes, refresh failures and corrupt-storage preservation. Browser checks assert that calendar interactions send no write requests.

On 10 October 2026, all nine calendar checks and the browser suite passed. Full discovery ran 237 tests against the merged source and 228 against the untouched `5cb7ee0` baseline in the same minimal environment. Both had identical three failure reports, three errors and ten skipped checks: missing NumPy/PyTorch imports and existing matching/quality cases. The calendar introduced no additional failures. Full semantic acceptance still requires the pinned dependencies and both local models; this check does not claim live Bitrix acceptance.

## Local history, columns and Windows paths

Run `python -m unittest discover -s tests -p test_local_history.py -v`. Sixteen isolated checks cover SQLite restart/pagination/search, connection/profile isolation, failed refresh and disk-full preservation, background index cancellation, unchanged-index reuse, scheduler cache reuse, token retention, JSON-column settings, legacy notes and Windows paths longer than 260 characters. A 1,000-task check verifies one project-directory scan per sync; a 1,000-candidate check verifies one semantic-maximum calculation per query. These operation-count checks do not establish end-to-end latency on a production corpus.

Optional browser checks: export with `python tests/test_local_history.py --export output/columns-fixtures`, set `COLUMNS_FIXTURES` to that directory, and run `node tests/diwan_columns_browser.cjs` with Playwright available. The suite covers English/Arabic, narrow screens, dark themes, saved column headings/values, CSRF headers and no extra token prompts. Both this suite and the calendar browser suite passed on 10 October 2026.

Full discovery after these changes ran 253 tests, with the same three failure reports, three errors and ten skipped semantic checks documented above. No new failures were introduced. Production-scale analysis and live Diwan acceptance remain unverified in this minimal environment.

## Optional Diwany connection and complete columns

Run `python -m unittest discover -s tests -p test_optional_diwan.py -v` and the equivalent command for `test_diwan_catalog.py`. All 22 checks passed on 10 October 2026: navigation without credentials, Bitrix-only operation, retained mutation/CSRF guards, the exact 72-field catalog, nested/form/detail values, secret filtering, token preview isolation, and saved selections larger than 20 columns.

The extended columns browser suite passed in English/Arabic, dark themes and narrow screens. It verifies no automatic token prompt, explicit connection, navigation to column settings after validation, Select all/Clear, persistence and table values. A restarted server returned HTTP 200 for all eight main navigation pages without a Diwany token.

Full discovery ran 275 tests: four failure reports, three errors and ten skipped checks. Besides the previously documented semantic/dependency issues, a notification worker timed out; another notification-suite rerun reported a summary-response error. Both notification checks passed when run together in isolation, indicating intermittent behavior. Full-suite acceptance remains incomplete; the targeted new feature and browser checks passed.

## Portable release checks

Runtime configuration, credentials, workspaces, caches, exports, private training artifacts and development environments are excluded. Historical user-specific verification notes are omitted from the shareable documentation. Archive checks verify every file against the release SHA-256 inventory and ZIP CRC, both pinned model inventories and offline dependency availability. A fresh isolated configuration is used for the application smoke check.

## Remaining acceptance

Validate Diwan field mappings, permissions and delegation internally. Independently reviewed Arabic evaluation cases, target-machine memory/concurrency measurements, actual network-share permissions and user accessibility acceptance remain deployment checks. Export preserves the current implementation; packaging does not repair application defects.

See admin-guide.md, release-checklist.md, AUTOMATIC_DOMAINS_AR.md and AUTOMATIC_NOTIFICATIONS_AR.md.
