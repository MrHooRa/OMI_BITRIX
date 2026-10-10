"""Local bilingual phrase normalization and explicit request scope.
These lexical translations do not define business topics.
"""
import re
from similarity import normalize

# Phrases, rather than broad ambiguous words such as compensation or finance.
PHRASE_ALIASES = {
    "مسير الرواتب": "رواتب", "مسيرات الرواتب": "رواتب", "مسير الاجور": "رواتب",
    "مسيرات الاجور": "رواتب", "كشف الاجور": "رواتب", "كشف المستحقات الشهريه": "رواتب",
    "صرف مستحقات العاملين": "رواتب", "employee remuneration": "payroll",
    "wage statement": "payroll", "wage statements": "payroll", "wages": "payroll",
    "accounts payable": "invoices", "حسابات الموردين": "فواتير",
    "ضريبه القيمه المضافه": "ضريبه", "value added tax": "tax",
    "الاتصال بالشبكه": "شبكه", "network connection": "network",
    "نسخ احتياطي لقواعد البيانات": "database", "relational database": "database",
    "حمايه سيبرانيه": "cybersecurity", "cyber security": "cybersecurity",
    "التعلم الالي": "ai", "تعلم الاله": "ai", "generative ai": "ai",
    "لوحات المعلومات": "dashboard", "لوحات المؤشرات": "dashboard",
    "مرتبات": "رواتب", "المرتبات": "الرواتب",
    "مستحقات الموظفين الشهريه": "رواتب", "مستحقات العاملين الشهريه": "رواتب",
    "salary deductions": "payroll deductions", "الاستقطاعات": "استقطاعات",
    "تسويه": "مطابقه", "audit": "review", "auditing": "review",
    "تدقيق": "مراجعه", "استخراح": "استخراج",
    "التوفيق": "مطابقه", "reconcile": "reconciliation", "reconciling": "reconciliation",
}
# Keep excluded subjects out of the matching text. Only explicit scope clauses
# are recognized, not arbitrary negation or inferred intent.
EXCLUSION = re.compile(
    r"(?:باستثناء|لا يشمل|لا تشمل|ليس عن|ليست عن|not about|excluding)"
    r"\s+(.+?)(?=[،,.;؛()\n]|\s+(?:ولكن|بل|ويشمل|وتشمل|but|rather|instead)\b|$)", re.I)


def language_text(text):
    text = re.sub(r"\[OMI[^\]]*\]|https?://\S+", " ", str(text or ""), flags=re.I)
    text = re.sub(r"[^\s@]+@[^\s@]+", " ", text)
    text = normalize(text)
    for phrase, alias in sorted(PHRASE_ALIASES.items(), key=lambda p: -len(p[0])):
        text = re.sub(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", alias, text)
    return text


def scope_text(text):
    original = str(text or "")
    excluded = [match.group(1).strip() for match in EXCLUSION.finditer(original)]
    return EXCLUSION.sub(" ", original), excluded


def validate_domain_rules(raw):
    if not isinstance(raw, list) or len(raw) > 100:
        raise ValueError("Use at most 100 domain rules")
    rows, seen = [], set()
    for value in raw:
        if not isinstance(value, dict):
            raise ValueError("Invalid domain rule")
        ident = str(value.get("id", "")).strip()
        aliases = value.get("aliases")
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", ident) or ident in seen:
            raise ValueError("Use distinct lowercase domain identifiers")
        if not isinstance(aliases, list) or not 1 <= len(aliases) <= 40:
            raise ValueError("Each domain needs 1 to 40 phrases")
        phrases = [str(a).strip() for a in aliases]
        if any(not a or len(a) > 120 for a in phrases):
            raise ValueError("Invalid domain phrase")
        ar, en = str(value.get("ar", "")).strip(), str(value.get("en", "")).strip()
        if not ar or not en or len(ar) > 120 or len(en) > 120:
            raise ValueError("Supply Arabic and English domain names")
        seen.add(ident)
        rows.append({"id": ident, "ar": ar, "en": en, "aliases": phrases})
    return rows
