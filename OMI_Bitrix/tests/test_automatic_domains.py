"""Automatic topic contracts; embeddings mocked here, real model tested separately."""
import os
import unittest
from unittest.mock import patch
import numpy as np
from recommendation_matching import RelevanceIndex, query_profile
from recommendations import rank
from semantic_engine import AutomaticDomains, SemanticSpace, clean_text
from semantic_cases import records


class FixtureEncoder:
    def encode(self, texts):
        vectors=[]
        for text in texts:
            group=0 if 'alpha' in text else 1 if 'beta' in text else 2
            vector=np.zeros(4,dtype=np.float32);vector[group]=1
            vector[3]=len(text)%7*.002
            vectors.append(vector/np.linalg.norm(vector))
        return np.asarray(vectors)


def corpus():
    return [{"source":"bitrix","id":str(group*10+i),"title":word+' '+suffix,
             "description":"","completed":True,"created_at":"2025-01-01","completed_at":"2025-01-03",
             "assignee_id":str(group+1),"project_id":"1","category":""}
            for group,word in enumerate(('alpha','beta')) for i,suffix in enumerate(('collection','research','inventory','operations'))]


class AutomaticDomainContracts(unittest.TestCase):
    def setUp(self):
        self.mode=patch.dict(os.environ,{'TASK_MODEL_MODE':'semantic'});self.mode.start();self.addCleanup(self.mode.stop)
        self.verifier=patch('semantic_engine.get_reranker',return_value=None);self.verifier.start();self.addCleanup(self.verifier.stop)
        self.match_verifier=patch('recommendation_matching.get_reranker',return_value=None);self.match_verifier.start();self.addCleanup(self.match_verifier.stop)

    def test_unavailable_model_does_not_substitute_manual_domains(self):
        with patch('semantic_engine.get_encoder',return_value=None):
            index=RelevanceIndex(corpus())
            profile=query_profile('مراجعة الرواتب',index)
            self.assertEqual(profile['domains'],[])
            self.assertFalse(profile['needs_clarification'])
            self.assertFalse(index.model_summary()['pretrained'])
            self.assertEqual(index.model_summary()['id'],'lexical-no-taxonomy')

    def test_discovery_has_no_domain_seeds(self):
        index=RelevanceIndex(corpus(),encoder=FixtureEncoder())
        topics=index.domain_model.topics
        self.assertEqual(len(topics),2)
        self.assertTrue(all(t['id'].startswith('topic_') for t in topics))
        self.assertTrue(all(t['basis']=='discovered_topic' for t in topics))
        self.assertFalse(index.model_summary()['discovery']['predefined_domains'])

    def test_duplicates_do_not_manufacture_cluster_support(self):
        rows=corpus();copies=rows+[dict(rows[0],id=str(i+100)) for i in range(50)]
        base=RelevanceIndex(rows,encoder=FixtureEncoder())
        repeated=RelevanceIndex(copies,encoder=FixtureEncoder())
        self.assertEqual(repeated.domain_model.unique_documents,8)
        self.assertEqual(sorted(t['support'] for t in repeated.domain_model.topics),[4,4])
        self.assertEqual({t['id'] for t in base.domain_model.topics},{t['id'] for t in repeated.domain_model.topics})

    def test_topic_identity_survives_same_scope_refresh(self):
        base=RelevanceIndex(corpus(),encoder=FixtureEncoder())
        updated=RelevanceIndex(list(reversed(corpus())),encoder=FixtureEncoder(),previous_domains=base.domain_model)
        self.assertEqual({t['id'] for t in base.domain_model.topics},{t['id'] for t in updated.domain_model.topics})

    def test_sparse_history_does_not_invent_topics(self):
        index=RelevanceIndex(corpus()[:2],encoder=FixtureEncoder())
        self.assertEqual(index.domain_model.topics,[])
        self.assertEqual(index.model_summary()['discovery']['status'],'insufficient_corpus')
        self.assertTrue(index.related('alpha collection'))

    def test_scopes_do_not_share_topic_training(self):
        a=RelevanceIndex(corpus(),encoder=FixtureEncoder())
        b=RelevanceIndex([dict(r,title='gamma '+r['title']) for r in corpus()[:2]],encoder=FixtureEncoder())
        self.assertTrue(a.domain_model.topics)
        self.assertEqual(b.domain_model.topics,[])
        self.assertIsNot(a.domain_model,b.domain_model)

    def test_metadata_not_used_as_text_features(self):
        rows=corpus();changed=[dict(r,assignee_name='Another person',assignee_id='555',category='unrelated') for r in rows]
        a=RelevanceIndex(rows,encoder=FixtureEncoder());b=RelevanceIndex(changed,encoder=FixtureEncoder())
        np.testing.assert_array_equal(a.semantic.vectors,b.semantic.vectors)
        self.assertEqual({t['id'] for t in a.domain_model.topics},{t['id'] for t in b.domain_model.topics})

    def test_ticket_and_explicit_exclusion_removed_before_embedding(self):
        cleaned=clean_text('مراجعة الرواتب (باستثناء الضرائب) [REQ-4444] https://internal.example/a')
        self.assertIn('الرواتب',cleaned);self.assertNotIn('الضرائب',cleaned)
        self.assertNotIn('REQ',cleaned);self.assertNotIn('internal',cleaned)

    def test_future_text_cannot_teach_discovery(self):
        rows=[dict(r,created_at='2099-01-01',completed_at='2099-01-03') for r in corpus()]
        index=RelevanceIndex(rows,encoder=FixtureEncoder())
        self.assertEqual(index.domain_model.unique_documents,0)
        self.assertEqual(index.domain_model.topics,[])

    def test_known_outlier_is_not_reassigned_to_a_topic(self):
        index=RelevanceIndex(corpus(),encoder=FixtureEncoder())
        from semantic_engine import fingerprint
        index.domain_model.outlier_keys.add(fingerprint('an isolated subject'))
        with patch.object(index.semantic.encoder,'encode',side_effect=AssertionError('Do not encode a known outlier')):
            self.assertEqual(index.domain_model.labels('an isolated subject'),[])

    def test_unknown_tool_alone_cannot_create_recommendation(self):
        index=RelevanceIndex(corpus(),encoder=FixtureEncoder())
        self.assertEqual(index.related('Excel report'),[])
        self.assertEqual(index.related('مهمة [REQ-4444]'),[])


if __name__=='__main__':unittest.main()
