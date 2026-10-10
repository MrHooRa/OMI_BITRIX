"""Anonymous Arabic-dominant cases fixed before semantic integration evaluation."""
GROUPS = {
    "library": [
        "فهرسة المخطوطات القديمة وإدخال بيانات المؤلفين في سجل المكتبة",
        "رقمنة الوثائق التراثية وحفظ النسخ المصورة للمخطوطات",
        "تصنيف الكتب وفق الموضوع والمؤلف وترتيب مقتنيات المكتبة",
        "إعداد كشاف للمخطوطات وتوثيق العناوين وتواريخ النسخ",
        "تحديث الفهرس الإلكتروني للمكتبة وربط صور الوثائق بالسجلات",
    ],
    "gardening": [
        "تحديد احتياجات ري النباتات وتوزيع المياه على أحواض الزراعة",
        "فحص خصوبة التربة واختيار السماد المناسب للأشجار",
        "تشخيص إصابة النباتات بالآفات ووضع خطة مكافحة الحشرات",
        "جدولة تقليم الأشجار والعناية بالحدائق والمساحات المزروعة",
        "تقييم صحة المزروعات ومعالجة نقص العناصر الغذائية في التربة",
    ],
    "translation": [
        "ترجمة دليل الاستخدام من الإنجليزية إلى العربية وتوحيد المصطلحات",
        "مراجعة الترجمة العربية للنصوص الإنجليزية والتحقق من دقة المعنى",
        "تعريب محتوى الموقع ومطابقة النص المترجم مع النسخة الأصلية",
        "إعداد معجم للمصطلحات وتدقيق الترجمة اللغوية للوثائق",
        "تحرير نص مترجم والتحقق من سلامة الأسلوب والقواعد العربية",
    ],
    "payroll": [
        "مراجعة مسير أجور العاملين ومطابقة البدلات والاستقطاعات",
        "تدقيق رواتب الموظفين والتحقق من صافي المبالغ المستحقة",
        "مطابقة كشف الرواتب مع سجل الحضور واحتساب الخصومات",
        "استخراج تقرير الفروقات بين مسيرات الأجور الشهرية",
        "التحقق من احتساب بدلات العاملين وتسوية استقطاعات الرواتب",
    ],
}
QUERIES = [
    ("تنظيم سجلات المؤلفات وحفظ صور المخطوطات التراثية", "library"),
    ("Digitise historical manuscripts and catalogue library holdings", "library"),
    ("معالجة اصفرار أوراق الشجر وتحديد برنامج التسميد والري", "gardening"),
    ("Inspect soil fertility and plant irrigation needs", "gardening"),
    ("نقل النص إلى العربية ومراجعة المصطلحات ودقة الصياغة", "translation"),
    ("Proofread Arabic translations of an English user manual", "translation"),
    ("تحليل واستخراج تقرير لمراجعة رواتب الموظفين لآخر ثلاثة أشهر", "payroll"),
    ("Audit employee remuneration and monthly salary deductions", "payroll"),
]

def records():
    result=[]
    for group_no,(group,texts) in enumerate(GROUPS.items(),1):
        for n,text in enumerate(texts):
            result.append({"source":"bitrix","id":str(group_no*100+n),"title":text,"description":"",
                "assignee_id":str(group_no),"assignee_name":"Employee "+str(group_no),"project_id":"1",
                "category":"","completed":True,"created_at":"2025-01-01T08:00:00+03:00",
                "completed_at":"2025-01-03T08:00:00+03:00","group_truth":group})
    return result
