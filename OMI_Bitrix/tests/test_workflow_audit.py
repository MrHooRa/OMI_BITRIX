"""Regression checks for the assignment/workspace audit, using isolated sources."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
import test_diwany as fixtures
import test_recommendations as flows
from workspace import task_folder
from similarity import attach_similarities, task_similarity


class WorkflowAuditTests(unittest.TestCase):
    setUp = fixtures.AppTests.setUp
    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post
    prepare = flows.RecommendationFlowTests.prepare

    def test_failed_directory_refresh_preserves_members_blocks_assignment_and_retries(self):
        self.prepare()
        state = self.service._state(self.service.context(self.profile))
        members, checked = list(state['members']), state['directory_checked']
        self.api.project_members.side_effect = TimeoutError('directory unavailable')
        self.service.refresh(self.profile, force=True)
        self.assertEqual(state['members'], members)
        self.assertEqual(state['directory_checked'], checked)
        self.assertEqual(self.service.snapshot(self.profile)['error'], 'directory_unavailable')
        result = self.service.recommend(self.profile, '99')
        self.assertTrue(result['stale'])
        self.assertIn('directory_unavailable', result['status_reasons'])
        response = self.post(self.a, '/api/recommendations/tasks/99/assign',
                             {'confirmed': True, 'employee_id': '11', 'expected_assignee': '1'})
        self.assertEqual(response.status_code, 400)
        self.api.reassign_task.assert_not_called()
        self.api.project_members.side_effect = None
        state['next'] = 0
        self.service.refresh(self.profile)
        self.assertIsNone(self.service.snapshot(self.profile)['error'])

    def test_legacy_route_cannot_bypass_uncertain_operation(self):
        self.prepare()
        fixtures.main.STORE.set_many({'vault_root': self.directory.name, 'employee_name': 'Test supervisor'}, profile_id=self.profile)
        self.service.operation(self.profile, '99', '11', 'uncertain')
        with self.a.session_transaction() as session:
            token = session['csrf_token']
        response = self.a.post('/supervisor/task/99/reassign',
            data={'responsible_id': '11', 'expected_assignee': '1'}, headers={'X-CSRF-Token': token})
        self.assertEqual(response.status_code, 302)
        self.api.reassign_task.assert_not_called()
        self.assertEqual(self.service.operation(self.profile, '99')['status'], 'uncertain')

    def test_assignment_moves_workspace_and_preserves_files(self):
        self.prepare()
        root = Path(self.directory.name) / 'workspace'
        fixtures.main.STORE.set_many({'vault_root': str(root), 'employee_name': 'Original worker'}, profile_id=self.profile)
        source = task_folder(root, 'Test', self.raw, 'Original worker')
        source.mkdir(); (source / 'evidence.txt').write_text('preserved evidence', encoding='utf-8')
        response = self.post(self.a, '/api/recommendations/tasks/99/assign',
            {'confirmed': True, 'employee_id': '11', 'expected_assignee': '1'})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(response.json['warnings'], [])
        operation = self.service.operation(self.profile, '99')
        target = task_folder(root, 'Test', self.raw, operation['workspace']['new_employee'])
        self.assertFalse(source.exists())
        self.assertEqual((target / 'evidence.txt').read_text(), 'preserved evidence')
        self.api.send_message.assert_called_once()

    def test_source_change_during_inference_blocks_the_write(self):
        self.prepare()
        original = self.service.recommend
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            self.raw['responsibleId'] = 'another-worker'
            return result
        with patch.object(self.service, 'recommend', side_effect=changed):
            response = self.post(self.a, '/api/recommendations/tasks/99/assign',
                {'confirmed': True, 'employee_id': '11', 'expected_assignee': '1'})
        self.assertEqual(response.status_code, 409)
        self.api.reassign_task.assert_not_called()

    def test_existing_destination_is_never_overwritten(self):
        self.prepare()
        root = Path(self.directory.name) / 'workspace'
        fixtures.main.STORE.set_many({'vault_root': str(root), 'employee_name': 'Original worker'}, profile_id=self.profile)
        source = task_folder(root, 'Test', self.raw, 'Original worker')
        source.mkdir(); (source / 'evidence.txt').write_text('original')
        with fixtures.main.app.test_request_context():
            from flask import g
            g.profile_id = self.profile
            metadata = fixtures.main.assignment_workspace_context(__import__('history').bitrix_record(self.raw), '11')
        destination = task_folder(root, 'Test', self.raw, metadata['new_employee'])
        destination.mkdir(); (destination / 'evidence.txt').write_text('existing destination')
        response = self.post(self.a, '/api/recommendations/tasks/99/assign',
            {'confirmed': True, 'employee_id': '11', 'expected_assignee': '1'})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertTrue(response.json['warnings'])
        self.assertEqual((source / 'evidence.txt').read_text(), 'original')
        self.assertEqual((destination / 'evidence.txt').read_text(), 'existing destination')

    def test_inference_does_not_hold_snapshot_lock_and_changed_inputs_are_stale(self):
        import threading
        from recommendations import rank
        self.prepare()
        state = self.service._state(self.service.context(self.profile))
        acquired = threading.Event()
        def infer(*args, **kwargs):
            def concurrent_update():
                with self.service.lock:
                    state['generation'] = state.get('generation', 0) + 1
                    acquired.set()
            worker = threading.Thread(target=concurrent_update)
            worker.start()
            self.assertTrue(acquired.wait(2), 'Inference held the shared snapshot lock')
            worker.join()
            return rank(*args, **kwargs)
        with patch('recommendation_service.rank', side_effect=infer):
            result = self.service.recommend(self.profile, '99')
        self.assertTrue(result['stale'])
        self.assertIn('snapshot_changed', result['status_reasons'])

    def test_unresolved_assignment_cannot_be_replaced_by_self_decision(self):
        self.prepare()
        self.service.operation(self.profile, '99', '11', 'uncertain')
        for action in ('self', 'needs-assignment'):
            self.assertEqual(self.post(self.a, '/api/recommendations/tasks/99/'+action, {}).status_code, 400)
        self.assertEqual(self.service.operation(self.profile, '99')['status'], 'uncertain')

    def test_comment_failure_does_not_repeat_remote_assignment_or_comment(self):
        self.prepare()
        self.api.send_message.side_effect = TimeoutError()
        response = self.post(self.a, '/api/recommendations/tasks/99/assign',
            {'confirmed': True, 'employee_id': '11', 'expected_assignee': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['warnings'])
        self.assertEqual(self.service.operation(self.profile, '99')['status'], 'confirmed')
        verified = self.post(self.a, '/api/recommendations/tasks/99/verify', {})
        self.assertEqual(verified.status_code, 200)
        self.api.reassign_task.assert_called_once()
        self.api.send_message.assert_called_once()

    def test_explicit_ranking_is_not_called_by_refresh_or_stored_as_source_narrative(self):
        self.prepare()
        with patch('recommendation_service.rank', side_effect=AssertionError('Background ranking')):
            self.service.refresh(self.profile, force=True)
        self.assertIsNone(self.service.snapshot(self.profile)['error'])
        journal = self.service.journal.read(self.service.context(self.profile)['key'])
        row = journal['tasks']['99']
        self.assertNotIn('description', row)
        self.assertNotIn('title', row)
        self.assertNotIn('recommendation', row)
        self.assertEqual(self.service.snapshot(self.profile)['tasks'][0]['title'], self.raw['title'])

    def test_existing_journal_fields_are_not_deleted(self):
        self.prepare()
        context = self.service.context(self.profile)
        journal = self.service.journal.read(context['key'])
        journal['tasks']['99']['description'] = 'legacy retained'
        self.service.journal.write(context['key'], journal)
        self.service.refresh(self.profile, force=True)
        self.assertEqual(self.service.journal.read(context['key'])['tasks']['99']['description'], 'legacy retained')

    def test_operation_state_is_visible_for_reconciliation(self):
        self.prepare()
        self.service.operation(self.profile, '99', '11', 'uncertain')
        self.assertEqual(self.service.snapshot(self.profile)['tasks'][0]['operation']['status'], 'uncertain')

    def test_history_does_not_compute_example_pairs_until_requested(self):
        self.prepare()
        index = self.service.history.index(self.profile, 'bitrix')
        self.assertIsNone(index.preview)
        with patch.object(index, 'examples', return_value=[]) as examples, patch.object(fixtures.main.app.extensions['history_scheduler'], 'tick'):
            self.a.get('/api/intelligence?source=diwan&pairs=1')
            examples.assert_not_called()
            self.a.get('/api/intelligence?source=bitrix&pairs=1')
            examples.assert_called_once()

    def test_ticket_and_boilerplate_do_not_make_unrelated_work_similar(self):
        a = {'id': '1', 'title': 'مراجعة رواتب الموظفين [OMI-SIM-20261003]',
             'description': 'Synthetic similarity test only. No real work required.', 'groupId': '1'}
        b = {**a, 'id': '2', 'title': 'تشخيص انقطاع الشبكة [OMI-SIM-20261003]'}
        self.assertEqual(task_similarity(a, b), 0)
        self.assertEqual(attach_similarities([a, b]), [])
        self.assertEqual(a['similarTasks'], [])


if __name__ == '__main__':
    unittest.main()
