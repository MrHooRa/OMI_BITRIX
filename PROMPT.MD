Build a production-ready internal web application from scratch called **OMI Bitrix**.

Do NOT modify or reuse an older implementation. Design the architecture, backend, frontend, UI, folder handling, Bitrix integration, and performance strategy cleanly from zero.

The application is an internal productivity cockpit integrated with **Bitrix24 Tasks**. Its purpose is to reduce the overhead of starting tasks, planning daily work, documenting work, managing shared folders, updating Bitrix, supervising employees, reviewing completed tasks, handling missed deadlines, and generating team reports.

The application will normally run on a Windows computer/server inside a corporate network and may be accessed by multiple employees at the same time through the host machine's IP/port.

## Core technical requirements

Use:

- Python
- Flask
- Python standard library wherever practical
- SQLite only for configuration/profile/application state
- Vanilla HTML
- Vanilla CSS
- Vanilla JavaScript

Avoid:

- React
- Vue
- Node build systems
- Bootstrap
- Tailwind
- external CDN dependencies
- unnecessary Python packages
- unnecessary database abstraction layers
- storing a duplicate Bitrix task database

The application must be extremely easy to deploy:

```text
pip install flask
python app.py
```

Keep the code modular and readable.

Suggested architecture:

```text
omi_bitrix/
    app.py
    bitrix.py
    config_store.py
    workspace.py
    planner.py
    similarity.py
    reports.py
    utils.py

    templates/
        base.html
        setup.html
        dashboard.html
        my_tasks.html
        supervisor.html
        task.html
        settings.html

    static/
        css/
            app.css
        js/
            app.js

    data/
        config.db

    README.md
    requirements.txt
    start.bat
```

Do not over-engineer.

## Performance is extremely important

Optimize the application for responsiveness.

Do not fetch all Bitrix information repeatedly on every page render.

Use:

- lazy loading
- short-lived in-memory caching
- batch REST calls where Bitrix supports them
- client-side lazy comment loading
- pagination
- debounce for search
- minimal DOM manipulation
- minimal JavaScript
- indexed lookup structures
- efficient filesystem scanning
- caching for project members and metadata
- background-safe polling from the browser where appropriate

The dashboard should feel immediate even if the account has many tasks.

Never make 100 sequential REST calls during one page request when a batch or lazy approach can be used.

Task comments must load only when the user expands the discussion area.

Supervisor permissions may also be loaded lazily.

## Multi-user behavior

Do NOT create another username/password authentication system.

Each browser receives a random local profile identifier stored in a cookie.

SQLite stores configuration separately for each browser profile.

Therefore:

```text
Browser A
→ employee A configuration
→ employee A Bitrix webhook

Browser B
→ employee B configuration
→ employee B Bitrix webhook
```

The same Flask server can therefore serve multiple employees.

Never define a person globally as either "employee" or "supervisor".

Roles are determined PER TASK.

One employee may simultaneously be:

- assignee of Task A
- creator/supervisor of Task B
- observer of Task C

The UI must reflect those relationships independently.

## Initial setup

On first launch, show a polished setup wizard.

Ask for:

- Employee display name
- Bitrix24 incoming webhook URL
- Storage/workspace root
- Preferred language
- selected Bitrix projects/groups
- optional manually entered default Project/Group IDs
- workday start time
- planner duration, default 8 hours
- optional application/storage mode

Test the Bitrix webhook before saving.

Fetch available Bitrix projects AND workgroups.

Do not filter out normal workgroups.

Allow project selection from fetched results.

Also provide a manual field:

```text
Default Project / Group IDs
123,456,789
```

These IDs must be accepted even if Bitrix does not return them in the fetched project list.

Support multiple IDs.

## Storage must NOT depend on Obsidian

Do not design the application around Obsidian.

The user should choose the workspace type in Settings.

Options:

```text
Shared Folder
Obsidian Vault
Local Folder
Network Share
```

Internally they can all use filesystem folders.

Obsidian should simply provide additional Markdown linking behavior when selected.

For a normal shared folder, everything should still work perfectly.

Example:

```text
\\server\department\Team Work
```

or:

```text
S:\Team Work
```

or:

```text
C:\Work
```

If Obsidian mode is chosen, the same physical directory can act as the vault.

Do NOT create separate "work folder" and "Obsidian folder" unless the user explicitly requests that.

## Network path handling

This is extremely important.

The company uses Windows shared folders with:

- UNC network paths
- Arabic characters
- spaces
- potentially long paths

Examples:

```text
\\prdfls\Shared Data\إدارة البيانات\المهام
```

Support these correctly.

Do not corrupt UNC paths.

Do not turn:

```text
\\server\share
```

into malformed variants with extra separators.

Normalize paths safely.

Support Arabic Unicode filenames naturally.

Do not unnecessarily call `.resolve()` on remote paths.

Do not reject a valid path simply because the complete generated task path is long.

When required on Windows, use proper long-path handling internally while preserving the human-readable path for display and Bitrix comments.

Add a server-side folder browser in Settings.

The user should be able to:

- browse drives
- browse mapped drives
- browse directories
- enter UNC paths manually
- select the workspace root

Do not upload folders through HTML.

This is a filesystem picker for the server hosting Flask.

## Workspace structure

Create one separate top-level folder per employee.

Example:

```text
Workspace Root/
    Bitrix Work/
        Employee C/
            Project Name/
                12345 - Task Name/
                    Task.md
                    01_Input/
                    02_Workflow/
                    03_Queries/
                    04_Output/
                    05_Evidence/
```

Employee name comes from Settings.

Sanitize invalid Windows filename characters without unnecessarily removing Arabic.

If a task is reassigned to another employee, safely move its workspace to the new employee's directory if possible.

Never overwrite another existing workspace.

If a collision exists, warn the user.

## Automatic task setup

When a task assigned to the user appears in one of the configured projects/groups:

automatically create its workspace.

Create:

```text
01_Input
02_Workflow
03_Queries
04_Output
05_Evidence
```

Also create a documentation file.

If storage mode is Obsidian:

```text
Task Name.md
```

with normal relative Markdown links.

If storage mode is generic Shared Folder:

Markdown is still acceptable because it is simple and portable.

The documentation should contain:

```text
Task information
Objective
Requirements
Inputs
Work performed
Business logic
SQL / Queries
Alteryx / Python / Power BI work
Validation
Issues / blockers
Result
Deliverables
Handover
Referenced files
```

Automatically scan the task folders and maintain a "Referenced files" section.

Examples:

```text
02_Workflow/reconciliation.yxmd
02_Workflow/analysis.py
03_Queries/validation.sql
04_Output/result.xlsx
05_Evidence/check.png
```

Do not rewrite or destroy user-written documentation.

## Main navigation

Keep the application simple.

Primary navigation:

```text
Home
My Tasks
Supervisor
Planner
Search
Settings
```

Do NOT create excessive pages.

## My Tasks

Show tasks where the current Bitrix user is the assignee.

Use a dense quick-look design.

Do not put every task inside a giant floating card.

Prefer compact operational rows.

Each task row should clearly show:

```text
Task
Project
Priority
Status
Deadline
Planner state
Documentation state
Actions
```

Main actions should be immediately accessible:

```text
Start
Pause
Open
Workspace
Comment
Complete
```

Secondary actions may use a compact menu.

## Start task behavior

When a user presses Start:

use the real Bitrix Start action.

The task becomes In Progress.

A future task that is manually started must immediately become eligible for TODAY'S planner even if its deadline is tomorrow or later.

Starting a future task MUST NOT require a justification.

Example:

```text
Deadline: next week
Status: waiting
→ not in today's planner

User presses Start
→ status In Progress
→ appears in today's planner
```

## Pause behavior

For an In Progress task whose deadline is NOT today and which is NOT overdue, allow:

```text
Pause
```

Use Bitrix's native pause/waiting behavior when available.

Paused future tasks should disappear from today's planner.

Pause requires NO justification.

Do not allow this shortcut for overdue tasks.

Do not treat pause as completion.

## 8-hour Today Planner

Default planner capacity:

```text
480 minutes
```

Configurable later if desired.

The planner includes:

1. unfinished tasks due today
2. overdue active tasks
3. future tasks manually started by the user

Do NOT include all future queued tasks.

Allocate time automatically.

Use weighting based on:

- Bitrix priority
- deadline urgency
- In Progress state
- Bitrix estimated time when available

Use 15-minute increments.

The allocation must total exactly the configured daily capacity.

Allow:

```text
+15
-15
move up
move down
```

Planner adjustments may be stored in browser localStorage rather than SQLite.

Priority should visibly influence planning.

High-priority work should be easy to identify.

## Missed deadline workflow

Justification is required ONLY when the actual task deadline has passed.

Starting, pausing or working on future tasks does not require justification.

When the deadline passes and the task remains incomplete:

prompt:

```text
سبب التأخير
Why was this task not completed by the deadline?
```

Provide quick choices such as:

```text
بانتظار مدخلات
عائق تقني
تغير نطاق العمل
الحاجة إلى تحقق إضافي
اعتماد من جهة أخرى
أخرى
```

Require meaningful text.

Post the justification as a Bitrix task comment.

Save a small marker inside:

```text
05_Evidence/.deadline_justification.json
```

Do not use SQLite for these task records.

If the supervisor later changes the deadline and the NEW deadline is missed, ask for a new justification.

## Task completion

Before completing a task, check documentation readiness.

Require at least:

```text
Objective
Work performed
Validation
Result / Deliverables
```

Before sending the Bitrix Complete command, first post a Bitrix comment containing:

```text
Result
Workspace root
Employee task workspace
Documentation file
```

Example:

```text
Work completed.

Result:
VAT reconciliation completed and validated.

Workspace:
\\server\TeamWork\Employee C\VAT\1234 - Reconciliation

Documentation:
\\server\TeamWork\Employee C\VAT\1234 - Reconciliation\1234 - Reconciliation.md
```

If posting this comment fails:

DO NOT complete the task.

Task completion should therefore behave transactionally.

## Comments / discussion

Both My Tasks and Supervisor views need expandable discussion history.

Do not show only one latest comment.

When the user expands Discussion:

fetch recent Bitrix comments lazily.

Display:

```text
author
timestamp
comment
```

Preserve multiline formatting.

Load perhaps 10 initially.

Provide:

```text
Show more
Refresh
```

Support up to approximately 50 recent comments.

Use short-lived caching.

Invalidate the cache whenever OMI Bitrix itself posts a comment.

Comments must work in both employee and supervisor views.

## Supervisor view

A person is NOT globally marked as supervisor.

A task appears in Supervisor when the current Bitrix user is related to it as:

- creator
- observer
- auditor/other supervisory relationship exposed by Bitrix

Separate this completely from My Tasks because supervisors may have their own assigned tasks.

Supervisor dashboard should show:

```text
Pending approval
Late tasks
At-risk tasks
High priority
Employee workload
Recent justifications
```

Keep it compact and quick to scan.

## Bitrix permissions

Do not assume that a creator can perform every action.

Where possible, inspect the task's allowed actions/permissions.

Enable supervisor controls only when Bitrix allows that action.

Examples:

```text
Approve
Return for revision
Edit
Change deadline
Change priority
Reassign
Delegate
Comment
```

Do not expose a button that will certainly fail.

## Pending approval

Support Bitrix tasks waiting for approval/review.

Supervisor can:

```text
Approve
Return for revision
```

Allow supervisor feedback text.

Post feedback as a task comment.

## Supervisor assessment

The company's evaluation model has TWO dimensions.

Delivery:

```text
On-time delivery
Late delivery
```

Performance:

```text
5 - Significantly exceeds expectations
4 - Completed task successfully
3 - Meets minimal requirements
2 - Needs more supervision
1 - Task not completed
```

Search Bitrix task fields dynamically.

Use the Bitrix API to inspect standard and custom fields.

If equivalent company custom fields exist:

write the actual value to those fields.

Do not hard-code assumed custom-field IDs.

If they do not exist:

preserve the assessment in a structured task comment and the supervisor report.

Do not pretend standard Bitrix MARK is a five-point system if it is not.

## Supervisor deadline control

Where Bitrix permissions allow, supervisor may:

- change deadline
- extend deadline
- replan
- modify priority

After changing the deadline:

refresh planner/task state.

Make priority a strong visual and planning signal for employees.

## Reassignment

Supervisor can reassign a task to another employee where permitted.

Fetch team/project members from Bitrix.

Before reassignment show:

```text
employee
active tasks
tasks due today
high-priority tasks
estimated workload
```

This allows informed reassignment.

After reassignment:

update workspace ownership safely.

Do not delete documentation.

Do not overwrite an existing destination folder.

## Search

Create fast global task search.

Search by:

```text
task ID
task title
employee
project/group
status
priority
deadline
```

Search My Tasks and Supervisor tasks.

Debounce input.

Do not make an API call on every keystroke if the required task set is already cached.

## Similarity analysis

For upcoming/current tasks, identify potentially related or duplicate work.

Use lightweight local similarity.

No external AI service is required.

Support Arabic and English.

Normalize:

- punctuation
- Arabic character variants
- whitespace
- common generic task words
- English capitalization

Compare task titles/descriptions.

Use a reasonable standard-library algorithm such as:

```text
difflib.SequenceMatcher
token overlap / Jaccard
combined score
```

Show something like:

```text
Possible related task
82% similarity
```

Use this in both employee and supervisor workflows where useful.

Do not make similarity analysis computationally expensive.

## Team statistics

Supervisor should see useful team statistics:

```text
employee
assigned tasks
in progress
completed
overdue
due today
high priority
pending approval
on-time deliveries
late deliveries
average assessment
```

Do not create meaningless vanity charts.

Prefer useful operational numbers and compact visualizations.

## Excel team report

Supervisor can export `.xlsx`.

If avoiding external dependencies, generate valid OOXML directly.

If using an Excel package is necessary, isolate that dependency clearly.

Workbook sheets:

```text
Team Summary
Task Detail
Late Justifications
```

Task Detail should include:

```text
Task ID
Task
Employee
Project
Priority
Status
Deadline
Completed Date
Delivery Status
Performance Assessment
Supervisor Feedback
Workspace
Documentation
```

Late Justifications should include:

```text
Employee
Task
Original Deadline
Current Deadline
Justification
Date Submitted
Supervisor
```

The generated workbook should have professional neutral styling.

## Languages

Full support:

```text
English
العربية
```

Arabic MUST feel naturally written by a Saudi/Gulf enterprise software team.

Absolutely avoid awkward literal Google-Translate-style Arabic.

Examples of preferred wording:

```text
مهامي
مهام الفريق
قيد التنفيذ
بانتظار التنفيذ
بانتظار المراجعة
الموعد النهائي
الأولوية
سبب التأخير
إعادة التخطيط
إعادة الإسناد
بدء المهمة
إيقاف مؤقت
اعتماد المهمة
إعادتها للتعديل
التوثيق
المخرجات
آخر التحديثات
```

Do not translate technical names unnecessarily.

Keep:

```text
SQL
Python
Alteryx
Power BI
Bitrix24
Excel
```

as recognizable technical terms.

RTL must be a complete layout direction change, not merely text-align:right.

However these should remain LTR:

```text
Windows paths
SQL
task IDs
filenames
timestamps
URLs
Bitrix webhook
```

## UI redesign from zero

Create a completely new UI.

Do not imitate ZATCA or Bitrix.

Do not use the previous purple design.

Use a professional BLUE-based productivity design.

Think:

```text
deep blue
clear blue
sky accents
neutral grays
subtle semantic green/red/amber
```

Support excellent:

```text
Light Mode
Dark Mode
```

Default to OS preference.

Remember manual selection in localStorage.

Dark mode must be designed independently, not simply inverted.

## Typography

Use system fonts only.

Preferred English/Latin stack:

```css
font-family:
    "Segoe UI Variable",
    "Segoe UI",
    "Aptos",
    system-ui,
    sans-serif;
```

For Arabic ensure a natural Windows-safe fallback, for example:

```css
Tahoma,
"Segoe UI",
Arial,
sans-serif
```

Typography must be compact, highly readable and appropriate for an operations dashboard.

## UI philosophy

The application should feel like a fast operating console.

Use FEWER CARDS.

Avoid:

```text
card inside card
huge rounded boxes
excessive shadows
oversized empty space
dashboard template appearance
```

Prefer:

- clear surfaces
- compact task rows
- sticky toolbar where appropriate
- information-dense tables
- thin dividers
- quick actions
- status pills used sparingly
- progressive disclosure
- expandable details
- good typography hierarchy

The most common actions must require the fewest clicks.

## Dashboard

Top area should provide a quick operational summary.

Example:

```text
Today
7 tasks

3 in progress
2 due today
1 overdue
1 pending review
```

Then:

```text
Today Planner
My Queue
Supervisor Attention
```

Do not duplicate the same information repeatedly.

## Responsive design

This must be truly responsive.

Desktop:

```text
left sidebar
dense workspace
wide tables
```

Tablet:

```text
compact navigation
2-column layouts where possible
```

Mobile:

```text
bottom navigation
single-column task rows
large touch targets
no accidental horizontal overflow
```

Task actions should become a sensible grid on small screens.

Supervisor controls should stack cleanly.

Dialogs must never exceed viewport size.

Tables may use controlled horizontal scrolling where necessary.

Test layouts around:

```text
320px
375px
430px
768px
1024px
1366px
1920px
```

Also account for browser zoom around 125% and 150%.

## Focus quotes

At the top of the app include a small unobtrusive rotating focus message.

Examples English:

```text
Finish the next useful thing.
Make progress visible.
Document while the context is fresh.
Close the loop before moving on.
Protect your focus.
```

Arabic should be independently written naturally, for example:

```text
أنهِ الخطوة المفيدة التالية.
خل تقدمك واضح.
وثّق العمل والمعلومة ما زالت حاضرة.
أغلق المهمة قبل الانتقال لغيرها.
ركّز على ما يحرّك العمل فعلاً.
```

Rotate locally every 45–60 seconds.

Allow manual next quote.

Do not fetch quotes from the internet.

## Application branding

Application name:

```text
OMI Bitrix
```

This is fixed branding.

Do not allow normal users to rename it from Settings.

## Settings

Settings should remain simple.

Sections:

```text
Profile
Bitrix Connection
Projects & Groups
Workspace
Planner
Language
Appearance
Diagnostics
```

Project settings must support BOTH:

```text
Fetch projects/groups
Manual Project/Group IDs
```

Workspace settings:

```text
Storage Mode:
- Shared Folder
- Obsidian Vault
- Local Folder
- Network Share

Root Path:
[ Browse ] [ Test ]

Preview:
Root / Bitrix Work / Employee / Project / Task
```

Add a "Test Folder" action.

It should check:

- path exists or can be created
- read permission
- write permission
- Unicode filename support
- long path handling

Do not permanently leave test files behind.

## Security

Never expose one user's Bitrix webhook to another browser profile.

Never render webhook secrets back into normal pages unnecessarily.

Do not log full webhook URLs.

Do not include webhook secrets in generated documentation.

Use local-only/session-safe CSRF protection for mutation forms if practical without introducing unnecessary frameworks.

Escape task/comment content in HTML.

Do not execute file contents.

## Reliability

Every Bitrix mutation should have clear success/error handling.

For example:

```text
Start failed
Pause failed
Comment failed
Deadline update failed
Approval failed
```

Do not silently ignore failures.

Important state-changing actions should refresh only the affected data where possible rather than reloading the entire application.

Use sensible HTTP timeouts.

Return actionable error messages.

## Diagnostics

Settings should include a compact diagnostics section:

```text
Bitrix connection      OK
Current Bitrix user    Employee C
Projects loaded        6
Workspace access       OK
Write test             OK
API latency            184 ms
```

Do not expose sensitive data.

## Development quality

Use:

- type hints where useful
- docstrings only where helpful
- small functions
- centralized Bitrix request handling
- centralized path handling
- centralized translations
- centralized configuration access

Avoid giant 2,000-line `app.py`.

Do not duplicate REST logic across routes.

Create one reusable Bitrix client.

## Before delivering

Perform actual automated validation.

At minimum:

1. Python compilation
2. Flask route validation
3. Jinja template parsing
4. JavaScript syntax validation
5. translation-key coverage
6. planner totals exactly 480 minutes
7. future queued task excluded
8. future started task included
9. future paused task excluded
10. pause does not require justification
11. overdue task does require justification
12. workspace creation with Arabic names
13. workspace creation with spaces
14. UNC network path normalization
15. very long network path handling
16. employee-separated folders
17. reassignment workspace safety
18. comment pagination
19. English/Arabic similarity test
20. Excel workbook validity
21. responsive CSS sanity
22. ZIP/package integrity

Create a useful README containing:

```text
installation
first run
Bitrix webhook creation
multi-user hosting
Windows firewall note
network share considerations
UNC path examples
folder permissions
backup
upgrading
troubleshooting
```

## Important implementation philosophy

This application is meant to make work faster.

Every feature should answer one of these:

```text
What should I work on now?
What is blocked?
What is late?
What does my supervisor need?
Where are the work files?
Is the work documented?
Can I close the task?
How is the team doing?
```

If a UI element does not help answer one of those questions, reconsider whether it is needed.

Prioritize:

```text
speed
clarity
low maintenance
few dependencies
safe automation
fast actions
natural Arabic
excellent Windows/network-share support
```

Build the complete working application, not merely mockups or pseudocode.

When implementation decisions are uncertain because Bitrix24 REST behavior may have changed, consult the current official Bitrix24 REST/API documentation before coding that portion.

At the end, provide the complete source project as a ZIP and a concise README.