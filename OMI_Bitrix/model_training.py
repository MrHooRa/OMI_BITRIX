"""Local, reviewed-pair fine-tuning. Never treat an assignment as a relevance label."""
import argparse
import hashlib
import json
import os
import random
from collections import defaultdict
from pathlib import Path

from semantic_engine import clean_text, model_text_key, RERANKER_PATH, RERANKER_ID, RERANKER_REVISION
from recommendation_matching import term_counts
from sla import parse

SPLITS = ("train", "validation", "test")


def family_key(text):
    # Ignore tickets, recurring dates and workflow boilerplate when checking leakage.
    return " ".join(sorted(term_counts(text))) or model_text_key(text)


def validate_dataset(data, minimum_groups=(20, 5, 5)):
    if data.get("schema_version") != 1 or not isinstance(data.get("scope_id"), str) or not data["scope_id"].strip():
        raise ValueError("schema_version=1 and an explicit organisation/source scope_id are required")
    rows = data.get("pairs")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No reviewed pairs. Historical assignees are not relevance labels")
    ownership = {}; queries = {}; groups = defaultdict(set); dates = defaultdict(list); seen = set()
    for row in rows:
        split = row.get("split")
        if split not in SPLITS:
            raise ValueError("Every reviewed pair needs train, validation or test split")
        for field in ("query_id", "group_id", "document_id", "reviewed_by"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"Missing {field}; use opaque identifiers rather than personal names")
        if row.get("label_source") != "human_review" or type(row.get("label")) is not int or row["label"] not in (0, 1):
            raise ValueError("A human-reviewed 0/1 relevance label is required; unreviewed is not negative")
        for field in ("query", "document"):
            value = row.get(field)
            if not isinstance(value, str) or not clean_text(value) or len(value) > 16000:
                raise ValueError(f"{field} must be nonempty text of at most 16000 characters")
        at, done, observed, judged = (parse(row.get(k)) for k in ("query_at", "document_completed_at", "document_observed_at", "judged_at"))
        if not all((at, done, observed, judged)) or not done < at or observed > at or judged < at:
            raise ValueError("Invalid chronology: evidence must be completed/observed before the query, and reviewed afterwards")
        if row.get("document_completed") is not True:
            raise ValueError("Training evidence must be explicitly completed; pending work is not success")
        identity = (row["query_id"], row["document_id"])
        pair = (model_text_key(row["query"]), model_text_key(row["document"]))
        if identity in seen or pair in seen:
            raise ValueError("Duplicate query/document pair; review once instead of inflating support")
        seen.update((identity, pair))
        qid = row["query_id"]
        description = (model_text_key(row["query"]), at, row["group_id"])
        if qid in queries and queries[qid] != description:
            raise ValueError("A query ID must have one text, time and task-family group")
        queries[qid] = description
        for key in (("query", qid), ("family", row["group_id"]), ("content", family_key(row["query"]))):
            if key in ownership and ownership[key] != split:
                raise ValueError("Task-family/query leakage between training and held-out splits")
            ownership[key] = split
        groups[split].add(row["group_id"]); dates[split].append(at)
    for split, minimum in zip(SPLITS, minimum_groups):
        if len(groups[split]) < minimum:
            raise ValueError(f"Need at least {minimum} distinct {split} task families; found {len(groups[split])}")
        labels = defaultdict(set)
        for row in rows:
            if row["split"] == split: labels[row["query_id"]].add(row["label"])
        if any(values != {0, 1} for values in labels.values()):
            raise ValueError("Each query needs reviewed relevant and irrelevant candidates")
    if max(dates["train"]) >= min(dates["validation"]) or max(dates["validation"]) >= min(dates["test"]):
        raise ValueError("Use chronological train/validation/test partitions")
    return {"pairs": len(rows), "queries": len(queries), "families": {s: len(groups[s]) for s in SPLITS},
            "scope_id": data["scope_id"], "source": "explicit_human_relevance"}


def prepare_review(snapshot, scope_id, limit=50):
    """Mine challenging candidates for review, leaving every label unset."""
    from recommendation_matching import RelevanceIndex
    instant = parse(snapshot.get("snapshot_at"))
    if not instant or not scope_id.strip() or not isinstance(snapshot.get("records"), list):
        raise ValueError("Provide an accessible source snapshot with snapshot_at, records and scope_id")
    rows = snapshot["records"]
    if any(not parse(r.get("observed_at")) or parse(r["observed_at"]) > instant for r in rows):
        raise ValueError("Every snapshot record needs an observed_at no later than snapshot_at")
    completed = [r for r in rows if r.get("completed") and parse(r.get("completed_at")) and parse(r["completed_at"]) < instant]
    index = RelevanceIndex(completed)
    by_key = {(r.get("source", "bitrix"), str(r["id"])): r for r in completed}
    pairs=[]; families=set()
    for row in rows:
        query = clean_text(row.get("title", "") + " " + row.get("description", ""))
        family = family_key(query)
        if not query or family in families: continue
        families.add(family)
        key = (row.get("source", "bitrix"), str(row["id"]))
        candidates = [m["task"] for m in index.related(query, exclude=key, limit=6)]
        # Include low-similarity alternatives as unlabelled examples, never automatic negatives.
        candidates += [r for k,r in by_key.items() if k != key and r not in candidates][:2]
        seen=set()
        for document in candidates:
            document_text=clean_text(document.get("title", "")+" "+document.get("description", ""))
            if model_text_key(document_text) in seen or model_text_key(document_text)==model_text_key(query):continue
            seen.add(model_text_key(document_text))
            pairs.append({"query_id": ":".join(key), "group_id": hashlib.sha256(family.encode()).hexdigest()[:16],
                "query":query,"query_at":snapshot["snapshot_at"],
                "document_id":document.get("source", "bitrix")+":"+str(document["id"]),"document":document_text,
                "document_completed":True,"document_completed_at":document["completed_at"],
                "document_observed_at":document["observed_at"],"label":None,"label_source":"unreviewed",
                "reviewed_by":"","judged_at":"","split":""})
        if len(families)>=limit:break
    return {"schema_version":1,"scope_id":scope_id,"pairs":pairs,
            "note":"Review text relevance, not employee identity. No automatic positive or negative labels. Temporal production evaluation still needs later independently reviewed queries."}


def ranking_metrics(rows, scores, k=3):
    from recommendation_evaluation import metrics
    grouped=defaultdict(list)
    for row,score in zip(rows,scores):grouped[row["query_id"]].append((row,float(score)))
    values=[]; false_positives=0; negatives=0
    for pairs in grouped.values():
        pairs.sort(key=lambda p:(-p[1],p[0]["document_id"]))
        judgments={r["document_id"]:r["label"] for r,_ in pairs}
        values.append(metrics([r["document_id"] for r,_ in pairs],judgments,k))
        for row,score in pairs:
            if not row["label"]:negatives+=1;false_positives+=score>=.5
    return {"queries":len(values), **{name:sum(v[name] for v in values)/len(values) for name in ("ndcg_at_k","mrr","recall_at_k")},
            "negative_acceptance_at_0_5":false_positives/max(1,negatives)}


def predict(model, tokenizer, rows, batch_size=4):
    import torch
    model.eval();scores=[]
    for start in range(0,len(rows),batch_size):
        batch=rows[start:start+batch_size]
        inputs=tokenizer([(clean_text(r["query"]),clean_text(r["document"])) for r in batch],
                         padding=True,truncation=True,max_length=512,return_tensors="pt")
        with torch.inference_mode():scores.extend(torch.sigmoid(model(**inputs).logits.reshape(-1).float()).tolist())
    return scores


def set_trainable_head(model):
    if not hasattr(model,"classifier"):
        raise ValueError("Expected the local XLM-R classification head")
    for parameter in model.parameters():parameter.requires_grad_(False)
    for parameter in model.classifier.parameters():parameter.requires_grad_(True)
    return [p for p in model.parameters() if p.requires_grad]


def training_epoch(model, tokenizer, rows, optimizer, batch_size=4, accumulation=4, seed=37):
    import torch
    order=list(rows);random.Random(seed).shuffle(order)
    # Keep the frozen backbone deterministic; train dropout only in the head.
    model.eval();model.classifier.train();optimizer.zero_grad(set_to_none=True)
    batches=[order[i:i+batch_size] for i in range(0,len(order),batch_size)]
    positives=sum(r["label"] for r in rows)
    positive_weight=torch.tensor((len(rows)-positives)/max(1,positives),dtype=torch.float32)
    total=0.0
    for number,batch in enumerate(batches):
        inputs=tokenizer([(clean_text(r["query"]),clean_text(r["document"])) for r in batch],
                         padding=True,truncation=True,max_length=512,return_tensors="pt")
        logits=model(**inputs).logits.reshape(-1).float()
        loss=torch.nn.functional.binary_cross_entropy_with_logits(logits,torch.tensor([r["label"] for r in batch],dtype=torch.float32),pos_weight=positive_weight)
        if not torch.isfinite(loss):raise ValueError("Non-finite training loss; candidate was not saved")
        window_start=(number//accumulation)*accumulation
        window_samples=sum(len(v) for v in batches[window_start:window_start+accumulation])
        (loss*len(batch)/window_samples).backward();total+=float(loss.detach())*len(batch)
        if (number+1)%accumulation==0 or number+1==len(batches):
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad],1.0)
            optimizer.step();optimizer.zero_grad(set_to_none=True)
    return total/max(1,len(rows))


def train_candidate(data, output, epochs=3, learning_rate=1e-5, batch_size=4, accumulation=4):
    summary=validate_dataset(data)
    if not 1<=epochs<=10 or not 0<learning_rate<=.001 or not 1<=batch_size<=32 or not 1<=accumulation<=32:
        raise ValueError("Invalid bounded training settings")
    output=Path(output).resolve()
    if output.exists():raise ValueError("Choose a fresh candidate output directory; existing models are never overwritten")
    root=Path(__file__).resolve().parent
    if not output.is_relative_to(root/"data"/"model-candidates"):
        raise ValueError("Candidate output must stay under data/model-candidates (excluded from releases)")
    manifest=json.loads((root/'models'/'MODEL_MANIFEST.json').read_text(encoding='utf-8'))
    pinned=next(m for m in manifest['models'] if m['repo']==RERANKER_ID and m['revision']==RERANKER_REVISION)
    with (RERANKER_PATH/'model.safetensors').open('rb') as stream:
        base_sha256=hashlib.file_digest(stream,'sha256').hexdigest()
    if base_sha256!=pinned['sha256']['model.safetensors']:
        raise ValueError('Base weights differ from the pinned model; training stopped')
    os.environ.update(HF_HUB_OFFLINE="1",TRANSFORMERS_OFFLINE="1",HF_HUB_DISABLE_TELEMETRY="1")
    import torch
    from transformers import AutoModelForSequenceClassification,AutoTokenizer
    torch.set_num_threads(min(4,os.cpu_count() or 1));torch.manual_seed(37)
    tokenizer=AutoTokenizer.from_pretrained(str(RERANKER_PATH),local_files_only=True,trust_remote_code=False)
    model=AutoModelForSequenceClassification.from_pretrained(str(RERANKER_PATH),local_files_only=True,trust_remote_code=False,use_safetensors=True)
    parts={split:[r for r in data["pairs"] if r["split"]==split] for split in SPLITS}
    # The training loss uses complete short pairs; reject silent truncation here.
    for row in data["pairs"]:
        size=len(tokenizer.encode(clean_text(row['query']),add_special_tokens=False))+len(tokenizer.encode(clean_text(row['document']),add_special_tokens=False))+tokenizer.num_special_tokens_to_add(pair=True)
        if size>512:raise ValueError("Review a self-contained evidence excerpt for pairs longer than 512 tokens; never silently truncate training labels")
    params=set_trainable_head(model)
    optimizer=torch.optim.AdamW(params,lr=learning_rate,weight_decay=.01)
    baseline={split:ranking_metrics(parts[split],predict(model,tokenizer,parts[split],batch_size)) for split in ("validation","test")}
    best_metric=baseline["validation"]["ndcg_at_k"];best={k:v.detach().clone() for k,v in model.classifier.state_dict().items()};history=[];best_epoch=0
    for epoch in range(epochs):
        loss=training_epoch(model,tokenizer,parts['train'],optimizer,batch_size,accumulation,37+epoch)
        validation=ranking_metrics(parts['validation'],predict(model,tokenizer,parts['validation'],batch_size))
        history.append({"epoch":epoch+1,"loss":loss,"validation":validation})
        if validation['ndcg_at_k']>best_metric:
            best_metric=validation['ndcg_at_k'];best={k:v.detach().clone() for k,v in model.classifier.state_dict().items()};best_epoch=epoch+1
    model.classifier.load_state_dict(best);model.eval()
    final={split:ranking_metrics(parts[split],predict(model,tokenizer,parts[split],batch_size)) for split in ('validation','test')}
    eligible=best_epoch>0 and all(final[s]['ndcg_at_k']>=baseline[s]['ndcg_at_k'] and final[s]['mrr']>=baseline[s]['mrr'] and final[s]['recall_at_k']>=baseline[s]['recall_at_k'] and final[s]['negative_acceptance_at_0_5']<=baseline[s]['negative_acceptance_at_0_5'] for s in ('validation','test'))
    output.mkdir(parents=True)
    if best_epoch>0:
        model.save_pretrained(output/'model',safe_serialization=True);tokenizer.save_pretrained(output/'model')
    report={"base_model":RERANKER_ID,"base_revision":RERANKER_REVISION,"base_sha256":base_sha256,"dataset":summary,
        "dataset_sha256":hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),
        "trained_parameters":sum(p.numel() for p in params),"method":"frozen_backbone_classification_head_bce",
        "seed":37,"settings":{"learning_rate":learning_rate,"batch_size":batch_size,"accumulation":accumulation,"positive_weight":sum(1-r["label"] for r in parts["train"])/sum(r["label"] for r in parts["train"])},"epochs":history,"selected_epoch":best_epoch,"baseline":baseline,"candidate":final,
        "eligible_for_review":eligible,"deployed":False,
        "deployment_gate":"A reranker score-scale change requires end-to-end assignment evaluation and validation-only threshold calibration. No automatic activation.",
        "scope_id":data['scope_id'],"artifact":"model" if best_epoch>0 else None}
    (output/'training_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    prepare=commands.add_parser('prepare-review');prepare.add_argument('--input',required=True);prepare.add_argument('--scope',required=True);prepare.add_argument('--output',required=True)
    audit=commands.add_parser('audit');audit.add_argument('--input',required=True)
    train=commands.add_parser('train');train.add_argument('--input',required=True);train.add_argument('--output',required=True);train.add_argument('--epochs',type=int,default=3);train.add_argument('--learning-rate',type=float,default=1e-5)
    args=parser.parse_args();data=json.loads(Path(args.input).read_text(encoding='utf-8-sig'))
    if args.command=='prepare-review':
        output=Path(args.output).resolve();root=Path(__file__).resolve().parent
        if not output.is_relative_to(root/'data'/'model-training') or output.exists():raise ValueError('Use a new file under data/model-training; existing reviews are not overwritten')
        prepared=prepare_review(data,args.scope);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(prepared,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'unreviewed_pairs':len(prepared['pairs']),'output':str(output)}))
    elif args.command=='audit':print(json.dumps(validate_dataset(data),ensure_ascii=False,indent=2))
    else:print(json.dumps(train_candidate(data,args.output,args.epochs,args.learning_rate),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
