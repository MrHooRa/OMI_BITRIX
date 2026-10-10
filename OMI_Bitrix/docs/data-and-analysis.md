# Data and Analysis — task-scoped-3.2

## Current representation (3.7)

Accessible titles and descriptions are embedded using locally bundled multilingual E5. HDBSCAN discovers density groups without business seeds, and class TF-IDF supplies provisional source-language names. A local BGE pair model verifies task subjects. Snapshots remain in RAM, refresh every 7,200 seconds, and never grant new source rights. Completed evidence alone supports employee recommendations; pending affinity stays separate. See [current Arabic data flow and equations](AUTOMATIC_DOMAINS_AR.md). The previous manually defined domain/corpus-association descriptions below are historical, not the active discovery method.


The current step-by-step specification, data sources, formulas and limitations are in [ALGORITHM_AR.md](ALGORITHM_AR.md). This page summarizes operational behavior; earlier same-day ranking formulas are superseded.

## Data flow

1. The independent history scheduler reads accessible selected-project Bitrix tasks and unfiltered Diwan pages every 7,200 seconds while running. Diwan history is enriched with task details. A partial failure preserves the prior successful index and retries after 300 seconds.
2. Source-specific watchers refresh open tasks every 60 seconds. Bitrix membership/activity refreshes every two hours; Diwan roles and recipients require explicit verified configuration.
3. History/indexes remain in profile/source memory. Decision journals persist bounded operational task/decision data and archived audit events, and contain sensitive business information.
4. Relevance uses normalized Arabic/English tokens, a small explicit alias map, IDF weights and cosine similarity (floor 0.16). Source IDs, test markers and generic boilerplate cannot establish suitability. The index retrieves up to 300 matches. Technical allowlists are limited, not general semantic understanding.
5. Eligibility precedes ranking: active, enabled, permitted project/category and not in a configured absence interval. There is no maximum open-task count.
6. Completed task-specific evidence supports the 50/20/30 similarity/experience/workload baseline. Open related work is separate. Without relevance, names are manual choices, not recommendations.

## Metadata and attribution

Configure actual custom-field codes for quality, delivery, team, department, task type, effort and reopened state. Values are preserved as evidence; their names alone do not establish valid performance measures. Current assignee and current deadline are not verified historical ownership/deadline snapshots. Do not train optimal-employee labels from assignment IDs.

Sources and employees are not automatically merged. Workload measures accessible source tasks only, so undisclosed work and cross-system identity differences remain limits.

## Duration and SLA

At least three completed records with valid positive elapsed durations are required for median and empirical 10th/90th historical bounds. These include waiting and are not active working hours or calibrated forecast intervals. Candidate duration uses that employee's matching completed evidence.

Configured category/service SLA targets use business hours (default Asia/Riyadh, Sunday–Thursday, 08:00–16:00), working-day and holiday rules. Targets never mutate source deadlines. Task-history chronological duration evaluation is separate from employee-ranking evaluation.

## Evaluation and data quality

History diagnostics expose missing narrative/category/executor, invalid completion dates, duplicate content groups and date coverage. They do not establish real outcome quality. See [ranking-evaluation.md](ranking-evaluation.md) for explicit judged snapshots and model/least-load/experience comparisons. No representative accuracy result has been certified.


## Typed evidence in 3.2

`employee_insights.py` classifies task text with 22 explicit local bilingual labels (business domain, task type, tool/system, deliverable, concept). These are observed-work labels, not certified employee skills. Known disjoint business domains reject a lexical match even when a tool overlaps. Unknown domains still use the lexical baseline.

For candidates with completed related evidence, similarity combines 75% mean top-three text relevance and 25% coverage of requested known domains/tools/concepts. When none are recognized, text relevance remains the full similarity component. General work types and deliverables do not increase coverage. The outer 50/20/30 weights remain unchanged. Coverage absence means no supporting accessible evidence, not an inability judgment.

Employee profiles aggregate completed executor records, deduplicate source/ID pairs, and keep active workload separate. The read-only `/api/recommendations/people` endpoint supports `source`, `q`, `topic`, `employee` and `page`; list and task pages contain up to 20 entries. Source configuration changes invalidate the old corpus on read. Unique ingestion revision IDs prevent same-second refreshes from reusing an obsolete index.

Complementary experience is a greedy additional-coverage suggestion over eligible completed-evidence candidates, limited to three displayed people. It never assigns a group. See [the adoption review](RAB6_ADOPTION_AR.md) for reference decisions and limitations.
