"""Local semantic retrieval with independent subject verification.
Unsupervised topics are fitted to accessible text, never employee identity.
"""
import re
from collections import Counter, defaultdict
from math import log, sqrt
from functools import lru_cache
from similarity import normalize, STOPWORDS
from employee_insights import classify, task_labels
from task_language import language_text, scope_text
from semantic_engine import clean_text, SemanticSpace, AutomaticDomains, MIN_SEMANTIC_COSINE, MODEL_ID, MODEL_REVISION, get_reranker, RERANKER_ID, RERANKER_REVISION
from sla import parse, TZ
from datetime import datetime

# Generic workflow words cannot establish an employee's subject expertise.
GENERIC = set(normalize("using use utilization استخدام باستخدام تحليل استخراج استخراح تقرير تقارير مراجعة مراجعته تفاصيل طلب مهمة مهام عمل تنفيذ الموظفين موظفين employee employees task report review analysis extract آخر اخر شهور شهر اشهر شهري سبتمبر اكتوبر نوفمبر ديسمبر يناير فبراير مارس ابريل مايو يونيو يوليو اغسطس the and for from with this that please new synthetic similarity test only no real work required january february march april may june july august september october november december month months monthly last").split())


GENERIC.update(normalize(" ".join(STOPWORDS)).split())
GENERIC.update(normalize("مطابقة مطابقه تسوية تسويه reconcile reconciliation audit auditing inspect inspection proofread digitise diagnose validation verification maintenance ").split())
GENERIC.update(normalize("ولكن تشمل يشمل include includes instead rather but اعداد انشاء دراسة تجهيز checking check prepare preparation create study validation verify data").split())

# Lexical translations support exact matching; they do not define or seed topics.
ALIASES = {
    "مرتبات": "رواتب", "اجور": "رواتب", "راتب": "رواتب", "payroll": "رواتب", "salary": "رواتب", "salaries": "رواتب",
    "invoice": "فاتوره", "invoices": "فاتوره", "فواتير": "فاتوره",
    "network": "شبكه", "networks": "شبكه", "شبكات": "شبكه",
    "tax": "ضريبه", "taxes": "ضريبه", "taxation": "ضريبه", "ضرائب": "ضريبه", "vat": "ضريبه",
    "database": "database", "databases": "database",
    "procurement": "مشتريات", "purchasing": "مشتريات", "شراء": "مشتريات",
    "recruitment": "توظيف", "hiring": "توظيف", "استقطاب": "توظيف",
    "contracts": "عقد", "contract": "عقد", "عقود": "عقد",
    "cybersecurity": "cybersecurity", "اكسل": "excel", "اكسيل": "excel", "بايثون": "python",
    "genai": "ai", "خصم": "استقطاعات", "خصومات": "استقطاعات",
    "deduction": "استقطاعات", "deductions": "استقطاعات",
    "allowance": "بدلات", "allowances": "بدلات", "بدل": "بدلات",
    "supplier": "مورد", "suppliers": "مورد", "موردين": "مورد",
    "remuneration": "رواتب", "lease": "عقد", "leases": "عقد",
}
PHRASES = {
    "power bi": "powerbi", "باور بي اي": "powerbi", "اس كيو ال": "sql",
    "قواعد البيانات": "database", "قاعده البيانات": "database",
    "ذكاء اصطناعي": "ai", "الذكاء الاصطناعي": "ai", "ذكاء الاصطناعي": "ai",
    "للذكاء الاصطناعي": "ai",
    "امن سيبراني": "cybersecurity", "الامن السيبراني": "cybersecurity",
}
MODEL = {"id": "local-semantic-4.1", "representation": "sentence_embeddings_bm25_and_work_intent",
         "concept_weight": .2, "text_weight": .65, "bm25_weight": .15,
         "bm25_k1": 1.2, "bm25_b": .75, "action_mismatch_floor": .75,
         "title_weight": 2, "description_weight": 1, "minimum_similarity": .16,
         "domain_anchor_required": False, "offline": True, "organization_fine_tuned": False, "topic_discovery_supervised": False, "pretrained": True}
_ALIAS_SPELL = set(ALIASES) | set(ALIASES.values())
_ALIAS_DELETES = defaultdict(set)
for _word in _ALIAS_SPELL:
    if 5 <= len(_word) <= 40:
        for _key in {_word, *(_word[:i]+_word[i+1:] for i in range(len(_word)))}:
            _ALIAS_DELETES[_key].add(_word)

TECHNICAL = {"ai", "bi", "it", "hr", "qa", "ui", "ux", "ip", "ml", "db"}


def term_counts(text):
    return Counter(_term_counts(str(text or "")))


@lru_cache(maxsize=4096)
def _term_counts(text):
    text = re.sub(r"\[OMI[^\]]*\]", " ", str(text or ""), flags=re.I)
    text = re.sub(r"https?://\S+", " ", text, flags=re.I)
    text = re.sub(r"(?<!\w)[\w-]*\d[\w-]*(?!\w)",
                  lambda m: m.group() if re.fullmatch(r"(?:ipv[46]|iso[0-9]{4,5}|sql[0-9]{4})", m.group(), re.I) else " ", text)
    scoped, _ = scope_text(text)
    clean = language_text(scoped)
    for phrase, canonical in sorted(PHRASES.items(), key=lambda item: -len(item[0])):
        clean = re.sub(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", canonical, clean)
    result = Counter()
    known = set(ALIASES) | {"excel", "python", "sql", "powerbi", "sap", "api", "ai", "bi"}
    for token in clean.split():
        for prefix in ("وبال", "وال", "بال", "لل", "ال", "و", "ب", "ف", "ل"):
            if token.startswith(prefix) and token[len(prefix):] in known:
                token = token[len(prefix):]
                break
        if token.isdigit() or (len(token) < 3 and token not in TECHNICAL):
            continue
        if re.fullmatch(r"[\u0621-\u064a]+", token):
            # Only attached articles/prepositions; avoid destructive root guessing.
            for prefix in ("وبال", "وال", "بال", "كال", "فال", "لل", "ال"):
                if token.startswith(prefix) and len(token) - len(prefix) >= 3:
                    token = token[len(prefix):]
                    break
            if token[:1] in {"ل", "و", "ف"} and len(token) > 3 and token[1:] in GENERIC:
                token = token[1:]
        if token not in GENERIC:
            canonical = ALIASES.get(token, token)
            if token not in _ALIAS_SPELL and 5 <= len(token) <= 40:
                candidates = set()
                for key in {token, *(token[:i]+token[i+1:] for i in range(len(token)))}:
                    candidates.update(_ALIAS_DELETES.get(key, ()))
                replacements = {ALIASES.get(v,v) for v in candidates if one_edit(token,v)}
                if len(replacements) == 1:
                    canonical = next(iter(replacements))
            result[canonical] += 1
            if canonical == "powerbi":
                result["bi"] += 1
    return result


def terms(text):
    return set(term_counts(text))


def subject_text(text, tool_words=()):
    """Keep natural word order/surface while dropping workflow words and tools."""
    excluded=set(tool_words)
    return " ".join(token for token in re.findall(r"[\w]+",clean_text(text))
                    if set(term_counts(token))-excluded)


def subject_verification_floor(query, document):
    """Short subjects require stronger verification; cross-script prose differs."""
    def script(value):
        arabic=len(re.findall(r"[\u0621-\u064a]",value))
        latin=len(re.findall(r"[a-zA-Z]",value))
        return 'ar' if arabic>latin else 'en' if latin else None
    cross_script=script(query) and script(document) and script(query)!=script(document)
    return .005 if cross_script and len(query.split())>=3 else .05


def query_profile(text, index=None):
    labels = index.classify(text) if index else classify(text)
    query = set(index.query_counts(text)) if index else terms(text)
    tool_terms = set().union(*(terms(tag["en"]) | terms(tag["ar"]) for tag in labels if tag["type"] == "SYSTEM_OR_TOOL")) if labels else set()
    status = "no_subject" if not query else "tool_only" if query <= tool_terms else "specific"
    return {"status": status, "terms": sorted(query), "labels": labels,
            "domains": [tag for tag in labels if tag["type"] == "BUSINESS_DOMAIN"],
            "tools": [tag for tag in labels if tag["type"] == "SYSTEM_OR_TOOL"],
            "actions": [tag for tag in labels if tag["type"] == "TASK_TYPE"],
            "deliverables": [tag for tag in labels if tag["type"] == "DELIVERABLE_TYPE"],
            "domain_known": any(tag["type"] == "BUSINESS_DOMAIN" for tag in labels),
            "excluded_labels": [tag for clause in scope_text(text)[1] for tag in (index.classify(clause) if index else classify(clause))],
            "needs_clarification": status != "specific",
            "domain_discovery": index.domain_model.summary() if index and hasattr(index.domain_model,"summary") else {"status":"legacy"}}


class RelevanceIndex:
    """Sparse TF-IDF fitted to this source snapshot, never to employee identity.

    Each title term has weight 2 and each description term weight 1. Duplicate
    term-set documents count once for IDF, while source tasks remain distinct.
    """
    def __init__(self, records, domain_rules=None, domain_model=None, at=None, encoder=None, previous_domains=None):
        self.records = records
        self.identities = {(r.get("source","bitrix"),r.get("id")) for r in records}
        dates = [(parse(r.get("created_at")),parse(r.get("completed_at"))) for r in records]
        self.completed_valid = all(r.get("completed") and start and end and start < end for r,(start,end) in zip(records,dates))
        self.latest_completion = max((end for _,end in dates if end),default=None)
        self.domain_rules = domain_rules or []
        self.domain_phrases = [(rule, tuple(" " + language_text(a) + " " for a in rule["aliases"]))
                               for rule in self.domain_rules]
        counts = [(term_counts(r.get("title", "")), term_counts(r.get("description", ""))) for r in records]
        self.spell_words = set(ALIASES) | {word for pair in counts for field in pair for word in field}
        self.spell_deletes = defaultdict(set)
        for word in self.spell_words:
            if 5 <= len(word) <= 40:
                for key in {word, *(word[:i] + word[i+1:] for i in range(len(word)))}:
                    self.spell_deletes[key].add(word)
        self.semantic = SemanticSpace(records, encoder=encoder)
        self.domain_model = domain_model or AutomaticDomains(self.semantic, previous=previous_domains)
        self.patterns = [(tuple(sorted(title)),tuple(sorted(description))) for title,description in counts]
        self.field_counts = counts
        self.field_lengths = [[sum(field.values()) for field in pair] for pair in counts]
        self.field_vectors, self.field_norms = [], []
        self.words, self.labels, self.vectors, self.norms = [], [], [], []
        self.inverted = defaultdict(set)
        self.domain_inverted = defaultdict(set)
        raw, document_words = [], {}
        for index, row in enumerate(records):
            title, description = counts[index]
            words = set(title) | set(description)
            self.words.append(words)
            self.labels.append(self.classify(row.get("title", "") + " " + row.get("description", "")))
            for tag in self.labels[-1]:
                if tag["type"] == "BUSINESS_DOMAIN":
                    self.domain_inverted[tag["id"]].add(index)
            vector = {word: MODEL["title_weight"] * (1 + log(title[word])) if title[word] else 0 for word in words}
            for word in description:
                vector[word] += MODEL["description_weight"] * (1 + log(description[word]))
            raw.append(vector)
            document_words[(tuple(sorted(title)), tuple(sorted(description)))] = words
            for word in words:
                self.inverted[word].add(index)
        self.document_count = len(document_words)
        frequencies = Counter(word for words in document_words.values() for word in words)
        unique_fields = {(tuple(sorted(pair[0])),tuple(sorted(pair[1]))): pair for pair in counts}
        self.average_lengths = [sum(sum(pair[f].values()) for pair in unique_fields.values()) / max(1, len(unique_fields)) for f in (0, 1)]
        self.bm25_idf = {word: log(1 + (self.document_count - count + .5)/(count + .5)) for word, count in frequencies.items()}
        self.idf = {word: 1 + log((self.document_count + 1) / (count + 1)) for word, count in frequencies.items()}
        for vector in raw:
            weighted = {word: value * self.idf[word] for word, value in vector.items()}
            self.vectors.append(weighted)
            self.norms.append(sqrt(sum(value * value for value in weighted.values())))
        for pair in counts:
            fields = [{word: (1 + log(count))*self.idf[word] for word,count in field.items()} for field in pair]
            self.field_vectors.append(fields)
            self.field_norms.append([sqrt(sum(v*v for v in field.values())) for field in fields])

    def rule_labels(self, text):
        labels = [tag for tag in classify(text) if tag["type"] != "BUSINESS_DOMAIN"]
        cleaned = " " + language_text(scope_text(text)[0]) + " "
        for rule, phrases in self.domain_phrases:
            if any(phrase in cleaned for phrase in phrases):
                tag = {k: rule[k] for k in ("id", "ar", "en")}
                tag.update(type="BUSINESS_DOMAIN", basis="configured_rule")
                if not any(t["id"] == tag["id"] for t in labels):
                    labels.append(tag)
        return labels

    def query_counts(self, text):
        original = term_counts(text)
        counts = Counter()
        explicit = {t["id"] for t in self.rule_labels(text) if t["type"] == "BUSINESS_DOMAIN"}
        for word, count in original.items():
            corrected = word
            if word not in self.spell_words and 5 <= len(word) <= 40:
                candidates = set()
                for key in {word, *(word[:i]+word[i+1:] for i in range(len(word)))}:
                    candidates.update(self.spell_deletes.get(key, ()))
                candidates = {v for v in candidates if one_edit(word, v)}
                canonical = {}
                for candidate in candidates:
                    value = ALIASES.get(candidate, candidate)
                    domains = {t["id"] for t in self.rule_labels(value) if t["type"] == "BUSINESS_DOMAIN"}
                    if not explicit or not domains or explicit & domains:
                        canonical[value] = candidate
                if len(canonical) == 1:
                    corrected = next(iter(canonical))
            counts[corrected] += count
        return counts

    def classify(self, text):
        counts = self.query_counts(text)
        labels = self.rule_labels(text)
        known = {t["id"] for t in labels}
        for tag in self.rule_labels(" ".join(counts)):
            if tag["type"] in {"BUSINESS_DOMAIN", "SYSTEM_OR_TOOL", "CONCEPT"} and tag["id"] not in known:
                labels.append(tag); known.add(tag["id"])
        # Automatic topics supplement typed actions/tools; manual taxonomy is never consulted.
        return labels + self.domain_model.labels(scope_text(text)[0])

    def model_summary(self):
        ready = self.semantic is not None and self.semantic.status == "ready"
        verifier = get_reranker() if ready else None
        return {**MODEL, "id": MODEL["id"] if ready else "lexical-no-taxonomy",
                "pretrained": ready, "embedding_model": MODEL_ID if ready else None,
                "embedding_revision": MODEL_REVISION if ready else None,
                "reranker": RERANKER_ID if verifier else None,
                "reranker_revision": RERANKER_REVISION if verifier else None,
                "semantic_status": "ready" if ready else "unavailable",
                "verification_status": "ready" if verifier else "unavailable",
                "reranker_precision": getattr(verifier,"precision","fp32") if verifier else None,
                "long_pair_policy": "semantic_top_3_windows",
                "discovery": self.domain_model.summary() if hasattr(self.domain_model,"summary") else {"status":"legacy"},
                "fitted_documents": self.document_count, "vocabulary_size": len(self.idf)}

    def bm25(self, index, counts):
        k1, b = MODEL["bm25_k1"], MODEL["bm25_b"]
        unknown = log(1 + (self.document_count + .5)/.5)
        denominator = sum(self.bm25_idf.get(word, unknown)*(1+log(count)) for word,count in counts.items())
        score = 0
        for word, count in counts.items():
            weight = self.bm25_idf.get(word, unknown)*(1+log(count))
            for f, boost in ((0,2),(1,1)):
                field = self.field_counts[index][f]; frequency = field.get(word,0)
                if frequency:
                    length = self.field_lengths[index][f]
                    score += boost*weight*frequency*(k1+1)/(frequency+k1*(1-b+b*length/max(1,self.average_lengths[f])))
        return score / max(.001, denominator*3*(k1+1))

    def related(self, text, exclude=None, limit=300):
        counts = self.query_counts(text)
        if not counts:
            return []
        if query_profile(text, self)["status"] != "specific":
            return []
        query_labels = self.classify(text)
        query_domains = {tag["id"] for tag in query_labels if tag["type"] == "BUSINESS_DOMAIN"}
        unknown_idf = 1 + log(self.document_count + 1)
        query = {word: (1 + log(count)) * self.idf.get(word, unknown_idf) for word, count in counts.items()}
        qnorm = sqrt(sum(value * value for value in query.values()))
        possible = set().union(*(self.inverted.get(word, set()) for word in query))
        # Retrieve concept-equivalent text even if the surface words differ.
        if query_domains:
            possible.update(set().union(*(self.domain_inverted[d] for d in query_domains)))
        semantic_scores = None
        verifier = get_reranker() if self.semantic is not None and self.semantic.status=="ready" else None
        semantic_floor = .78 if verifier else MIN_SEMANTIC_COSINE
        if self.semantic is not None:
            _, semantic_scores = self.semantic.query(scope_text(text)[0])
            if semantic_scores is not None:
                possible.update(int(i) for i in (semantic_scores >= semantic_floor).nonzero()[0])
        matches = []
        method = self.model_summary()["id"]
        tool_words = set().union(*(terms(t["ar"] + " " + t["en"]) for t in query_labels if t["type"] == "SYSTEM_OR_TOOL"))
        for index in possible:
            row, words = self.records[index], self.words[index]
            if exclude == (row.get("source"), row.get("id")):
                continue
            row_domains = {tag["id"] for tag in self.labels[index] if tag["type"] == "BUSINESS_DOMAIN"}
            shared = set(query) & words
            cosine = sum(query[word] * self.vectors[index][word] for word in shared) / max(.001, qnorm * self.norms[index])
            field_cosines = [sum(query[word]*field[word] for word in set(query)&field.keys()) /
                             max(.001,qnorm*norm) for field,norm in zip(self.field_vectors[index],self.field_norms[index])]
            text_score = max(cosine, .85*field_cosines[0]+.15*field_cosines[1])
            bm25 = self.bm25(index, counts)
            qtopics = {t["id"] for t in query_labels if t["type"] in {"BUSINESS_DOMAIN", "SYSTEM_OR_TOOL", "CONCEPT"}}
            rtopics = {t["id"] for t in self.labels[index] if t["type"] in {"BUSINESS_DOMAIN", "SYSTEM_OR_TOOL", "CONCEPT"}}
            concept = len(qtopics & rtopics) / max(1, len(qtopics | rtopics))
            # Concept-only retrieval requires a real domain, never just Excel.
            semantic_cosine = float(semantic_scores[index]) if semantic_scores is not None else None
            semantic_strong = semantic_cosine is not None and semantic_cosine >= semantic_floor and semantic_cosine >= float(semantic_scores.max()) - (.10 if verifier else .05)
            if not shared and not (query_domains & row_domains) and not semantic_strong:
                continue
            subject_coverage = 0
            subject_words = set(counts) - tool_words
            subject_overlap = subject_words & shared
            subject_coverage = len(subject_overlap)/max(1,len(subject_words))
            if not semantic_strong and (not subject_overlap or subject_coverage < .5):
                continue
            combined = .65*text_score + .15*bm25 + .2*concept if qtopics and rtopics else .85*text_score + .15*bm25
            query_actions = {t["id"] for t in query_labels if t["type"] == "TASK_TYPE"}
            row_actions = {t["id"] for t in self.labels[index] if t["type"] == "TASK_TYPE"}
            action_coverage = len(query_actions & row_actions)/len(query_actions) if query_actions else 1
            # Missing source detail is not an explicit contradictory work type.
            action_factor = .75 + .25*action_coverage if query_actions and row_actions else 1
            semantic_score = max(0, min(1, (semantic_cosine - .70)/.30)) if semantic_cosine is not None else None
            if semantic_score is not None:
                combined = .70 * semantic_score + .30 * combined
            combined *= action_factor
            if combined < MODEL["minimum_similarity"]:
                continue
            ordered = sorted(shared, key=lambda word: (-query[word] * self.vectors[index][word], word))
            matches.append(({"task": row, "score": round(100 * min(1, combined)),
                            "lexical_score": round(100 * min(1, text_score)), "bm25_score": round(100*bm25),
                            "semantic_cosine": round(semantic_cosine,4) if semantic_cosine is not None else None,
                            "semantic_score": round(100*semantic_score,2) if semantic_score is not None else None,
                            "subject_coverage": round(subject_coverage,4),
                            "action_coverage": round(action_coverage,3), "concept_score": round(100 * concept),
                            "shared_terms": ordered, "labels": self.labels[index],
                            "subject_match": bool(query_domains & row_domains), "method": method}, index))
        # Verify candidate pairs jointly, without a business taxonomy. Distinct
        # content is cached by the verifier so repeated tasks do not repeat work.
        reranker = verifier
        if reranker and matches:
            preliminary=sorted(matches,key=lambda pair:-pair[0]["score"])
            budget=min(300,max(40,limit))
            chosen=[];people=set();chosen_ids=set()
            for match,i in preliminary:
                person=(match["task"].get("source"),match["task"].get("assignee_id"))
                if person not in people and len(chosen)<budget:
                    chosen.append((match,i));people.add(person);chosen_ids.add(i)
            for match,i in preliminary:
                if i not in chosen_ids and len(chosen)<budget:chosen.append((match,i));chosen_ids.add(i)
            # Copies retain their source IDs after their shared content is verified.
            patterns={self.patterns[i] for _,i in chosen}
            matches=[pair for pair in matches if pair[1] in chosen_ids or self.patterns[pair[1]] in patterns]
            subject_query=subject_text(text,tool_words)
            subject_pairs=[]
            for _,i in matches:
                row_tools=set().union(*(terms(t["ar"]+" "+t["en"]) for t in self.labels[i] if t["type"]=="SYSTEM_OR_TOOL"))
                subject_pairs.append((subject_query,subject_text(self.semantic.texts[i],row_tools)))
            needs_subject=[j for j,(match,_) in enumerate(matches) if match["subject_coverage"]<.5]
            subject_verification=[None]*len(matches)
            full_pairs=[(text,self.semantic.texts[i]) for _,i in matches]
            all_scores=reranker.score(full_pairs+[subject_pairs[j] for j in needs_subject])
            verification=all_scores[:len(matches)]
            for j,value in zip(needs_subject,all_scores[len(matches):]):
                subject_verification[j]=value
            verified=[]
            for (match,i),score,subject_score,subject_pair in zip(matches,verification,subject_verification,subject_pairs):
                match["verification_score"]=round(score,4)
                # Exact/synonym subject overlap supports a lower verification floor;
                # purely semantic retrieval needs stronger independent verification.
                minimum=0 if match["subject_coverage"]>=.5 else .05
                if not subject_pair[1] or score<minimum or (minimum and subject_score<subject_verification_floor(*subject_pair)):continue
                match["subject_verification_score"]=round(subject_score,4) if subject_score is not None else None
                match["verification_basis"]="neural_subject" if subject_score is not None else "lexical_subject"
                match["score"]=round(.6*match["score"]+.4*100*score)
                if match["score"]>=16:verified.append((match,i))
            matches=verified
        ordered = sorted(matches, key=lambda item: (-item[0]["score"], str(item[0]["task"]["id"])))
        if len(ordered) <= limit:
            return [match for match,_ in ordered]
        chosen, people, patterns = set(),set(),set()
        # Preserve the best evidence for different executors before copies consume the retrieval budget.
        for match,index in ordered:
            row = match["task"]; person = (row.get("source"),row.get("assignee_id"))
            if row.get("assignee_id") and person not in people and len(chosen) < limit:
                chosen.add(index);people.add(person)
                patterns.add((person,self.patterns[index]))
        for match,index in ordered:
            row = match["task"]; person = (row.get("source"),row.get("assignee_id"))
            key = (person,self.patterns[index])
            if key not in patterns and len(chosen) < limit:
                chosen.add(index);patterns.add(key)
        for _,index in ordered:
            if len(chosen) >= limit:
                break
            chosen.add(index)
        return [match for match,index in ordered if index in chosen]


def one_edit(a, b):
    if abs(len(a)-len(b)) > 1 or a == b:
        return False
    # Never correct between scripts.
    if bool(re.search("[ا-ي]",a)) != bool(re.search("[ا-ي]",b)):
        return False
    if len(a) == len(b):
        changed = [i for i,(x,y) in enumerate(zip(a,b)) if x != y]
        return len(changed) == 1 or (len(changed) == 2 and changed[1] == changed[0]+1
            and a[changed[0]] == b[changed[1]] and a[changed[1]] == b[changed[0]])
    short, long = (a,b) if len(a) < len(b) else (b,a)
    return any(long[:i]+long[i+1:] == short for i in range(len(long)))


def group_related(matches):
    """Group exact normalized content for display, preserving every source ID."""
    groups = {}
    for match in matches:
        row = match["task"]
        title = re.sub(r"\[OMI[^\]]*\]", "", row.get("title", ""), flags=re.I)
        key = (row.get("source"), normalize(title), normalize(row.get("description", "")))
        group = groups.setdefault(key, {**match, "duplicate_tasks": []})
        group["duplicate_tasks"].append({"id": row["id"], "assignee": row.get("assignee_name") or row.get("assignee_id", "")})
    return list(groups.values())

