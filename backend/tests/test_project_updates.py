"""Real API tests: temporary SQLite only, synthetic resources, fixed server clock."""
from contextlib import closing
from datetime import datetime
import unittest
from unittest.mock import patch

import test_projects as existing
import test_project_maintenance as maintenance


class ProjectUpdateTests(unittest.TestCase):
    setUpClass = classmethod(existing.ProjectTests.setUpClass.__func__)
    tearDownClass = classmethod(existing.ProjectTests.tearDownClass.__func__)
    request = classmethod(existing.ProjectTests.request.__func__)
    setUp = maintenance.MaintenanceTests.setUp
    grant = maintenance.MaintenanceTests.grant
    create = maintenance.MaintenanceTests.create
    edit = maintenance.MaintenanceTests.edit
    logs = maintenance.MaintenanceTests.logs
    upload = existing.ProjectTests.upload
    confirm = existing.ProjectTests.confirm
    import_projects = existing.ProjectTests.import_projects

    def read(self, query=''):
        status, _, result = self.request('GET', '/api/projects', admin=False, query=query)
        self.assertEqual(status, 200, result)
        return result

    def save_at(self, project, when, **changes):
        with patch('project_write_api.utc_now', return_value=when):
            status, _, result = self.edit(project, **changes)
        self.assertEqual(status, 200, result)
        return result

    def test_creation_initial_import_ag_and_noop_are_not_updates(self):
        from project_board_fixtures import synthetic_projects
        raw = synthetic_projects()[0]
        raw['progressUpdate'] = '有'
        self.import_projects([raw])
        created = self.create(name='虚构新建不计更新', resource='虚构独立创建来源')
        self.assertEqual(created['fieldUpdates'], {})
        self.assertIsNone(created['nodesUpdatedAt'])
        self.assertEqual(self.read()['summary']['updated'], 0)
        self.assertEqual(self.read('view=daily')['filteredCount'], 0)
        count = self.logs(created)['total']
        unchanged = self.edit(created, situation=created['situation'])[2]
        self.assertTrue(unchanged['unchanged'])
        self.assertEqual(self.logs(created)['total'], count)
        self.assertEqual(self.read()['summary']['updated'], 0)
        persisted = self.request('GET', '/api/projects', admin=False)[2]['projects']
        self.assertEqual(next(p for p in persisted if p['name'] == raw['name'])['progressUpdate'], '有')
        saved = self.edit(created, situation='虚构真正的网页修改')[2]
        self.assertTrue(saved['updated'])
        self.edit(saved, nextStep='同项目再次更新')
        self.assertEqual(self.read()['summary']['updated'], 1)

    def test_independent_persistent_dates_latest_history_and_archive_nodes_isolation(self):
        project = self.create()
        project = self.save_at(project, '2025-12-31T15:00:00+00:00', situation='虚构去年 AD')
        project = self.save_at(project, '2026-01-01T01:00:00+00:00', nextStep='虚构昨日 AE')
        project = self.save_at(project, '2026-01-02T01:00:00+00:00', coordination='虚构今日 AF')
        expected = {'situation': '2025-12-31T15:00:00+00:00', 'nextStep': '2026-01-01T01:00:00+00:00', 'coordination': '2026-01-02T01:00:00+00:00'}
        self.assertEqual(project['fieldUpdates'], expected)
        project = self.save_at(project, '2026-01-02T02:00:00+00:00', situation='虚构最新 AD')
        expected['situation'] = '2026-01-02T02:00:00+00:00'
        nodes = list(project['stages'])
        nodes[8] = '进行中'
        project = self.save_at(project, '2026-01-02T03:00:00+00:00', stages=nodes)
        self.assertEqual(project['fieldUpdates'], expected)
        self.assertEqual(project['nodesUpdatedAt'], '2026-01-02T03:00:00+00:00')
        project = self.save_at(project, '2026-01-02T04:00:00+00:00', owner='虚构仅档案修改')
        self.assertEqual(project['fieldUpdates'], expected)
        self.assertEqual(project['nodesUpdatedAt'], '2026-01-02T03:00:00+00:00')
        self.assertEqual(project['latestBusinessUpdateAt'], '2026-01-02T04:00:00+00:00')
        self.assertEqual(len(self.logs(project, 'situation')['items']), 3)  # initial + two writes
        with patch('projects_api.update_now', return_value=datetime.fromisoformat('2026-01-03T02:00:00+00:00')):
            self.assertEqual(self.read()['summary']['updated'], 0)
            result = self.read('view=daily&update_days=7')['projects'][0]
            self.assertEqual(result['fieldUpdates'], expected)
            self.assertEqual(result['nodesUpdatedAt'], project['nodesUpdatedAt'])
            detail = self.request('GET', f'/api/projects/{project["id"]}', admin=False)[2]
            self.assertEqual(detail['fieldUpdates'], expected)

    def test_beijing_calendar_ranges_dedup_and_descending_actual_time(self):
        now = datetime.fromisoformat('2026-10-21T04:00:00+00:00')
        times = ['2026-10-20T16:00:00+00:00', '2026-10-20T15:59:59+00:00',
                 '2026-10-14T16:00:00+00:00', '2026-10-14T15:59:59+00:00',
                 '2026-09-21T16:00:00+00:00', '2026-09-21T15:59:59+00:00']
        ids = []
        for i, when in enumerate(times):
            project = self.create(name=f'虚构日期边界项目{i}', resource=f'虚构日期来源{i}')
            project = self.save_at(project, when, situation=f'虚构日期修改{i}')
            ids.append(project['id'])
        self.save_at(project, times[-1], nextStep='同项目同日第二次修改')
        with patch('projects_api.update_now', return_value=now):
            for days, expected in [(1, ids[:1]), (7, ids[:3]), (30, ids[:5])]:
                result = self.read(f'view=daily&update_days={days}&sort=name&owner=ignored')
                self.assertEqual([p['id'] for p in result['projects']], expected)
                self.assertEqual(result['summary']['updated'], 1)
                self.assertEqual(result['filteredCount'], len(set(expected)))
            for value in ['0', '2', '31', 'abc']:
                self.assertEqual(self.request('GET', '/api/projects', admin=False, query=f'update_days={value}')[0], 422)
        with patch('projects_api.update_now', return_value=datetime.fromisoformat('2026-10-20T15:59:59+00:00')):
            self.assertEqual([p['id'] for p in self.read('view=daily')['projects']], [ids[1]])

    def test_year_boundary_and_offsets_use_same_shanghai_day(self):
        from project_updates import in_update_range, timestamp
        now = datetime.fromisoformat('2027-01-01T00:00:00+08:00')
        self.assertTrue(in_update_range('2026-12-31T16:00:00Z', now, 1))
        self.assertFalse(in_update_range('2026-12-31T15:59:59Z', now, 1))
        self.assertTrue(in_update_range('2026-12-31T15:59:59Z', now, 7))
        self.assertIsNone(timestamp('2026-01-01'))
        self.assertIsNone(timestamp('bad time'))

    def test_only_existing_import_changes_count_not_initial_or_ag_only(self):
        from project_board_fixtures import synthetic_projects
        raw = synthetic_projects()[0]
        self.import_projects([raw])
        self.assertEqual(self.read()['summary']['updated'], 0)
        raw['progressUpdate'] = '有'
        self.import_projects([raw])
        self.assertEqual(self.read()['summary']['updated'], 0)
        raw['situation'] = '虚构管理员受控导入中的实际内容更新'
        self.import_projects([raw])
        result = self.read()
        self.assertEqual(result['summary']['updated'], 1)
        self.assertEqual(set(result['projects'][0]['fieldUpdates']), {'situation'})

    def test_failed_transaction_leaves_no_false_markers_and_bad_logs_are_ignored(self):
        project = self.create()
        with patch('project_write_api.record_changes', side_effect=RuntimeError('synthetic rollback')):
            with self.assertRaises(RuntimeError):
                self.edit(project, situation='必须回滚')
        self.assertEqual(self.read()['summary']['updated'], 0)
        from project_changes import log
        with closing(self.database.get_db_connection()) as connection, connection:
            for field, before, after, kind, when in [
                ('situation', '相同', '相同', 'update', '2026-10-21T01:00:00Z'),
                ('progressUpdate', '无', '有', 'update', '2026-10-21T01:00:00Z'),
                ('situation', None, '初始值', 'baseline', '2026-10-21T01:00:00Z'),
                ('nextStep', None, '未知时间', 'fill', 'bad time'),
            ]:
                log(connection, project['id'], field, before, after, None, 2, 'synthetic', when, kind)
        result = self.read()['projects'][0]
        self.assertIsNone(result['latestBusinessUpdateAt'])
        self.assertEqual(result['fieldUpdates'], {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
