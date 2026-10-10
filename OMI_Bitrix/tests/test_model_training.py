"""Training admission and real autograd checks; no organisational labels fabricated."""
import copy
import json
import math
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
import torch
from model_training import validate_dataset,training_epoch,set_trainable_head,ranking_metrics,train_candidate,prepare_review


def dataset():
    pairs=[]
    for index,split in enumerate(('train','validation','test'),1):
        for label,document in ((1,'دليل مرتبط بالمخطوطات'),(0,'عمل منفصل في الزراعة')):
            pairs.append({'query_id':f'q{index}','group_id':f'family{index}','query':('مخطوطات','مزروعات','ترجمة')[index-1],
                'document_id':f'd{label}','document':document,'label':label,'label_source':'human_review',
                'reviewed_by':'reviewer-opaque','query_at':f'2025-0{index+1}-01',
                'judged_at':'2025-06-01','document_completed':True,'document_completed_at':'2025-01-01',
                'document_observed_at':'2025-01-02','split':split})
    return {'schema_version':1,'scope_id':'fixture-only','pairs':pairs}


class TrainingContracts(unittest.TestCase):
    def test_no_assignment_or_missing_label_becomes_truth(self):
        for change in ({'label':None},{'label_source':'historical_assignee'},{'label':True},{'reviewed_by':''}):
            data=dataset();data['pairs'][0].update(change)
            with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))

    def test_future_pending_and_unobserved_evidence_rejected(self):
        for change in ({'document_completed':False},{'document_completed_at':'2030-01-01'},
                       {'document_observed_at':'2030-01-01'},{'judged_at':'2024-01-01'}):
            data=dataset();data['pairs'][0].update(change)
            with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))

    def test_groups_queries_and_recurring_content_cannot_leak(self):
        for change in ({'group_id':'family1'},{'query_id':'q1'},{'query':'مخطوطات [REQ-999]'}):
            data=dataset();data['pairs'][2].update(change)
            with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))

    def test_chronological_splits_and_support_required(self):
        self.assertEqual(validate_dataset(dataset(),(1,1,1))['queries'],3)
        with self.assertRaises(ValueError):validate_dataset(dataset())
        data=dataset();data['pairs'][0]['query_at']='2025-05-01';data['pairs'][1]['query_at']='2025-05-01'
        with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))

    def test_duplicate_reviews_and_missing_negatives_rejected(self):
        data=dataset();data['pairs'].append(copy.deepcopy(data['pairs'][0]))
        with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))
        data=dataset();data['pairs'][1]['label']=1
        with self.assertRaises(ValueError):validate_dataset(data,(1,1,1))

    def test_unlabelled_history_cannot_start_model_training(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'candidate'
            with self.assertRaises(ValueError):train_candidate({'schema_version':1,'scope_id':'x','pairs':[]},path)
            self.assertFalse(path.exists())

    def test_query_ranking_metrics_use_reviewed_labels(self):
        rows=dataset()['pairs'][:2]
        good=ranking_metrics(rows,[.9,.1],1);bad=ranking_metrics(rows,[.1,.9],1)
        self.assertEqual(good['ndcg_at_k'],1);self.assertEqual(bad['ndcg_at_k'],0)
        self.assertEqual(bad['negative_acceptance_at_0_5'],1)

    def test_prepare_leaves_nearest_and_easy_candidates_unlabelled(self):
        rows=[{'source':'bitrix','id':str(i),'title':title,'description':'','completed':True,
               'created_at':'2025-01-01','completed_at':'2025-01-02','observed_at':'2025-02-01'}
              for i,title in enumerate(('مخطوطات قديمة','مخطوطات نادرة','حدائق منزلية'),1)]
        class Index:
            def __init__(self,records):pass
            def related(self,*args,**kwargs):return [{'task':rows[1]}]
        with patch('recommendation_matching.RelevanceIndex',Index):
            result=prepare_review({'snapshot_at':'2025-03-01','records':rows},'fixture',1)
        self.assertEqual(len(result['pairs']),2)
        self.assertTrue(all(r['label'] is None and r['label_source']=='unreviewed' for r in result['pairs']))
        self.assertNotIn('assignee_id',result['pairs'][0])

    def test_real_backward_updates_head_and_preserves_backbone(self):
        from transformers import XLMRobertaConfig,XLMRobertaForSequenceClassification
        previous_threads=torch.get_num_threads();self.addCleanup(torch.set_num_threads,previous_threads)
        torch.manual_seed(7);torch.set_num_threads(2)
        model=XLMRobertaForSequenceClassification(XLMRobertaConfig(vocab_size=30,hidden_size=16,
            num_hidden_layers=1,num_attention_heads=2,intermediate_size=24,num_labels=1,
            max_position_embeddings=64,hidden_dropout_prob=0,attention_probs_dropout_prob=0))
        class Tokenizer:
            def __call__(self,pairs,**kwargs):
                ids=torch.tensor([[0,4+len(a)%20,5+len(b)%20,2] for a,b in pairs])
                return {'input_ids':ids,'attention_mask':torch.ones_like(ids)}
        frozen={k:p.detach().clone() for k,p in model.roberta.state_dict().items()}
        before={k:p.detach().clone() for k,p in model.classifier.state_dict().items()}
        params=set_trainable_head(model);optimizer=torch.optim.AdamW(params,lr=.01)
        loss=training_epoch(model,Tokenizer(),dataset()['pairs'][:3],optimizer,batch_size=2,accumulation=2)
        self.assertTrue(math.isfinite(loss))
        self.assertTrue(any(not torch.equal(v,model.classifier.state_dict()[k]) for k,v in before.items()))
        self.assertTrue(all(torch.equal(v,model.roberta.state_dict()[k]) for k,v in frozen.items()))
