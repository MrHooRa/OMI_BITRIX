"""Tiny dependency-free UI localization for OMI Bitrix."""

TRANSLATIONS = {
    "en": {
        "language_name": "English",
        "switch_language": "العربية",
        "dashboard": "Dashboard",
        "settings": "Settings",
        "brand_subtitle": "Bitrix + Workspace",
        "local_first": "Local-first",
        "local_first_copy": "Config in SQLite. Every task lives once inside your shared Obsidian vault.",
        "delivery_queue": "YOUR DELIVERY QUEUE",
        "hero_title": "Good work starts with less friction.",
        "selected_projects_count": "{count} selected projects",
        "sync_bitrix": "↻ Sync Bitrix",
        "overdue": "Overdue",
        "needs_update": "needs an update",
        "ending_today": "Ending today",
        "today_focus": "Today's focus",
        "due_today_or_started": "due today + started tasks",
        "focus_8h": "8-hour focus plan",
        "due_72h": "Due ≤72h",
        "coming_next": "coming next",
        "active_tasks": "Active tasks",
        "selected_projects": "selected projects",
        "last_sync_issue": "Last sync issue: {error}",
        "today_8h": "TODAY · 8 HOURS",
        "focus_planner": "Focus planner",
        "planner_copy": "Tasks due on {date}, plus any task you have already started in Bitrix. Starting a future task pulls it into today's plan without changing its deadline.",
        "planned": "planned",
        "reset_auto_plan": "Reset auto-plan",
        "high_priority": "High priority",
        "in_progress": "In progress",
        "started_into_today": "Pulled into today",
        "deadline": "Deadline",
        "move_earlier": "Move earlier",
        "move_later": "Move later",
        "less_15": "Give this task 15 minutes less",
        "more_15": "Give this task 15 minutes more",
        "start": "Start",
        "pause": "Pause",
        "pause_task": "Pause task",
        "pause_future_hint": "Pause future work and remove it from today's plan until you start it again.",
        "pause_future_only": "Pause is available only for an in-progress task whose deadline is after today or has no deadline.",
        "task_paused_success": "Task paused in Bitrix24 and removed from today's plan.",
        "update": "Update",
        "cant_finish": "Can't finish",
        "no_tasks_today": "No tasks end today",
        "no_focus_tasks": "Nothing planned yet",
        "start_task_to_plan": "Start any queued task below and it will join today's 8-hour planner—even when its deadline is later.",
        "capacity_clear": "Your 8-hour capacity is clear. Upcoming work remains in the queue below.",
        "assigned_to_me": "Tasks assigned to me",
        "sorted_deadline": "Sorted by deadline. Workspace creation happens automatically when enabled.",
        "last_sync": "Last sync: {value}",
        "not_yet": "not yet",
        "due_within_72h": "Due within 72h",
        "no_deadline": "No deadline",
        "workspace_ready": "Workspace ready",
        "workspace_not_created": "Workspace not created",
        "docs": "docs",
        "open": "Open",
        "folder": "Folder",
        "open_file_explorer": "Open task folder in File Explorer",
        "justification_required": "Justification required",
        "justified": "Justified",
        "no_active_tasks": "No active tasks in your selected projects",
        "empty_queue_copy": "Sync again, or adjust project selection in Settings.",
        "bitrix_update": "BITRIX UPDATE",
        "progress_update": "Progress update",
        "quick_in_progress": "In progress",
        "quick_blocked": "Blocked",
        "quick_more_time": "Need more time",
        "quick_finalizing": "Finalizing",
        "msg_in_progress": "Work is in progress. No blocker at the moment.",
        "msg_blocked": "Work is in progress, but I have a blocker: ",
        "msg_more_time": "I need additional time to finish the task. Current status: ",
        "msg_finalizing": "The analysis is complete and I am finalizing documentation and output validation.",
        "write_update": "Write a concise task update…",
        "cancel": "Cancel",
        "post_bitrix": "Post to Bitrix24",
        "deadline_justification": "DEADLINE JUSTIFICATION",
        "why_miss_deadline": "Why will this task miss its deadline?",
        "delay_dialog_copy": "This is posted directly to the selected Bitrix24 task. It does not close the task.",
        "delay_placeholder": "Explain the reason clearly: dependency, data issue, blocker, changed scope, pending validation, stakeholder input…",
        "waiting_input": "Waiting for input",
        "technical_blocker": "Technical blocker",
        "scope_changed": "Scope changed",
        "validation_needed": "Validation needed",
        "justify_waiting": "Pending required data/input from another party. Current progress: ",
        "justify_technical": "A technical/data blocker is preventing completion: ",
        "justify_scope": "The scope changed and additional work is required: ",
        "justify_validation": "Additional validation/reconciliation is required before I can safely close the task: ",
        "post_justification": "Post justification to Bitrix24",
        "configuration": "CONFIGURATION",
        "settings_title": "Settings",
        "settings_copy": "Change the Bitrix connection, project scope, language, or the single shared Obsidian vault.",
        "webhook_root": "Bitrix24 incoming webhook root",
        "test_refresh": "Test & refresh projects",
        "shared_vault_root": "Shared Obsidian vault root",
        "vault_help": "This is both the shared work root and the Obsidian vault. No mirrored copy is created.",
        "app_name": "App name",
        "language": "Language",
        "sync_interval": "Sync interval",
        "planner_starts": "8-hour planner starts",
        "selected_bitrix_projects": "Selected Bitrix projects",
        "selected_projects_help": "Only tasks in checked projects are fetched.",
        "search_projects": "Search projects…",
        "select_all": "Select all",
        "clear": "Clear",
        "auto_scaffold": "Automatically create missing workspaces",
        "save_settings": "Save settings",
        "setup_title": "Set up OMI Bitrix",
        "first_run_setup": "FIRST-RUN SETUP",
        "setup_hero": "Connect Bitrix24 once.\nRemove the admin overhead.",
        "setup_intro": "Choose the projects you actually work on, then point the app at one shared folder that is also your Obsidian vault.",
        "bitrix_connection": "Bitrix24 connection",
        "bitrix_connection_help": "Use an incoming webhook with task + user + social network/project permissions.",
        "incoming_webhook": "Incoming webhook root",
        "test_fetch_projects": "Test & fetch projects",
        "choose_projects": "Choose projects",
        "choose_projects_help": "Only tasks assigned to you inside these Bitrix24 projects will appear or auto-create folders.",
        "search_fetched": "Search fetched projects…",
        "test_to_fetch": "Test the Bitrix connection to fetch your projects.",
        "shared_obsidian_vault": "Shared Obsidian vault",
        "shared_obsidian_help": "One path only. This folder is both the team/shared work location and the Obsidian vault.",
        "shared_vault_path": "Shared vault root path",
        "vault_structure_help": "Tasks are created under Bitrix Work/<Project>/<Task>/. The task note and Input / Workflow / Queries / Output / Evidence folders all live together.",
        "sync_every": "Sync every",
        "save_launch": "Save configuration & launch cockpit",
        "back_dashboard": "← Dashboard",
        "start_in_bitrix": "Start in Bitrix",
        "pause_in_bitrix": "Pause in Bitrix",
        "open_task_folder": "Open task folder",
        "open_obsidian": "Open Obsidian",
        "documentation": "DOCUMENTATION",
        "document_before_close": "Close the task with evidence, not memory.",
        "ready": "ready",
        "objective": "Objective",
        "work_performed": "Work performed",
        "queries_logic": "Queries / business logic",
        "validation": "Validation",
        "result_deliverables": "Result / deliverables",
        "next_handover": "Next step / handover",
        "save_documentation": "Save documentation",
        "workspace": "WORKSPACE",
        "artifact_pulse": "Artifact pulse",
        "input": "Input",
        "workflow": "Workflow",
        "queries": "Queries",
        "output": "Output",
        "evidence": "Evidence",
        "shared_vault": "Shared vault",
        "task_folder_in_vault": "Task folder inside vault",
        "task_note": "Task note",
        "quick_update": "QUICK UPDATE",
        "keep_deadline_visible": "Keep the deadline visible.",
        "quick_update_placeholder": "What changed? Any blocker? What happens next?",
        "post_update": "Post update",
        "deadline_control": "DEADLINE CONTROL",
        "deadline_passed": "This deadline has passed.",
        "cant_finish_today": "Can't finish today?",
        "justification_already": "A deadline justification has already been posted for this deadline.",
        "overdue_requires_justification": "A justification is required. Post it to the Bitrix task before continuing work.",
        "today_justify_early": "If you already know the task will miss today's deadline, record the reason now instead of waiting until it becomes overdue.",
        "update_justification": "Update justification",
        "add_required_justification": "Add required justification",
        "cant_finish_before_deadline": "I can't finish before deadline",
        "finish": "FINISH",
        "finish_flow": "Document → post paths → complete.",
        "finish_copy": "Finishing first posts the shared-vault path, task folder, exact task-note path, and result into Bitrix24. If that comment cannot be posted, the task stays open.",
        "complete_in_bitrix": "Complete in Bitrix24",
        "finish_docs_first": "Finish the core documentation first",
        "required_fields": "Required: Objective, Work performed, Validation, Result.",
        "task_delay_copy": "This justification will be posted directly into the same Bitrix24 task comments. The task will remain open.",
        "sec": "sec",
        "min": "min",
        "members": "members",
        "untitled": "Untitled",
        "no_projects_returned": "No projects were returned for this webhook user.",
        "connected_as": "Connected as {name} · {count} projects fetched.",
        "could_not_fetch": "Could not fetch projects",
        "connecting": "Connecting to Bitrix24…",
        "connection_failed": "Connection failed",
        "fetching_projects": "Connected as {name} (#{id}). Fetching projects…",
        "bitrix_user": "Bitrix user",
        "justify_delay_prefix": "Justify delay · {title}",
        "bitrix_deadline": "Bitrix deadline: {deadline}",
        "deadline_unavailable": "Bitrix deadline not available",
        "hour_short": "h",
        "minute_short": "m",
    },
    "ar": {
        "language_name": "العربية",
        "switch_language": "English",
        "dashboard": "لوحة العمل",
        "settings": "الإعدادات",
        "brand_subtitle": "Bitrix + مساحة العمل",
        "local_first": "محلي وآمن",
        "local_first_copy": "الإعدادات فقط في SQLite، وكل مهمة لها نسخة واحدة داخل مستودع Obsidian المشترك.",
        "delivery_queue": "قائمة التنفيذ",
        "hero_title": "ركّز على إنجاز العمل، وخَلّ التنظيم على النظام.",
        "selected_projects_count": "{count} مشروع محدد",
        "sync_bitrix": "↻ مزامنة Bitrix",
        "overdue": "متأخرة",
        "needs_update": "تحتاج تحديثًا",
        "ending_today": "مستحقة اليوم",
        "today_focus": "تركيز اليوم",
        "due_today_or_started": "المستحقة اليوم + المهام التي بدأت بها",
        "focus_8h": "خطة تركيز لـ 8 ساعات",
        "due_72h": "خلال 72 ساعة",
        "coming_next": "القادمة بعد ذلك",
        "active_tasks": "المهام النشطة",
        "selected_projects": "ضمن المشاريع المحددة",
        "last_sync_issue": "مشكلة في آخر مزامنة: {error}",
        "today_8h": "اليوم · 8 ساعات",
        "focus_planner": "خطة اليوم",
        "planner_copy": "يعرض المهام المستحقة بتاريخ {date}، إضافة إلى أي مهمة بدأت تنفيذها في Bitrix حتى لو كان موعدها لاحقًا. بدء المهمة لا يغيّر موعدها النهائي.",
        "planned": "مخطط",
        "reset_auto_plan": "إعادة الخطة التلقائية",
        "high_priority": "أولوية عالية",
        "in_progress": "قيد التنفيذ",
        "started_into_today": "أُضيفت لخطة اليوم",
        "deadline": "الموعد النهائي",
        "move_earlier": "تقديم المهمة",
        "move_later": "تأخير المهمة",
        "less_15": "تقليل وقت المهمة 15 دقيقة",
        "more_15": "زيادة وقت المهمة 15 دقيقة",
        "start": "بدء",
        "pause": "إيقاف مؤقت",
        "pause_task": "إيقاف المهمة مؤقتًا",
        "pause_future_hint": "أوقف العمل المستقبلي مؤقتًا ليخرج من خطة اليوم، ويمكنك إعادته بمجرد بدء المهمة مرة أخرى.",
        "pause_future_only": "الإيقاف المؤقت متاح فقط للمهمة قيد التنفيذ إذا كان موعدها بعد اليوم أو بدون موعد نهائي.",
        "task_paused_success": "تم إيقاف المهمة مؤقتًا في Bitrix24 وإزالتها من خطة اليوم.",
        "update": "تحديث",
        "cant_finish": "لن أتمكن من الإنجاز",
        "no_tasks_today": "لا توجد مهام مستحقة اليوم",
        "no_focus_tasks": "لا توجد مهام في خطة اليوم حتى الآن",
        "start_task_to_plan": "ابدأ أي مهمة من القائمة أدناه وستدخل مباشرة في خطة الـ 8 ساعات، حتى لو كان موعدها النهائي في يوم لاحق.",
        "capacity_clear": "ساعات اليوم متاحة. ستجد المهام القادمة في القائمة أدناه.",
        "assigned_to_me": "المهام المسندة لي",
        "sorted_deadline": "مرتبة حسب الموعد النهائي، ويتم إنشاء مساحة العمل تلقائيًا عند تفعيل الخيار.",
        "last_sync": "آخر مزامنة: {value}",
        "not_yet": "لم تتم بعد",
        "due_within_72h": "مستحقة خلال 72 ساعة",
        "no_deadline": "بدون موعد نهائي",
        "workspace_ready": "مساحة العمل جاهزة",
        "workspace_not_created": "مساحة العمل لم تُنشأ بعد",
        "docs": "التوثيق",
        "open": "فتح",
        "folder": "المجلد",
        "open_file_explorer": "فتح مجلد المهمة في مستكشف الملفات",
        "justification_required": "يلزم توضيح سبب التأخير",
        "justified": "تم توضيح السبب",
        "no_active_tasks": "لا توجد مهام نشطة ضمن المشاريع المحددة",
        "empty_queue_copy": "جرّب المزامنة مرة أخرى أو عدّل المشاريع من الإعدادات.",
        "bitrix_update": "تحديث المهمة في Bitrix",
        "progress_update": "تحديث حالة المهمة",
        "quick_in_progress": "قيد التنفيذ",
        "quick_blocked": "يوجد عائق",
        "quick_more_time": "أحتاج وقتًا إضافيًا",
        "quick_finalizing": "اللمسات الأخيرة",
        "msg_in_progress": "العمل جارٍ حاليًا ولا توجد عوائق في الوقت الحالي.",
        "msg_blocked": "العمل جارٍ، لكن يوجد عائق يؤثر على الإنجاز: ",
        "msg_more_time": "أحتاج وقتًا إضافيًا لإكمال المهمة. الوضع الحالي: ",
        "msg_finalizing": "تم الانتهاء من التحليل، وأعمل حاليًا على استكمال التوثيق والتحقق النهائي من المخرجات.",
        "write_update": "اكتب تحديثًا مختصرًا وواضحًا عن المهمة…",
        "cancel": "إلغاء",
        "post_bitrix": "إرسال إلى Bitrix24",
        "deadline_justification": "توضيح سبب التأخير",
        "why_miss_deadline": "ما سبب عدم إمكانية إنهاء المهمة قبل الموعد؟",
        "delay_dialog_copy": "سيتم نشر التوضيح مباشرة في المهمة نفسها على Bitrix24، ولن يتم إغلاق المهمة.",
        "delay_placeholder": "اكتب السبب بوضوح، مثل: انتظار بيانات، عائق تقني، تغيير في النطاق، حاجة لمطابقة إضافية، أو انتظار رد من جهة أخرى…",
        "waiting_input": "بانتظار بيانات أو رد",
        "technical_blocker": "عائق تقني",
        "scope_changed": "تغيّر نطاق العمل",
        "validation_needed": "يحتاج تحققًا إضافيًا",
        "justify_waiting": "بانتظار بيانات أو مدخلات مطلوبة من جهة أخرى. التقدم الحالي: ",
        "justify_technical": "يوجد عائق تقني أو متعلق بالبيانات يمنع إكمال المهمة: ",
        "justify_scope": "تغيّر نطاق العمل وأصبحت المهمة تتطلب أعمالًا إضافية: ",
        "justify_validation": "تحتاج النتائج إلى تحقق أو مطابقة إضافية قبل إغلاق المهمة بشكل سليم: ",
        "post_justification": "إرسال التوضيح إلى Bitrix24",
        "configuration": "الإعدادات",
        "settings_title": "الإعدادات",
        "settings_copy": "عدّل اتصال Bitrix، نطاق المشاريع، اللغة، أو مسار Obsidian المشترك.",
        "webhook_root": "رابط Webhook الوارد من Bitrix24",
        "test_refresh": "اختبار الاتصال وتحديث المشاريع",
        "shared_vault_root": "مسار مستودع Obsidian المشترك",
        "vault_help": "هذا المسار هو مساحة العمل المشتركة ومستودع Obsidian في الوقت نفسه، ولا يتم إنشاء نسخة مكررة.",
        "app_name": "اسم التطبيق",
        "language": "اللغة",
        "sync_interval": "فترة المزامنة",
        "planner_starts": "بداية خطة الـ 8 ساعات",
        "selected_bitrix_projects": "مشاريع Bitrix المحددة",
        "selected_projects_help": "سيتم جلب المهام التابعة للمشاريع المحددة فقط.",
        "search_projects": "ابحث في المشاريع…",
        "select_all": "تحديد الكل",
        "clear": "إلغاء التحديد",
        "auto_scaffold": "إنشاء مساحة العمل تلقائيًا للمهام الجديدة",
        "save_settings": "حفظ الإعدادات",
        "setup_title": "إعداد OMI Bitrix",
        "first_run_setup": "الإعداد لأول مرة",
        "setup_hero": "اربط Bitrix24 مرة واحدة.\nوتخلّص من الأعمال الإدارية المتكررة.",
        "setup_intro": "حدّد المشاريع التي تعمل عليها فعليًا، ثم اختر مجلدًا مشتركًا واحدًا ليكون هو نفسه مستودع Obsidian ومساحة العمل.",
        "bitrix_connection": "الاتصال بـ Bitrix24",
        "bitrix_connection_help": "استخدم Incoming Webhook بصلاحيات المهام والمستخدم والمشاريع/مجموعات العمل.",
        "incoming_webhook": "رابط Incoming Webhook",
        "test_fetch_projects": "اختبار الاتصال وجلب المشاريع",
        "choose_projects": "اختر المشاريع",
        "choose_projects_help": "لن تظهر إلا المهام المسندة لك داخل المشاريع التي تحددها هنا، وهي فقط التي سيُنشأ لها مجلد تلقائيًا.",
        "search_fetched": "ابحث في المشاريع التي تم جلبها…",
        "test_to_fetch": "اختبر اتصال Bitrix أولًا ليتم جلب المشاريع المتاحة لك.",
        "shared_obsidian_vault": "مستودع Obsidian المشترك",
        "shared_obsidian_help": "مسار واحد فقط: هو موقع العمل المشترك وهو نفسه مستودع Obsidian.",
        "shared_vault_path": "مسار المستودع المشترك",
        "vault_structure_help": "تُنشأ المهام داخل Bitrix Work/<Project>/<Task>/. ملف التوثيق ومجلدات Input / Workflow / Queries / Output / Evidence كلها داخل مجلد المهمة نفسه.",
        "sync_every": "المزامنة كل",
        "save_launch": "حفظ الإعدادات وفتح لوحة العمل",
        "back_dashboard": "→ لوحة العمل",
        "start_in_bitrix": "بدء المهمة في Bitrix",
        "pause_in_bitrix": "إيقاف مؤقت في Bitrix",
        "open_task_folder": "فتح مجلد المهمة",
        "open_obsidian": "فتح في Obsidian",
        "documentation": "التوثيق",
        "document_before_close": "وثّق العمل قبل إغلاق المهمة.",
        "ready": "جاهز",
        "objective": "الهدف",
        "work_performed": "ما تم إنجازه",
        "queries_logic": "الاستعلامات ومنطق العمل",
        "validation": "التحقق والمطابقة",
        "result_deliverables": "النتيجة والمخرجات",
        "next_handover": "الخطوة التالية / التسليم",
        "save_documentation": "حفظ التوثيق",
        "workspace": "مساحة العمل",
        "artifact_pulse": "ملخص الملفات",
        "input": "المدخلات",
        "workflow": "سير العمل",
        "queries": "الاستعلامات",
        "output": "المخرجات",
        "evidence": "الأدلة",
        "shared_vault": "المستودع المشترك",
        "task_folder_in_vault": "مجلد المهمة داخل المستودع",
        "task_note": "ملف توثيق المهمة",
        "quick_update": "تحديث سريع",
        "keep_deadline_visible": "حدّث حالة المهمة بدون ما يضيع الموعد من بالك.",
        "quick_update_placeholder": "ما الذي تم؟ هل يوجد عائق؟ وما الخطوة التالية؟",
        "post_update": "إرسال التحديث",
        "deadline_control": "إدارة الموعد النهائي",
        "deadline_passed": "تجاوزت المهمة موعدها النهائي.",
        "cant_finish_today": "لن تتمكن من إنهائها اليوم؟",
        "justification_already": "تم بالفعل نشر توضيح سبب التأخير لهذا الموعد النهائي.",
        "overdue_requires_justification": "يلزم توضيح سبب التأخير ونشره في مهمة Bitrix قبل متابعة العمل.",
        "today_justify_early": "إذا كنت تعرف من الآن أن المهمة لن تنتهي اليوم، وثّق السبب الآن بدل الانتظار إلى ما بعد الموعد.",
        "update_justification": "تحديث سبب التأخير",
        "add_required_justification": "إضافة التوضيح المطلوب",
        "cant_finish_before_deadline": "لن أتمكن من الإنجاز قبل الموعد",
        "finish": "إنهاء المهمة",
        "finish_flow": "وثّق ← أرسل المسارات ← أغلق المهمة.",
        "finish_copy": "عند الإنهاء، يرسل النظام أولًا مسار المستودع المشترك ومجلد المهمة وملف التوثيق والنتيجة إلى Bitrix24. إذا تعذر نشر التعليق، تبقى المهمة مفتوحة.",
        "complete_in_bitrix": "إنهاء المهمة في Bitrix24",
        "finish_docs_first": "أكمل التوثيق الأساسي أولًا",
        "required_fields": "المطلوب: الهدف، ما تم إنجازه، التحقق والمطابقة، والنتيجة.",
        "task_delay_copy": "سيتم نشر هذا التوضيح مباشرة ضمن تعليقات المهمة نفسها في Bitrix24، وستبقى المهمة مفتوحة.",
        "sec": "ثانية",
        "min": "دقيقة",
        "members": "عضو",
        "untitled": "بدون اسم",
        "no_projects_returned": "لم يتم العثور على مشاريع متاحة لهذا المستخدم عبر الـ Webhook.",
        "connected_as": "تم الاتصال باسم {name} · تم جلب {count} مشروع.",
        "could_not_fetch": "تعذر جلب المشاريع",
        "connecting": "جارٍ الاتصال بـ Bitrix24…",
        "connection_failed": "تعذر الاتصال",
        "fetching_projects": "تم الاتصال باسم {name} (#{id})، وجارٍ جلب المشاريع…",
        "bitrix_user": "مستخدم Bitrix",
        "justify_delay_prefix": "توضيح التأخير · {title}",
        "bitrix_deadline": "الموعد النهائي في Bitrix: {deadline}",
        "deadline_unavailable": "الموعد النهائي غير متاح في Bitrix",
        "hour_short": "س",
        "minute_short": "د",
    },
}


# Supervisor, search, shared-folder browser and multi-employee additions.
TRANSLATIONS["en"].update({
    "my_tasks": "My tasks",
    "supervisor_view": "Supervisor",
    "supervisor_dashboard": "Supervisor dashboard",
    "supervisor_copy": "Tasks you created or observe are kept separate from your own assigned work.",
    "employee_name": "Employee name",
    "employee_name_help": "Used to create a dedicated folder under Bitrix Work. Keep it close to your Bitrix display name so supervisors can locate the same shared workspace.",
    "browse": "Browse",
    "choose_folder": "Choose shared vault folder",
    "folder_browser_help": "Browse folders on the machine running OMI Bitrix. You can still type a mapped drive or UNC path manually.",
    "use_this_folder": "Use this folder",
    "go_up": "Up",
    "folder_roots": "Locations",
    "loading_folders": "Loading folders…",
    "no_subfolders": "No subfolders here.",
    "search_tasks": "Search tasks, project, ID or employee…",
    "search": "Search",
    "clear_search": "Clear search",
    "similarity_analysis": "Upcoming task similarity",
    "similarity_copy": "Highlights likely duplicate or related tasks using local title/description similarity. No external AI service is used.",
    "similar": "similar",
    "related_tasks": "Related tasks",
    "no_related_tasks": "No strong similarities found in your current upcoming queue.",
    "observed_created": "Created / observed tasks",
    "observed_created_copy": "Creator = approval authority. Observer = visibility and comments. Your own assigned tasks remain in My tasks.",
    "pending_review": "Pending review",
    "waiting": "Waiting",
    "deferred": "Deferred",
    "creator": "Creator",
    "observer": "Observer",
    "creator_observer": "Creator + observer",
    "employee_progress": "Employee progress",
    "late_justifications": "Late justifications",
    "no_justification": "No justification recorded in the shared workspace",
    "review_task": "Review task",
    "approve_close": "Approve & close",
    "return_revision": "Return for revision",
    "supervisor_feedback": "Supervisor feedback",
    "feedback_placeholder": "Write a short, useful note for the employee…",
    "rating": "Rating",
    "rating_5": "5 — Completed successfully",
    "rating_4": "4 — Strong completion",
    "rating_3": "3 — Meets minimum requirements",
    "rating_2": "2 — Needs improvement",
    "rating_1": "1 — Requires rework",
    "native_mark_note": "The exact 1–5 score is posted as a Bitrix comment. Bitrix's native task mark is still positive / negative / unrated.",
    "cannot_approve_observer": "Observer — view/comment only",
    "workspace_employee": "Employee workspace",
    "assigned_count": "{count} assigned to me",
    "supervisor_count": "{count} created/observed",
    "profile_note": "No login is used. This browser keeps its own employee configuration while task roles come from Bitrix24.",
    "no_supervisor_tasks": "No created or observed tasks in the selected projects.",
    "review_queue": "Review queue",
    "team_active": "Team active",
    "team_overdue": "Team overdue",
    "team_justified": "Late with justification",
    "open_workspace": "Open workspace",
    "status": "Status",
    "responsible": "Responsible",
    "task_role": "Your role",
    "view_employee_docs": "View employee files",
})

TRANSLATIONS["ar"].update({
    "my_tasks": "مهامي",
    "supervisor_view": "إشراف الفريق",
    "supervisor_dashboard": "لوحة إشراف الفريق",
    "supervisor_copy": "المهام التي أنشأتها أو تتابعها منفصلة تمامًا عن المهام المسندة لك شخصيًا.",
    "employee_name": "اسم الموظف",
    "employee_name_help": "يُستخدم لإنشاء مجلد مستقل داخل Bitrix Work. يفضّل أن يكون مطابقًا أو قريبًا من اسمك في Bitrix حتى يصل المشرف إلى نفس مساحة العمل المشتركة.",
    "browse": "استعراض",
    "choose_folder": "اختيار مجلد المستودع المشترك",
    "folder_browser_help": "يعرض المجلدات الموجودة على الجهاز الذي يشغّل OMI Bitrix. ويمكنك أيضًا كتابة مسار قرص مشترك أو UNC يدويًا.",
    "use_this_folder": "استخدام هذا المجلد",
    "go_up": "رجوع للمجلد الأعلى",
    "folder_roots": "المواقع",
    "loading_folders": "جارٍ تحميل المجلدات…",
    "no_subfolders": "لا توجد مجلدات فرعية هنا.",
    "search_tasks": "ابحث باسم المهمة أو المشروع أو الرقم أو الموظف…",
    "search": "بحث",
    "clear_search": "مسح البحث",
    "similarity_analysis": "تشابه المهام القادمة",
    "similarity_copy": "يكشف المهام المتقاربة أو المحتمل تكرارها اعتمادًا على العنوان والوصف محليًا، بدون إرسال البيانات إلى أي خدمة ذكاء اصطناعي خارجية.",
    "similar": "تشابه",
    "related_tasks": "مهام مرتبطة",
    "no_related_tasks": "لم يظهر تشابه قوي بين المهام القادمة حاليًا.",
    "observed_created": "المهام التي أنشأتها أو تتابعها",
    "observed_created_copy": "منشئ المهمة يملك الاعتماد، بينما المراقب للمتابعة والتعليق. مهامك الشخصية تبقى في قسم مهامي.",
    "pending_review": "بانتظار المراجعة",
    "waiting": "بانتظار البدء",
    "deferred": "مؤجلة",
    "creator": "منشئ المهمة",
    "observer": "مراقب",
    "creator_observer": "منشئ ومراقب",
    "employee_progress": "تقدم الموظفين",
    "late_justifications": "مبررات التأخير",
    "no_justification": "لا يوجد مبرر تأخير مسجل في مساحة العمل المشتركة",
    "review_task": "مراجعة المهمة",
    "approve_close": "اعتماد وإغلاق",
    "return_revision": "إعادة للاستكمال",
    "supervisor_feedback": "ملاحظة المشرف",
    "feedback_placeholder": "اكتب ملاحظة قصيرة وواضحة للموظف…",
    "rating": "التقييم",
    "rating_5": "5 — أُنجزت بنجاح",
    "rating_4": "4 — إنجاز جيد جدًا",
    "rating_3": "3 — يفي بالحد الأدنى من المتطلبات",
    "rating_2": "2 — يحتاج إلى تحسين",
    "rating_1": "1 — يحتاج إلى إعادة عمل",
    "native_mark_note": "يتم حفظ تقييم 1–5 كاملًا في تعليق Bitrix. أما تقييم المهمة الأصلي في Bitrix فهو إيجابي / سلبي / بدون تقييم فقط.",
    "cannot_approve_observer": "مراقب — متابعة وتعليق فقط",
    "workspace_employee": "مساحة عمل الموظف",
    "assigned_count": "{count} مهمة مسندة لي",
    "supervisor_count": "{count} مهمة أنشأتها/أتابعها",
    "profile_note": "لا يوجد نظام دخول. هذا المتصفح يحتفظ بإعدادات الموظف الخاصة به، بينما دورك في كل مهمة يأتي مباشرة من Bitrix24.",
    "no_supervisor_tasks": "لا توجد مهام أنشأتها أو تتابعها ضمن المشاريع المحددة.",
    "review_queue": "بانتظار الاعتماد",
    "team_active": "مهام الفريق النشطة",
    "team_overdue": "متأخرة لدى الفريق",
    "team_justified": "متأخرة مع مبرر",
    "open_workspace": "فتح مساحة العمل",
    "status": "الحالة",
    "responsible": "المسؤول",
    "task_role": "دورك",
    "view_employee_docs": "عرض ملفات الموظف",
})



# OMI Bitrix team/supervisor expansion. These are deliberately written as
# normal workplace Arabic rather than literal English translations.
TRANSLATIONS["en"].update({
    "global_search": "Search",
    "search_everything": "Search across my tasks and team tasks",
    "search_scope_all": "All roles",
    "search_scope_mine": "Assigned to me",
    "search_scope_supervisor": "Created / observed",
    "search_results": "Task search",
    "search_hint": "Search by title, ID, project, employee or description. Related-task similarity is calculated locally.",
    "no_search_results": "No matching tasks found.",
    "role_assignee": "Assignee",
    "role_creator": "Creator",
    "role_observer": "Observer",
    "roles": "My role on this task",
    "supervisor_scope_only": "This task is not in your creator/observer scope.",
    "assignee_action_only": "This action is available only when you are the task assignee.",
    "no_deadline_permission": "Bitrix24 does not allow you to change this task's deadline.",
    "no_edit_permission": "Bitrix24 does not allow you to edit this task.",
    "no_reassign_permission": "Bitrix24 does not allow you to reassign this task.",
    "no_review_permission": "Bitrix24 does not allow you to approve/return this task.",
    "choose_replan_change": "Choose a new deadline and/or priority.",
    "choose_employee": "Choose an employee.",
    "employee_not_in_project": "The selected employee is not a member of this Bitrix project.",
    "not_pending_review": "This task is not currently pending approval in Bitrix24.",
    "feedback_required_return": "Write a useful comment before returning the task for revision.",
    "employee_workspace_missing": "The employee workspace has not been created in the shared vault yet.",
    "employee_note_missing": "The employee documentation note has not been created yet.",
    "team_dashboard": "Team oversight",
    "team_dashboard_copy": "A separate view for tasks you created or observe. Your own assigned queue stays in My tasks—even when you are also a supervisor.",
    "my_work": "My tasks",
    "team_work": "Team oversight",
    "export_excel": "Export Excel report",
    "team_statistics": "Team statistics",
    "priority_load": "Priority load",
    "priority_load_help": "Simple workload signal: High=3, Medium=2, Low=1 for open tasks.",
    "high_priority_tasks": "High priority",
    "late_tasks": "Late tasks",
    "justified_late": "Late + justified",
    "completed_recent": "Completed",
    "pending_approval": "Pending approval",
    "pending_approval_copy": "Work submitted by employees and waiting for creator approval.",
    "active_team_tasks": "Active team tasks",
    "active_team_copy": "Use deadline, priority and reassignment to steer work without mixing it with your personal queue.",
    "recent_completed": "Recently completed",
    "recent_completed_copy": "Included for team statistics and the Excel report.",
    "replan": "Replan",
    "replan_task": "Replan task",
    "new_deadline": "New deadline",
    "priority": "Priority",
    "priority_low": "Low",
    "priority_medium": "Medium",
    "priority_high": "High",
    "replan_reason": "Reason / direction to employee",
    "replan_reason_placeholder": "Why is the deadline or priority changing?",
    "save_replan": "Update task",
    "reassign": "Reassign",
    "reassign_task": "Reassign task",
    "assign_to": "Assign to",
    "reassign_reason": "Reason for reassignment",
    "reassign_reason_placeholder": "Workload, specialization, leave, dependency…",
    "confirm_reassign": "Reassign in Bitrix24",
    "review_and_close": "Review employee delivery",
    "delivery_timing": "Delivery timing",
    "delivery_on_time": "On-time delivery",
    "delivery_late": "Late delivery",
    "outcome_5": "Significantly exceeds expectations",
    "outcome_4": "Completed task successfully",
    "outcome_3": "Meets minimal requirements",
    "outcome_2": "Needs more supervision",
    "outcome_1": "Task not completed",
    "review_feedback": "Comment to employee",
    "review_feedback_placeholder": "What was good, what should change, or what is needed next?",
    "approve": "Approve & close",
    "return_employee": "Return for revision",
    "company_field_detected": "Company review fields detected in this Bitrix portal.",
    "company_field_fallback": "No matching company review custom fields were detected. The full assessment will still be written to the task comment and report.",
    "late_justification": "Late-task justification",
    "no_late_justification": "No justification found yet.",
    "supervisor_can_comment": "You can still comment even if Bitrix does not grant edit/approval rights on this task.",
    "assigned_and_supervisor_note": "Roles are task-based. The same person may be an assignee here and a supervisor on other tasks.",
    "team_members": "Team members",
    "report_window": "Completed-task report window",
    "days": "days",
    "folder_browser": "Folder browser",
    "folder_browser_select": "Select this folder",
    "folder_browser_close": "Close",
    "folder_browser_empty": "No readable subfolders here.",
    "folder_browser_server_note": "This browses folders on the Windows/server machine running OMI Bitrix; it does not upload files.",
    "employee_folder_preview": "Employee workspace folder",
    "employee_folder_structure": "Tasks are stored as Vault / Bitrix Work / Employee / Project / Task.",
    "supervisor_relationship": "Supervisor relationship",
    "observed_only": "Observer",
    "creator_control": "Creator / approval owner",
    "permission_limited": "Bitrix permissions limit this action",
    "similarity_score": "{score}% related",
    "related_upcoming": "Related upcoming work",
    "related_upcoming_copy": "Useful for spotting repeated requests, reusable SQL/Alteryx work, or tasks that should be handled together.",
    "open_team_workspace": "Open employee workspace",
    "status_waiting": "Waiting",
    "status_in_progress": "In progress",
    "status_pending": "Pending approval",
    "status_completed": "Completed",
    "status_deferred": "Deferred",
})

TRANSLATIONS["ar"].update({
    "global_search": "البحث",
    "search_everything": "البحث في مهامي ومهام الفريق",
    "search_scope_all": "كل المهام",
    "search_scope_mine": "المسندة لي",
    "search_scope_supervisor": "التي أنشأتها أو أتابعها",
    "search_results": "البحث في المهام",
    "search_hint": "ابحث بعنوان المهمة أو رقمها أو المشروع أو اسم الموظف أو الوصف. تحليل التشابه يتم محليًا داخل التطبيق.",
    "no_search_results": "لا توجد مهام مطابقة للبحث.",
    "role_assignee": "منفذ المهمة",
    "role_creator": "منشئ المهمة",
    "role_observer": "مراقب",
    "roles": "دوري في هذه المهمة",
    "supervisor_scope_only": "هذه المهمة ليست ضمن المهام التي أنشأتها أو تتابعها.",
    "assignee_action_only": "هذا الإجراء متاح عندما تكون أنت منفذ المهمة فقط.",
    "no_deadline_permission": "صلاحيات Bitrix24 لا تسمح لك بتغيير الموعد النهائي لهذه المهمة.",
    "no_edit_permission": "صلاحيات Bitrix24 لا تسمح لك بتعديل هذه المهمة.",
    "no_reassign_permission": "صلاحيات Bitrix24 لا تسمح لك بإعادة إسناد هذه المهمة.",
    "no_review_permission": "صلاحيات Bitrix24 لا تسمح لك باعتماد المهمة أو إعادتها للاستكمال.",
    "choose_replan_change": "حدد موعدًا نهائيًا جديدًا و/أو غيّر الأولوية.",
    "choose_employee": "اختر الموظف الذي ستُسند إليه المهمة.",
    "employee_not_in_project": "الموظف المحدد ليس عضوًا في مشروع Bitrix الخاص بهذه المهمة.",
    "not_pending_review": "المهمة ليست حاليًا بانتظار الاعتماد في Bitrix24.",
    "feedback_required_return": "اكتب ملاحظة واضحة ومفيدة قبل إعادة المهمة للموظف.",
    "employee_workspace_missing": "لم يتم إنشاء مساحة عمل الموظف داخل المستودع المشترك حتى الآن.",
    "employee_note_missing": "لم يتم إنشاء ملف توثيق الموظف لهذه المهمة حتى الآن.",
    "team_dashboard": "إشراف الفريق",
    "team_dashboard_copy": "قسم مستقل للمهام التي أنشأتها أو تتابعها. مهامك الشخصية تبقى في «مهامي» حتى لو كنت مشرفًا في الوقت نفسه.",
    "my_work": "مهامي",
    "team_work": "إشراف الفريق",
    "export_excel": "تصدير تقرير Excel",
    "team_statistics": "إحصاءات الفريق",
    "priority_load": "حمل الأولويات",
    "priority_load_help": "مؤشر بسيط للضغط: العالية = 3، المتوسطة = 2، المنخفضة = 1 للمهام المفتوحة.",
    "high_priority_tasks": "مهام عالية الأولوية",
    "late_tasks": "مهام متأخرة",
    "justified_late": "متأخرة مع مبرر",
    "completed_recent": "مكتملة",
    "pending_approval": "بانتظار الاعتماد",
    "pending_approval_copy": "مهام رفع الموظفون إنجازها وتنتظر اعتماد منشئ المهمة.",
    "active_team_tasks": "مهام الفريق النشطة",
    "active_team_copy": "غيّر الموعد أو الأولوية أو أعد الإسناد لتوجيه العمل، بدون خلطها مع مهامك الشخصية.",
    "recent_completed": "المهام المكتملة مؤخرًا",
    "recent_completed_copy": "تظهر لدعم إحصاءات الفريق وتقرير Excel.",
    "replan": "إعادة تخطيط",
    "replan_task": "إعادة تخطيط المهمة",
    "new_deadline": "الموعد النهائي الجديد",
    "priority": "الأولوية",
    "priority_low": "منخفضة",
    "priority_medium": "متوسطة",
    "priority_high": "عالية",
    "replan_reason": "سبب التعديل / توجيه للموظف",
    "replan_reason_placeholder": "لماذا تغيّر الموعد أو الأولوية؟",
    "save_replan": "تحديث المهمة",
    "reassign": "إعادة إسناد",
    "reassign_task": "إعادة إسناد المهمة",
    "assign_to": "إسناد إلى",
    "reassign_reason": "سبب إعادة الإسناد",
    "reassign_reason_placeholder": "توزيع الأحمال، تخصص، إجازة، اعتماد على طرف آخر…",
    "confirm_reassign": "إعادة الإسناد في Bitrix24",
    "review_and_close": "مراجعة تسليم الموظف",
    "delivery_timing": "وقت التسليم",
    "delivery_on_time": "تم التسليم في الوقت المحدد",
    "delivery_late": "تم التسليم متأخرًا",
    "outcome_5": "يتجاوز التوقعات بشكل ملحوظ",
    "outcome_4": "تم إنجاز المهمة بنجاح",
    "outcome_3": "يحقق الحد الأدنى من المتطلبات",
    "outcome_2": "يحتاج إلى إشراف أكبر",
    "outcome_1": "لم يتم إنجاز المهمة",
    "review_feedback": "ملاحظة للموظف",
    "review_feedback_placeholder": "ما الذي تم بشكل جيد؟ ما المطلوب تحسينه؟ وما الخطوة التالية؟",
    "approve": "اعتماد وإغلاق",
    "return_employee": "إعادة للاستكمال",
    "company_field_detected": "تم التعرف على حقول تقييم الشركة في بوابة Bitrix الحالية.",
    "company_field_fallback": "لم يتم العثور على حقول مخصصة مطابقة. سيُحفظ التقييم كاملًا في تعليق المهمة وفي التقرير.",
    "late_justification": "مبرر التأخير",
    "no_late_justification": "لا يوجد مبرر تأخير حتى الآن.",
    "supervisor_can_comment": "يمكنك التعليق حتى لو لم يمنحك Bitrix صلاحية التعديل أو الاعتماد على هذه المهمة.",
    "assigned_and_supervisor_note": "الأدوار مرتبطة بالمهمة نفسها؛ قد تكون منفذًا في مهمة ومشرفًا أو مراقبًا في مهمة أخرى.",
    "team_members": "أعضاء الفريق",
    "report_window": "فترة إدراج المهام المكتملة في التقرير",
    "days": "يوم",
    "folder_browser": "استعراض المجلدات",
    "folder_browser_select": "استخدام هذا المجلد",
    "folder_browser_close": "إغلاق",
    "folder_browser_empty": "لا توجد مجلدات فرعية يمكن قراءتها هنا.",
    "folder_browser_server_note": "الاستعراض يتم على الجهاز أو الخادم الذي يشغّل OMI Bitrix، ولا يتم رفع أي ملفات.",
    "employee_folder_preview": "مجلد مساحة عمل الموظف",
    "employee_folder_structure": "يتم حفظ المهام بالشكل: المستودع / Bitrix Work / الموظف / المشروع / المهمة.",
    "supervisor_relationship": "علاقتي بالمهمة",
    "observed_only": "مراقب",
    "creator_control": "منشئ المهمة وصاحب الاعتماد",
    "permission_limited": "الإجراء غير متاح حسب صلاحيات Bitrix",
    "similarity_score": "تشابه {score}%",
    "related_upcoming": "أعمال قادمة مرتبطة",
    "related_upcoming_copy": "تفيد في اكتشاف الطلبات المتكررة وإعادة استخدام SQL أو Alteryx أو جمع المهام المتشابهة معًا.",
    "open_team_workspace": "فتح مساحة عمل الموظف",
    "status_waiting": "بانتظار البدء",
    "status_in_progress": "قيد التنفيذ",
    "status_pending": "بانتظار الاعتماد",
    "status_completed": "مكتملة",
    "status_deferred": "مؤجلة",
})

TRANSLATIONS["en"].update({
    "comment_employee": "Comment to employee",
    "comment_employee_placeholder": "Write a clear progress note, request, or direction…",
    "send_comment": "Post comment",
    "team_similarity": "Duplicate-work radar",
    "team_similarity_copy": "Flags similar active team tasks so you can reuse SQL/Alteryx work or combine duplicated effort before it grows.",
    "member_load": "Load",
    "active_short": "active",
    "high_short": "high",
    "reassign_load_hint": "Members are sorted by the current priority-load signal; a lower score can indicate more room, but use project context and specialization before reassigning.",
    "confirm_reassign_prompt": "Reassign this Bitrix24 task to the selected employee?",
    "confirm_replan_prompt": "Apply this new deadline / priority in Bitrix24?",
    "confirm_review_prompt": "Apply this review decision in Bitrix24?",
    "late_report_note": "Late status is based on the actual submission/close time for reviewed or completed tasks—not simply on an old deadline.",
    "review_field_note": "If your company assessment fields exist as Bitrix task custom fields, OMI Bitrix detects their enum values automatically. Otherwise the exact assessment remains in the task comment and Excel report.",
})

TRANSLATIONS["ar"].update({
    "comment_employee": "تعليق للموظف",
    "comment_employee_placeholder": "اكتب توجيهًا واضحًا أو طلبًا أو تحديثًا مختصرًا…",
    "send_comment": "إرسال التعليق",
    "team_similarity": "رادار الأعمال المتشابهة",
    "team_similarity_copy": "يكشف المهام النشطة المتقاربة لتسهيل إعادة استخدام SQL أو Alteryx أو دمج الجهود المتكررة قبل أن تكبر.",
    "member_load": "حمل العمل",
    "active_short": "نشطة",
    "high_short": "عالية",
    "reassign_load_hint": "يتم ترتيب أعضاء المشروع حسب مؤشر حمل الأولويات الحالي. الرقم الأقل قد يعني مساحة أكبر، لكن يظل التخصص وسياق المهمة أهم عند إعادة الإسناد.",
    "confirm_reassign_prompt": "هل تريد إعادة إسناد هذه المهمة في Bitrix24 إلى الموظف المحدد؟",
    "confirm_replan_prompt": "هل تريد تطبيق الموعد أو الأولوية الجديدة على المهمة في Bitrix24؟",
    "confirm_review_prompt": "هل تريد تطبيق قرار المراجعة على المهمة في Bitrix24؟",
    "late_report_note": "يُحتسب التأخير للمهام المسلّمة أو المكتملة بناءً على وقت التسليم/الإغلاق الفعلي، وليس فقط لأن الموعد القديم أصبح في الماضي.",
    "review_field_note": "إذا كانت حقول تقييم الشركة موجودة كحقول مخصصة للمهمة في Bitrix، يتعرف التطبيق على قيمها تلقائيًا. وإلا يبقى التقييم كاملًا في تعليق المهمة وتقرير Excel.",
})

TRANSLATIONS["en"].update({
    "discussion": "Discussion",
    "recent_comments": "Recent comments",
    "open_to_load_comments": "Open to load the recent Bitrix24 discussion.",
    "loading_comments": "Loading comments…",
    "no_comments": "No comments on this task yet.",
    "comments_error": "Could not load comments.",
    "show_more_comments": "Show more",
    "refresh_comments": "Refresh",
    "comments_count": "{count} comments",
    "focus_note": "FOCUS NOTE",
    "focus_quote_default": "Finish the next useful thing.",
    "next_quote": "Another focus note",
})

TRANSLATIONS["ar"].update({
    "discussion": "النقاش",
    "recent_comments": "آخر التعليقات",
    "open_to_load_comments": "افتح لعرض آخر نقاشات المهمة من Bitrix24.",
    "loading_comments": "جارٍ تحميل التعليقات…",
    "no_comments": "لا توجد تعليقات على هذه المهمة حتى الآن.",
    "comments_error": "تعذر تحميل التعليقات.",
    "show_more_comments": "عرض المزيد",
    "refresh_comments": "تحديث",
    "comments_count": "{count} تعليق",
    "focus_note": "دفعة تركيز",
    "focus_quote_default": "أنهِ الخطوة المفيدة التالية.",
    "next_quote": "عبارة أخرى",
})

TRANSLATIONS["en"].update({
    "cal_title": "Calendar", "cal_heading": "Your tasks, your plan",
    "cal_connect": "Connect Bitrix to see your tasks",
    "cal_connect_hint": "Add your personal Bitrix connection and choose projects in Settings, then return to Calendar.",
    "cal_intro": "Drag tasks to plan your days. Bitrix deadlines stay unchanged.",
    "cal_private": "Personal dates and colleague reminders are saved only in this browser. They do not sync to other devices. No messages are sent.",
    "cal_today": "Today", "cal_previous": "Previous month", "cal_next": "Next month",
    "cal_refresh": "Refresh tasks", "cal_search": "Find a task…", "cal_projects": "All selected projects",
    "cal_all": "All tasks", "cal_active": "Active tasks", "cal_completed": "Completed tasks",
    "cal_undated": "Unscheduled", "cal_undated_hint": "Drop a task here to clear its personal date.",
    "cal_none_undated": "No unscheduled tasks in this view.",
    "cal_empty": "No matching tasks.", "cal_loading": "Loading your tasks…",
    "cal_load_error": "Could not load tasks. Check your connection and Bitrix settings, then refresh.",
    "cal_saved": "Personal plan saved. Bitrix deadline unchanged.",
    "cal_storage_error": "Your browser could not save this change. Enable local storage and try again.",
    "cal_storage_invalid": "Saved calendar data could not be read. It has been left untouched; recover it or clear this calendar's browser storage before saving.",
    "cal_plan_date": "Personal plan date", "cal_deadline": "Bitrix deadline",
    "cal_reset": "Use Bitrix deadline", "cal_save": "Save plan", "cal_close": "Close",
    "cal_followups": "Colleague follow-ups", "cal_followup_hint": "Reminders to contact your colleagues.",
    "cal_colleague": "Colleague", "cal_choose": "Choose a colleague", "cal_manual": "Or enter a colleague's name",
    "cal_remind_date": "Remind me on", "cal_note": "What to follow up on", "cal_add": "Add reminder",
    "cal_done": "Mark done", "cal_reopen": "Reopen", "cal_remove": "Remove",
    "cal_due": "Due follow-ups", "cal_none_due": "No follow-ups due. Add one from a task.",
    "cal_no_followups": "No reminders for this task.", "cal_need_colleague": "Choose or enter a colleague and a reminder date.",
    "cal_reminder_saved": "Private reminder saved.", "cal_open": "Open task",
    "cal_completed_note": "Completed in Bitrix", "cal_high": "High priority",
    "cal_count": "tasks shown", "cal_plan": "Planned", "cal_undo": "Undo last change",
})
TRANSLATIONS["ar"].update({
    "cal_title": "التقويم", "cal_heading": "مهامك وخطتك",
    "cal_connect": "اربط حساب Bitrix لعرض مهامك",
    "cal_connect_hint": "أضف رابط حسابك في Bitrix واختر المشاريع في الإعدادات، ثم عد إلى التقويم.",
    "cal_intro": "اسحب المهام لتوزيعها على أيامك. مواعيد التسليم في Bitrix لا تتغير.",
    "cal_private": "مواعيد خطتك وتذكيرات الزملاء محفوظة في هذا المتصفح فقط، ولا تنتقل إلى الأجهزة الأخرى. لا تُرسل أي رسائل.",
    "cal_today": "اليوم", "cal_previous": "الشهر السابق", "cal_next": "الشهر التالي",
    "cal_refresh": "تحديث المهام", "cal_search": "ابحث عن مهمة…", "cal_projects": "كل المشاريع المحددة",
    "cal_all": "كل المهام", "cal_active": "المهام النشطة", "cal_completed": "المهام المكتملة",
    "cal_undated": "غير مجدولة", "cal_undated_hint": "اسحب مهمة هنا لإلغاء تاريخها الشخصي.",
    "cal_none_undated": "لا توجد مهام غير مجدولة في هذا العرض.",
    "cal_empty": "لا توجد مهام مطابقة.", "cal_loading": "جارٍ تحميل مهامك…",
    "cal_load_error": "تعذر تحميل المهام. تحقق من الاتصال وإعدادات Bitrix ثم حدّث الصفحة.",
    "cal_saved": "تم حفظ خطتك الشخصية دون تغيير موعد التسليم في Bitrix.",
    "cal_storage_error": "تعذر حفظ التغيير في المتصفح. فعّل التخزين المحلي ثم حاول مجددًا.",
    "cal_storage_invalid": "تعذرت قراءة بيانات التقويم المحفوظة. لم تُعدّل البيانات؛ استعدها أو امسح تخزين هذا التقويم في المتصفح قبل الحفظ.",
    "cal_plan_date": "التاريخ في خطتك الشخصية", "cal_deadline": "موعد التسليم في Bitrix",
    "cal_reset": "استخدام موعد Bitrix", "cal_save": "حفظ الخطة", "cal_close": "إغلاق",
    "cal_followups": "متابعة الزملاء", "cal_followup_hint": "تذكيراتك للتواصل مع الزملاء.",
    "cal_colleague": "الزميل", "cal_choose": "اختر زميلًا", "cal_manual": "أو أدخل اسم الزميل",
    "cal_remind_date": "ذكّرني بتاريخ", "cal_note": "موضوع المتابعة", "cal_add": "إضافة تذكير",
    "cal_done": "تمت المتابعة", "cal_reopen": "إعادة فتح", "cal_remove": "حذف",
    "cal_due": "متابعات مستحقة", "cal_none_due": "لا توجد متابعات مستحقة. أضف تذكيرًا من إحدى المهام.",
    "cal_no_followups": "لا توجد تذكيرات لهذه المهمة.", "cal_need_colleague": "اختر زميلًا أو أدخل اسمه وحدد تاريخ التذكير.",
    "cal_reminder_saved": "تم حفظ التذكير الخاص بك.", "cal_open": "فتح المهمة",
    "cal_completed_note": "مكتملة في Bitrix", "cal_high": "أولوية عالية",
    "cal_count": "مهمة معروضة", "cal_plan": "مخططة", "cal_undo": "التراجع عن آخر تغيير",
})


def normalize_language(value):
    return "ar" if str(value or "").lower().startswith("ar") else "en"


def get_text(lang, key, **kwargs):
    lang = normalize_language(lang)
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key)
    if text is None:
        text = TRANSLATIONS["en"].get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def js_strings(lang):
    keys = [
        "members", "untitled", "no_projects_returned", "connected_as", "could_not_fetch",
        "bitrix_user", "progress_update", "justify_delay_prefix", "why_miss_deadline",
        "connecting", "connection_failed", "fetching_projects",
        "bitrix_deadline", "deadline_unavailable", "hour_short", "minute_short",
        "choose_folder", "folder_browser_help", "use_this_folder", "go_up", "folder_roots",
        "loading_folders", "no_subfolders", "folder_browser_empty", "employee_name",
        "loading_comments", "no_comments", "comments_error", "show_more_comments",
        "refresh_comments", "comments_count"
    ]
    keys += [key for key in TRANSLATIONS["en"] if key.startswith("cal_")]
    return {key: get_text(lang, key) for key in keys}

# Diwan and local task intelligence.
TRANSLATIONS["en"]["d_diwan"] = "Diwany"
TRANSLATIONS["ar"]["d_diwan"] = "ديواني"
TRANSLATIONS["en"]["d_tasks_analysis"] = "Tasks"
TRANSLATIONS["ar"]["d_tasks_analysis"] = "مهام"
TRANSLATIONS["en"]["d_connections"] = "Connections & analysis settings"
TRANSLATIONS["ar"]["d_connections"] = "إعدادات الربط والتحليل"
TRANSLATIONS["en"]["d_connection_intro"] = "Configure your internal endpoints and your own Diwan connection. These settings belong to this browser profile."
TRANSLATIONS["ar"]["d_connection_intro"] = "أدخل روابط الخدمات الداخلية واربط حسابك في ديواني. هذه الإعدادات خاصة بملفك في هذا المتصفح."
TRANSLATIONS["en"]["d_diwan_intro"] = "Your requests, details, and delegation in one place."
TRANSLATIONS["ar"]["d_diwan_intro"] = "طلباتك وتفاصيلها وإسنادها من مكان واحد."
TRANSLATIONS["en"]["d_analysis_intro"] = "Local evidence from accessible history. Recommendations support your decision; they never assign work automatically."
TRANSLATIONS["ar"]["d_analysis_intro"] = "تحليل محلي للسجل المتاح لك. الترشيحات تساعدك في القرار ولا تسند المهام تلقائيًا."
TRANSLATIONS["en"]["d_connect"] = "Connect Diwan"
TRANSLATIONS["ar"]["d_connect"] = "ربط حساب ديواني"
TRANSLATIONS["en"]["d_replace_token"] = "Replace token"
TRANSLATIONS["ar"]["d_replace_token"] = "تغيير الرمز"
TRANSLATIONS["en"]["d_remove_token"] = "Remove token"
TRANSLATIONS["ar"]["d_remove_token"] = "حذف الرمز"
TRANSLATIONS["en"]["d_token_title"] = "Connect your Diwan account"
TRANSLATIONS["ar"]["d_token_title"] = "ربط حسابك في ديواني"
TRANSLATIONS["en"]["d_token_help"] = "Use your personal token. It is protected on this Windows PC and is never shared with other profiles."
TRANSLATIONS["ar"]["d_token_help"] = "أدخل رمز الوصول الخاص بك. يُحفظ محميًا على جهاز ويندوز ولا يُشارك مع الملفات الأخرى."
TRANSLATIONS["en"]["d_token"] = "Personal access token"
TRANSLATIONS["ar"]["d_token"] = "رمز الوصول الشخصي"
TRANSLATIONS["en"]["d_show"] = "Show / hide"
TRANSLATIONS["ar"]["d_show"] = "إظهار / إخفاء"
TRANSLATIONS["en"]["d_validate_save"] = "Validate & save"
TRANSLATIONS["ar"]["d_validate_save"] = "تحقق واحفظ"
TRANSLATIONS["en"]["d_cancel"] = "Cancel"
TRANSLATIONS["ar"]["d_cancel"] = "إلغاء"
TRANSLATIONS["en"]["d_save"] = "Save"
TRANSLATIONS["ar"]["d_save"] = "حفظ"
TRANSLATIONS["en"]["d_saved"] = "Saved successfully."
TRANSLATIONS["ar"]["d_saved"] = "تم الحفظ بنجاح."
TRANSLATIONS["en"]["d_working"] = "Working…"
TRANSLATIONS["ar"]["d_working"] = "جارٍ التنفيذ…"
TRANSLATIONS["en"]["d_endpoint_help"] = "Configure the internal listing endpoint in Settings before connecting."
TRANSLATIONS["ar"]["d_endpoint_help"] = "أضف رابط جلب الطلبات الداخلي في الإعدادات قبل الربط."
TRANSLATIONS["en"]["d_endpoints"] = "Diwan endpoints"
TRANSLATIONS["ar"]["d_endpoints"] = "روابط خدمات ديواني"
TRANSLATIONS["en"]["d_list_url"] = "List URL"
TRANSLATIONS["ar"]["d_list_url"] = "رابط قائمة الطلبات"
TRANSLATIONS["en"]["d_detail_url"] = "Details URL"
TRANSLATIONS["ar"]["d_detail_url"] = "رابط التفاصيل"
TRANSLATIONS["en"]["d_delegate_url"] = "Delegation URL (optional)"
TRANSLATIONS["ar"]["d_delegate_url"] = "رابط الإسناد (اختياري)"
TRANSLATIONS["en"]["d_method"] = "HTTP method"
TRANSLATIONS["ar"]["d_method"] = "طريقة الطلب"
TRANSLATIONS["en"]["d_id_field"] = "Internal task ID field"
TRANSLATIONS["ar"]["d_id_field"] = "حقل المعرّف الداخلي للمهمة"
TRANSLATIONS["en"]["d_assignee_field"] = "Assignee field in details response"
TRANSLATIONS["ar"]["d_assignee_field"] = "حقل الموظف المسند إليه في استجابة التفاصيل"
TRANSLATIONS["en"]["d_recipient_kind"] = "Recipient identifier"
TRANSLATIONS["ar"]["d_recipient_kind"] = "نوع معرّف الموظف"
TRANSLATIONS["en"]["d_email"] = "Email"
TRANSLATIONS["ar"]["d_email"] = "البريد الإلكتروني"
TRANSLATIONS["en"]["d_identifier"] = "Internal ID"
TRANSLATIONS["ar"]["d_identifier"] = "المعرّف الداخلي"
TRANSLATIONS["en"]["d_completed_statuses"] = "Completed status values (comma separated)"
TRANSLATIONS["ar"]["d_completed_statuses"] = "قيم حالات الإنجاز (مفصولة بفواصل)"
TRANSLATIONS["en"]["d_endpoint_note"] = "HTTPS internal endpoints only. For details, use {task_id} in the URL or a base URL. Changing this connection removes the saved token."
TRANSLATIONS["ar"]["d_endpoint_note"] = "روابط داخلية آمنة HTTPS فقط. يمكن استخدام {task_id} في رابط التفاصيل أو إدخال الرابط الأساسي. تغيير الاتصال يحذف الرمز المحفوظ."
TRANSLATIONS["en"]["d_contract_confirm"] = "I verified the delegation payload and assignee response field with the service owner."
TRANSLATIONS["ar"]["d_contract_confirm"] = "تحققت مع مسؤول الخدمة من حقول الإسناد وحقل الموظف في استجابة التفاصيل."
TRANSLATIONS["en"]["d_recipients"] = "Employee directory"
TRANSLATIONS["ar"]["d_recipients"] = "قائمة الموظفين"
TRANSLATIONS["en"]["d_recipients_help"] = "Add verified employee identifiers. The source service still decides whether delegation is allowed."
TRANSLATIONS["ar"]["d_recipients_help"] = "أضف معرّفات الموظفين المعتمدة. تظل صلاحية الإسناد خاضعة للنظام المصدر."
TRANSLATIONS["en"]["d_name_en"] = "English name"
TRANSLATIONS["ar"]["d_name_en"] = "الاسم بالإنجليزية"
TRANSLATIONS["en"]["d_name_ar"] = "Arabic name"
TRANSLATIONS["ar"]["d_name_ar"] = "الاسم بالعربية"
TRANSLATIONS["en"]["d_away_from"] = "Unavailable from"
TRANSLATIONS["ar"]["d_away_from"] = "غير متاح من"
TRANSLATIONS["en"]["d_away_to"] = "Unavailable until"
TRANSLATIONS["ar"]["d_away_to"] = "غير متاح حتى"
TRANSLATIONS["en"]["d_add_employee"] = "Add employee"
TRANSLATIONS["ar"]["d_add_employee"] = "إضافة موظف"
TRANSLATIONS["en"]["d_remove"] = "Remove"
TRANSLATIONS["ar"]["d_remove"] = "حذف"
TRANSLATIONS["en"]["d_source"] = "Source"
TRANSLATIONS["ar"]["d_source"] = "المصدر"
TRANSLATIONS["en"]["d_sync"] = "Fetch all pages"
TRANSLATIONS["ar"]["d_sync"] = "جلب جميع الصفحات"
TRANSLATIONS["en"]["d_history_sync"] = "Fetch Bitrix history"
TRANSLATIONS["ar"]["d_history_sync"] = "جلب سجل Bitrix"
TRANSLATIONS["en"]["d_export"] = "Export Excel"
TRANSLATIONS["ar"]["d_export"] = "تصدير Excel"
TRANSLATIONS["en"]["d_search"] = "Search requests"
TRANSLATIONS["ar"]["d_search"] = "البحث في الطلبات"
TRANSLATIONS["en"]["d_request_id"] = "Request number"
TRANSLATIONS["ar"]["d_request_id"] = "رقم الطلب"
TRANSLATIONS["en"]["d_task_id"] = "Task ID"
TRANSLATIONS["ar"]["d_task_id"] = "معرّف المهمة"
TRANSLATIONS["en"]["d_status"] = "Status"
TRANSLATIONS["ar"]["d_status"] = "الحالة"
TRANSLATIONS["en"]["d_status_filter"] = "Status ID (optional)"
TRANSLATIONS["ar"]["d_status_filter"] = "معرّف الحالة (اختياري)"
TRANSLATIONS["en"]["d_from"] = "From"
TRANSLATIONS["ar"]["d_from"] = "من"
TRANSLATIONS["en"]["d_to"] = "To"
TRANSLATIONS["ar"]["d_to"] = "إلى"
TRANSLATIONS["en"]["d_details"] = "Details"
TRANSLATIONS["ar"]["d_details"] = "التفاصيل"
TRANSLATIONS["en"]["d_delegate"] = "Delegate"
TRANSLATIONS["ar"]["d_delegate"] = "إسناد"
TRANSLATIONS["en"]["d_reconcile"] = "Check uncertain delegation"
TRANSLATIONS["ar"]["d_reconcile"] = "التحقق من إسناد غير مؤكد"
TRANSLATIONS["en"]["d_confirm_delegate"] = "Confirm delegation to this employee?"
TRANSLATIONS["ar"]["d_confirm_delegate"] = "تأكيد إسناد المهمة إلى هذا الموظف؟"
TRANSLATIONS["en"]["d_confirm_remove"] = "Remove this profile's token and cached Diwan data?"
TRANSLATIONS["ar"]["d_confirm_remove"] = "حذف رمز ملفك وبيانات ديواني المؤقتة؟"
TRANSLATIONS["en"]["d_empty"] = "No records yet. Configure your connection and fetch tasks."
TRANSLATIONS["ar"]["d_empty"] = "لا توجد سجلات بعد. اضبط الاتصال ثم اجلب المهام."
TRANSLATIONS["en"]["d_complete"] = "Last fetch completed"
TRANSLATIONS["ar"]["d_complete"] = "اكتمل آخر جلب"
TRANSLATIONS["en"]["d_partial"] = "Incomplete data"
TRANSLATIONS["ar"]["d_partial"] = "بيانات غير مكتملة"
TRANSLATIONS["en"]["d_last_sync"] = "Last successful fetch"
TRANSLATIONS["ar"]["d_last_sync"] = "آخر جلب ناجح"
TRANSLATIONS["en"]["d_count"] = "Records"
TRANSLATIONS["ar"]["d_count"] = "السجلات"
TRANSLATIONS["en"]["d_pages"] = "Pages"
TRANSLATIONS["ar"]["d_pages"] = "الصفحات"
TRANSLATIONS["en"]["d_previous"] = "Previous"
TRANSLATIONS["ar"]["d_previous"] = "السابق"
TRANSLATIONS["en"]["d_next"] = "Next"
TRANSLATIONS["ar"]["d_next"] = "التالي"
TRANSLATIONS["en"]["d_history_note"] = "History stays in memory and is cleared on restart. Counts cover only records accessible to your connection. Employee-directory entries are configured, not discovered permissions."
TRANSLATIONS["ar"]["d_history_note"] = "السجل مؤقت في الذاكرة ويُمسح عند إعادة التشغيل. الأعداد تشمل السجلات المتاحة لاتصالك فقط. قائمة الموظفين مُعدّة يدويًا وليست إثباتًا للصلاحيات."
TRANSLATIONS["en"]["d_analyze"] = "Analyze"
TRANSLATIONS["ar"]["d_analyze"] = "تحليل"
TRANSLATIONS["en"]["d_query"] = "Describe the task"
TRANSLATIONS["ar"]["d_query"] = "اكتب وصف المهمة"
TRANSLATIONS["en"]["d_category"] = "Category / service"
TRANSLATIONS["ar"]["d_category"] = "التصنيف / الخدمة"
TRANSLATIONS["en"]["d_related"] = "Related historical tasks"
TRANSLATIONS["ar"]["d_related"] = "مهام سابقة ذات صلة"
TRANSLATIONS["en"]["d_recommendations"] = "Suggested employees"
TRANSLATIONS["ar"]["d_recommendations"] = "الموظفون المرشحون"
TRANSLATIONS["en"]["d_insufficient"] = "Insufficient evidence"
TRANSLATIONS["ar"]["d_insufficient"] = "الأدلة غير كافية"
TRANSLATIONS["en"]["d_estimate"] = "Historical elapsed time"
TRANSLATIONS["ar"]["d_estimate"] = "المدة المنقضية تاريخيًا"
TRANSLATIONS["en"]["d_elapsed_help"] = "Creation to completion, including waiting. This is not working effort or an SLA promise."
TRANSLATIONS["ar"]["d_elapsed_help"] = "من الإنشاء إلى الإنجاز، بما يشمل الانتظار. ليست ساعات عمل فعلية أو التزامًا باتفاقية مستوى الخدمة."
TRANSLATIONS["en"]["d_samples"] = "Completed examples"
TRANSLATIONS["ar"]["d_samples"] = "أمثلة منجزة"
TRANSLATIONS["en"]["d_active"] = "Active tasks"
TRANSLATIONS["ar"]["d_active"] = "المهام النشطة"
TRANSLATIONS["en"]["d_overdue"] = "Overdue"
TRANSLATIONS["ar"]["d_overdue"] = "متأخرة"
TRANSLATIONS["en"]["d_hours"] = "hours"
TRANSLATIONS["ar"]["d_hours"] = "ساعة"
TRANSLATIONS["en"]["d_rules"] = "Priorities & SLA calendar"
TRANSLATIONS["ar"]["d_rules"] = "الأولويات وتقويم مستوى الخدمة"
TRANSLATIONS["en"]["d_rule_help"] = "Local rules do not update source priorities. SLA targets use business hours; estimates remain elapsed time."
TRANSLATIONS["ar"]["d_rule_help"] = "القواعد المحلية لا تغيّر أولوية المصدر. مستهدفات الخدمة بساعات العمل، والتقديرات مبنية على المدة المنقضية."
TRANSLATIONS["en"]["d_tag"] = "Tag"
TRANSLATIONS["ar"]["d_tag"] = "الوسم"
TRANSLATIONS["en"]["d_priority"] = "Priority"
TRANSLATIONS["ar"]["d_priority"] = "الأولوية"
TRANSLATIONS["en"]["d_add_rule"] = "Add rule"
TRANSLATIONS["ar"]["d_add_rule"] = "إضافة قاعدة"
TRANSLATIONS["en"]["d_sla_target"] = "SLA target (business hours)"
TRANSLATIONS["ar"]["d_sla_target"] = "مستهدف الخدمة (ساعات عمل)"
TRANSLATIONS["en"]["d_start_hour"] = "Workday starts (hour)"
TRANSLATIONS["ar"]["d_start_hour"] = "بداية الدوام (الساعة)"
TRANSLATIONS["en"]["d_end_hour"] = "Workday ends (hour)"
TRANSLATIONS["ar"]["d_end_hour"] = "نهاية الدوام (الساعة)"
TRANSLATIONS["en"]["d_holidays"] = "Holidays (one YYYY-MM-DD per line)"
TRANSLATIONS["ar"]["d_holidays"] = "الإجازات الرسمية (تاريخ YYYY-MM-DD في كل سطر)"
TRANSLATIONS["en"]["d_workdays"] = "Working days"
TRANSLATIONS["ar"]["d_workdays"] = "أيام العمل"
TRANSLATIONS["en"]["d_monday"] = "Monday"
TRANSLATIONS["ar"]["d_monday"] = "الاثنين"
TRANSLATIONS["en"]["d_tuesday"] = "Tuesday"
TRANSLATIONS["ar"]["d_tuesday"] = "الثلاثاء"
TRANSLATIONS["en"]["d_wednesday"] = "Wednesday"
TRANSLATIONS["ar"]["d_wednesday"] = "الأربعاء"
TRANSLATIONS["en"]["d_thursday"] = "Thursday"
TRANSLATIONS["ar"]["d_thursday"] = "الخميس"
TRANSLATIONS["en"]["d_friday"] = "Friday"
TRANSLATIONS["ar"]["d_friday"] = "الجمعة"
TRANSLATIONS["en"]["d_saturday"] = "Saturday"
TRANSLATIONS["ar"]["d_saturday"] = "السبت"
TRANSLATIONS["en"]["d_sunday"] = "Sunday"
TRANSLATIONS["ar"]["d_sunday"] = "الأحد"
TRANSLATIONS["en"]["d_evaluate"] = "Evaluate historical baseline"
TRANSLATIONS["ar"]["d_evaluate"] = "تقييم التقدير التاريخي"
TRANSLATIONS["en"]["d_evaluation"] = "Chronological evaluation"
TRANSLATIONS["ar"]["d_evaluation"] = "تقييم زمني على السجل"
TRANSLATIONS["en"]["d_evaluation_help"] = "Only tasks completed before each evaluated task was created are used as evidence. Sparse histories may have no evaluable samples."
TRANSLATIONS["ar"]["d_evaluation_help"] = "يستند التقييم إلى مهام أُنجزت قبل إنشاء المهمة المُقيّمة. قد لا يكفي السجل المتاح لإجراء التقييم."
TRANSLATIONS["en"]["d_workflow"] = "Workflow history"
TRANSLATIONS["ar"]["d_workflow"] = "سجل الإجراءات"
TRANSLATIONS["en"]["d_fields"] = "Request fields"
TRANSLATIONS["ar"]["d_fields"] = "حقول الطلب"
TRANSLATIONS["en"]["d_connected"] = "Token saved for this profile"
TRANSLATIONS["ar"]["d_connected"] = "الرمز محفوظ لملفك"
TRANSLATIONS["en"]["d_not_connected"] = "Not connected"
TRANSLATIONS["ar"]["d_not_connected"] = "غير متصل"
TRANSLATIONS["en"]["d_open_settings"] = "Open Settings"
TRANSLATIONS["ar"]["d_open_settings"] = "فتح الإعدادات"
TRANSLATIONS["en"]["d_no_recipients"] = "Configure verified recipients in Settings before delegation."
TRANSLATIONS["ar"]["d_no_recipients"] = "أضف الموظفين المعتمدين في الإعدادات قبل الإسناد."
TRANSLATIONS["en"]["d_details_export"] = "Export includes details already opened in this session."
TRANSLATIONS["ar"]["d_details_export"] = "يشمل التصدير التفاصيل التي فُتحت في هذه الجلسة."
TRANSLATIONS["en"]["d_sla_deadline"] = "Configured SLA deadline"
TRANSLATIONS["ar"]["d_sla_deadline"] = "موعد الخدمة المحدد"
TRANSLATIONS["en"]["d_effective_priority"] = "Local priority"
TRANSLATIONS["ar"]["d_effective_priority"] = "الأولوية المحلية"
TRANSLATIONS["en"]["d_error_invalid_method"] = "Choose a supported HTTP method."
TRANSLATIONS["ar"]["d_error_invalid_method"] = "اختر طريقة طلب مدعومة."
TRANSLATIONS["en"]["d_error_invalid_endpoint"] = "Use an HTTPS endpoint without credentials, query parameters, or fragments."
TRANSLATIONS["ar"]["d_error_invalid_endpoint"] = "استخدم رابط HTTPS دون بيانات دخول أو معاملات استعلام أو جزء لاحق."
TRANSLATIONS["en"]["d_error_missing_endpoint"] = "Configure the required endpoint in Settings first."
TRANSLATIONS["ar"]["d_error_missing_endpoint"] = "أضف رابط الخدمة المطلوب في الإعدادات أولًا."
TRANSLATIONS["en"]["d_error_invalid_id_field"] = "Choose a supported task ID field."
TRANSLATIONS["ar"]["d_error_invalid_id_field"] = "اختر حقل معرّف مهمة مدعومًا."
TRANSLATIONS["en"]["d_error_invalid_assignee_field"] = "Enter a valid assignee field name."
TRANSLATIONS["ar"]["d_error_invalid_assignee_field"] = "أدخل اسم حقل الموظف بشكل صحيح."
TRANSLATIONS["en"]["d_error_token_required"] = "Connect your personal Diwan token first."
TRANSLATIONS["ar"]["d_error_token_required"] = "اربط رمز ديواني الخاص بك أولًا."
TRANSLATIONS["en"]["d_error_invalid_token"] = "Enter a token without spaces."
TRANSLATIONS["ar"]["d_error_invalid_token"] = "أدخل الرمز دون مسافات."
TRANSLATIONS["en"]["d_error_token_invalid"] = "The token was rejected or expired. Please reconnect."
TRANSLATIONS["ar"]["d_error_token_invalid"] = "الرمز مرفوض أو منتهي. أعد الربط."
TRANSLATIONS["en"]["d_error_permission_denied"] = "Your source account does not allow this action."
TRANSLATIONS["ar"]["d_error_permission_denied"] = "حسابك في النظام المصدر لا يسمح بهذا الإجراء."
TRANSLATIONS["en"]["d_error_source_unavailable"] = "The source did not respond successfully. Check the internal connection; do not blindly repeat a delegation."
TRANSLATIONS["ar"]["d_error_source_unavailable"] = "لم تستجب الخدمة بنجاح. تحقق من الاتصال الداخلي ولا تكرر الإسناد قبل التحقق من نتيجته."
TRANSLATIONS["en"]["d_error_invalid_response"] = "Unexpected source response. Check the endpoint and response mapping."
TRANSLATIONS["ar"]["d_error_invalid_response"] = "استجابة غير متوقعة. تحقق من الرابط وحقول الاستجابة."
TRANSLATIONS["en"]["d_error_source_rejected"] = "The source rejected this request."
TRANSLATIONS["ar"]["d_error_source_rejected"] = "رفض النظام المصدر الطلب."
TRANSLATIONS["en"]["d_error_redirect_blocked"] = "Endpoint redirects are blocked to protect your token. Use the final endpoint URL."
TRANSLATIONS["ar"]["d_error_redirect_blocked"] = "أُوقف تحويل الرابط لحماية الرمز. استخدم الرابط النهائي للخدمة."
TRANSLATIONS["en"]["d_error_response_too_large"] = "The response exceeds the safe size limit. Reduce the source page size."
TRANSLATIONS["ar"]["d_error_response_too_large"] = "حجم الاستجابة يتجاوز الحد المسموح."
TRANSLATIONS["en"]["d_error_missing_task_id"] = "A record is missing the configured internal task ID."
TRANSLATIONS["ar"]["d_error_missing_task_id"] = "يفتقد أحد السجلات حقل معرّف المهمة المحدد."
TRANSLATIONS["en"]["d_error_task_id_mismatch"] = "The detail response belongs to a different task ID."
TRANSLATIONS["ar"]["d_error_task_id_mismatch"] = "استجابة التفاصيل تخص معرّف مهمة مختلفًا."
TRANSLATIONS["en"]["d_error_pagination_stalled"] = "The source repeated a page. Results may be incomplete."
TRANSLATIONS["ar"]["d_error_pagination_stalled"] = "كرر المصدر صفحة سابقة. قد تكون النتائج غير مكتملة."
TRANSLATIONS["en"]["d_error_page_limit"] = "The page safety limit was reached; results are incomplete."
TRANSLATIONS["ar"]["d_error_page_limit"] = "وصل الجلب إلى حد الصفحات؛ النتائج غير مكتملة."
TRANSLATIONS["en"]["d_error_record_limit"] = "The record limit was reached; results are incomplete."
TRANSLATIONS["ar"]["d_error_record_limit"] = "وصل الجلب إلى حد السجلات؛ النتائج غير مكتملة."
TRANSLATIONS["en"]["d_error_cancelled"] = "Fetch cancelled."
TRANSLATIONS["ar"]["d_error_cancelled"] = "أُلغي الجلب."
TRANSLATIONS["en"]["d_error_sync_running"] = "A fetch is already running."
TRANSLATIONS["ar"]["d_error_sync_running"] = "يوجد جلب قيد التنفيذ."
TRANSLATIONS["en"]["d_error_server_busy"] = "Other fetches are running. Try shortly."
TRANSLATIONS["ar"]["d_error_server_busy"] = "توجد عمليات جلب أخرى. حاول بعد قليل."
TRANSLATIONS["en"]["d_error_sync_failed"] = "Fetch failed. Previously fetched data may be stale."
TRANSLATIONS["ar"]["d_error_sync_failed"] = "تعذر الجلب. قد تكون البيانات السابقة قديمة."
TRANSLATIONS["en"]["d_error_not_found"] = "This item is not available in your current profile."
TRANSLATIONS["ar"]["d_error_not_found"] = "هذا العنصر غير متاح لملفك الحالي."
TRANSLATIONS["en"]["d_error_connection_changed"] = "The connection changed. Refresh and try again."
TRANSLATIONS["ar"]["d_error_connection_changed"] = "تغير الاتصال. حدّث الصفحة وحاول مجددًا."
TRANSLATIONS["en"]["d_error_invalid_input"] = "Check the supplied values."
TRANSLATIONS["ar"]["d_error_invalid_input"] = "تحقق من القيم المدخلة."
TRANSLATIONS["en"]["d_error_invalid_recipient"] = "Check the employee identifier, email, and duplicate entries."
TRANSLATIONS["ar"]["d_error_invalid_recipient"] = "تحقق من معرّف الموظف والبريد والسجلات المكررة."
TRANSLATIONS["en"]["d_error_recipient_unavailable"] = "This employee is marked unavailable today."
TRANSLATIONS["ar"]["d_error_recipient_unavailable"] = "الموظف مسجل كغير متاح اليوم."
TRANSLATIONS["en"]["d_error_confirmation_required"] = "Confirm delegation before submitting."
TRANSLATIONS["ar"]["d_error_confirmation_required"] = "أكد الإسناد قبل الإرسال."
TRANSLATIONS["en"]["d_error_already_assigned"] = "The task is already assigned to that employee."
TRANSLATIONS["ar"]["d_error_already_assigned"] = "المهمة مسندة بالفعل لهذا الموظف."
TRANSLATIONS["en"]["d_error_task_completed"] = "Completed tasks cannot be delegated here."
TRANSLATIONS["ar"]["d_error_task_completed"] = "لا يمكن إسناد المهام المنجزة من هنا."
TRANSLATIONS["en"]["d_error_delegation_disabled"] = "Configure and verify delegation settings before using this action."
TRANSLATIONS["ar"]["d_error_delegation_disabled"] = "اضبط إعدادات الإسناد وتحقق منها قبل استخدام الإجراء."
TRANSLATIONS["en"]["d_error_delegation_uncertain"] = "Delegation is unconfirmed. Use Check uncertain delegation; do not submit it again."
TRANSLATIONS["ar"]["d_error_delegation_uncertain"] = "لم تُؤكد نتيجة الإسناد. استخدم التحقق من الإسناد غير المؤكد ولا ترسله مجددًا."
TRANSLATIONS["en"]["d_error_bitrix_required"] = "Configure Bitrix and selected projects first."
TRANSLATIONS["ar"]["d_error_bitrix_required"] = "اضبط Bitrix والمشاريع المختارة أولًا."
TRANSLATIONS["en"]["d_error_credential_protection"] = "Windows could not protect or read this credential. Reconnect under the configured Windows account."
TRANSLATIONS["ar"]["d_error_credential_protection"] = "تعذر على ويندوز حماية الرمز أو قراءته. أعد الربط باستخدام حساب ويندوز المعتمد."
TRANSLATIONS["en"]["d_error_csrf"] = "This page has expired. Reload it before submitting."
TRANSLATIONS["ar"]["d_error_csrf"] = "انتهت صلاحية الصفحة. أعد تحميلها قبل الإرسال."

TRANSLATIONS["en"].update(d_storage_mode="Storage mode", d_daily_minutes="Daily planner minutes", d_manual_projects="Additional project/group IDs")
TRANSLATIONS["ar"].update(d_storage_mode="نوع المجلد", d_daily_minutes="دقائق التخطيط اليومية", d_manual_projects="معرّفات مشاريع أو مجموعات إضافية")

TRANSLATIONS["en"].update(shared_vault_root="Workspace root path", shared_obsidian_vault="Workspace folder", d_test_folder="Test folder", d_folder_ok="Folder read/write, Unicode and long-path checks passed.", d_folder_failed="Folder test failed. Check Windows permissions and long-path support.")
TRANSLATIONS["ar"].update(shared_vault_root="مسار مجلد العمل", shared_obsidian_vault="مجلد العمل", d_test_folder="اختبار المجلد", d_folder_ok="نجحت اختبارات القراءة والكتابة والأسماء العربية والمسار الطويل.", d_folder_failed="تعذر اختبار المجلد. تحقق من صلاحيات ويندوز ودعم المسارات الطويلة.")

TRANSLATIONS["en"].update(d_relevance="Relevance %", d_recommendations_help="Ranked by comparable completed assignments, active/late counts and priority load. Current assignees are attribution proxies; these are not productivity ratings. Availability is unknown unless configured.", shared_vault_path="Workspace root path", setup_intro="Choose your Bitrix projects and a local or shared work folder. Obsidian is optional.", shared_obsidian_help="One folder holds documentation and work files. Obsidian links are optional.")
TRANSLATIONS["ar"].update(d_relevance="درجة التشابه %", d_recommendations_help="الترتيب حسب المهام المشابهة المنجزة والأعمال النشطة والمتأخرة والأولوية. الإسناد الحالي مؤشر تقريبي وليس تقييمًا للإنتاجية. التوفر غير معلوم ما لم يُضبط.", shared_vault_path="مسار مجلد العمل", setup_intro="اختر مشاريع Bitrix ومجلد العمل المحلي أو المشترك. استخدام Obsidian اختياري.", shared_obsidian_help="مجلد واحد للتوثيق وملفات العمل. روابط Obsidian اختيارية.")

TRANSLATIONS["en"]['d_tasks_analysis'] = 'Tasks & similarity'
TRANSLATIONS["ar"]['d_tasks_analysis'] = 'مهام وتشابه'

TRANSLATIONS["en"]['d_history_sync'] = 'Refresh selected source now'
TRANSLATIONS["ar"]['d_history_sync'] = 'تحديث المصدر المحدد الآن'

TRANSLATIONS["en"]['d_history_note'] = 'History refreshes automatically at startup and every 2 hours while the server is running. Failed fetches retry after 5 minutes. The last successful in-memory index stays available during refresh.'
TRANSLATIONS["ar"]['d_history_note'] = 'يُحدّث السجل تلقائيًا عند التشغيل وكل ساعتين ما دام الخادم يعمل. تُعاد المحاولة بعد 5 دقائق عند الفشل، ويبقى آخر فهرس ناجح متاحًا أثناء التحديث.'

TRANSLATIONS["en"]['d_similar_pairs'] = 'Similar tasks'
TRANSLATIONS["ar"]['d_similar_pairs'] = 'المهام المتشابهة'

TRANSLATIONS["en"]['d_pairs_help'] = 'Examples from up to 100 tasks per source. Use Find similar on any listed task, or enter a new task below. Scores measure shared words, not semantic understanding.'
TRANSLATIONS["ar"]['d_pairs_help'] = 'أمثلة من 100 مهمة لكل مصدر. استخدم البحث عن مشابه لأي مهمة في القائمة أو أدخل مهمة جديدة أدناه. تقيس النتيجة الكلمات المشتركة ولا تعني فهم المعنى.'

TRANSLATIONS["en"]['d_find_similar'] = 'Find similar'
TRANSLATIONS["ar"]['d_find_similar'] = 'البحث عن مشابه'

TRANSLATIONS["en"]['d_shared_terms'] = 'Shared words'
TRANSLATIONS["ar"]['d_shared_terms'] = 'الكلمات المشتركة'

TRANSLATIONS["en"]['d_no_matches'] = 'No matching tasks. Try relevant Arabic or English keywords; synonyms and translations may not match.'
TRANSLATIONS["ar"]['d_no_matches'] = 'لا توجد مهام مطابقة. جرّب كلمات مرتبطة بالعربية أو الإنجليزية؛ قد لا تتطابق المرادفات والترجمات.'

TRANSLATIONS["en"]['d_no_pairs'] = 'No similar pairs yet. Check the source connection and refresh status above.'
TRANSLATIONS["ar"]['d_no_pairs'] = 'لا توجد أزواج متشابهة حاليًا. تحقق من اتصال المصدر وحالة التحديث أعلاه.'

TRANSLATIONS["en"]['d_not_connected'] = 'Not connected'
TRANSLATIONS["ar"]['d_not_connected'] = 'غير متصل'

TRANSLATIONS["en"]['d_records'] = 'tasks indexed'
TRANSLATIONS["ar"]['d_records'] = 'مهمة مفهرسة'

TRANSLATIONS["en"]['d_last_refresh'] = 'Last successful refresh'
TRANSLATIONS["ar"]['d_last_refresh'] = 'آخر تحديث ناجح'

TRANSLATIONS["en"]['d_next_refresh'] = 'Next refresh'
TRANSLATIONS["ar"]['d_next_refresh'] = 'التحديث القادم'

TRANSLATIONS["en"]['d_historical_tasks'] = 'Historical tasks'
TRANSLATIONS["ar"]['d_historical_tasks'] = 'سجل المهام'

TRANSLATIONS["en"]['d_display_limit'] = 'Up to 1,000 rows shown; similarity searches the entire fetched history.'
TRANSLATIONS["ar"]['d_display_limit'] = 'يُعرض حتى 1000 صف؛ يبحث التشابه في كامل السجل المجلوب.'

TRANSLATIONS["en"]['d_history_incomplete'] = 'History is incomplete or stale. Results use the last successful refresh, if available.'
TRANSLATIONS["ar"]['d_history_incomplete'] = 'السجل غير مكتمل أو قديم. تستخدم النتائج آخر تحديث ناجح إن توفر.'

TRANSLATIONS["en"]['d_r_title'] = 'Employee recommendations'
TRANSLATIONS["ar"]['d_r_title'] = 'توصيات الموظفين'

TRANSLATIONS["en"]['d_r_offline'] = 'Local ranking'
TRANSLATIONS["ar"]['d_r_offline'] = 'ترتيب محلي'

TRANSLATIONS["en"]['d_r_intro'] = 'Rank eligible employees using completed-task evidence and current workload. Assignment stays under your control.'
TRANSLATIONS["ar"]['d_r_intro'] = 'ترتيب الموظفين المؤهلين حسب أدلة المهام المكتملة والحمل الحالي. قرار الإسناد يبقى لك.'

TRANSLATIONS["en"]['d_r_refresh'] = 'Refresh open tasks'
TRANSLATIONS["ar"]['d_r_refresh'] = 'تحديث المهام المفتوحة'

TRANSLATIONS["en"]['d_r_inbox'] = 'Tasks needing assignment'
TRANSLATIONS["ar"]['d_r_inbox'] = 'مهام تحتاج إسنادًا'

TRANSLATIONS["en"]['d_r_rank'] = 'Recommend employees'
TRANSLATIONS["ar"]['d_r_rank'] = 'اقتراح الموظفين'

TRANSLATIONS["en"]['d_r_task'] = 'Open task'
TRANSLATIONS["ar"]['d_r_task'] = 'المهمة المفتوحة'

TRANSLATIONS["en"]['d_r_preview'] = 'Preview a new task'
TRANSLATIONS["ar"]['d_r_preview'] = 'تجربة وصف مهمة جديدة'

TRANSLATIONS["en"]['d_r_text'] = 'Task description (for preview)'
TRANSLATIONS["ar"]['d_r_text'] = 'وصف المهمة للتجربة'

TRANSLATIONS["en"]['d_r_project'] = 'Project'
TRANSLATIONS["ar"]['d_r_project'] = 'المشروع'

TRANSLATIONS["en"]['d_r_category'] = 'Category'
TRANSLATIONS["ar"]['d_r_category'] = 'الفئة'

TRANSLATIONS["en"]['d_r_needs'] = 'Needs an executor'
TRANSLATIONS["ar"]['d_r_needs'] = 'تحتاج إسناد منفّذ'

TRANSLATIONS["en"]['d_r_self'] = 'I will do this task myself'
TRANSLATIONS["ar"]['d_r_self'] = 'سأنفذ هذه المهمة بنفسي'

TRANSLATIONS["en"]['d_r_verify'] = 'Verify assignment'
TRANSLATIONS["ar"]['d_r_verify'] = 'التحقق من الإسناد'

TRANSLATIONS["en"]['d_r_policy'] = 'Eligibility and ranking settings'
TRANSLATIONS["ar"]['d_r_policy'] = 'إعدادات الأهلية والترتيب'

TRANSLATIONS["en"]['d_r_policy_help'] = 'Verified active project members are enabled initially. History-only employees need your eligibility confirmation. Projects and categories restrict eligibility; blank categories allow any category. IDs are Bitrix user IDs.'
TRANSLATIONS["ar"]['d_r_policy_help'] = 'تُفعّل عضوية المشروع النشطة المتحقق منها مبدئيًا. الموظفون المعروفون من التاريخ فقط يحتاجون اعتماد أهليتهم. المشاريع والفئات تحدد الأهلية؛ الفئات الفارغة تسمح بكل الفئات. المعرّفات تخص مستخدمي Bitrix.'

TRANSLATIONS["en"]['d_r_intake'] = 'Supervisor/intake account IDs (comma separated)'
TRANSLATIONS["ar"]['d_r_intake'] = 'معرّفات حسابات المشرف أو استقبال المهام (بفواصل)'

TRANSLATIONS["en"]['d_r_supervisors'] = 'Notification recipient IDs (comma separated)'
TRANSLATIONS["ar"]['d_r_supervisors'] = 'معرّفات المشرفين المستلمين للتنبيهات (بفواصل)'

TRANSLATIONS["en"]['d_r_routing_help'] = 'If recipients are blank, the Bitrix project owner receives the local alert. Intake assignees mean awaiting assignment unless explicitly claimed or assigned. Notifications appear only in a connected profile belonging to a recipient.'
TRANSLATIONS["ar"]['d_r_routing_help'] = 'عند ترك المستلمين فارغين، يستلم مالك المشروع في Bitrix التنبيه المحلي. المهام عند حسابات الاستقبال تنتظر الإسناد حتى تأكيد التنفيذ أو الإسناد. تظهر التنبيهات في ملف الاتصال الخاص بالمستلم.'

TRANSLATIONS["en"]['d_r_category_field'] = 'Category API field code (optional)'
TRANSLATIONS["ar"]['d_r_category_field'] = 'رمز حقل الفئة في API (اختياري)'

TRANSLATIONS["en"]['d_r_topn'] = 'Number of recommendations'
TRANSLATIONS["ar"]['d_r_topn'] = 'عدد المرشحين'

TRANSLATIONS["en"]['d_r_weights_help'] = 'Weights must total 100. These are configurable baseline rules, not trained or calibrated probabilities.'
TRANSLATIONS["ar"]['d_r_weights_help'] = 'مجموع الأوزان يجب أن يكون 100. هذه قواعد أولية قابلة للتعديل وليست احتمالات مدربة أو معايرة.'

TRANSLATIONS["en"]['d_r_similarity'] = 'Relevant task similarity'
TRANSLATIONS["ar"]['d_r_similarity'] = 'تشابه المهام ذات الصلة'

TRANSLATIONS["en"]['d_r_experience'] = 'Relevant completed experience'
TRANSLATIONS["ar"]['d_r_experience'] = 'خبرة الإنجاز ذات الصلة'

TRANSLATIONS["en"]['d_r_capacity'] = 'Remaining capacity'
TRANSLATIONS["ar"]['d_r_capacity'] = 'السعة المتاحة'

TRANSLATIONS["en"]['d_r_add_employee'] = 'Add employee by Bitrix ID'
TRANSLATIONS["ar"]['d_r_add_employee'] = 'إضافة موظف بمعرّف Bitrix'

TRANSLATIONS["en"]['d_r_save'] = 'Save policy'
TRANSLATIONS["ar"]['d_r_save'] = 'حفظ الإعدادات'

TRANSLATIONS["en"]['d_r_limits'] = 'Only accessible selected-project tasks are counted. Quality and SLA outcomes do not affect this first baseline. Current assignee is an imperfect proxy for historical executor. No suitable history means capacity-based suggestions, not proven expertise.'
TRANSLATIONS["ar"]['d_r_limits'] = 'تُحتسب المهام المتاحة في المشاريع المختارة فقط. لا تدخل الجودة أو نتائج SLA في ترتيب النسخة الأولى. المنفذ الحالي ليس إثباتًا كاملًا لمن أنجز العمل سابقًا. غياب التاريخ يعني ترشيحًا حسب السعة لا خبرة مثبتة.'

TRANSLATIONS["en"]['d_r_working'] = 'Working…'
TRANSLATIONS["ar"]['d_r_working'] = 'جارٍ التنفيذ…'

TRANSLATIONS["en"]['d_r_saved'] = 'Saved'
TRANSLATIONS["ar"]['d_r_saved'] = 'تم الحفظ'

TRANSLATIONS["en"]['d_r_no_alerts'] = 'No tasks currently need assignment for your account.'
TRANSLATIONS["ar"]['d_r_no_alerts'] = 'لا توجد مهام تحتاج إسنادًا موجهة لحسابك حاليًا.'

TRANSLATIONS["en"]['d_r_alert'] = 'Tasks awaiting your assignment decision'
TRANSLATIONS["ar"]['d_r_alert'] = 'مهام تنتظر قرار الإسناد منك'

TRANSLATIONS["en"]['d_r_read'] = 'Mark read'
TRANSLATIONS["ar"]['d_r_read'] = 'تعليم كمقروء'

TRANSLATIONS["en"]['d_r_select_task'] = 'Select an existing task first.'
TRANSLATIONS["ar"]['d_r_select_task'] = 'اختر مهمة موجودة أولًا.'

TRANSLATIONS["en"]['d_r_confirm_needs'] = 'Mark this task as awaiting an executor? This records a local assignment decision; it does not remove the Bitrix assignee.'
TRANSLATIONS["ar"]['d_r_confirm_needs'] = 'تأكيد أن المهمة تحتاج منفذًا؟ يُسجل القرار محليًا ولا يحذف المسؤول الحالي في Bitrix.'

TRANSLATIONS["en"]['d_r_confirm_self'] = 'Confirm you will personally execute this task?'
TRANSLATIONS["ar"]['d_r_confirm_self'] = 'هل تؤكد أنك ستنفذ هذه المهمة بنفسك؟'

TRANSLATIONS["en"]['d_r_confirm_assign'] = 'Confirm changing the task assignee in Bitrix?'
TRANSLATIONS["ar"]['d_r_confirm_assign'] = 'تأكيد تغيير الموظف المسند إليه في Bitrix؟'

TRANSLATIONS["en"]['d_r_assign'] = 'Confirm assignment in Bitrix'
TRANSLATIONS["ar"]['d_r_assign'] = 'تأكيد الإسناد في Bitrix'

TRANSLATIONS["en"]['d_r_override'] = 'Choose any eligible employee'
TRANSLATIONS["ar"]['d_r_override'] = 'اختيار أي موظف مؤهل'

TRANSLATIONS["en"]['d_r_reason'] = 'Operational reason (optional)'
TRANSLATIONS["ar"]['d_r_reason'] = 'سبب القرار (اختياري)'

TRANSLATIONS["en"]['d_r_no_candidates'] = 'No eligible candidates. Review eligibility, project restrictions, absence and capacity below.'
TRANSLATIONS["ar"]['d_r_no_candidates'] = 'لا يوجد مرشح مؤهل. راجع الأهلية والمشاريع والغياب والسعة أدناه.'

TRANSLATIONS["en"]['d_r_score'] = 'Ranking score / 100 — not a probability'
TRANSLATIONS["ar"]['d_r_score'] = 'درجة ترتيب من 100 — ليست احتمالًا'

TRANSLATIONS["en"]['d_r_cold_start'] = 'No completed similar-task evidence; capacity-based fallback.'
TRANSLATIONS["ar"]['d_r_cold_start'] = 'لا توجد أدلة مهام مشابهة مكتملة؛ الترشيح بديل يعتمد على السعة.'

TRANSLATIONS["en"]['d_r_limited'] = 'Limited completed-task evidence'
TRANSLATIONS["ar"]['d_r_limited'] = 'أدلة إنجاز محدودة'

TRANSLATIONS["en"]['d_r_historical'] = 'Completed-task evidence available'
TRANSLATIONS["ar"]['d_r_historical'] = 'تتوفر أدلة مهام مكتملة'

TRANSLATIONS["en"]['d_r_samples'] = 'Similar completed tasks'
TRANSLATIONS["ar"]['d_r_samples'] = 'مهام مشابهة مكتملة'

TRANSLATIONS["en"]['d_r_active'] = 'Open tasks / capacity'
TRANSLATIONS["ar"]['d_r_active'] = 'مهام مفتوحة / السعة'

TRANSLATIONS["en"]['d_r_excluded'] = 'Excluded candidates and reasons'
TRANSLATIONS["ar"]['d_r_excluded'] = 'المستبعدون وأسباب الاستبعاد'

TRANSLATIONS["en"]['d_r_eligibility_unconfirmed'] = 'Eligibility not confirmed'
TRANSLATIONS["ar"]['d_r_eligibility_unconfirmed'] = 'الأهلية غير معتمدة'

TRANSLATIONS["en"]['d_r_inactive'] = 'Inactive employee'
TRANSLATIONS["ar"]['d_r_inactive'] = 'الموظف غير نشط'

TRANSLATIONS["en"]['d_r_project_not_allowed'] = 'Project not allowed'
TRANSLATIONS["ar"]['d_r_project_not_allowed'] = 'المشروع خارج نطاق الأهلية'

TRANSLATIONS["en"]['d_r_category_not_allowed'] = 'Category not allowed'
TRANSLATIONS["ar"]['d_r_category_not_allowed'] = 'الفئة خارج نطاق الأهلية'

TRANSLATIONS["en"]['d_r_unavailable'] = 'Unavailable'
TRANSLATIONS["ar"]['d_r_unavailable'] = 'غير متاح'

TRANSLATIONS["en"]['d_r_capacity_full'] = 'At capacity'
TRANSLATIONS["ar"]['d_r_capacity_full'] = 'وصل للسعة المحددة'

TRANSLATIONS["en"]['d_r_enabled'] = 'Eligible'
TRANSLATIONS["ar"]['d_r_enabled'] = 'مؤهل'

TRANSLATIONS["en"]['d_r_employee_active'] = 'Active'
TRANSLATIONS["ar"]['d_r_employee_active'] = 'نشط'

TRANSLATIONS["en"]['d_r_id'] = 'User ID'
TRANSLATIONS["ar"]['d_r_id'] = 'معرّف الموظف'

TRANSLATIONS["en"]['d_r_name'] = 'Name'
TRANSLATIONS["ar"]['d_r_name'] = 'الاسم'

TRANSLATIONS["en"]['d_r_projects'] = 'Project IDs'
TRANSLATIONS["ar"]['d_r_projects'] = 'معرّفات المشاريع'

TRANSLATIONS["en"]['d_r_categories'] = 'Categories'
TRANSLATIONS["ar"]['d_r_categories'] = 'الفئات'

TRANSLATIONS["en"]['d_r_max_tasks'] = 'Task capacity'
TRANSLATIONS["ar"]['d_r_max_tasks'] = 'سعة المهام'

TRANSLATIONS["en"]['d_r_away_from'] = 'Away from'
TRANSLATIONS["ar"]['d_r_away_from'] = 'غياب من'

TRANSLATIONS["en"]['d_r_away_to'] = 'Away to'
TRANSLATIONS["ar"]['d_r_away_to'] = 'غياب إلى'

TRANSLATIONS["en"]['d_r_checked'] = 'Last open-task refresh'
TRANSLATIONS["ar"]['d_r_checked'] = 'آخر تحديث للمهام المفتوحة'

TRANSLATIONS["en"]['d_r_evidence'] = 'Completed historical records'
TRANSLATIONS["ar"]['d_r_evidence'] = 'سجلات إنجاز تاريخية'

TRANSLATIONS["en"]['d_r_cadence'] = 'Open tasks: every minute. Historical evidence: every two hours while the server runs.'
TRANSLATIONS["ar"]['d_r_cadence'] = 'المهام المفتوحة: كل دقيقة. الأدلة التاريخية: كل ساعتين أثناء تشغيل الخادم.'

TRANSLATIONS["en"]['d_r_stale'] = 'Source refresh failed or history is not ready. Evidence may be incomplete.'
TRANSLATIONS["ar"]['d_r_stale'] = 'فشل تحديث المصدر أو لم يجهز التاريخ بعد. الأدلة قد تكون ناقصة.'

TRANSLATIONS["en"]['d_r_not_connected'] = 'Configure Bitrix and select projects first.'
TRANSLATIONS["ar"]['d_r_not_connected'] = 'اضبط اتصال Bitrix واختر المشاريع أولًا.'

TRANSLATIONS["en"]['d_r_needs_assignment'] = 'Awaiting executor'
TRANSLATIONS["ar"]['d_r_needs_assignment'] = 'تنتظر منفذًا'

TRANSLATIONS["en"]['d_r_assigned'] = 'Assigned'
TRANSLATIONS["ar"]['d_r_assigned'] = 'مسندة'

TRANSLATIONS["en"]['d_r_self_assigned'] = 'Supervisor executing'
TRANSLATIONS["ar"]['d_r_self_assigned'] = 'المشرف ينفذها'

TRANSLATIONS["en"]['d_r_pending_review'] = 'Pending review'
TRANSLATIONS["ar"]['d_r_pending_review'] = 'بانتظار المراجعة'

TRANSLATIONS["en"]['d_r_closed'] = 'Completed'
TRANSLATIONS["ar"]['d_r_closed'] = 'مكتملة'

TRANSLATIONS["en"]['d_r_no_longer_open'] = 'No longer in open scope'
TRANSLATIONS["ar"]['d_r_no_longer_open'] = 'لم تعد ضمن المهام المفتوحة'

TRANSLATIONS["en"]["d_r_weighted_load"] = "Weighted workload (high-priority task = 1.5; other task = 1)"
TRANSLATIONS["ar"]["d_r_weighted_load"] = "الحمل الموزون (المهمة عالية الأهمية = 1.5، وغيرها = 1)"

# Evidence-led recommendation workspace.
TRANSLATIONS["en"]["d_r_workspace"] = 'Assignment desk'
TRANSLATIONS["ar"]["d_r_workspace"] = 'مكتب إسناد المهام'
TRANSLATIONS["en"]["d_r_intro"] = 'Review the task, inspect the evidence, choose its executor.'
TRANSLATIONS["ar"]["d_r_intro"] = 'راجع المهمة وأدلة الخبرة، ثم اختر الموظف الذي سينفذها.'
TRANSLATIONS["en"]["d_r_policy_short"] = 'Eligibility settings'
TRANSLATIONS["ar"]["d_r_policy_short"] = 'إعدادات الأهلية'
TRANSLATIONS["en"]["d_r_queue_hint"] = 'Tasks held by a project supervisor await an executor unless personally claimed.'
TRANSLATIONS["ar"]["d_r_queue_hint"] = 'المهام لدى مشرف المشروع تحتاج اختيار منفّذ، ما لم يؤكد أنه سيعمل عليها بنفسه.'
TRANSLATIONS["en"]["d_r_task_brief"] = 'What needs to be done?'
TRANSLATIONS["ar"]["d_r_task_brief"] = 'ما المهمة المطلوب تنفيذها؟'
TRANSLATIONS["en"]["d_r_private"] = 'Local analysis'
TRANSLATIONS["ar"]["d_r_private"] = 'تحليل محلي'
TRANSLATIONS["en"]["d_r_query_example"] = 'Analyse payroll and produce a review report for the last three months'
TRANSLATIONS["ar"]["d_r_query_example"] = 'تحليل واستخراج تقرير لمراجعة رواتب الموظفين لآخر 3 شهور'
TRANSLATIONS["en"]["d_r_optional"] = 'Optional'
TRANSLATIONS["ar"]["d_r_optional"] = 'اختياري'
TRANSLATIONS["en"]["d_r_human_decision"] = 'No assignment without your confirmation'
TRANSLATIONS["ar"]["d_r_human_decision"] = 'لا يتغير الإسناد دون تأكيدك'
TRANSLATIONS["en"]["d_r_other_actions"] = 'Other task actions'
TRANSLATIONS["ar"]["d_r_other_actions"] = 'إجراءات أخرى للمهمة'
TRANSLATIONS["en"]["d_r_start_title"] = 'The evidence comes first'
TRANSLATIONS["ar"]["d_r_start_title"] = 'الدليل قبل الترشيح'
TRANSLATIONS["en"]["d_r_start_help"] = 'Select a task from the queue or describe a new task. Relevant work appears beside each employee.'
TRANSLATIONS["ar"]["d_r_start_help"] = 'اختر مهمة من القائمة أو اكتب وصف مهمة جديدة. ستظهر الأعمال ذات الصلة بجانب كل موظف.'
TRANSLATIONS["en"]["d_r_cancel"] = 'Cancel'
TRANSLATIONS["ar"]["d_r_cancel"] = 'إلغاء'
TRANSLATIONS["en"]["d_r_confirm"] = 'Confirm'
TRANSLATIONS["ar"]["d_r_confirm"] = 'تأكيد'
TRANSLATIONS["en"]["d_r_no_evidence"] = 'No relevant work was found. We will not recommend someone only because they have spare capacity.'
TRANSLATIONS["ar"]["d_r_no_evidence"] = 'لم نجد أعمالًا مرتبطة بهذا الوصف. لن نرشّح شخصًا لمجرد أن لديه وقتًا متاحًا.'
TRANSLATIONS["en"]["d_r_no_completed_match"] = 'No eligible employee has a matching completed task in the available records.'
TRANSLATIONS["ar"]["d_r_no_completed_match"] = 'لا توجد مهمة مكتملة مرتبطة بهذا الوصف لموظف مؤهل ضمن السجلات المتاحة.'
TRANSLATIONS["en"]["d_r_provisional_title"] = 'Related open work'
TRANSLATIONS["ar"]["d_r_provisional_title"] = 'أعمال جارية ذات صلة'
TRANSLATIONS["en"]["d_r_provisional_help"] = 'These employees hold similar open tasks. This suggests subject exposure, not proven successful delivery.'
TRANSLATIONS["ar"]["d_r_provisional_help"] = 'لدى هؤلاء الموظفين مهام مفتوحة مشابهة. هذه صلة بالمجال، وليست دليلًا على إنجاز ناجح.'
TRANSLATIONS["en"]["d_r_open_only"] = 'Open-task evidence · completion unverified'
TRANSLATIONS["ar"]["d_r_open_only"] = 'دليل من مهمة مفتوحة · الإنجاز غير مثبت'
TRANSLATIONS["en"]["d_r_open_matches"] = 'Similar open tasks'
TRANSLATIONS["ar"]["d_r_open_matches"] = 'مهام مفتوحة مشابهة'
TRANSLATIONS["en"]["d_r_matched_terms"] = 'Shared subject terms'
TRANSLATIONS["ar"]["d_r_matched_terms"] = 'الكلمات المشتركة'
TRANSLATIONS["en"]["d_r_score_details"] = 'How this recommendation was ranked'
TRANSLATIONS["ar"]["d_r_score_details"] = 'كيف احتُسب ترتيب هذا الترشيح؟'
TRANSLATIONS["en"]["d_r_result_title"] = 'Evidence and candidates'
TRANSLATIONS["ar"]["d_r_result_title"] = 'الأدلة والمرشحون'
TRANSLATIONS["en"]["d_r_manual_only"] = 'Eligible, without matching evidence — manual choice only'
TRANSLATIONS["ar"]["d_r_manual_only"] = 'مؤهلون دون دليل مرتبط — للاختيار اليدوي فقط'
TRANSLATIONS["en"]["d_r_manual_help"] = 'You may choose any eligible employee. Names without matching evidence are not system recommendations.'
TRANSLATIONS["ar"]["d_r_manual_help"] = 'يمكنك اختيار أي موظف مؤهل. الأسماء دون دليل مرتبط ليست توصيات من النظام.'
TRANSLATIONS["en"]["d_r_choose_employee"] = 'Choose an employee'
TRANSLATIONS["ar"]["d_r_choose_employee"] = 'اختر الموظف'
TRANSLATIONS["en"]["d_r_limits"] = 'Results use accessible Bitrix projects. Completed work supports recommendations; similar open work is shown separately. Capacity alone never establishes task suitability.'
TRANSLATIONS["ar"]["d_r_limits"] = 'النتائج ضمن مشاريع بتركس المتاحة. الإنجاز السابق يدعم الترشيح، وتظهر المهام المفتوحة المشابهة منفصلة. الفراغ وحده لا يثبت ملاءمة الموظف.'
TRANSLATIONS["en"]["d_r_intake"] = 'Additional supervisor / intake IDs'
TRANSLATIONS["ar"]["d_r_intake"] = 'معرّفات مشرفين أو حسابات استقبال إضافية'
TRANSLATIONS["en"]["d_r_routing_help"] = 'Project owners and moderators are detected from Bitrix. Their tasks await an executor until personally claimed. Extra intake IDs cover other supervisors. Blank notification recipients use project owners; the holding supervisor also receives the alert.'
TRANSLATIONS["ar"]["d_r_routing_help"] = 'يُكتشف مالك المشروع والمشرفون من بتركس تلقائيًا. مهامهم تنتظر منفذًا حتى يؤكدوا التنفيذ بأنفسهم. أضف معرّفات المشرفين الآخرين عند الحاجة. يصل التنبيه لمالك المشروع افتراضيًا وللمشرف الذي لديه المهمة.'
TRANSLATIONS["en"]["d_r_cold_start"] = 'No completed evidence; not a recommendation'
TRANSLATIONS["ar"]["d_r_cold_start"] = 'لا توجد أدلة إنجاز؛ ليس ترشيحًا'
TRANSLATIONS["en"]["d_r_no_relevance"] = 'No related task evidence'
TRANSLATIONS["ar"]["d_r_no_relevance"] = 'لا توجد أدلة مهام ذات صلة'

TRANSLATIONS["en"]["d_r_blocked_evidence"]='Relevant work, eligibility blocked'
TRANSLATIONS["ar"]["d_r_blocked_evidence"]='أعمال مرتبطة، لكن الأهلية غير مستوفاة'

TRANSLATIONS["en"]["d_r_blocked_help"]='The evidence points to these employees, but an eligibility rule prevents recommending or assigning them. Review the rule before proceeding.'
TRANSLATIONS["ar"]["d_r_blocked_help"]='تشير الأدلة إلى هؤلاء الموظفين، لكن أحد شروط الأهلية يمنع ترشيحهم أو إسناد المهمة لهم. راجع السبب أولًا.'

TRANSLATIONS["en"]["d_r_eligibility_blocked"]='Requires eligibility review'
TRANSLATIONS["ar"]["d_r_eligibility_blocked"]='يتطلب مراجعة الأهلية'

TRANSLATIONS["en"]["d_r_review_eligibility"]='Review this employee’s eligibility'
TRANSLATIONS["ar"]["d_r_review_eligibility"]='مراجعة أهلية هذا الموظف'

TRANSLATIONS["en"]['d_tasks_analysis']='Tasks, similarity & assignment'
TRANSLATIONS["ar"]['d_tasks_analysis']='المهام والتشابه والإسناد'

TRANSLATIONS["en"]['d_workspace_sections']='Task workspace sections'
TRANSLATIONS["ar"]['d_workspace_sections']='أقسام مساحة المهام'

TRANSLATIONS["en"]['d_analysis_tab']='Analyse a task'
TRANSLATIONS["ar"]['d_analysis_tab']='تحليل مهمة'

TRANSLATIONS["en"]['d_assignment_tab']='Assignment decisions'
TRANSLATIONS["ar"]['d_assignment_tab']='قرارات الإسناد'

TRANSLATIONS["en"]['d_history_tab']='History & updates'
TRANSLATIONS["ar"]['d_history_tab']='السجل والتحديثات'

TRANSLATIONS["en"]['d_analysis_intro']='Find related work, compare employee experience and workload, and review tasks you supervise.'
TRANSLATIONS["ar"]['d_analysis_intro']='ابحث عن أعمال مشابهة، وقارن خبرة الموظفين وضغط العمل، وراجع المهام التي تشرف عليها.'

TRANSLATIONS["en"]['d_r_queue_hint']='Tasks you own or observe that still need an executor. Project membership alone does not grant supervision.'
TRANSLATIONS["ar"]['d_r_queue_hint']='المهام التي أنشأتها أو تراقبها وتحتاج منفذًا. عضوية المشروع وحدها لا تجعلك مشرفًا على مهامه.'

TRANSLATIONS["en"]['d_r_capacity']='Workload balance'
TRANSLATIONS["ar"]['d_r_capacity']='موازنة ضغط العمل'

TRANSLATIONS["en"]['d_r_active']='Open tasks'
TRANSLATIONS["ar"]['d_r_active']='المهام المفتوحة'

TRANSLATIONS["en"]['d_r_routing_help']='The task owner and its listed observers can manage assignment, subject to live Bitrix permission. An assignee alone cannot reassign through this workspace. Owner-as-assignee means awaiting an executor until personal execution is confirmed.'
TRANSLATIONS["ar"]['d_r_routing_help']='منشئ المهمة والمراقبون المسجلون عليها يديرون الإسناد مع التحقق من صلاحية بتركس. كونك المنفذ فقط لا يمنحك حق إعادة الإسناد هنا. إذا كان المنشئ هو المنفذ، تنتظر المهمة اختيار موظف ما لم يؤكد التنفيذ بنفسه.'

TRANSLATIONS["en"]['d_r_policy_help']='Confirm employee eligibility, projects, categories and absence. Workload affects ranking without a maximum task count or automatic exclusion.'
TRANSLATIONS["ar"]['d_r_policy_help']='اعتمد أهلية الموظف ومشاريعه وفئاته والغياب. ضغط العمل يؤثر في الترتيب دون حد أقصى لعدد المهام أو استبعاد تلقائي.'

TRANSLATIONS["en"]['d_grouped_duplicates']='Identical task content is grouped; all source IDs and assignees are retained. Different IDs remain separate source tasks.'
TRANSLATIONS["ar"]['d_grouped_duplicates']='جُمّع المحتوى المتطابق مع إظهار جميع المعرّفات والمنفذين. اختلاف المعرّف يعني سجلًا مستقلًا في المصدر.'

TRANSLATIONS["en"]["d_r_start_help"] = "Select a task you supervise to review its candidates. Use Analyse a task for a new description."
TRANSLATIONS["ar"]["d_r_start_help"] = "اختر مهمة تشرف عليها لمراجعة المرشحين. استخدم تبويب تحليل مهمة لتجربة وصف جديد."

TRANSLATIONS["en"]["d_r_queue_search"]='Find a task'
TRANSLATIONS["ar"]["d_r_queue_search"]='ابحث عن مهمة'

TRANSLATIONS["en"]["d_r_scope"]='Show'
TRANSLATIONS["ar"]["d_r_scope"]='عرض'

TRANSLATIONS["en"]["d_r_all_supervised"]='All tasks I supervise'
TRANSLATIONS["ar"]["d_r_all_supervised"]='كل المهام التي أشرف عليها'

TRANSLATIONS["en"]["d_r_sort"]='Order by'
TRANSLATIONS["ar"]["d_r_sort"]='الترتيب حسب'

TRANSLATIONS["en"]["d_r_deadline"]='Deadline'
TRANSLATIONS["ar"]["d_r_deadline"]='الموعد النهائي'

TRANSLATIONS["en"]["d_r_review_task"]='Review task and candidates'
TRANSLATIONS["ar"]["d_r_review_task"]='مراجعة المهمة والمرشحين'

TRANSLATIONS["en"]["d_r_close"]='Close'
TRANSLATIONS["ar"]["d_r_close"]='إغلاق'

TRANSLATIONS["en"]["d_r_decisions"]='Decision log'
TRANSLATIONS["ar"]["d_r_decisions"]='سجل القرارات'

TRANSLATIONS["en"]["d_r_decisions_help"]='Recent decisions on tasks you may supervise. Source permissions and current visibility apply.'
TRANSLATIONS["ar"]["d_r_decisions_help"]='القرارات الأخيرة للمهام التي يحق لك الإشراف عليها، ضمن صلاحيات المصدر والنطاق المتاح.'

TRANSLATIONS["en"]["d_r_no_decisions"]='No recorded decisions in the current scope.'
TRANSLATIONS["ar"]["d_r_no_decisions"]='لا توجد قرارات مسجلة ضمن النطاق الحالي.'

TRANSLATIONS["en"]["d_r_task_status"]='Source status'
TRANSLATIONS["ar"]["d_r_task_status"]='حالة المصدر'

TRANSLATIONS["en"]["d_r_assignee"]='Executor ID'
TRANSLATIONS["ar"]["d_r_assignee"]='معرّف المنفّذ'

TRANSLATIONS["en"]["d_r_owner"]='Owner ID'
TRANSLATIONS["ar"]["d_r_owner"]='معرّف منشئ المهمة'

TRANSLATIONS["en"]["d_r_completed_at"]='Completed on'
TRANSLATIONS["ar"]["d_r_completed_at"]='تاريخ الإنجاز'

TRANSLATIONS["en"]["d_r_missing_description"]='No description is available from the source.'
TRANSLATIONS["ar"]["d_r_missing_description"]='لا يوجد وصف متاح من المصدر.'

TRANSLATIONS["en"]["d_r_priority"]='Priority'
TRANSLATIONS["ar"]["d_r_priority"]='الأولوية'

TRANSLATIONS["en"]["d_r_elapsed"]='Historical elapsed time, including waiting'
TRANSLATIONS["ar"]["d_r_elapsed"]='المدة التاريخية المنقضية، وتشمل الانتظار'

TRANSLATIONS["en"]["d_r_hours"]='hours'
TRANSLATIONS["ar"]["d_r_hours"]='ساعة'

TRANSLATIONS["en"]["d_r_choose_candidate"]='Choose this employee'
TRANSLATIONS["ar"]["d_r_choose_candidate"]='اختيار هذا الموظف'

TRANSLATIONS["en"]["d_r_release"]='Reconcile unsuccessful assignment'
TRANSLATIONS["ar"]["d_r_release"]='تسوية محاولة إسناد لم تنجح'

TRANSLATIONS["en"]["d_r_confirm_release"]='The source will be checked. Release the uncertain attempt only if the requested employee is not the current executor.'
TRANSLATIONS["ar"]["d_r_confirm_release"]='سيُفحص المصدر. تُغلق المحاولة غير المؤكدة فقط إذا لم يكن الموظف المطلوب هو المنفّذ الحالي.'

TRANSLATIONS["en"]["d_r_recommendation"]='Recommendation generated'
TRANSLATIONS["ar"]["d_r_recommendation"]='إنشاء توصية'

TRANSLATIONS["en"]["d_r_assignee_changed"]='Executor changed in source'
TRANSLATIONS["ar"]["d_r_assignee_changed"]='تغيّر المنفّذ في المصدر'

TRANSLATIONS["en"]["d_r_observed_completion"]='Completion observed'
TRANSLATIONS["ar"]["d_r_observed_completion"]='رصد إنجاز المهمة'

TRANSLATIONS["en"]["d_r_self"]='Personal execution confirmed'
TRANSLATIONS["ar"]["d_r_self"]='تأكيد التنفيذ الشخصي'

TRANSLATIONS["en"]["d_r_diwan_mapping"]='Diwan role mapping'
TRANSLATIONS["ar"]["d_r_diwan_mapping"]='ربط أدوار ديوان'

TRANSLATIONS["en"]["d_r_diwan_mapping_help"]='Enter the verified field containing supervisor identity and the identity belonging to your token. Nested paths are supported. Request owner, pending department and executor are not assumed interchangeable.'
TRANSLATIONS["ar"]["d_r_diwan_mapping_help"]='أدخل مسار حقل هوية مشرف المهمة بعد التحقق من معناه، وهوية حساب توكنك. يمكن استخدام مسارات متداخلة. لا يُفترض أن صاحب الطلب أو جهة انتظار الطلب هو المنفّذ.'

TRANSLATIONS["en"]["d_r_supervisor_field"]='Verified supervisor identity field'
TRANSLATIONS["ar"]["d_r_supervisor_field"]='حقل هوية المشرف الموثّق'

TRANSLATIONS["en"]["d_r_current_identity"]='Identity belonging to this token'
TRANSLATIONS["ar"]["d_r_current_identity"]='هوية الحساب الخاص بهذا التوكن'

TRANSLATIONS["en"]["d_r_roles_confirmed"]='I verified the field meanings and token identity with the service administrator.'
TRANSLATIONS["ar"]["d_r_roles_confirmed"]='تحققت من معاني الحقول وهوية التوكن مع مسؤول الخدمة.'

TRANSLATIONS["en"]["d_r_diwan_policy"]='Diwan recipients and absences are maintained in connection settings.'
TRANSLATIONS["ar"]["d_r_diwan_policy"]='تُدار أسماء منفّذي ديوان وفترات غيابهم في إعدادات الاتصال.'

TRANSLATIONS["en"]["d_r_diwan_setup"]='Connect Diwan and verify its supervisor field and token identity in Settings before using assignment recommendations.'
TRANSLATIONS["ar"]["d_r_diwan_setup"]='اربط ديوان واضبط حقل المشرف وهوية التوكن في الإعدادات قبل استخدام توصيات الإسناد.'

TRANSLATIONS["en"]["d_quality_title"]='Data quality and coverage'
TRANSLATIONS["ar"]["d_quality_title"]='جودة البيانات والتغطية'

TRANSLATIONS["en"]["d_history_prev"]='Previous'
TRANSLATIONS["ar"]["d_history_prev"]='السابق'

TRANSLATIONS["en"]["d_history_next"]='Next'
TRANSLATIONS["ar"]["d_history_next"]='التالي'

TRANSLATIONS["en"]["d_quality_records"]='Accessible records'
TRANSLATIONS["ar"]["d_quality_records"]='السجلات المتاحة'

TRANSLATIONS["en"]["d_quality_completed"]='Completed records'
TRANSLATIONS["ar"]["d_quality_completed"]='السجلات المكتملة'

TRANSLATIONS["en"]["d_quality_invalid_completion_dates"]='Completed records with invalid dates'
TRANSLATIONS["ar"]["d_quality_invalid_completion_dates"]='سجلات مكتملة بتواريخ غير صالحة'

TRANSLATIONS["en"]["d_quality_missing_description"]='Missing descriptions'
TRANSLATIONS["ar"]["d_quality_missing_description"]='أوصاف مفقودة'

TRANSLATIONS["en"]["d_quality_missing_category"]='Missing categories'
TRANSLATIONS["ar"]["d_quality_missing_category"]='تصنيفات مفقودة'

TRANSLATIONS["en"]["d_quality_missing_executor"]='Missing executor identities'
TRANSLATIONS["ar"]["d_quality_missing_executor"]='هويات منفّذ مفقودة'

TRANSLATIONS["en"]["d_quality_duplicate_content_groups"]='Groups with identical content'
TRANSLATIONS["ar"]["d_quality_duplicate_content_groups"]='مجموعات بمحتوى متطابق'

TRANSLATIONS["en"]["d_quality_first_created"]='Earliest creation date'
TRANSLATIONS["ar"]["d_quality_first_created"]='أقدم تاريخ إنشاء'

TRANSLATIONS["en"]["d_quality_last_created"]='Latest creation date'
TRANSLATIONS["ar"]["d_quality_last_created"]='أحدث تاريخ إنشاء'

TRANSLATIONS["en"]["d_r_data_fields"]='Source field mapping'
TRANSLATIONS["ar"]["d_r_data_fields"]='ربط حقول المصدر'

TRANSLATIONS["en"]["d_r_data_fields_help"]='Select verified source fields. Values are retained as evidence and outcomes; quality and delivery codes are not automatically converted into performance scores.'
TRANSLATIONS["ar"]["d_r_data_fields_help"]='اختر حقول المصدر بعد التحقق من معناها. تُحفظ قيمها ضمن الأدلة والنتائج؛ لا تتحول رموز الجودة والتسليم تلقائيًا إلى درجات أداء.'

TRANSLATIONS["en"]["d_r_field_quality"]='Task quality'
TRANSLATIONS["ar"]["d_r_field_quality"]='جودة المهمة'

TRANSLATIONS["en"]["d_r_field_delivery"]='Delivery outcome'
TRANSLATIONS["ar"]["d_r_field_delivery"]='نتيجة التسليم'

TRANSLATIONS["en"]["d_r_field_team"]='Team'
TRANSLATIONS["ar"]["d_r_field_team"]='الفريق'

TRANSLATIONS["en"]["d_r_field_department"]='Department'
TRANSLATIONS["ar"]["d_r_field_department"]='الإدارة'

TRANSLATIONS["en"]["d_r_field_task_type"]='Task type'
TRANSLATIONS["ar"]["d_r_field_task_type"]='نوع المهمة'

TRANSLATIONS["en"]["d_r_field_effort"]='Recorded effort'
TRANSLATIONS["ar"]["d_r_field_effort"]='الجهد المسجل'

TRANSLATIONS["en"]["d_r_field_reopened"]='Reopened indicator'
TRANSLATIONS["ar"]["d_r_field_reopened"]='مؤشر إعادة الفتح'

TRANSLATIONS["en"]["d_r_limits"] = "Results use accessible source records. Completed work supports recommendations; similar open work is shown separately. Workload alone does not establish suitability."
TRANSLATIONS["ar"]["d_r_limits"] = "النتائج من سجلات المصدر المتاحة. الإنجاز السابق يدعم الترشيح، وتظهر المهام المفتوحة المشابهة منفصلة. انخفاض الضغط وحده لا يثبت الملاءمة."
TRANSLATIONS["en"]["d_r_self"] = "I will do this task myself"
TRANSLATIONS["ar"]["d_r_self"] = "سأنفذ هذه المهمة بنفسي"

TRANSLATIONS["en"]["d_error_roles_required"] = "Configure and confirm Diwan supervisor, executor and current-user mappings in Settings first."
TRANSLATIONS["ar"]["d_error_roles_required"] = "اضبط واعتمد حقول مشرف ديوان والمنفذ وهوية حسابك في الإعدادات أولًا."

# Evidence discovery and typed task coverage.
TRANSLATIONS["en"]["d_r_people"] = 'Employee evidence'
TRANSLATIONS["ar"]["d_r_people"] = 'أدلة خبرات الموظفين'
TRANSLATIONS["en"]["d_r_people_help"] = 'Explore completed work by person and topic within your accessible source records. Labels describe observed work, not certified skills.'
TRANSLATIONS["ar"]["d_r_people_help"] = 'استعرض الأعمال المكتملة حسب الموظف والمجال ضمن سجلات المصدر المتاحة لك. التصنيفات تصف أعمالًا سابقة، وليست مهارات معتمدة.'
TRANSLATIONS["en"]["d_r_people_search"] = 'Name or observed topic'
TRANSLATIONS["ar"]["d_r_people_search"] = 'اسم الموظف أو مجال أعماله السابقة'
TRANSLATIONS["en"]["d_r_people_empty"] = 'No employees match these filters.'
TRANSLATIONS["ar"]["d_r_people_empty"] = 'لا يوجد موظفون يطابقون البحث.'
TRANSLATIONS["en"]["d_r_profile"] = 'View evidence profile'
TRANSLATIONS["ar"]["d_r_profile"] = 'عرض ملف الأدلة'
TRANSLATIONS["en"]["d_r_back_results"] = 'Back to results'
TRANSLATIONS["ar"]["d_r_back_results"] = 'العودة إلى النتائج'
TRANSLATIONS["en"]["d_r_profile_work"] = 'Completed work'
TRANSLATIONS["ar"]["d_r_profile_work"] = 'الأعمال المكتملة'
TRANSLATIONS["en"]["d_r_profile_no_work"] = 'No completed work is available for this employee in the current source scope.'
TRANSLATIONS["ar"]["d_r_profile_no_work"] = 'لا تتوفر أعمال مكتملة لهذا الموظف ضمن نطاق المصدر الحالي.'
TRANSLATIONS["en"]["d_r_profile_topics"] = 'Topics observed in completed work'
TRANSLATIONS["ar"]["d_r_profile_topics"] = 'المجالات الظاهرة في الأعمال المكتملة'
TRANSLATIONS["en"]["d_r_profile_note"] = 'Counts reflect accessible records and the recorded assignee. They are not a performance rating or proof of who completed every step.'
TRANSLATIONS["ar"]["d_r_profile_note"] = 'تعكس الأعداد السجلات المتاحة والمنفّذ المسجّل. ليست تقييمًا للأداء أو إثباتًا لمن أنجز كل خطوة.'
TRANSLATIONS["en"]["d_r_BUSINESS_DOMAIN"] = 'Business domains'
TRANSLATIONS["ar"]["d_r_BUSINESS_DOMAIN"] = 'مجالات العمل'
TRANSLATIONS["en"]["d_r_TASK_TYPE"] = 'Types of work'
TRANSLATIONS["ar"]["d_r_TASK_TYPE"] = 'أنواع العمل'
TRANSLATIONS["en"]["d_r_SYSTEM_OR_TOOL"] = 'Systems and tools'
TRANSLATIONS["ar"]["d_r_SYSTEM_OR_TOOL"] = 'الأنظمة والأدوات'
TRANSLATIONS["en"]["d_r_DELIVERABLE_TYPE"] = 'Deliverables'
TRANSLATIONS["ar"]["d_r_DELIVERABLE_TYPE"] = 'المخرجات'
TRANSLATIONS["en"]["d_r_CONCEPT"] = 'Concepts'
TRANSLATIONS["ar"]["d_r_CONCEPT"] = 'المفاهيم'
TRANSLATIONS["en"]["d_r_inferred_topics"] = 'Task understanding'
TRANSLATIONS["ar"]["d_r_inferred_topics"] = 'فهم المهمة'
TRANSLATIONS["en"]["d_r_inferred_help"] = 'Labels extracted locally from the description. Coverage measures known topics only; it does not capture every requirement.'
TRANSLATIONS["ar"]["d_r_inferred_help"] = 'تصنيفات مستخرجة محليًا من الوصف. التغطية تقيس المجالات المعروفة فقط، ولا تمثل جميع متطلبات المهمة.'
TRANSLATIONS["en"]["d_r_no_labels"] = 'No known labels detected; matching uses the task text.'
TRANSLATIONS["ar"]["d_r_no_labels"] = 'لم تُكتشف تصنيفات معروفة؛ تُستخدم كلمات المهمة في المطابقة.'
TRANSLATIONS["en"]["d_r_covered"] = 'Supported by related completed work'
TRANSLATIONS["ar"]["d_r_covered"] = 'تدعمها أعمال مكتملة مرتبطة'
TRANSLATIONS["en"]["d_r_missing_topics"] = 'Not evidenced in related completed work'
TRANSLATIONS["ar"]["d_r_missing_topics"] = 'لم تظهر في الأعمال المكتملة المرتبطة'
TRANSLATIONS["en"]["d_r_no_topic_coverage"] = 'No topic coverage established'
TRANSLATIONS["ar"]["d_r_no_topic_coverage"] = 'لم تثبت تغطية المجالات'
TRANSLATIONS["en"]["d_r_why_person"] = 'Why this employee?'
TRANSLATIONS["ar"]["d_r_why_person"] = 'لماذا هذا الموظف؟'
TRANSLATIONS["en"]["d_r_lexical"] = 'Text relevance'
TRANSLATIONS["ar"]["d_r_lexical"] = 'تشابه النص'
TRANSLATIONS["en"]["d_r_coverage"] = 'Known-topic coverage'
TRANSLATIONS["ar"]["d_r_coverage"] = 'تغطية المجالات المعروفة'
TRANSLATIONS["en"]["d_r_coverage_formula"] = 'Similarity combines 75% text relevance and 25% topic coverage when topics are known. The final score is a ranking aid, not a probability.'
TRANSLATIONS["ar"]["d_r_coverage_formula"] = 'يجمع التشابه 75% من تشابه النص و25% من تغطية المجالات عندما تكون معروفة. الدرجة تساعد على الترتيب وليست احتمال نجاح.'
TRANSLATIONS["en"]["d_r_complementary"] = 'Complementary experience'
TRANSLATIONS["ar"]["d_r_complementary"] = 'خبرات متكاملة'
TRANSLATIONS["en"]["d_r_complementary_help"] = 'These people bring different parts of the requested experience. This is a discussion suggestion, not a team assignment or a recommendation to split the task.'
TRANSLATIONS["ar"]["d_r_complementary_help"] = 'يغطي هؤلاء جوانب مختلفة من الخبرة المطلوبة. هذا اقتراح للاستفادة من خبراتهم، وليس إسنادًا جماعيًا أو توصية بتجزئة المهمة.'
TRANSLATIONS["en"]["d_r_all_topics"] = 'All topics'
TRANSLATIONS["ar"]["d_r_all_topics"] = 'جميع المجالات'
TRANSLATIONS["en"]["d_r_topic_filter"] = 'Observed topic'
TRANSLATIONS["ar"]["d_r_topic_filter"] = 'المجال المرصود'
TRANSLATIONS["en"]["d_r_page"] = 'Page'
TRANSLATIONS["ar"]["d_r_page"] = 'الصفحة'
TRANSLATIONS["en"]["d_r_scope_count"] = 'Employees in these results'
TRANSLATIONS["ar"]["d_r_scope_count"] = 'الموظفون في هذه النتائج'
TRANSLATIONS["en"]["d_r_completed_count"] = 'Accessible completions'
TRANSLATIONS["ar"]["d_r_completed_count"] = 'الأعمال المكتملة المتاحة'
TRANSLATIONS["en"]["d_r_open_count"] = 'Current open work'
TRANSLATIONS["ar"]["d_r_open_count"] = 'الأعمال المفتوحة الحالية'
TRANSLATIONS["en"]["d_r_unknown_coverage"] = 'Not measured'
TRANSLATIONS["ar"]["d_r_unknown_coverage"] = 'غير مقاسة'

# Shared page structure and workspace navigation.
TRANSLATIONS["en"]["ui_work"] = 'Workspace'
TRANSLATIONS["ar"]["ui_work"] = 'مساحة العمل'
TRANSLATIONS["en"]["ui_discover"] = 'Discover'
TRANSLATIONS["ar"]["ui_discover"] = 'الاستكشاف'
TRANSLATIONS["en"]["ui_manage"] = 'Management'
TRANSLATIONS["ar"]["ui_manage"] = 'الإدارة'
TRANSLATIONS["en"]["ui_main_nav"] = 'Main navigation'
TRANSLATIONS["ar"]["ui_main_nav"] = 'التنقل الرئيسي'
TRANSLATIONS["en"]["ui_menu"] = 'Menu'
TRANSLATIONS["ar"]["ui_menu"] = 'القائمة'
TRANSLATIONS["en"]["ui_skip"] = 'Skip to content'
TRANSLATIONS["ar"]["ui_skip"] = 'الانتقال إلى المحتوى'
TRANSLATIONS["en"]["ui_task_tools"] = 'Workspace tools'
TRANSLATIONS["ar"]["ui_task_tools"] = 'أدوات مساحة المهام'
TRANSLATIONS["en"]["ui_analysis_help"] = 'Describe the work. Compare relevant employees, then inspect the tasks behind the recommendation.'
TRANSLATIONS["ar"]["ui_analysis_help"] = 'صف العمل المطلوب، وقارن الموظفين المناسبين، ثم افحص المهام التي تدعم الترشيح.'
TRANSLATIONS["en"]["ui_analysis_example"] = 'For example: review the last three months of payroll and prepare a report.'
TRANSLATIONS["ar"]["ui_analysis_example"] = 'مثال: مراجعة رواتب الموظفين لآخر ثلاثة أشهر وإعداد تقرير.'
TRANSLATIONS["en"]["ui_options"] = 'Search scope and category'
TRANSLATIONS["ar"]["ui_options"] = 'نطاق البحث والتصنيف'
TRANSLATIONS["en"]["ui_scope_help"] = 'Results use the source and projects available to your profile.'
TRANSLATIONS["ar"]["ui_scope_help"] = 'تعتمد النتائج على المصدر والمشاريع المتاحة لملفك.'
TRANSLATIONS["en"]["ui_results"] = 'Analysis results'
TRANSLATIONS["ar"]["ui_results"] = 'نتائج التحليل'
TRANSLATIONS["en"]["ui_candidates"] = 'Employees'
TRANSLATIONS["ar"]["ui_candidates"] = 'الموظفون'
TRANSLATIONS["en"]["ui_related"] = 'Related tasks'
TRANSLATIONS["ar"]["ui_related"] = 'المهام المشابهة'
TRANSLATIONS["en"]["ui_analysis_empty_title"] = 'Find the right experience for your task'
TRANSLATIONS["ar"]["ui_analysis_empty_title"] = 'ابحث عن الخبرة المناسبة للمهمة'
TRANSLATIONS["en"]["ui_analysis_empty_help"] = 'Start with a clear description of the subject and tools needed. Results explain the evidence, missing coverage and current workload.'
TRANSLATIONS["ar"]["ui_analysis_empty_help"] = 'ابدأ بوصف واضح للمجال والأدوات المطلوبة. توضح النتائج الأدلة والجوانب غير المثبتة وضغط العمل الحالي.'
TRANSLATIONS["en"]["ui_related_empty_title"] = 'Related work will appear here'
TRANSLATIONS["ar"]["ui_related_empty_title"] = 'ستظهر الأعمال المشابهة هنا'
TRANSLATIONS["en"]["ui_no_related_help"] = 'Try a more specific description or check the history coverage in Workspace tools.'
TRANSLATIONS["ar"]["ui_no_related_help"] = 'جرّب وصفًا أكثر تحديدًا، أو تحقق من تغطية البيانات التاريخية ضمن أدوات مساحة المهام.'
TRANSLATIONS["en"]["ui_query_summary"] = 'Analysed task'
TRANSLATIONS["ar"]["ui_query_summary"] = 'المهمة التي تم تحليلها'
TRANSLATIONS["en"]["ui_refine"] = 'Refine description'
TRANSLATIONS["ar"]["ui_refine"] = 'تعديل الوصف'
TRANSLATIONS["en"]["ui_task_context"] = 'Task context'
TRANSLATIONS["ar"]["ui_task_context"] = 'سياق المهمة'
TRANSLATIONS["en"]["ui_evidence_basis"] = 'Evidence basis'
TRANSLATIONS["ar"]["ui_evidence_basis"] = 'أساس الأدلة'
TRANSLATIONS["en"]["ui_show_more"] = 'Show more tasks'
TRANSLATIONS["ar"]["ui_show_more"] = 'عرض المزيد من المهام'
TRANSLATIONS["en"]["ui_history_count"] = 'Showing {shown} tasks on this page · {total} in the available history'
TRANSLATIONS["ar"]["ui_history_count"] = 'عرض {shown} مهمة في هذه الصفحة · {total} في السجل المتاح'
TRANSLATIONS["en"]["ui_people_help"] = 'Find an employee by name or observed experience. Open a profile to inspect completed work.'
TRANSLATIONS["ar"]["ui_people_help"] = 'ابحث عن موظف بالاسم أو الخبرة المرصودة، ثم افتح ملفه لفحص أعماله المكتملة.'
TRANSLATIONS["en"]["ui_queue_filters"] = 'Queue filters'
TRANSLATIONS["ar"]["ui_queue_filters"] = 'تصفية قائمة المهام'
TRANSLATIONS["en"]["ui_select_task"] = 'Choose a task to review'
TRANSLATIONS["ar"]["ui_select_task"] = 'اختر مهمة للمراجعة'
TRANSLATIONS["en"]["ui_history_intro"] = 'Monitor refreshes, inspect coverage and browse the accessible task history.'
TRANSLATIONS["ar"]["ui_history_intro"] = 'تابع التحديثات، وافحص التغطية، واستعرض التاريخ المتاح للمهام.'
TRANSLATIONS["en"]["ui_diagnostics"] = 'Coverage diagnostics'
TRANSLATIONS["ar"]["ui_diagnostics"] = 'تفاصيل التغطية'
TRANSLATIONS["en"]["ui_connections"] = 'Connections'
TRANSLATIONS["ar"]["ui_connections"] = 'الاتصالات'
TRANSLATIONS["en"]["ui_connection_help"] = 'Configure each source, then manage recipients and analysis rules.'
TRANSLATIONS["ar"]["ui_connection_help"] = 'اضبط كل مصدر، ثم أدر الموظفين المستلمين وقواعد التحليل.'
TRANSLATIONS["en"]["ui_diwan_connection"] = 'Diwan connection'
TRANSLATIONS["ar"]["ui_diwan_connection"] = 'اتصال ديوان'
TRANSLATIONS["en"]["ui_bitrix_connection"] = 'Bitrix connection'
TRANSLATIONS["ar"]["ui_bitrix_connection"] = 'اتصال بتركس'
TRANSLATIONS["en"]["ui_recipients"] = 'Recipients'
TRANSLATIONS["ar"]["ui_recipients"] = 'الموظفون المستلمون'
TRANSLATIONS["en"]["ui_analysis_rules"] = 'Analysis rules'
TRANSLATIONS["ar"]["ui_analysis_rules"] = 'قواعد التحليل'
TRANSLATIONS["en"]["ui_settings_nav"] = 'Settings sections'
TRANSLATIONS["ar"]["ui_settings_nav"] = 'أقسام الإعدادات'
TRANSLATIONS["en"]["ui_credentials"] = 'Connection and identity'
TRANSLATIONS["ar"]["ui_credentials"] = 'الاتصال والهوية'
TRANSLATIONS["en"]["ui_workspace_storage"] = 'Workspace and folders'
TRANSLATIONS["ar"]["ui_workspace_storage"] = 'مساحة العمل والمجلدات'
TRANSLATIONS["en"]["ui_projects"] = 'Project scope'
TRANSLATIONS["ar"]["ui_projects"] = 'نطاق المشاريع'
TRANSLATIONS["en"]["ui_schedule"] = 'Work schedule'
TRANSLATIONS["ar"]["ui_schedule"] = 'جدول العمل'
TRANSLATIONS["en"]["ui_settings_help"] = 'Configure your connection and workspace, then choose the projects you work with.'
TRANSLATIONS["ar"]["ui_settings_help"] = 'اضبط اتصالك ومساحة العمل، ثم اختر المشاريع التي تعمل عليها.'
TRANSLATIONS["en"]["ui_diwan_search_help"] = 'Search fetched requests. Open a request for details and delegation.'
TRANSLATIONS["ar"]["ui_diwan_search_help"] = 'ابحث في الطلبات التي تم جلبها، وافتح الطلب لعرض تفاصيله وتفويضه.'
TRANSLATIONS["en"]["ui_fetch_filters"] = 'Fetch options'
TRANSLATIONS["ar"]["ui_fetch_filters"] = 'خيارات الجلب'
TRANSLATIONS["en"]["ui_data_help"] = 'Fetched requests stay within the current connection scope.'
TRANSLATIONS["ar"]["ui_data_help"] = 'تظهر الطلبات التي تم جلبها ضمن نطاق الاتصال الحالي.'
TRANSLATIONS["en"]["ui_search_count"] = 'Results: {count}'
TRANSLATIONS["ar"]["ui_search_count"] = 'النتائج: {count}'
TRANSLATIONS["en"]["ui_close"] = 'Close navigation'
TRANSLATIONS["ar"]["ui_close"] = 'إغلاق القائمة'
TRANSLATIONS["en"]["ui_profile_observed"] = 'Observed experience'
TRANSLATIONS["ar"]["ui_profile_observed"] = 'الخبرة المرصودة'
TRANSLATIONS["en"]["ui_every_topic"] = 'All observed topics'
TRANSLATIONS["ar"]["ui_every_topic"] = 'جميع المجالات المرصودة'
TRANSLATIONS["en"]["ui_analysis_failed"] = 'Analysis could not be completed. Update the description or retry.'
TRANSLATIONS["ar"]["ui_analysis_failed"] = 'تعذر إكمال التحليل. عدّل الوصف أو أعد المحاولة.'

TRANSLATIONS["en"]["ui_saved_credential"] = "Leave blank to keep the saved connection"
TRANSLATIONS["ar"]["ui_saved_credential"] = "اتركه فارغًا للاحتفاظ بالاتصال المحفوظ"
TRANSLATIONS["en"]["ui_settings_save_help"] = "Save applies the settings across all sections."
TRANSLATIONS["ar"]["ui_settings_save_help"] = "الحفظ يطبق إعدادات جميع الأقسام."

TRANSLATIONS['en']['ui_assignment_controls'] = 'Assignment controls'
TRANSLATIONS['ar']['ui_assignment_controls'] = 'ضوابط الإسناد'

# Human-readable local analysis guidance.
TRANSLATIONS["en"]["d_r_intent_help"] = 'Check the subject and tools understood from your description. Refine the description if something is missing.'
TRANSLATIONS["ar"]["d_r_intent_help"] = 'تحقق من الموضوع والأدوات التي فهمها النظام من وصفك. عدّل الوصف إذا كانت هناك معلومة ناقصة.'
TRANSLATIONS["en"]["d_r_intent_subject"] = 'Subject'
TRANSLATIONS["ar"]["d_r_intent_subject"] = 'موضوع العمل'
TRANSLATIONS["en"]["d_r_intent_tools"] = 'Tools'
TRANSLATIONS["ar"]["d_r_intent_tools"] = 'الأدوات'
TRANSLATIONS["en"]["d_r_intent_action"] = 'Work type'
TRANSLATIONS["ar"]["d_r_intent_action"] = 'نوع العمل'
TRANSLATIONS["en"]["d_r_intent_output"] = 'Deliverable'
TRANSLATIONS["ar"]["d_r_intent_output"] = 'المخرج المطلوب'
TRANSLATIONS["en"]["d_r_not_detected"] = 'Not identified from the description'
TRANSLATIONS["ar"]["d_r_not_detected"] = 'لم يتحدد من الوصف'
TRANSLATIONS["en"]["d_r_query_no_subject"] = 'Add the subject of the work, for example payroll, invoices or network troubleshooting. General words alone cannot establish relevant experience.'
TRANSLATIONS["ar"]["d_r_query_no_subject"] = 'أضف موضوع العمل، مثل الرواتب أو الفواتير أو معالجة مشكلة شبكة. الكلمات العامة وحدها لا تثبت خبرة مرتبطة.'
TRANSLATIONS["en"]["d_r_query_tool_only"] = 'An instrument is identified, but the work subject is missing. Describe what you want to achieve with this tool; the current matches only evidence its use.'
TRANSLATIONS["ar"]["d_r_query_tool_only"] = 'تحددت أداة دون موضوع العمل. وضّح ما تريد إنجازه بها؛ المطابقات الحالية تدل على استخدام الأداة فقط.'
TRANSLATIONS["en"]["d_r_query_unknown_domain"] = 'The subject is not in the local classification dictionary. Results still use text evidence; specify key subject terms and inspect the examples.'
TRANSLATIONS["ar"]["d_r_query_unknown_domain"] = 'الموضوع غير موجود في قاموس التصنيف المحلي. تعتمد النتائج على الأدلة النصية؛ حدد كلمات الموضوع وافحص الأمثلة.'
TRANSLATIONS["en"]["d_r_method_title"] = 'How the analysis works'
TRANSLATIONS["ar"]["d_r_method_title"] = 'كيف يعمل التحليل؟'
TRANSLATIONS["en"]["d_r_method_help"] = 'Local statistical text matching with Arabic/English aliases. Titles have more weight than descriptions. A shared tool cannot establish experience in a known different subject. Employee ranking then combines related completed work and current workload. This is not a trained language model or a success probability.'
TRANSLATIONS["ar"]["d_r_method_help"] = 'مطابقة نصية إحصائية محلية مع مرادفات عربية وإنجليزية. وزن العنوان أعلى من الوصف، والأداة المشتركة لا تثبت خبرة في موضوع معروف مختلف. يرتب النظام الموظفين بحسب الأعمال المكتملة المرتبطة وضغط العمل الحالي. هذه ليست نتائج نموذج لغوي أو احتمالات نجاح.'
TRANSLATIONS["en"]["d_r_model_version"] = 'Version'
TRANSLATIONS["ar"]["d_r_model_version"] = 'الإصدار'
TRANSLATIONS["en"]["d_r_model_documents"] = 'Distinct term patterns'
TRANSLATIONS["ar"]["d_r_model_documents"] = 'أنماط المصطلحات المختلفة'
TRANSLATIONS["en"]["d_r_model_vocabulary"] = 'Indexed terms'
TRANSLATIONS["ar"]["d_r_model_vocabulary"] = 'المصطلحات المفهرسة'
TRANSLATIONS["en"]["d_r_pattern_count"] = 'Distinct evidence patterns'
TRANSLATIONS["ar"]["d_r_pattern_count"] = 'أنماط الأدلة المختلفة'
TRANSLATIONS["en"]["d_r_patterns_help"] = 'Repeated text does not prove independent effort; inspect the source tasks.'
TRANSLATIONS["ar"]["d_r_patterns_help"] = 'تكرار النص لا يثبت استقلال الجهد؛ افحص مهام المصدر.'
TRANSLATIONS["en"]["d_r_subject_evidence"] = 'Completed work supports this subject'
TRANSLATIONS["ar"]["d_r_subject_evidence"] = 'أعمال مكتملة تدعم هذا الموضوع'

TRANSLATIONS["en"]["d_r_repeated"] = "Completed work with recurring text patterns"
TRANSLATIONS["ar"]["d_r_repeated"] = "أعمال مكتملة بأنماط نصية متكررة"

TRANSLATIONS["en"]["ui_workspace_group"] = "Workspace"
TRANSLATIONS["ar"]["ui_workspace_group"] = "مساحة العمل"
TRANSLATIONS["en"]["ui_analysis_group"] = "Analysis"
TRANSLATIONS["ar"]["ui_analysis_group"] = "التحليل"

TRANSLATIONS["en"]["d_r_open_affinity"] = 'Related pending work'
TRANSLATIONS["ar"]["d_r_open_affinity"] = 'قرب الأعمال المعلقة'

TRANSLATIONS["en"]["d_r_open_affinity_help"] = 'Independent text proximity ranking of related open work. These assignments have not been verified as completed and do not add completed experience to assignment recommendations.'
TRANSLATIONS["ar"]["d_r_open_affinity_help"] = 'ترتيب مستقل لقرب نصوص الأعمال المفتوحة من المطلوب. هذه الإسنادات ليست إنجازات موثقة ولا تضيف خبرة مكتملة إلى ترشيح الإسناد.'

TRANSLATIONS["en"]["d_r_open_affinity_empty"] = 'No eligible employee has related pending execution work in this snapshot.'
TRANSLATIONS["ar"]["d_r_open_affinity_empty"] = 'لا يوجد موظف مؤهل لديه عمل تنفيذي معلق مرتبط ضمن هذه اللقطة.'

TRANSLATIONS["en"]["d_r_closest_open"] = 'Closest pending-work record'
TRANSLATIONS["ar"]["d_r_closest_open"] = 'أقرب سجل في الأعمال المعلقة'

TRANSLATIONS["en"]["d_r_open_difference"] = 'The closest pending-work record can differ from the assignment recommendation. Inspect pending work separately from completed evidence and workload.'
TRANSLATIONS["ar"]["d_r_open_difference"] = 'قد يختلف أقرب سجل للأعمال المعلقة عن ترشيح الإسناد. قارن العمل المعلق بالدليل المكتمل وضغط العمل قبل القرار.'

TRANSLATIONS["en"]["d_r_compare_open"] = 'Compare pending work'
TRANSLATIONS["ar"]["d_r_compare_open"] = 'قارن الأعمال المعلقة'

TRANSLATIONS["en"]["d_r_mentioned_periods"] = 'Work periods mentioned in titles'
TRANSLATIONS["ar"]["d_r_mentioned_periods"] = 'فترات العمل المذكورة في العناوين'

TRANSLATIONS["en"]["d_r_periods_help"] = 'Different named periods distinguish recurring requests; they are not proof of execution on different dates. Only explicit title periods count. Text match sorts first; period and content variety break ties. Exact repeated content does not strengthen this ranking.'
TRANSLATIONS["ar"]["d_r_periods_help"] = 'اختلاف الفترات يميز الطلبات الدورية، ولا يثبت تنفيذها في تواريخ مختلفة. تؤخذ الفترات الصريحة من العنوان فقط. يرتب تطابق النص أولًا، ثم اختلاف الفترات والمحتوى لكسر التعادل. تكرار النص المتطابق لا يقوي هذا الترتيب.'

TRANSLATIONS["en"]["d_r_open_not_completed"] = 'Pending; completion not verified'
TRANSLATIONS["ar"]["d_r_open_not_completed"] = 'معلقة؛ الإنجاز غير موثق'

TRANSLATIONS["en"]["d_r_source_status"] = 'Source status code'
TRANSLATIONS["ar"]["d_r_source_status"] = 'رمز حالة المصدر'

TRANSLATIONS["en"]["d_r_source_created"] = 'Created on'
TRANSLATIONS["ar"]["d_r_source_created"] = 'أُنشئت في'

TRANSLATIONS["en"]["d_r_text_match"] = "Text match"
TRANSLATIONS["ar"]["d_r_text_match"] = "تطابق النص"
TRANSLATIONS["en"]["d_r_source_details"] = "Source details"
TRANSLATIONS["ar"]["d_r_source_details"] = "تفاصيل المصدر"

TRANSLATIONS["en"]["d_r_affinity_evidence"] = "Inspect pending tasks and periods"
TRANSLATIONS["ar"]["d_r_affinity_evidence"] = "افحص المهام المعلقة وفتراتها"

# Unified identities and local task understanding (3.5).
TRANSLATIONS["en"]["d_directory_title"] = "Unified employee directory"
TRANSLATIONS["ar"]["d_directory_title"] = "دليل الموظفين الموحد"
TRANSLATIONS["en"]["d_directory_help"] = "Link the same person's Bitrix and Diwan accounts explicitly. Names never merge accounts. Completed evidence and workload can then be compared across your accessible sources; source permissions still control assignment."
TRANSLATIONS["ar"]["d_directory_help"] = "اربط حسابي بتركس وديوان للشخص نفسه صراحةً. تشابه الأسماء لا يدمج الحسابات. يجمع الربط أدلة الإنجاز والضغط من المصادر المتاحة لحسابك، وتظل صلاحية الإسناد خاضعة للمصدر."
TRANSLATIONS["en"]["d_directory_search"] = "Search name, team or account identifier"
TRANSLATIONS["ar"]["d_directory_search"] = "ابحث بالاسم أو الفريق أو معرّف الحساب"
TRANSLATIONS["en"]["d_directory_bitrix"] = "Unlinked Bitrix account"
TRANSLATIONS["ar"]["d_directory_bitrix"] = "حساب بتركس غير مرتبط"
TRANSLATIONS["en"]["d_directory_diwan"] = "Unlinked Diwan account"
TRANSLATIONS["ar"]["d_directory_diwan"] = "حساب ديوان غير مرتبط"
TRANSLATIONS["en"]["d_directory_link"] = "Link these accounts"
TRANSLATIONS["ar"]["d_directory_link"] = "ربط هذين الحسابين"
TRANSLATIONS["en"]["d_directory_unlink"] = "Separate these accounts"
TRANSLATIONS["ar"]["d_directory_unlink"] = "فصل هذين الحسابين"
TRANSLATIONS["en"]["d_directory_name"] = "Display name"
TRANSLATIONS["ar"]["d_directory_name"] = "الاسم المعروض"
TRANSLATIONS["en"]["d_directory_team"] = "Team (administrative information)"
TRANSLATIONS["ar"]["d_directory_team"] = "الفريق (معلومة إدارية)"
TRANSLATIONS["en"]["d_directory_active"] = "Employee available for recommendations"
TRANSLATIONS["ar"]["d_directory_active"] = "الموظف مفعّل للتوصيات"
TRANSLATIONS["en"]["d_directory_enabled"] = "Allow as assignment recipient"
TRANSLATIONS["ar"]["d_directory_enabled"] = "السماح باختياره للإسناد"
TRANSLATIONS["en"]["d_directory_choose"] = "Choose an account"
TRANSLATIONS["ar"]["d_directory_choose"] = "اختر حسابًا"
TRANSLATIONS["en"]["d_directory_empty"] = "No observed or configured employees. Connect a source or add a Diwan recipient below."
TRANSLATIONS["ar"]["d_directory_empty"] = "لا توجد حسابات موظفين مرصودة أو مضافة. اربط مصدرًا أو أضف مستلم ديوان أدناه."
TRANSLATIONS["en"]["d_directory_add_source"] = "Add or edit source recipients"
TRANSLATIONS["ar"]["d_directory_add_source"] = "إضافة مستلمين أو تعديلهم في المصدر"
TRANSLATIONS["en"]["d_directory_unsaved"] = "Changes are not saved. Review the linked identifiers before saving."
TRANSLATIONS["ar"]["d_directory_unsaved"] = "التغييرات لم تحفظ. راجع معرّفات الحسابات المرتبطة ثم احفظ."
TRANSLATIONS["en"]["d_directory_reload_hint"] = "Save your directory changes, then reload to include the new source recipients."
TRANSLATIONS["ar"]["d_directory_reload_hint"] = "احفظ تعديلات الدليل ثم أعد تحميل الصفحة لإظهار المستلمين المضافين."
TRANSLATIONS["en"]["d_directory_source_inactive"] = "Inactive in source; linking does not enable the account."
TRANSLATIONS["ar"]["d_directory_source_inactive"] = "غير نشط في المصدر؛ الربط لا يفعّل الحساب."
TRANSLATIONS["en"]["d_domain_title"] = "Task understanding"
TRANSLATIONS["ar"]["d_domain_title"] = "فهم المهمة"
TRANSLATIONS["en"]["d_domain_help"] = "Add domains used by your organisation and their exact Arabic/English phrases. One phrase per line. These explicit rules complement corpus-derived associations; they do not certify an employee's skills. Do not use generic actions such as review or report as subject phrases."
TRANSLATIONS["ar"]["d_domain_help"] = "أضف مجالات عمل الجهة وعباراتها العربية والإنجليزية المحددة، عبارة في كل سطر. تكمل هذه القواعد ارتباطات المصطلحات المستخرجة من السجل، ولا تثبت مهارات الموظف. لا تستخدم أفعالًا عامة مثل مراجعة أو تقرير كعبارات للموضوع."
TRANSLATIONS["en"]["d_domain_add"] = "Add a domain"
TRANSLATIONS["ar"]["d_domain_add"] = "إضافة مجال"
TRANSLATIONS["en"]["d_domain_id"] = "Domain identifier (e.g. licensing)"
TRANSLATIONS["ar"]["d_domain_id"] = "معرّف المجال (مثل licensing)"
TRANSLATIONS["en"]["d_domain_aliases"] = "Exact subject phrases, one per line"
TRANSLATIONS["ar"]["d_domain_aliases"] = "عبارات الموضوع المحددة، عبارة في كل سطر"
TRANSLATIONS["en"]["d_domain_builtin"] = "Built-in domains"
TRANSLATIONS["ar"]["d_domain_builtin"] = "المجالات المدمجة"
TRANSLATIONS["en"]["d_r_learned_subject"] = "Subject inferred from completed text patterns"
TRANSLATIONS["ar"]["d_r_learned_subject"] = "موضوع استُدل عليه من أنماط نصية مكتملة"
TRANSLATIONS["en"]["d_r_learned_terms"] = "Corpus-derived term associations"
TRANSLATIONS["ar"]["d_r_learned_terms"] = "ارتباطات مصطلحات مستخرجة من السجل"
TRANSLATIONS["en"]["d_r_excluded_subjects"] = "Explicitly excluded from scope"
TRANSLATIONS["ar"]["d_r_excluded_subjects"] = "مستبعد صراحةً من نطاق المهمة"
TRANSLATIONS["en"]["d_r_linked_evidence"] = "Evidence from linked accounts"
TRANSLATIONS["ar"]["d_r_linked_evidence"] = "أدلة الحسابات المرتبطة"
TRANSLATIONS["en"]["d_r_concept_match"] = "Subject/concept overlap"
TRANSLATIONS["ar"]["d_r_concept_match"] = "تطابق الموضوع أو المفهوم"
TRANSLATIONS["en"]["d_r_primary_evidence"] = "Closest completed evidence"
TRANSLATIONS["ar"]["d_r_primary_evidence"] = "أقرب دليل مكتمل"
TRANSLATIONS["en"]["d_r_method_help"] = "Local matching combines field-weighted text, BM25 and typed concepts, then checks the requested work type. Bounded spelling correction and completed-pattern associations improve subject recognition. Copies do not add experience credit; explicit recurring periods are retained. Shared tools alone cannot establish subject expertise. Scores are not success probabilities."
TRANSLATIONS["ar"]["d_r_method_help"] = "تجمع المطابقة المحلية بين تشابه الحقول وBM25 والمفاهيم، ثم تتحقق من نوع العمل المطلوب. يحسن التصحيح الإملائي المحدود وارتباطات الأنماط المكتملة التعرف على الموضوع. النسخ لا تضيف رصيد خبرة، مع حفظ الفترات الدورية الصريحة. الأداة المشتركة وحدها لا تثبت الاختصاص، والدرجة ليست احتمال نجاح."


TRANSLATIONS["en"]["d_r_retrieval"] = "Evidence relevance"
TRANSLATIONS["ar"]["d_r_retrieval"] = "قرب الأدلة"
TRANSLATIONS["en"]["d_r_coverage_formula"] = "Similarity component: 75% retrieval relevance plus 25% requested topic coverage, when topic coverage is available."
TRANSLATIONS["ar"]["d_r_coverage_formula"] = "مكوّن التشابه: 75% من قرب الأدلة و25% من تغطية الموضوعات المطلوبة عند توفرها."

TRANSLATIONS["en"]["d_completed_evidence"] = "Completed task"
TRANSLATIONS["ar"]["d_completed_evidence"] = "مهمة مكتملة"
TRANSLATIONS["en"]["d_open_evidence"] = "Open task; not completed evidence"
TRANSLATIONS["ar"]["d_open_evidence"] = "مهمة مفتوحة؛ ليست دليل إنجاز"
TRANSLATIONS["en"]["d_r_status_source_unavailable"] = "The open-task source refresh failed. Refresh before assigning."
TRANSLATIONS["ar"]["d_r_status_source_unavailable"] = "تعذر تحديث المهام المفتوحة من المصدر. حدّثها قبل الإسناد."
TRANSLATIONS["en"]["d_r_status_workload_old"] = "Current-source workload is older than two minutes. Refresh before assigning."
TRANSLATIONS["ar"]["d_r_status_workload_old"] = "بيانات ضغط العمل في المصدر الحالي أقدم من دقيقتين. حدّثها قبل الإسناد."
TRANSLATIONS["en"]["d_r_status_linked_workload_old"] = "Linked-source workload is older than two minutes or unavailable. Refresh both sources before assigning."
TRANSLATIONS["ar"]["d_r_status_linked_workload_old"] = "بيانات الضغط في المصدر المرتبط قديمة أو غير متاحة. حدّث المصدرين قبل الإسناد."
TRANSLATIONS["en"]["d_r_status_history_incomplete"] = "Historical evidence has not finished loading or its last refresh failed. These results may be incomplete."
TRANSLATIONS["ar"]["d_r_status_history_incomplete"] = "لم يكتمل تحميل أدلة الإنجاز أو تعذر تحديثها الأخير. قد تكون النتائج غير مكتملة."


# 3.7: automatic topics are extracted corpus descriptions, not verified domains.
TRANSLATIONS["en"].update({
    "d_domain_builtin": "Automatically discovered topics",
    "d_domain_help": "Topics are discovered locally from task meaning without a predefined domain list. Optional phrases below are your annotations; they do not determine eligibility or train the discovery model. Topic names use the language present in the evidence.",
    "d_no_discovered_topics": "Not enough distinct related texts to discover stable topics yet.",
    "d_r_semantic_method_help": "Local multilingual sentence embeddings retrieve related tasks; a local pair model verifies their subject, supported by lexical matching and work type. Topics are discovered from accessible texts and named using extracted phrases. Completed evidence supports recommendations; pending work is separate. Scores are relevance measures, not success probabilities.",
    "d_r_semantic_unavailable": "The local sentence model is unavailable. Only lexical matching is active; automatic domain discovery is unavailable. No manual business taxonomy is substituted.",
    "d_r_discovered_topics": "Discovered topics",
    "d_r_topic_provisional": "Extracted descriptions; not verified organisational domains",
    "d_r_query_unknown_domain": "No sufficiently supported topic was found. Relevant work can still be compared directly by meaning.",
})
TRANSLATIONS["ar"].update({
    "d_domain_builtin": "الموضوعات المكتشفة تلقائيًا",
    "d_domain_help": "تُكتشف الموضوعات محليًا من معنى المهام دون قائمة مجالات مسبقة. العبارات الاختيارية أدناه ملاحظات تضيفها أنت؛ لا تحدد الأهلية ولا تدرب نموذج الاكتشاف. تستخدم أسماء الموضوعات اللغة الموجودة في الأدلة.",
    "d_no_discovered_topics": "لا توجد نصوص مختلفة ومترابطة كافية لاكتشاف موضوعات مستقرة بعد.",
    "d_r_semantic_method_help": "يسترجع نموذج جمل متعدد اللغات المهام ذات الصلة، ويتحقق نموذج محلي ثانٍ من موضوع كل زوج، مع دعم من المطابقة النصية ونوع العمل. تُكتشف الموضوعات من النصوص المتاحة وتُوصف بعبارات مستخرجة منها. يعتمد الترشيح على الإنجاز الموثق، وتُعرض الأعمال المعلقة مستقلة. الدرجات مقاييس صلة وليست احتمالات نجاح.",
    "d_r_semantic_unavailable": "نموذج الجمل المحلي غير متاح. يعمل التشابه النصي فقط، ولا يتاح اكتشاف المجالات تلقائيًا. لا يُستبدل بقاموس مجالات يدوي.",
    "d_r_discovered_topics": "الموضوعات المكتشفة",
    "d_r_topic_provisional": "أوصاف مستخرجة؛ ليست مجالات تنظيمية معتمدة",
    "d_r_query_unknown_domain": "لم يُكتشف موضوع بأدلة كافية. يمكن مقارنة الأعمال ذات الصلة مباشرةً بالمعنى.",
})

TRANSLATIONS["en"]["d_r_verification_unavailable"] = "Local pair verification is unavailable; semantic retrieval uses a stricter threshold. Review the evidence before assignment."
TRANSLATIONS["ar"]["d_r_verification_unavailable"] = "نموذج التحقق من أزواج المهام غير متاح؛ يستخدم الاسترجاع الدلالي حدًا أشد. راجع الأدلة قبل الإسناد."

# Workflow audit corrections.
TRANSLATIONS["en"].update({
    "d_r_status_directory_unavailable": "Employee verification failed. The last successful directory is retained; refresh before assigning.",
    "d_r_refresh_before_assign": "Refresh and verify the task before assigning. Current evidence is stale or an assignment remains unresolved.",
    "d_r_ranking_label": "Ranking score",
    "d_display_limit": "50 rows per page; analysis searches the fetched history.",
    "d_sla_overdue": "SLA overdue",
    "d_pairs_help": "Examples are calculated when this section opens, from up to 100 tasks in the selected source using the same relevance model as analysis.",
})
TRANSLATIONS["ar"].update({
    "d_r_status_directory_unavailable": "تعذر التحقق من الموظفين. احتُفظ بآخر دليل ناجح؛ حدّث البيانات قبل الإسناد.",
    "d_r_refresh_before_assign": "حدّث المهمة وتحقق منها قبل الإسناد؛ البيانات قديمة أو توجد عملية إسناد لم تُحسم.",
    "d_r_ranking_label": "درجة الترتيب",
    "d_display_limit": "50 سجلًا في الصفحة؛ يبحث التحليل في السجل المجلوب.",
    "d_sla_overdue": "تجاوز موعد الخدمة",
    "d_pairs_help": "تُحسب الأمثلة عند فتح هذا القسم من أول 100 مهمة في المصدر المحدد باستخدام نموذج التشابه نفسه المستخدم في التحليل.",
})

TRANSLATIONS["en"]["d_r_status_snapshot_changed"] = "The source snapshot changed during analysis. Refresh the recommendation before assigning."
TRANSLATIONS["ar"]["d_r_status_snapshot_changed"] = "تغيرت البيانات أثناء التحليل. حدّث الترشيح قبل الإسناد."

# Automatically generated assignment notifications.
TRANSLATIONS["en"].update({
    "d_columns_title": "Diwany table columns",
    "d_columns_search": "Search columns", "d_column_assignee": "Assigned to",
    "d_columns_help": "Choose the columns to show in Diwany, then save. All standard task, employee, request, form and detail columns are available. You can rename headings or select all columns.",
    "d_columns_reload": "Reload available columns",
    "d_column_label": "Optional column heading",
    "d_preparing_history": "Saved tasks are available. Preparing the analysis index in the background…",
    "d_columns_fetch_hint": "The full standard column list is available now. Connect or fetch tasks to discover additional JSON fields; unavailable values stay blank.",
    "d_bitrix_setup_help": "Connect Bitrix and choose your projects in Settings to load your tasks. Diwany is optional and its token is not required for Bitrix pages.",
    "d_diwan_optional_help": "Diwany is optional. You can use all other pages without a Diwany token. Connect only when you want to fetch Diwany requests; then choose the columns to display.",
    "d_created": "Created", "d_completed": "Completed", "d_due": "Deadline",
    "d_error_index_building": "Your saved history is being prepared for analysis. Please try again shortly.",
    "d_error_cache_write_failed": "Could not save the history locally. Your previous saved history is still available.",
    "d_error_index_failed": "Could not prepare the saved history for analysis. Refresh history to retry.",
})
TRANSLATIONS["ar"].update({
    "d_columns_title": "أعمدة جدول ديواني",
    "d_columns_search": "البحث في الأعمدة", "d_column_assignee": "الموظف المسند إليه",
    "d_columns_help": "اختر الأعمدة التي تريد عرضها في ديواني ثم احفظ. جميع أعمدة المهمة والموظف والطلب والنموذج والتفاصيل متاحة. يمكنك تعديل العناوين أو اختيار جميع الأعمدة.",
    "d_columns_reload": "تحديث الأعمدة المتاحة",
    "d_column_label": "عنوان اختياري للعمود",
    "d_preparing_history": "المهام المحفوظة متاحة. جارٍ تجهيز فهرس التحليل في الخلفية…",
    "d_columns_fetch_hint": "قائمة الأعمدة الأساسية الكاملة متاحة الآن. اربط الحساب أو اجلب المهام لاكتشاف حقول JSON إضافية؛ القيم غير المتاحة تظل فارغة.",
    "d_bitrix_setup_help": "اربط حساب Bitrix واختر المشاريع في الإعدادات لجلب مهامك. ديواني اختياري ورمزه غير مطلوب لصفحات Bitrix.",
    "d_diwan_optional_help": "ربط ديواني اختياري. يمكنك استخدام جميع الصفحات الأخرى دون رمز ديواني. اربط الحساب عند الرغبة في جلب طلبات ديواني، ثم اختر أعمدة العرض.",
    "d_created": "تاريخ الإنشاء", "d_completed": "تاريخ الإنجاز", "d_due": "الموعد النهائي",
    "d_error_index_building": "جارٍ تجهيز السجل المحفوظ للتحليل. يرجى المحاولة بعد قليل.",
    "d_error_cache_write_failed": "تعذر حفظ السجل محليًا. لا يزال السجل السابق متاحًا.",
    "d_error_index_failed": "تعذر تجهيز السجل المحفوظ للتحليل. حدّث السجل لإعادة المحاولة.",
})
TRANSLATIONS["en"].update({
    "d_r_auto_candidate": "Suggested employee: {name}",
    "d_r_auto_reason": "Evidence from similar completed tasks ({completed}). Current assigned open tasks: {active}.",
    "d_r_auto_pending": "Analysing the task to suggest an employee…",
    "d_r_auto_no_evidence": "No eligible employee has related completed evidence in the available history. Review the task to choose manually.",
    "d_r_auto_unavailable": "The task needs assignment. Refresh and verify the data before an employee can be suggested.",
    "d_r_auto_failed": "The automatic suggestion could not be generated. It will be retried; you can also open the task for analysis.",
})
TRANSLATIONS["ar"].update({
    "d_r_auto_candidate": "الموظف المقترح: {name}",
    "d_r_auto_reason": "دليل الترشيح: {completed} من المهام المكتملة ذات الصلة. الحمل الحالي: {active} من المهام المفتوحة.",
    "d_r_auto_pending": "جارٍ تحليل المهمة واقتراح الموظف المناسب…",
    "d_r_auto_no_evidence": "لا يوجد موظف مؤهل لديه إنجاز مكتمل مرتبط بالمهمة ضمن السجل المتاح. راجع المهمة للاختيار اليدوي.",
    "d_r_auto_unavailable": "المهمة تحتاج إسنادًا. يلزم تحديث البيانات والتحقق منها قبل اقتراح موظف.",
    "d_r_auto_failed": "تعذر توليد الاقتراح التلقائي. ستُعاد المحاولة، ويمكنك فتح المهمة لتحليلها.",
})
