# Diwan Integration Contract

## Configuration and authentication

All source URLs/methods are entered per profile on /connections. Credentials are entered only through the token popup.

URLs require HTTPS, no embedded credentials, query string, fragment, or whitespace. The adapter blocks redirects rather than forwarding credentials to a redirected host. TLS verification remains enabled. Use final internal endpoint URLs and configure corporate certificate trust on the server.

Supported method dropdowns:
- List: GET or POST.
- Details: GET or POST.
- Delegation: POST, PUT, or PATCH.

The adapter sends Authorization: Bearer <profile token>, Accept: application/json, and Content-Type: application/json. It uses a 25-second request timeout and an 8 MiB response limit. It never logs raw response bodies or token values.

## Listing

The reference POST body preserves current_strcuture.py:

~~~json
{
  "pageNumber": 1,
  "pageSize": 50,
  "filter": {
    "requestId": "", "serviceId": "", "from": "", "to": "",
    "groupCode": "", "employeeName": "", "statusId": 0,
    "statusIds": [], "nameEn": "", "nameAr": "", "name": "",
    "requestTypeCode": "", "taxpayer": "", "TIN": "",
    "TaxRegNumber": "", "userEmails": []
  },
  "orderByValue": [{"colId": "createdDate", "sort": "desc"}]
}
~~~

GET encodes the same top-level fields as query parameters; nested filter/order values are JSON strings. APIs expecting another GET encoding require an adapter change.

Accepted list locations:
- Top-level array.
- result.data, data, items, or result arrays.
- items, records, or tasks arrays inside a supported container.

A missing/null records container is an error, not an empty successful response. Pagination continues to an empty page, deduplicates internal task IDs, and detects repeated/no-progress pages. Limits are 2,000 pages and 100,000 records. Exceeding them produces incomplete results.

The adapter does not currently consume arbitrary vendor total/next-page metadata or guarantee a stable snapshot while records change. Compatibility must be verified by the service owner inside the internal environment; no source sample upload is required.

## Details

GET: replace {task_id} in the configured URL, or append /<URL-encoded-task-id> to a base URL.

POST: replace an optional URL placeholder and send:

~~~json
{"taskId": "<internal task ID>"}
~~~

The selected ID field is exactly one of id, taskId, or bpmTaskId. There is no silent fallback to requestId. A returned ID, when present, must match the requested ID.

Details support a dictionary at result.data, result, data, or the top level. Form controls are retained as a list of {id, label, value}, preserving duplicate labels. previousActions remains structured for display/export.

## Delegation

The reference body is:

~~~json
{
  "taskId": "<internal ID>",
  "requestId": "<business ticket>",
  "assignTo": "<configured email or employee ID>",
  "assignToNameEn": "<configured English name>",
  "assignToNameAr": "<configured Arabic name>"
}
~~~

The application does not assume that assignTo accepts email. Configure the actual recipient kind and the field in the detail response that confirms assignment.

Delegation is disabled until a URL and explicit contract-confirmed setting exist. It also requires a task in this profile's fetched records, a configured Diwan recipient, current details, and explicit user confirmation. Completed tasks are blocked when completed statuses have been configured.

After sending the mutation, the adapter rereads details and compares the configured assignee field with the requested recipient. A successful HTTP status alone is insufficient.

The legacy Diwany route retains its SQLite operation marker and now also uses the shared source/task journal used by recommendations. They prevent blind mutation retries across server restarts. Reconciliation reads the source; it does not repeat delegation. No remote idempotency key is assumed.

## Error handling

- 401: rejected/expired token; offer reconnect.
- 403: permission denied; keep credential.
- Explicit success:false or error: source rejection.
- Redirect, malformed JSON, timeout, unexpected response, or oversized response: actionable local error.
- Ambiguous mutation outcome: preserve uncertain marker and require read-back.

Profile token replacement/configuration change invalidates only that profile's Diwan cache generation. Late background results cannot restore invalidated data.

## Local routes

See diwany_routes.py for the implemented /api/diwany, /api/history, and /api/intelligence endpoints. Mutation routes require the signed profile session and X-CSRF-Token (or the standard form token).

Real portal compatibility and permitted recipient discovery are not certified by synthetic fixture tests. The initial employee directory is manual; no unverified employee-lookup endpoint is called.


## Unified recommendation roles and history (3.1)

Configure `supervisor_field`, `assignee_field`, `current_user_id` and `roles_confirmed`. Dotted field paths are supported. The supervisor field may hold an ID or a list of IDs; assignee must use the same identifier type as recipients. Values must be verified with the source owner. The current-user ID is configuration, not an independently verified login identity. Source-token authorization remains decisive for writes.

The adapter never infers executor from the request employee or isOwner. Request status code 4 is not assumed to mean Bitrix pending review. Both legacy Diwany delegation and unified assignment reject a non-supervisor using fresh details.

Every two hours, analysis reads all unfiltered pages and enriches each task with details before publishing the complete index. Known request-narrative form fields supplement text; other form values and workflow actors are retained for display. Open tasks refresh every minute, enriching new/changed tasks; without a modification timestamp, fresh details are necessary each pass. This can be expensive on a large source and needs real API-rate validation.

Any failed enrichment leaves the last complete index intact. Token/configuration changes invalidate profile scopes, and late results are discarded. Live compatibility, role interpretation and delegation remain unverified because no Diwan endpoint/token contract has been exercised here.
