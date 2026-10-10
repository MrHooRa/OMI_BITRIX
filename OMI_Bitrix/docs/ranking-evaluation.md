# Employee ranking evaluation

Run locally with no network calls or application state writes:

```powershell
.\.venv\Scripts\python.exe recommendation_evaluation.py --input verified-cases.json --k 3
```

## Input contract

The input is a JSON list. Each case has:

| Field | Meaning |
|---|---|
| `at` | Decision timestamp with timezone |
| `snapshot_at` | Actual captured snapshot timestamp, equal to `at` |
| `task` | Source-qualified target with `id`, `source`, `title`, `description`, `project_id`, optional `category` |
| `employees` | Candidate directory as of the decision: string ID, name, enabled/active booleans, project IDs, category/absence restrictions |
| `records` | Normalized source records as known then; each requires `observed_at` no later than `at` |
| `judgments` | Every eligible employee ID mapped to an independently reviewed suitability grade 0–3 |
| `judgment_source` | Reviewer/rubric/version or independently verified outcome source |
| `policy` | Optional complete ranking weights and local priority policy |

A record uses `source`, `id`, `title`, `description`, `project_id`, `category`, `assignee_id`, `completed`, `created_at`, `completed_at`, `status`, `priority` and `tags`. Active records should carry `awaiting_executor` derived from the then-current role/decision state. An open task waiting for assignment is not executor workload.

Small illustrative schema, not a measured dataset:

```json
[{
  "at": "2026-06-01T08:00:00+03:00",
  "snapshot_at": "2026-06-01T08:00:00+03:00",
  "task": {"source":"bitrix","id":"new","title":"payroll review","description":"salary deductions","project_id":"1"},
  "employees": [{"id":"1","name":"Example","enabled":true,"active":true,"projects":["1"]}],
  "records": [{"source":"bitrix","id":"old","title":"salary review","description":"payroll deductions","project_id":"1","assignee_id":"1","completed":true,"created_at":"2026-04-01T08:00:00+03:00","completed_at":"2026-04-02T08:00:00+03:00","observed_at":"2026-05-31T08:00:00+03:00"}],
  "judgments": {"1":3},
  "judgment_source":"Illustration only; replace with verified review"
}]
```

## Leakage and labeling controls

The evaluator rejects missing judgments for eligible candidates, future/undated observations, future task creation, and missing/mismatched snapshot dates. Ranking excludes target evidence and completions unavailable by the decision date. All eligible candidates enter baseline comparison, not just the first ten.

These are structural checks, not forensic certification of snapshots. Do not backdate current task state or use a final outcome field as an as-of feature. Snapshot capture, employee eligibility, outcome attribution and label reliability need independent verification. The current source assignee is not an optimal-employee label; employees not chosen are not negative examples.

## Outputs

The model is compared with least priority-weighted workload and matching-completed-experience baselines. Output reports macro-average Precision@K, Recall@K, NDCG@K, MRR (within K), abstentions, per-employee recommendation counts and average compute time. Grades above zero count as relevant. Precision divides by K, including abstentions; Recall/NDCG are null when no relevant candidate exists.

Recommendation counts expose concentration; they are not proof of fairness. Break down real cases by source/category, evidence availability and time period before accepting a policy. Weight/alias changes should be tuned on one period and evaluated on a later untouched period, against the same candidate eligibility and judgments. No representative comparison or accuracy certification has yet been run.
