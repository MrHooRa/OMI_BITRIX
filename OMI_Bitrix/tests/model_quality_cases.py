"""Anonymous offline relevance checks; judgments are engineering fixtures, not HR truth."""
from datetime import datetime
from sla import TZ


def row(ident, title, employee="1", description="", completed=True, source="bitrix"):
    return {"id": str(ident), "source": source, "title": title, "description": description,
            "assignee_id": employee, "project_id": "1", "category": "", "completed": completed,
            "created_at": "2025-01-01T08:00:00+03:00",
            "completed_at": "2025-01-02T08:00:00+03:00" if completed else None,
            "status": "5" if completed else "2", "priority": 0, "tags": []}


def person(ident):
    return {"id": ident, "name": "Employee " + ident, "enabled": True, "active": True,
            "projects": ["1"], "categories": []}


# Every expected executor follows task-specific completed work, never name or availability.
def cases():
    items = []
    def add(name, query, records, expected=None, forbidden=(), rules=()):
        items.append({"name": name, "query": query, "records": records,
                      "employee": expected, "forbidden": set(forbidden), "rules": list(rules)})
    payroll = [row(1,"مراجعة الرواتب ومطابقة الاستقطاعات والبدلات"),
               row(2,"تشخيص عطل الشبكة", "2"), row(3,"تسوية فواتير الموردين","3")]
    for number, query in enumerate(("مراجعة الرواتب","payroll review","مطابقة مسيرات الأجور",
        "تدقيق مرتبات العاملين","مطابقة مستحقات الموظفين الشهرية","review payrol",
        "مراجعة الرواتتب","استخراج تقرير عن الرواتب لآخر ثلاثة أشهر")):
        add("payroll_"+str(number),query,payroll,"1",("2","3"))
    invoice = [row(1,"مطابقة فواتير الموردين وضريبة القيمة المضافة"),
               row(2,"تحليل الرواتب","2"),row(3,"صيانة الشبكات","3")]
    for number, query in enumerate(("invoice reconciliation","تسوية حسابات الموردين",
        "مطابقة فواتير الموردين","مراجعة فواتير المورديين")):
        add("invoice_"+str(number),query,invoice,"1",("2","3"))
    # Equal subjects and loads; correct work type must break the tie.
    for name, query, titles in (
        ("extraction_ar","استخراج بيانات الرواتب",("مراجعة الرواتب","استخراج بيانات الرواتب")),
        ("review_en","payroll audit",("payroll extraction","payroll audit")),
        ("reconcile_ar","تسوية فواتير الموردين",("مراجعة فواتير الموردين","تسوية فواتير الموردين")),
        ("network_repair","diagnose network failure",("network configuration","diagnose network failure")),
        ("network_setup","تهيئة الشبكة",("اصلاح الشبكة","تهيئة الشبكة")),
    ):
        add(name,query,[row(1,titles[0]),row(2,titles[1],"2")],"2")
    add("long_description","payroll deductions Excel",[
        row(1,"payroll deductions Excel",description=" ".join("background"+chr(97+i%26)+chr(97+i//26) for i in range(200))),
        row(2,"Excel formatting payroll","2")],"1")
    add("duplicate_experience","payroll extraction",[row(1,"payroll extraction","2")]+
        [row(i,"payroll review","1") for i in range(2,42)],"2")
    add("excluded_tax","payroll excluding tax",[row(1,"payroll"),row(2,"tax","2")],"1",("2",))
    add("excluded_contrast","لا تشمل الضرائب ولكن تشمل الرواتب",[row(1,"payroll"),row(2,"tax","2")],"1",("2",))
    add("negation_parenthesis","مراجعة الرواتب (باستثناء الضرائب) باستخدام Excel",[
        row(1,"payroll Excel"),row(2,"tax Excel","2")],"1",("2",))
    add("generic_abstention","review report [REQ-777]",payroll,None,("1","2","3"))
    add("shared_ticket","[OMI-SIM-20261003]",payroll,None,("1","2","3"))
    add("cross_domain_tool","payroll Excel",[row(1,"payroll Excel"),row(2,"network Excel","2")],"1",("2",))
    add("unknown_subject","astronomy telescope calibration",[
        row(1,"astronomy telescope calibration"),row(2,"network calibration","2")],"1",("2",))
    add("cold_start","payroll",[],None,("1","2","3"))
    add("pending_is_not_success","payroll",[row(1,"payroll",completed=False)],None,("1",))
    return items


AT = datetime(2026, 10, 5, tzinfo=TZ)

def holdout_cases():
    """Separate probes written after the first change, without weight tuning."""
    items=[]
    def add(name,query,records,expected=None,forbidden=()):
        items.append({"name":name,"query":query,"records":records,"employee":expected,
                      "forbidden":set(forbidden),"rules":[]})
    for n,(query,title,other) in enumerate((
        ("tax extraction","tax extraction","tax review"),
        ("مراجعة ضريبة القيمة المضافة","tax review","network review"),
        ("تهيئة قواعد البيانات","database configuration","database repair"),
        ("تشخيص عطل الشبكات","network repair","network configuration"),
        ("مراجعة العقود","contract audit","invoice audit"),
        ("مراجعة مشتريات الجهة","procurement review","recruitment review"),
        ("تحليل بيانات التوظيف","recruitment analytics","payroll analytics"),
        ("تقرير باستخدام Python عن فواتير الموردين","invoice Python report","payroll Python report"),
        ("صيانة الشبكه وإصلاح عطل الاتصال","network repair","database repair"),
        ("استخراج الرواتب بواسطة Python","payroll Python extraction","payroll Excel extraction"),
    )):
        add("domain_"+str(n),query,[row(1,other),row(2,title,"2")],"2")
    add("history_spelling","payroll review",[row(1,"payrol review"),row(2,"network review","2")],"1",("2",))
    add("heldout_exclusion","tax excluding payroll but include Python",[
        row(1,"tax Python"),row(2,"payroll Python","2")],"1",("2",))
    add("not_database_backup","annual leave backup coverage",[
        row(1,"annual leave coverage"),row(2,"database backup","2")],"1",("2",))
    add("unfamiliar_subject","volcano seismic monitoring",[
        row(1,"volcano seismic monitoring"),row(2,"network monitoring","2")],"1",("2",))
    add("no_dated_history","network",[dict(row(1,"network"),completed_at=None)],None,("1",))
    add("only_general_action","مراجعة وإعداد تقرير",[
        row(1,"payroll review report"),row(2,"tax review report","2")],None,("1","2"))
    return items
