"""Automatic alert recommendations with isolated history and mocked sources."""
import copy
import threading
import time
import unittest
from unittest.mock import Mock, patch

import test_diwany as fixtures
import test_recommendations as flows
from diwany import validate_config
from history import now, connection_scope
from notification_suggestions import rank as engine_rank


class NotificationSuggestionTests(unittest.TestCase):
    def setUp(self):
        fixtures.AppTests.setUp(self)
        from employee_directory import EmployeeDirectory
        fixtures.main.app.extensions['employee_directory'] = EmployeeDirectory(
            fixtures.main.STORE, fixtures.main.app.extensions['diwan_history'],
            {source: fixtures.main.app.extensions[key] for source, key in
             (('bitrix', 'recommendations'), ('diwan', 'diwan_recommendations'))})

    pid = fixtures.AppTests.pid
    post = fixtures.AppTests.post
    prepare = flows.RecommendationFlowTests.prepare

    def wait_worker(self, service=None):
        worker = (service or self.service).suggestions
        end = time.monotonic() + 30
        while worker.thread and time.monotonic() < end:
            worker.thread.join(max(.01, end - time.monotonic()))
        self.assertIsNone(worker.thread, 'Automatic suggestion did not finish')

    def enable(self):
        self.service.automatic_suggestions = True
        # Cleanup runs before temporary workspace removal, even after a test fails.
        self.addCleanup(self.wait_worker)
        self.service.refresh(self.profile, force=True)
        self.wait_worker()

    def state(self):
        return self.service._state(self.service.context(self.profile))

    def suggestion(self):
        return self.service.snapshot(self.profile)['notifications'][0]['suggestion']

    def history(self, records, source='bitrix', service=None):
        service = service or self.service
        service.history.bind_scope(self.profile, source,
                                   connection_scope(fixtures.main.STORE, self.profile, service.source_name))
        job = service.history.start(self.profile, source, lambda _: iter([(1, records)]))
        end = time.monotonic() + 30
        while service.history.job(self.profile, job)['status'] == 'running' and time.monotonic() < end:
            time.sleep(.01)
        self.assertEqual(service.history.job(self.profile, job)['status'], 'complete')

    def blocked_rank(self):
        entered, release = threading.Event(), threading.Event()
        def blocked(*args, **kwargs):
            entered.set()
            if not release.wait(15):
                raise TimeoutError('Test release missing')
            return engine_rank(*args, **kwargs)
        self.addCleanup(release.set)
        return blocked, entered, release

    def test_new_task_alert_automatically_names_same_employee_as_engine_with_reason(self):
        self.prepare(); self.enable()
        suggestion = self.suggestion()
        manual = self.service.recommend(self.profile, '99')['candidates'][0]
        self.assertEqual(suggestion['status'], 'ready')
        self.assertEqual(suggestion['employee'], {'id': manual['id'], 'name': manual['name']})
        self.assertEqual(suggestion['reason']['similar_completed'], manual['similar_completed'])
        self.assertEqual(suggestion['reason']['active_tasks'], manual['active_tasks'])
        self.assertEqual(suggestion['reason']['evidence'][0]['id'], manual['examples'][0]['id'])
        self.assertNotIn('revision', suggestion)
        self.api.reassign_task.assert_not_called()
        self.api.send_message.assert_not_called()

    def test_diwan_alert_can_use_explicitly_linked_bitrix_completion(self):
        from test_unified_directory import DirectoryFlowTests
        DirectoryFlowTests.prepare(self)
        DirectoryFlowTests.link(self)
        service = self.services['diwan']
        self.addCleanup(self.wait_worker, service)
        service.automatic_suggestions = True
        with service.lock:
            service.process(service.context(self.profile), service._state(service.context(self.profile)))
        self.wait_worker(service)
        suggestion = service.snapshot(self.profile)['notifications'][0]['suggestion']
        self.assertEqual(suggestion['status'], 'ready')
        self.assertEqual(suggestion['employee']['id'], 'staff@internal.example')
        self.assertEqual(suggestion['reason']['evidence'][0]['source'], 'bitrix')

    def test_summary_returns_permission_scoped_named_alert_and_source(self):
        self.prepare(); self.enable()
        data = self.a.get('/api/recommendations?summary=1').json
        self.assertEqual(data['unread'], 1)
        self.assertEqual(data['alert']['source'], 'bitrix')
        self.assertEqual(data['alert']['suggestion']['status'], 'ready')
        self.assertTrue(data['alert']['suggestion']['reason']['evidence'])
        self.assertIsNone(self.b.get('/api/recommendations?summary=1').json['alert'])
        self.assertEqual(self.b.get('/api/recommendations').json['notifications'], [])

    def test_unchanged_poll_retains_read_state_and_does_not_rank_again(self):
        self.prepare(); self.enable()
        self.service.mark_read(self.profile, '99')
        before = self.service.journal.read(self.service.context(self.profile)['key'])['tasks']['99']['alert_id']
        with patch('notification_suggestions.rank', wraps=engine_rank) as ranked:
            self.service.refresh(self.profile, force=True)
            self.wait_worker()
            self.service.snapshot(self.profile)
            ranked.assert_not_called()
        self.assertEqual(self.service.snapshot(self.profile)['unread'], 0)
        self.assertIsNone(self.a.get('/api/recommendations?summary=1').json['alert'])
        self.assertEqual(self.service.journal.read(self.service.context(self.profile)['key'])['tasks']['99']['alert_id'], before)

    def test_task_text_change_recomputes_and_abstains_from_unrelated_completed_work(self):
        self.prepare(); self.enable()
        self.raw.update(title='astronomy telescope orbit', description='')
        self.service.refresh(self.profile, force=True); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'no_evidence')
        self.assertNotIn('employee', self.suggestion())

    def test_changed_history_reopens_alert_only_when_top_employee_changes(self):
        self.prepare(); self.enable(); self.service.mark_read(self.profile, '99')
        self.history([flows.record(i, '11', True) for i in range(3)])
        # History completion alone is picked up by the next snapshot, without explicit ranking.
        self.service.snapshot(self.profile); self.wait_worker()
        self.assertEqual(self.suggestion()['employee']['id'], '11')
        self.assertEqual(self.service.snapshot(self.profile)['unread'], 1)
        self.service.mark_read(self.profile, '99')
        self.history([flows.record(i, '11', True) for i in range(4)])
        self.service.snapshot(self.profile); self.wait_worker()
        self.assertEqual(self.service.snapshot(self.profile)['unread'], 0)

    def test_new_open_work_updates_pressure_without_imposing_a_task_limit(self):
        self.prepare(); self.enable()
        state = self.state()
        state['active'].extend({**flows.record(100+i, '1'), 'creator_id': '11'} for i in range(12))
        with self.service.lock:
            self.service.process(self.service.context(self.profile), state)
        self.wait_worker()
        self.assertEqual(self.suggestion()['employee']['id'], '1')
        self.assertEqual(self.suggestion()['reason']['active_tasks'], 12)

    def test_eligibility_and_absence_changes_remove_suggested_employee(self):
        self.prepare(); self.enable()
        policy = fixtures.main.STORE.get('recommendation_policy', profile_id=self.profile)
        policy['employees'][0].update(away_from='2020-01-01', away_to='2099-01-01')
        fixtures.main.STORE.set('recommendation_policy', policy, profile_id=self.profile)
        self.service.snapshot(self.profile); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'no_evidence')
        policy['employees'][0].update(away_from='', away_to='', enabled=False)
        fixtures.main.STORE.set('recommendation_policy', policy, profile_id=self.profile)
        self.service.snapshot(self.profile); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'no_evidence')

    def test_pending_only_and_invalid_completion_dates_cannot_supply_a_named_alert(self):
        self.prepare()
        self.history([flows.record(1, '11'), {**flows.record(2, '11', True), 'completed_at': None}])
        self.enable()
        self.assertEqual(self.suggestion()['status'], 'no_evidence')
        self.assertNotIn('employee', self.suggestion())

    def test_source_and_directory_failures_hide_cached_name_and_recover(self):
        self.prepare(); self.enable()
        self.api.project_members.side_effect = TimeoutError('source details must not be exposed')
        self.service.refresh(self.profile, force=True)
        self.assertEqual(self.suggestion()['status'], 'unavailable')
        self.assertNotIn('employee', self.suggestion())
        self.api.project_members.side_effect = None
        self.service.refresh(self.profile, force=True); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'ready')
        self.state()['checked_epoch'] = self.service.clock() - 121
        self.assertEqual(self.suggestion()['status'], 'unavailable')
        self.service.refresh(self.profile, force=True); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'ready')

    def test_incomplete_history_is_unavailable_and_retried_after_recovery(self):
        self.prepare(); self.enable()
        history = self.service.history
        with history.lock:
            history._state(self.profile)['sources']['bitrix']['complete'] = False
        self.assertEqual(self.suggestion()['status'], 'unavailable')
        with history.lock:
            history._state(self.profile)['sources']['bitrix']['complete'] = True
        self.service.snapshot(self.profile); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'ready')

    def test_linked_source_readiness_is_reloaded_instead_of_sticking_unavailable(self):
        self.prepare(); self.enable()
        inputs = self.service.ranking_inputs
        stale = [True]
        def linked(context, state):
            result = inputs(context, state)
            state['evidence_sources'] = [{'source': 'diwan', 'complete': True, 'open_fresh': not stale[0]}]
            return result
        with patch.object(self.service, 'ranking_inputs', side_effect=linked):
            self.assertEqual(self.suggestion()['status'], 'unavailable')
            stale[0] = False
            self.service.snapshot(self.profile); self.wait_worker()
            self.assertEqual(self.suggestion()['status'], 'ready')

    def test_blocked_inference_does_not_block_snapshot_and_old_task_result_is_discarded(self):
        self.prepare()
        blocked, entered, release = self.blocked_rank()
        with patch('notification_suggestions.rank', side_effect=blocked):
            self.service.automatic_suggestions = True
            self.addCleanup(self.wait_worker)
            self.service.refresh(self.profile, force=True)
            self.assertTrue(entered.wait(10))
            start = time.monotonic()
            self.assertEqual(self.suggestion()['status'], 'pending')
            self.assertLess(time.monotonic()-start, 2)
            self.raw.update(title='astronomy telescope orbit', description='')
            self.service.refresh(self.profile, force=True)
            release.set(); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'no_evidence')
        row = self.service.journal.read(self.service.context(self.profile)['key'])['tasks']['99']
        self.assertNotIn('suggested_employee_id', row)

    def test_self_claim_while_ranking_removes_notification_and_result(self):
        self.prepare()
        blocked, entered, release = self.blocked_rank()
        with patch('notification_suggestions.rank', side_effect=blocked):
            self.service.automatic_suggestions = True
            self.addCleanup(self.wait_worker)
            self.service.refresh(self.profile, force=True)
            self.assertTrue(entered.wait(10))
            task = copy.deepcopy(self.state()['active'][0])
            self.service.decision(self.profile, task, 'self', '1')
            release.set(); self.wait_worker()
        self.assertEqual(self.service.snapshot(self.profile)['notifications'], [])
        self.assertEqual(self.state()['suggestions'], {})

    def test_assignee_only_receives_neither_alert_nor_background_job(self):
        self.prepare()
        self.raw.update(createdBy='11', responsibleId='1', auditors=[])
        with patch('notification_suggestions.rank', wraps=engine_rank) as ranked:
            self.enable()
            ranked.assert_not_called()
        self.assertEqual(self.service.snapshot(self.profile)['notifications'], [])

    def test_uncertain_assignment_hides_suggestion_and_does_not_retry_assignment(self):
        self.prepare(); self.enable()
        self.service.operation(self.profile, '99', '11', 'uncertain')
        self.assertEqual(self.suggestion()['status'], 'unavailable')
        self.assertNotIn('employee', self.suggestion())
        self.api.reassign_task.assert_not_called()

    def test_changed_connection_discards_inflight_result(self):
        self.prepare()
        blocked, entered, release = self.blocked_rank()
        old_state = self.state()
        with patch('notification_suggestions.rank', side_effect=blocked):
            self.service.automatic_suggestions = True
            self.addCleanup(self.wait_worker)
            self.service.refresh(self.profile, force=True)
            self.assertTrue(entered.wait(10))
            fixtures.main.STORE.set('webhook_url', 'https://other.internal/rest/1/test/', profile_id=self.profile)
            release.set(); self.wait_worker()
        self.assertNotEqual(old_state['suggestions']['99']['status'], 'ready')
        self.assertEqual(self.service.snapshot(self.profile)['notifications'], [])

    def test_rank_failure_is_explained_and_retries_after_backoff(self):
        self.prepare()
        self.service.clock = lambda: 1000
        with patch('notification_suggestions.rank', side_effect=RuntimeError('private details')) as ranked:
            self.enable()
            self.assertEqual(self.suggestion()['status'], 'failed')
            self.service.snapshot(self.profile); self.wait_worker()
            ranked.assert_called_once()
        self.service.clock = lambda: 1301
        self.service.refresh(self.profile, force=True); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'ready')

    def test_journal_failure_does_not_kill_worker_or_leave_permanent_pending(self):
        self.prepare()
        blocked, entered, release = self.blocked_rank()
        with patch('notification_suggestions.rank', side_effect=blocked):
            self.service.automatic_suggestions = True
            self.addCleanup(self.wait_worker)
            self.service.refresh(self.profile, force=True)
            self.assertTrue(entered.wait(10))
            with patch.object(self.service.journal, 'write', side_effect=OSError('Disk unavailable')):
                release.set(); self.wait_worker()
        self.assertEqual(self.suggestion()['status'], 'failed')

    def test_journal_persists_only_candidate_id_and_read_metadata(self):
        self.prepare(); self.enable()
        row = self.service.journal.read(self.service.context(self.profile)['key'])['tasks']['99']
        self.assertEqual(row['suggested_employee_id'], '1')
        for field in ('title', 'description', 'suggestion', 'recommendation', 'reason', 'employee_name'):
            self.assertNotIn(field, row)

    def test_diwan_automatically_recommends_native_employee_without_delegation(self):
        self.prepare()
        store = fixtures.main.STORE
        config = validate_config({**fixtures.CONFIG, 'detail_url': '', 'supervisor_field': 'supervisor',
                                  'current_user_id': 'owner', 'roles_confirmed': True})
        store.set('diwan_config', config, profile_id=self.profile)
        store.set('diwan_employees', [{'source': 'diwan', 'value': 'staff@internal.example', 'name_ar': 'موظف الاختبار'}], profile_id=self.profile)
        service = fixtures.main.app.extensions['diwan_recommendations']
        service.vault.save(self.profile, 'isolated-token')
        self.history([{**flows.record(1, 'staff@internal.example', True), 'source': 'diwan', 'project_id': 'diwan'}],
                     source='diwan_analysis', service=service)
        api = Mock()
        task = {**flows.record(99, 'owner'), 'source': 'diwan', 'project_id': 'diwan',
                'creator_id': 'owner', 'auditor_ids': []}
        api.iter_pages.side_effect = lambda: iter([(1, [task])])
        with patch.object(service, 'client', return_value=api):
            service.automatic_suggestions = True
            self.addCleanup(self.wait_worker, service)
            service.refresh(self.profile, force=True); self.wait_worker(service)
            data = self.a.get('/api/recommendations?source=diwan&summary=1').json
        self.assertEqual(data['alert']['source'], 'diwan')
        self.assertEqual(data['alert']['suggestion']['employee']['id'], 'staff@internal.example')
        self.assertEqual(data['alert']['suggestion']['reason']['evidence'][0]['source'], 'diwan')
        api.delegate.assert_not_called()
        self.api.reassign_task.assert_not_called()


if __name__ == '__main__':
    unittest.main()
