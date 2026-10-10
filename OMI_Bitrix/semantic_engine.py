"""Offline sentence embeddings and unsupervised, snapshot-scoped topic discovery.
No predefined business domains, remote inference, task persistence or identity
features. Topic names are extracted phrases, not verified organisational roles.
"""
import hashlib
import os
import re
import threading
import unicodedata
from copy import deepcopy
from time import perf_counter
from collections import OrderedDict
from pathlib import Path

MODEL_ID = "intfloat/multilingual-e5-base"
RERANKER_ID = "BAAI/bge-reranker-v2-m3"
RERANKER_REVISION = "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
RERANKER_PATH = Path(__file__).resolve().parent / "models" / "bge-reranker-v2-m3"
_reranker = None
_reranker_error = None
MODEL_REVISION = "d128750597153bb5987e10b1c3493a34e5a4502a"
DEFAULT_PATH = Path(__file__).resolve().parent / "models" / "multilingual-e5-base"
MIN_SEMANTIC_COSINE = .84
MIN_TOPIC_COSINE = .86  # Initial engineering threshold, not a probability.
_lock = threading.RLock()
_encoder = None
_load_error = None


def clean_text(text):
    """Preserve natural Arabic; remove reference/transport noise."""
    from task_language import scope_text
    text = scope_text(str(text or ""))[0]
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = re.sub(r"https?://\S+|[^\s@]+@[^\s@]+|<[^>]*>", " ", text)
    text = re.sub(r"\[(?:/?(?:b|i|u|url|quote)|[^\]]*\d[^\]]*)\]", " ", text, flags=re.I)
    text = re.sub(r"(?<!\w)(?:[A-Za-z]+[-_]*)+\d[\w-]*", " ", text)
    text = re.sub(r"\b(?:ticket|request|task|تذكرة|التذكرة|طلب|الطلب)\s*(?:id|رقم|number|#|:)\s*\d+", " ", text, flags=re.I)
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text)
    text = re.sub(r"(?:synthetic(?:\s+\w+){0,3}\s+test\s+only|no real work required)[^.\n]*[.\n]?", " ", text, flags=re.I)
    return " ".join(text.split())[:16000]


def fingerprint(text):
    normalized = re.sub(r"[^\w\s]", " ", clean_text(text).casefold())
    return hashlib.sha256(" ".join(normalized.split()).encode("utf-8")).hexdigest()


def inference_threads():
    available=os.cpu_count() or 1
    default=8 if available>=16 else min(4,available)
    return max(1,min(int(os.environ.get('TASK_TORCH_THREADS',str(default))),available))


def model_text_key(text):
    """Inference keys preserve case and punctuation seen by the tokenizer."""
    return hashlib.sha256(clean_text(text).encode("utf-8")).hexdigest()


class LocalEncoder:
    def __init__(self, path):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        from sentence_transformers import SentenceTransformer
        import torch
        torch.set_num_threads(inference_threads())
        self.model = SentenceTransformer(str(path), device="cpu", local_files_only=True,
            trust_remote_code=False, model_kwargs={"use_safetensors": True})
        self.model.max_seq_length = 512
        self.lock = threading.RLock()
        self.cache = OrderedDict()  # Exact cleaned-text hash -> vector.
        self.stats = {"requests": 0, "cache_hits": 0, "encoded_texts": 0, "windows": 0, "inference_ms": 0.0}

    def encode(self, texts):
        import numpy as np
        with self.lock:
            cleaned = [clean_text(t) for t in texts]
            keys = [model_text_key(t) for t in cleaned]
            self.stats["requests"] += len(keys)
            self.stats["cache_hits"] += sum(key in self.cache for key in keys)
            missing = OrderedDict((key, t) for key, t in zip(keys, cleaned) if key not in self.cache)
            chunks, owners = [], []
            for key, text in missing.items():
                tokens = self.model.tokenizer.encode(text, add_special_tokens=False, verbose=False)
                for start in range(0, max(1, len(tokens)), 384):
                    chunk = self.model.tokenizer.decode(tokens[start:start + 448], skip_special_tokens=True)
                    chunks.append("query: " + chunk)  # E5 symmetric/clustering recipe.
                    owners.append(key)
                    if start + 448 >= len(tokens):
                        break
            if chunks:
                start_time = perf_counter()
                vectors = self.model.encode(chunks, batch_size=16, normalize_embeddings=True,
                    show_progress_bar=False, convert_to_numpy=True)
                self.stats["inference_ms"] += (perf_counter() - start_time) * 1000
                self.stats["encoded_texts"] += len(missing)
                self.stats["windows"] += len(chunks)
                grouped = {}
                for key, vector in zip(owners, vectors):
                    grouped.setdefault(key, []).append(vector)
                for key, values in grouped.items():
                    vector = np.mean(values, axis=0)
                    self.cache[key] = vector / max(float(np.linalg.norm(vector)), 1e-12)
            result = np.asarray([self.cache[key] for key in keys], dtype=np.float32)
            for key in keys:
                self.cache.move_to_end(key)
            while len(self.cache) > 4096:
                self.cache.popitem(last=False)
            return result


def get_encoder():
    global _encoder, _load_error
    if os.environ.get("TASK_MODEL_MODE") in {"lexical", "legacy"}:
        return None
    with _lock:
        if _encoder is not None:
            return _encoder
        if _load_error:
            return None
        path = Path(os.environ.get("TASK_EMBEDDING_PATH", str(DEFAULT_PATH)))
        if not (path / "model.safetensors").is_file():
            return None
        try:
            _encoder = LocalEncoder(path)
        except Exception as exc:
            _load_error = type(exc).__name__
        return _encoder


class LocalReranker:
    """Local pairwise semantic verification; score is not calibrated confidence."""
    def __init__(self, path):
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
        import torch
        torch.set_num_threads(inference_threads())
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        self.tokenizer = AutoTokenizer.from_pretrained(str(path),local_files_only=True,trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(str(path),local_files_only=True,
            trust_remote_code=False,use_safetensors=True).eval()
        self.precision=os.environ.get('TASK_RERANKER_PRECISION','fp32')
        if self.precision not in {'fp32','int8'}:
            raise ValueError('TASK_RERANKER_PRECISION must be fp32 or int8')
        if self.precision=='int8':
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',DeprecationWarning)
                self.model=torch.ao.quantization.quantize_dynamic(self.model,{torch.nn.Linear},dtype=torch.qint8)
        self.lock = threading.RLock()
        self.cache = OrderedDict()
        self.stats = {"requests": 0, "cache_hits": 0, "long_pairs": 0, "forward_items": 0, "forward_batches": 0, "inference_ms": 0.0}

    def windows(self, query, document):
        """Keep short pairs intact; select relevant windows for long pairs."""
        qids = self.tokenizer.encode(query, add_special_tokens=False, verbose=False)
        dids = self.tokenizer.encode(document, add_special_tokens=False, verbose=False)
        if len(qids) + len(dids) + self.tokenizer.num_special_tokens_to_add(pair=True) <= 512:
            return [(query, document)]
        def split(ids, width, stride):
            chunks=[]
            for start in range(0,max(1,len(ids)),stride):
                chunks.append(self.tokenizer.decode(ids[start:start+width],skip_special_tokens=True))
                if start+width>=len(ids):break
            return chunks
        queries = split(qids,192,160)
        documents = split(dids,288,240)
        encoder = get_encoder()
        if encoder:
            vectors = encoder.encode(queries+documents)
            scores = vectors[:len(queries)] @ vectors[len(queries):].T
            order = scores.reshape(-1).argsort(kind="stable")[::-1][:3]
            return [(queries[int(i)//len(documents)],documents[int(i)%len(documents)]) for i in order]
        # Without embeddings, cover the whole pair rather than silently dropping its tail.
        return [(q,d) for q in queries for d in documents]

    def score(self, pairs):
        import torch
        with self.lock:
            cleaned=[(clean_text(q),clean_text(d)) for q,d in pairs]
            keys=[(model_text_key(q),model_text_key(d)) for q,d in cleaned]
            self.stats["requests"] += len(keys)
            self.stats["cache_hits"] += sum(key in self.cache for key in keys)
            missing=OrderedDict((key,pair) for key,pair in zip(keys,cleaned) if key not in self.cache)
            items=[]
            for key,(query,document) in missing.items():
                windows=self.windows(query,document)
                self.stats["long_pairs"] += len(windows)>1
                items.extend((key,pair) for pair in windows)
            # Tokenize once, then bucket by actual token length with bounded padding.
            scores_by_key={}
            if items:
                encoded=self.tokenizer([pair for _,pair in items],padding=False,truncation=True,max_length=512)
                lengths=[len(ids) for ids in encoded['input_ids']]
                positions=sorted(range(len(items)),key=lambda i:lengths[i])
                batches=[];batch=[]
                for i in positions:
                    if batch and (len(batch)>=32 or lengths[i]*(len(batch)+1)>4096):
                        batches.append(batch);batch=[]
                    batch.append(i)
                if batch:batches.append(batch)
                for positions in batches:
                    inputs=self.tokenizer.pad({k:[values[i] for i in positions] for k,values in encoded.items()},padding=True,return_tensors='pt')
                    started=perf_counter()
                    with torch.inference_mode():
                        scores=torch.sigmoid(self.model(**inputs).logits.reshape(-1).float()).tolist()
                    self.stats['inference_ms']+=(perf_counter()-started)*1000
                    self.stats['forward_items']+=len(positions)
                    self.stats['forward_batches']+=1
                    for i,score in zip(positions,scores):
                        key=items[i][0]
                        scores_by_key[key]=max(scores_by_key.get(key,0.0),float(score))
            self.cache.update(scores_by_key)
            result=[self.cache[key] for key in keys]
            for key in keys:self.cache.move_to_end(key)
            while len(self.cache)>4096:self.cache.popitem(last=False)
            return result


def get_reranker():
    global _reranker,_reranker_error
    if os.environ.get("TASK_MODEL_MODE") in {"lexical","legacy"}:return None
    with _lock:
        if _reranker is not None:return _reranker
        if _reranker_error:return None
        path=Path(os.environ.get("TASK_RERANKER_PATH",str(RERANKER_PATH)))
        if not (path/"model.safetensors").is_file():return None
        try:_reranker=LocalReranker(path)
        except Exception as exc:_reranker_error=type(exc).__name__
        return _reranker


class SemanticSpace:
    def __init__(self, records, encoder=None):
        self.encoder = encoder if encoder is not None else (get_encoder() if records else None)
        self.status = "ready" if self.encoder else "unavailable"
        self.records = records
        self.vectors = None
        self.texts = [clean_text(r.get("title", "") + ". " + r.get("description", "")) for r in records]
        if self.encoder and records:
            import numpy as np
            titles = [clean_text(r.get("title", "")) for r in records]
            descriptions = [clean_text(r.get("description", "")) for r in records]
            title_vectors = self.encoder.encode(titles)
            desc_vectors = self.encoder.encode([d or t for d, t in zip(descriptions, titles)])
            vectors = .7 * title_vectors + .3 * desc_vectors
            self.vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)

    def query(self, text):
        if not self.encoder or self.vectors is None:
            return None, None
        vector = self.encoder.encode([text])[0]
        return vector, self.vectors @ vector


class AutomaticDomains:
    """Discover topics from this corpus only, without a domain vocabulary."""
    associations = {}

    def __init__(self, space, previous=None):
        self.space = space
        self.topics = []
        self.status = space.status
        self.outliers = 0
        self.memberships = {}
        self.outlier_keys = set()
        self.label_cache = OrderedDict()
        self.label_lock = threading.RLock()
        self.unique_documents = 0
        if space.vectors is None:
            return
        import numpy as np
        unique = OrderedDict()
        for i, text in enumerate(space.texts):
            if clean_text(text).strip(". "):
                unique.setdefault(fingerprint(text), i)
        from datetime import datetime
        from sla import parse, TZ
        instant = datetime.now(TZ)
        positions = [i for i in unique.values() if not (parse(space.records[i].get("created_at"))
            and parse(space.records[i]["created_at"]) > instant) and not (space.records[i].get("completed")
            and parse(space.records[i].get("completed_at")) and parse(space.records[i]["completed_at"]) > instant)]
        self.unique_documents = len(positions)
        if len(positions) < 6:
            self.status = "insufficient_corpus"
            return
        vectors = space.vectors[positions]
        from sklearn.cluster import HDBSCAN
        labels = HDBSCAN(min_cluster_size=3, min_samples=2,
            metric="euclidean", cluster_selection_method="leaf", copy=True).fit_predict(vectors)
        groups = []
        for label in sorted(set(labels)):
            members = [positions[i] for i, v in enumerate(labels) if v == label]
            if label == -1 or len(members) < 2:
                self.outliers += len(members)
                self.outlier_keys.update(fingerprint(self.space.texts[i]) for i in members)
                continue
            center = np.mean(space.vectors[members], axis=0)
            center /= max(float(np.linalg.norm(center)), 1e-12)
            groups.append((members, center))
        self._represent(groups, previous)
        self.status = "ready" if self.topics else "insufficient_structure"

    def _represent(self, groups, previous):
        if not groups:
            return
        import numpy as np
        from sklearn.feature_extraction.text import CountVectorizer
        from similarity import normalize, STOPWORDS
        generic = set(normalize(" ".join(STOPWORDS) + " مراجعة تحليل تقرير استخراج اعداد تنفيذ مهمة مهام طلب عمل شهر شهور الموظفين using report review analysis task tasks employee employees synthetic test only real work required").split())

        def tokenize(text):
            return [t for t in normalize(text).split() if len(t) >= 3 and not any(c.isdigit() for c in t) and t not in generic]

        vectorizer = CountVectorizer(tokenizer=tokenize, token_pattern=None,
                                    lowercase=False, ngram_range=(1, 2))
        texts = ["\n".join(self.space.texts[i] for i in members) for members, _ in groups]
        try:
            counts = vectorizer.fit_transform(texts).toarray().astype(float)
        except ValueError:
            return
        names = vectorizer.get_feature_names_out()
        lengths = counts.sum(axis=1)
        tf = counts / np.maximum(lengths[:, None], 1)
        weights = tf * np.log(1 + max(float(lengths.mean()), 1) / np.maximum(counts.sum(axis=0), 1))
        used_ids = set()
        for n, (members, center) in enumerate(groups):
            ordered = np.argsort(-weights[n], kind="stable")
            surface = {}
            for member in members:
                words = re.findall(r"[\w]+", self.space.texts[member])
                for width in (1,2):
                    for start in range(len(words)-width+1):
                        phrase = " ".join(words[start:start+width])
                        surface.setdefault(normalize(phrase), phrase)
            phrases = [surface.get(str(names[i]),str(names[i])) for i in ordered if weights[n, i] > 0][:12]
            if not phrases:
                continue
            arabic = [p for p in phrases if re.search(r"[\u0621-\u064a]", p)]
            english = [p for p in phrases if re.search(r"[a-zA-Z]", p) and not re.search(r"[\u0621-\u064a]", p)]
            signature = "|".join(sorted(phrases[:5]))
            ident = "topic_" + hashlib.sha256(signature.encode()).hexdigest()[:12]
            if previous:
                similar = sorted(((float(center @ t["center"]), t) for t in previous.topics
                                  if t["id"] not in used_ids), key=lambda v: -v[0])
                if similar and similar[0][0] >= .90:
                    ident = similar[0][1]["id"]
            if ident in used_ids:
                ident += "_" + fingerprint(self.space.texts[members[0]])[:6]
            used_ids.add(ident)
            ordered_members = sorted(members, key=lambda i: -float(self.space.vectors[i] @ center))
            topic = {"id": ident, "type": "BUSINESS_DOMAIN",
                "ar": " · ".join((arabic or phrases)[:3]), "en": " · ".join((english or arabic or phrases)[:3]),
                "basis": "discovered_topic", "terms": phrases[:8], "support": len(members),
                "center": center, "examples": [{"source": self.space.records[i].get("source", "bitrix"),
                    "id": self.space.records[i]["id"]} for i in ordered_members[:3]],
                "representative_texts": [self.space.texts[i] for i in ordered_members[:3]]}
            self.topics.append(topic)
            for member in members:self.memberships[fingerprint(self.space.texts[member].replace(". "," "))]=topic

    def labels(self, text, vector=None):
        with self.label_lock:
            return self._labels(text, vector)

    def _labels(self, text, vector=None):
        if not self.topics:
            return []
        known_key=fingerprint(text)
        if known_key in self.outlier_keys:
            return []
        known = self.memberships.get(known_key)
        if known:
            return [{k:v for k,v in known.items() if k not in {"center","representative_texts"}}]
        cache_key=model_text_key(text)
        if vector is None and cache_key in self.label_cache:
            self.label_cache.move_to_end(cache_key)
            return deepcopy(self.label_cache[cache_key])
        cacheable = vector is None
        if vector is None:
            vector = self.space.encoder.encode([text])[0]
        similarities = sorted(((float(vector @ t["center"]), t) for t in self.topics), key=lambda v: -v[0])
        best = similarities[0][0]
        candidates=[(score,topic) for score,topic in similarities[:2]
            if score>=MIN_TOPIC_COSINE and score>=best-.025]
        reranker=get_reranker()
        accepted=[]
        if reranker:
            from recommendation_matching import subject_text, subject_verification_floor, terms
            from employee_insights import classify
            def subject(value):
                tools=set().union(*(terms(t['ar']+' '+t['en']) for t in classify(value) if t['type']=='SYSTEM_OR_TOOL'))
                return subject_text(value,tools)
            query_subject=subject(text)
        checks=[]
        for score,topic in candidates:
            full=[(text,t) for t in topic['representative_texts']]
            subject_pairs=[(query_subject,subject(t)) for t in topic['representative_texts']] if reranker else []
            checks.append((score,topic,full,subject_pairs))
        values=iter(reranker.score([pair for _,_,full,subjects in checks for pair in full+subjects])) if reranker else None
        for score,topic,full,subject_pairs in checks:
            full_scores=[next(values) for _ in full] if values is not None else []
            subject_scores=[next(values) for _ in subject_pairs] if values is not None else []
            verified=max(full_scores) if full_scores else None
            if verified is not None and verified<.20:continue
            if reranker and (not query_subject or not any(pair[1] and value>=subject_verification_floor(*pair) for pair,value in zip(subject_pairs,subject_scores))):continue
            accepted.append({k:v for k,v in topic.items() if k not in {'center','representative_texts'}} |
                {'relevance':round(score,4),'verification_score':round(verified,4) if verified is not None else None})
        if cacheable:
            self.label_cache[cache_key]=deepcopy(accepted)
            while len(self.label_cache)>1024:self.label_cache.popitem(last=False)
        return accepted

    def summary(self):
        return {"status": self.status, "topics": len(self.topics),
                "unique_documents": self.unique_documents, "outliers": self.outliers,
                "method": "sentence_embeddings_hdbscan_class_tfidf", "predefined_domains": False}
