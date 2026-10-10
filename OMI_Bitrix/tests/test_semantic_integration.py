"""Opt-in real local-model checks; anonymous fixtures, no live source writes."""
import os
import socket
import unittest
from unittest.mock import patch
from pathlib import Path
from collections import Counter
from semantic_cases import records, QUERIES
from semantic_engine import DEFAULT_PATH, get_encoder
from recommendation_matching import RelevanceIndex, query_profile
from recommendations import rank


@unittest.skipUnless(os.environ.get('RUN_SEMANTIC_INTEGRATION')=='1','Set RUN_SEMANTIC_INTEGRATION=1 for real local encoder evaluation')
class RealSemanticIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mode=patch.dict(os.environ,{'TASK_MODEL_MODE':'semantic'})
        cls.mode.start();cls.addClassCleanup(cls.mode.stop)
        # Actual load and inference must succeed with all outbound TCP blocked.
        cls.network=patch.object(socket.socket,'connect',side_effect=AssertionError('Unexpected network access'))
        cls.network.start();cls.addClassCleanup(cls.network.stop)
        cls.rows=records();cls.index=RelevanceIndex(cls.rows)
        assert cls.index.model_summary()['pretrained'],cls.index.model_summary()

    def test_unknown_business_fields_are_discovered(self):
        topics=self.index.domain_model.topics
        self.assertGreaterEqual(len(topics),4)
        lookup={r['id']:r['group_truth'] for r in self.rows}
        for topic in topics:
            categories=[lookup[r['id']] for r in topic['examples']]
            self.assertEqual(len(set(categories)),1)
            self.assertTrue(topic['id'].startswith('topic_'))
            self.assertEqual(topic['basis'],'discovered_topic')

    def test_arabic_and_english_top_evidence(self):
        for query,expected in QUERIES:
            with self.subTest(query=query):
                matches=self.index.related(query)
                self.assertTrue(matches)
                self.assertEqual(matches[0]['task']['group_truth'],expected)
                self.assertTrue(all(m['semantic_cosine'] is not None for m in matches))
                self.assertEqual({m['task']['group_truth'] for m in matches[:3]},{expected})

    def test_employee_ranking_completed_evidence(self):
        people=[{'id':str(i),'name':'Employee '+str(i),'enabled':True,'active':True,
                 'projects':['1'],'categories':[]} for i in range(1,5)]
        expected_ids={'library':'1','gardening':'2','translation':'3','payroll':'4'}
        for query,expected in QUERIES:
            with self.subTest(query=query):
                task={'source':'bitrix','id':'new','title':query,'description':'','project_id':'1','category':''}
                result=rank(task,self.rows,people,prepared=self.index)
                self.assertTrue(result['candidates'])
                self.assertEqual(result['candidates'][0]['id'],expected_ids[expected])

    def test_unseen_subject_is_not_forced_into_topic(self):
        text='رصد الموجات الزلزالية في طبقات القشرة الأرضية'
        self.assertEqual(self.index.related(text),[])
        self.assertEqual(query_profile(text,self.index)['domains'],[])

    def test_ticket_and_tool_only_queries_have_no_evidence(self):
        for text in ('Excel report','مهمة [REQ-777]'):
            self.assertEqual(self.index.related(text),[])

    def test_open_exposure_cannot_be_completed_experience(self):
        rows=[dict(r,completed=False,completed_at=None) for r in self.rows]
        people=[{'id':'4','name':'Employee 4','enabled':True,'projects':['1'],'categories':[]}]
        result=rank({'source':'bitrix','id':'new','title':QUERIES[6][0],'description':'','project_id':'1'},rows,people)
        self.assertEqual(result['candidates'],[])
        self.assertTrue(result['open_affinity'])

    def test_new_arabic_topic_is_discovered_after_snapshot_refresh(self):
        previous=RelevanceIndex([r for r in self.rows if r['group_truth']!='gardening'])
        refreshed=RelevanceIndex(self.rows,previous_domains=previous.domain_model)
        lookup={r['id']:r['group_truth'] for r in self.rows}
        self.assertFalse(any(lookup[e['id']]=='gardening' for t in previous.domain_model.topics for e in t['examples']))
        self.assertTrue(any(all(lookup[e['id']]=='gardening' for e in t['examples']) for t in refreshed.domain_model.topics))

    def test_long_evidence_tail_is_verified_instead_of_truncated(self):
        from semantic_engine import get_reranker
        query='مراجعة رواتب الموظفين والبدلات والاستقطاعات'
        filler='هذا النص يشرح الإجراءات العامة للنظام وكيفية فتح الطلب. '*160
        relevant=filler+' تدقيق أجور العاملين ومطابقة البدلات والخصومات وصافي الرواتب.'
        unrelated=filler+' صيانة شبكة الحاسب وتغيير كابلات الاتصال.'
        reranker=get_reranker()
        windows=reranker.windows(query,relevant)
        self.assertLessEqual(len(windows),3)
        self.assertTrue(any('الرواتب' in document for _,document in windows))
        positive,negative=reranker.score([(query,relevant),(query,unrelated)])
        self.assertGreater(positive,negative)
        self.assertGreater(positive,.05)

    def test_cache_does_not_conflate_different_code_symbols(self):
        from semantic_engine import get_encoder,model_text_key
        self.assertNotEqual(model_text_key('C++'),model_text_key('C#'))
        encoder=get_encoder();values=['تطوير واجهة باستخدام C++','تطوير واجهة باستخدام C#']
        vectors=encoder.encode(values)
        self.assertFalse((vectors[0]==vectors[1]).all())
        before=encoder.stats['encoded_texts'];encoder.encode(values)
        self.assertEqual(encoder.stats['encoded_texts'],before)

    def test_real_encoder_handles_long_arabic_description(self):
        encoder=get_encoder()
        vector=encoder.encode(['مقدمة عامة. '*250+' مطابقة أجور العاملين والبدلات والاستقطاعات.'])
        self.assertEqual(vector.shape,(1,768))


if __name__=='__main__':unittest.main()
