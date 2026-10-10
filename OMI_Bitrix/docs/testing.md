# Testing and Distribution Verification

## Regression coverage

Run from OMI_Bitrix with the prepared environment:

    $env:RUN_SEMANTIC_INTEGRATION='1'
    .\.venv\Scripts\python.exe -m unittest discover -s tests

The latest local audit on 9 October 2026 passed 246 tests with the bundled semantic models. Source clients are mocked and configuration isolated. This does not establish live Diwan correctness or representative employee suitability accuracy.

Coverage includes completed versus pending evidence, multilingual retrieval, automatic topic discovery, temporal eligibility, per-task authorization, uncertain assignment outcomes, personal-token isolation, history scheduling, directory linking, automatic suggestions and reviewed-only training.

## Portable release checks

Runtime configuration, credentials, workspaces, caches, exports, private training artifacts and development environments are excluded. Historical user-specific verification notes are omitted from the shareable documentation. Archive checks verify every file against the release SHA-256 inventory and ZIP CRC, both pinned model inventories and offline dependency availability. A fresh isolated configuration is used for the application smoke check.

## Remaining acceptance

Validate Diwan field mappings, permissions and delegation internally. Independently reviewed Arabic evaluation cases, target-machine memory/concurrency measurements, actual network-share permissions and user accessibility acceptance remain deployment checks. Export preserves the current implementation; packaging does not repair application defects.

See admin-guide.md, release-checklist.md, AUTOMATIC_DOMAINS_AR.md and AUTOMATIC_NOTIFICATIONS_AR.md.
