# User Guide

## Your connection and token

Open Settings, enter your internal service URLs, and choose their methods. Configure only endpoints supplied by your organization.

The default reference mapping is:
- List: POST with pageNumber, pageSize, filter, and orderByValue.
- Details: GET with the internal task ID.
- Delegation: POST with taskId, requestId, and recipient fields.

Your actual service may differ. Select the matching methods and fields before entering a token.

The first visit to ديواني opens the token popup. If URLs are missing, the popup links to Settings and disables token submission. The token field starts masked, supports Show/Hide, and is cleared when the popup closes. Cancel or Escape leaves your configuration unchanged.

Validate & Save makes one read-only listing request. A successful response is required before replacing the stored token. Remove Token clears this profile's credential and Diwan cache. Reconnect after a confirmed 401 rejection; a permission denial or network timeout does not prove your token expired.

A different browser, browser profile, or cleared cookies creates a separate OMI profile. Tokens and endpoint settings do not follow you automatically.

## Fetch and inspect requests

1. Optionally enter request number, status ID, and date filters.
2. Select Fetch all pages.
3. Watch page/record progress; Cancel stops before further pages are processed.
4. Use the search box to filter fetched records locally.
5. Open Details to retrieve the request's form fields and workflow history.

Fetches continue until an empty source page; repeated pages and safety limits produce an explicit incomplete/error state. Page ordering can change while the source is active, so a completed fetch is not a transactionally frozen source snapshot.

Excel export contains three sheets: Requests, Form Fields, and Workflow. It includes details already opened during the session, not a hidden bulk download of every detail.

## Delegate a task

In Settings, add verified recipient identifiers with names. Choose whether Diwan expects email or an internal ID in assignTo. A directory entry is not proof of permission: the source system makes the final authorization decision.

Enable delegation only after verifying the endpoint, payload, supervisor/executor fields and your current-user identifier. The task must name you as a supervisor. Then:

1. Open the task details.
2. Select a configured Diwan recipient.
3. Select Delegate and confirm.
4. Wait for the follow-up detail read to confirm the new assignee.

The application uses the internal task ID; the request/ticket number remains separate. It never automatically changes a matching Bitrix task.

If the result is uncertain, use Check uncertain delegation. Do not repeatedly click Delegate. Automatic retries are blocked while an uncertain/pending marker exists. If read-back still cannot confirm, ask the source service owner to verify the outcome before resetting anything.

## Use مهام

The background scheduler fetches accessible Bitrix history and unfiltered Diwan analysis history independently of the browsing filters. Set Diwan completed-status values correctly or those records cannot supply completed-work evidence.

Select the source and describe the new task. Optionally choose a category/service. Analyze shows:
- Related records and relevance scores.
- A suggested category based on completed examples.
- Typical elapsed duration and historical range when at least three valid examples exist.
- Configured employees with comparable completed assignments, active/late counts, and priority load.

Recommendations are advisory. Current assignee IDs are attribution proxies, not proof that one employee performed all historical work. Workload counts are not remaining effort. Unknown availability stays unknown.

## Priority and SLA settings

Add local rules for actual Bitrix tags. Tag suggestions become available after history retrieval. The highest matching local tag priority is combined with the source priority; the source is not updated.

Add category/service SLA targets in business hours. Configure workday hours, working days, and holiday dates. The default calendar is Sunday–Thursday, 08:00–16:00, Asia/Riyadh.

The configured SLA deadline and historical elapsed estimate have different meanings. Neither modifies a Diwan or Bitrix deadline.

## Existing workflows

Use My Tasks for Bitrix execution and Team oversight for supervision. Configure projects/workspaces through Bitrix24 / Settings. Use a different UI language through the language control; theme selection stays in this browser.


## Unified assignment workspace (3.1)

Open `/tasks` and choose the source in the header. Use **Assignment decisions** to search the tasks you supervise and sort by priority or deadline. **Review task and candidates** shows its brief, historical evidence and related open work. Choose an employee beside the evidence, then confirm. No task-count ceiling excludes a busy employee; workload affects ranking only.

A task held by its creator/observer needs an executor until that holder confirms personal execution. Another task supervisor sees the same confirmed decision. If source ownership/executor changes, the old confirmation is invalidated. Merely being the assignee never grants assignment-management rights.

Use **Analyse a task** for a preview without any assignment action. **Find similar** excludes the chosen source task from both related work and recommendation evidence. **Decision log** shows accessible local audit events. **History & updates** provides source status, data-quality counts, search and pagination.

Eligibility policy is separate from analysis. Projects are selected by name; outcome-field mapping is optional and preserves raw evidence only. Settings are per browser profile. Diwan requires explicit role setup and recipients in Connections before recommendation assignment is enabled.

A read-only evidence dialog does not create a task workspace. An uncertain assignment must be verified against the source; release for retry is a separate confirmed action available only when read-back still shows another assignee.


## Discover employee evidence (3.2)

Use **Employee evidence** in the task workspace to search a name or observed topic and filter by a label. Open **View evidence profile** for completed-work counts, topic frequencies and paginated source tasks. Current open work appears separately. **Back to results** returns to the workspace view you came from.

Analysis now shows **Task understanding** before the candidates. Each candidate shows topics supported by completed related tasks and requested topics not evidenced there. Expand **Why this employee?** for examples and the ranking details for text/coverage components. Optional **Complementary experience** identifies different coverage contributions for discussion; it performs no group assignment.

The labels and counts describe accessible historical records, not a skill certification or performance rating. The dictionary is limited; a missing label is not proof of missing ability. Source and refresh warnings also apply to profiles. Colors, language controls and themes stay the same.


## Automatic employee suggestion in assignment alerts

For a task awaiting an executor, the assignment queue displays the suggested employee without first clicking **Recommend employees**. The reason shows related completed-work counts, current assigned open work and a link to the closest historical example. Outside the task workspace, the unread-task banner names the candidate and opens that task's assignment view.

While calculation is pending, the alert says it is analysing. With only pending or unrelated history it names no employee. Unavailable or stale source data must be refreshed before the suggestion appears. Marking an alert read preserves it in the queue; a different top candidate reopens it. Select **Review task and candidates** to inspect the full ranking. Assignment still requires your confirmation and current source permissions.
