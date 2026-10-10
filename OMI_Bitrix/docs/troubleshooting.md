# Troubleshooting

| Symptom | Next step |
|---|---|
| Token input is disabled | Save a valid list endpoint in connection settings first. |
| Invalid/expired token | Obtain your own current token and use Replace token. |
| Permission denied | Confirm source task/recipient permissions; replacing a token is not automatically the fix. |
| Endpoint changes remove token | Expected protection. Validate your token again for the new connection. |
| Service unavailable | Check internal connectivity, endpoint method, certificate trust, and service status. |
| Redirect blocked | Enter the final HTTPS endpoint directly. |
| Missing internal task ID | Select the correct id/taskId/bpmTaskId field. Never use the ticket number as a substitute. |
| Pagination repeats | Confirm the configured method and that the source honors pageNumber/pageSize and GET encoding if selected. |
| Details fail with an empty URL | Configure the details endpoint. For GET, use {task_id} or a base URL. |
| Delegation unavailable | Configure its URL, verify payload/assignee mapping, enable the verified-contract checkbox, and add recipients. |
| Delegation uncertain | Use read-back reconciliation. Check the source before attempting any administrative marker reset. |
| No recommendations | Fetch completed work, configure completed statuses, match employee identifiers, and review source/category coverage. |
| No duration estimate | At least three valid comparable completed records are needed. |
| History disappeared after restart | Expected: task data and indexes are memory-only. Fetch again. |
| Windows cannot read protected token | Reconnect under the intended Windows account; DPAPI is account/machine-bound. |
| Existing browser lost its connection after upgrade | Signed profiles replace the older unsigned cookie. Reconnect; old records were retained. |
| Timezone-data error | Install the bundled requirements-lock.txt from wheelhouse. |
| No compatible offline wheel | Use the target Python/architecture for wheel preparation. Included native wheels target Python 3.14 Windows x64. |
| Port 5055 is occupied | Stop the known existing OMI server or deliberately choose another PORT. Do not terminate unrelated processes. |
| Mapped drive missing | Use a UNC path accessible to the server's actual Windows account. |
| Folder probe fails | Check share and NTFS permissions plus Windows long-path support. |
| Submission rejected as expired | Reload the page to refresh the CSRF/session token. |

Do not send tokens, full webhooks, database files, browser cookies, or raw private task dumps in troubleshooting reports. Include a sanitized error code, selected method, expected response structure, and whether the check was mocked or live.
