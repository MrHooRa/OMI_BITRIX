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

## Portable release checks

Runtime configuration, credentials, workspaces, caches, exports, private training artifacts and development environments are excluded. Historical user-specific verification notes are omitted from the shareable documentation. Archive checks verify every file against the release SHA-256 inventory and ZIP CRC, both pinned model inventories and offline dependency availability. A fresh isolated configuration is used for the application smoke check.

## Remaining acceptance

Validate Diwan field mappings, permissions and delegation internally. Independently reviewed Arabic evaluation cases, target-machine memory/concurrency measurements, actual network-share permissions and user accessibility acceptance remain deployment checks. Export preserves the current implementation; packaging does not repair application defects.

See admin-guide.md, release-checklist.md, AUTOMATIC_DOMAINS_AR.md and AUTOMATIC_NOTIFICATIONS_AR.md.
