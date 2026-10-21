"""Stage-three maintenance tests use only temporary SQLite and invented employee/project data."""
import asyncio
from contextlib import closing
from http.cookies import SimpleCookie
import json
import unittest
from unittest.mock import patch

import test_projects as existing
from auth_support import employee_session
from project_board_fixtures import synthetic_projects


class MaintenanceTests(unittest.TestCase):
    setUpClass = classmethod(existing.ProjectTests.setUpClass.__func__)
    tearDownClass = classmethod(existing.ProjectTests.tearDownClass.__func__)
    request = classmethod(existing.ProjectTests.request.__func__)
    upload = existing.ProjectTests.upload
    confirm = existing.ProjectTests.confirm
    import_projects = existing.ProjectTests.import_projects

    def setUp(self):
        existing.ProjectTests.setUp(self)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("DELETE FROM auth_login_attempts")
        self.__class__.employee_cookie, self.__class__.csrf = employee_session(self.app, existing.call_app)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE employees SET can_edit_projects=0,is_active=1,must_change_password=0 WHERE username='fixture-employee'")

    def grant(self, enabled=True):
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE employees SET can_edit_projects=? WHERE username='fixture-employee'", (int(enabled),))

    def create(self, **changes):
        self.grant()
        values = {field: value for field, value in synthetic_projects()[1].items() if field not in {'serial','progressUpdate'}}
        values.update(changes)
        status, _, project = self.request('POST', '/api/projects', values, admin=False)
        self.assertEqual(status, 201, project)
        return project

    def edit(self, project, **changes):
        return self.request('PATCH', f'/api/projects/{project["id"]}', {'version': project['version'], 'changes': changes}, admin=False)

    def logs(self, project, field=''):
        status, _, result = self.request('GET', f'/api/projects/{project["id"]}/history', admin=False, query='field='+field)
        self.assertEqual(status, 200, result)
        return result

    def test_permissions_csrf_identity_and_disabled_revoked_logout(self):
        self.assertEqual(self.request('POST','/api/projects',{'name':'虚构无权限'},admin=False)[0],403)
        self.assertEqual(self.request('POST','/api/projects',{'name':'虚构管理员拥有项目维护权限'},admin=True)[0],201)
        status, _, _ = asyncio.run(existing.call_app(self.app,'GET','/api/projects/1/history'))
        self.assertEqual(status,401)
        project = self.create()
        with closing(self.database.get_db_connection()) as connection, connection:
            employee = dict(connection.execute("SELECT * FROM employees WHERE username='fixture-employee'").fetchone())
            connection.execute("UPDATE employees SET name='改名后虚构姓名' WHERE id=?", (employee['id'],))
        initial = self.logs(project,'situation')['items'][0]
        self.assertEqual(initial['employee_id'],employee['id'])
        self.assertEqual(initial['employee_name_snapshot'],employee['name'])
        self.grant(False)
        self.assertEqual(self.edit(project,situation='撤权后不得修改')[0],403)
        self.assertEqual(self.logs(project)['project']['id'],project['id'])
        self.grant()
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE employees SET is_active=0 WHERE id=?",(employee['id'],))
        self.assertEqual(self.edit(project,situation='停用后不得修改')[0],401)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE employees SET is_active=1 WHERE id=?",(employee['id'],))
        status, _, _ = asyncio.run(existing.call_app(self.app,'PATCH',f'/api/projects/{project["id"]}',json.dumps({'version':1,'changes':{'name':'虚构'}}).encode(),{'cookie':self.employee_cookie,'content-type':'application/json'}))
        self.assertEqual(status,403)
        self.request('POST','/api/employee/logout',admin=False)
        self.assertEqual(self.edit(project,situation='退出后不得修改')[0],401)

    def test_field_histories_group_noop_clear_restore_and_full_text(self):
        project = self.create(situation=None,nextStep=None,coordination=None)
        baseline = self.logs(project,'situation')['items'][0]
        self.assertEqual(baseline['new_value'],None)
        long_text = '虚构长正文\n<script>不能作为HTML执行</script>\n' * 100
        status, _, updated = self.edit(project,situation=long_text,nextStep='虚构下一步',coordination='虚构协调')
        self.assertEqual(status,200)
        self.assertEqual(updated['version'],2)
        groups=[]
        for field in ['situation','nextStep','coordination']:
            item=self.logs(project,field)['items'][0]
            self.assertEqual(item['old_value'],None)
            self.assertEqual(item['change_type'],'fill')
            self.assertEqual(item['project_version'],2)
            self.assertIn('+00:00',item['changed_at'])
            groups.append(item['change_group_id'])
        self.assertEqual(len(set(groups)),1)
        count=self.logs(project)['total']
        self.assertEqual(self.edit(updated,situation=long_text)[2]['version'],2)
        self.assertEqual(self.logs(project)['total'],count)
        cleared=self.edit(updated,situation=None)[2]
        self.assertEqual(self.logs(project,'situation')['items'][0]['change_type'],'clear')
        restored=self.edit(cleared,situation=long_text)[2]
        self.assertEqual(self.logs(project,'situation')['items'][0]['change_type'],'restore')
        self.assertEqual(restored['pvArea'],project['pvArea'])
        self.assertEqual(restored['storageCapacity'],project['storageCapacity'])

    def test_nodes_free_text_current_stage_and_strict_field_contract(self):
        project=self.create()
        nodes=[None,'自由文本：等待核查',None,None,None,None,'进行中',None,None,None,None]
        updated=self.edit(project,stages=nodes,currentStage='合同签约')[2]
        self.assertEqual(updated['completedCount'],0)
        self.assertEqual(updated['stages'],nodes)
        item=self.logs(project,'stage_02')['items'][0]
        self.assertEqual(item['new_value'],'自由文本：等待核查')
        self.assertEqual(self.logs(project,'currentStage')['items'][0]['new_value'],'合同签约')
        for changes in [{'version':100},{'id':999},{'employee_id':1},{'importId':1},{'stages':[]},{'stages':None},{'name':'  '},{'pvArea':0}]:
            self.assertEqual(self.edit(updated,**changes)[0],422,changes)
        self.assertEqual(self.request('GET',f'/api/projects/{project["id"]}/history',admin=False,query='field=bad')[0],422)

    def test_optimistic_conflict_rename_and_unique_resource(self):
        a=self.create(name='虚构并发一',resource='虚构独立资源一')
        b=self.create(name='虚构并发二',resource='虚构独立资源二')
        latest=self.edit(a,name='虚构改名',resource='虚构改来源',situation='第一次提交')[2]
        self.assertEqual(self.edit(a,situation='旧版本覆盖')[0],409)
        self.assertEqual(self.edit(latest,name=b['name'])[0],409)
        self.assertEqual(self.edit(latest,resource=b['resource'])[0],409)
        row=self.request('GET',f'/api/projects/{a["id"]}',admin=False)[2]
        self.assertEqual(row['situation'],'第一次提交')
        with closing(self.database.get_db_connection()) as connection:
            from project_data import key
            raw=connection.execute('SELECT name_key,resource_key FROM projects WHERE id=?',(a['id'],)).fetchone()
            self.assertEqual(tuple(raw),(key('虚构改名'),key('虚构改来源')))

    def test_node_priority_preservation_history_and_noop(self):
        # Import path intentionally retains mismatched legacy AC until node editing.
        raw = synthetic_projects()[0]
        raw.update(currentStage='历史AC原文', stages=['进行中'] + [None] * 10)
        self.import_projects([raw])
        project = self.request('GET', '/api/projects', admin=False)[2]['projects'][0]
        self.grant()
        baseline = self.logs(project)['total']
        untouched = self.edit(project, situation='只更新文字')[2]
        self.assertEqual(untouched['currentStage'], '历史AC原文')
        same_nodes = self.edit(untouched, stages=raw['stages'])[2]
        self.assertEqual(same_nodes['version'], untouched['version'])
        self.assertEqual(same_nodes['currentStage'], '历史AC原文')
        nodes = [None, '进行中', '进行中', None, '已完成', '暂缓', '不适用', '', '未开始', '自定义', None]
        saved = self.edit(untouched, stages=nodes)[2]
        self.assertEqual(saved['currentStage'], '实地勘察')
        self.assertEqual(saved['completedCount'], 1)
        self.assertEqual(saved['stages'], nodes)
        ac = self.logs(project, 'currentStage')['items'][0]
        node = self.logs(project, 'stage_02')['items'][0]
        self.assertEqual(ac['old_value'], '历史AC原文')
        self.assertEqual(ac['new_value'], '实地勘察')
        self.assertEqual(ac['change_group_id'], node['change_group_id'])
        self.assertEqual(ac['project_version'], saved['version'])
        self.assertIsNotNone(ac['employee_id'])
        self.assertIn('+00:00', ac['changed_at'])
        nodes[1], nodes[2], nodes[8] = '已完成', None, '进行中'
        later = self.edit(saved, stages=nodes)[2]
        self.assertEqual(later['currentStage'], '招标')
        self.assertEqual(later['completedCount'], 2)
        nodes[2] = '进行中'
        gap = self.edit(later, stages=nodes)[2]
        self.assertEqual(gap['currentStage'], '资料收集与方案设计')
        nodes[2], nodes[8] = '', '未开始'
        no_active = self.edit(gap, stages=nodes)[2]
        self.assertEqual(no_active['currentStage'], gap['currentStage'])
        self.assertEqual(no_active['stages'][7], '')
        count = self.logs(project)['total']
        self.assertGreater(count, baseline)
        self.assertEqual(self.edit(no_active, stages=nodes)[2]['version'], no_active['version'])
        self.assertEqual(self.logs(project)['total'], count)

    def test_new_nodes_priority_and_reader_cannot_write(self):
        nodes = [None, '进行中', None, '进行中', '已完成'] + [None] * 6
        project = self.create(stages=nodes, currentStage='错误客户端AC')
        self.assertEqual(project['currentStage'], '实地勘察')
        self.assertEqual(project['completedCount'], 1)
        self.grant(False)
        nodes[0] = '进行中'
        self.assertEqual(self.edit(project, stages=nodes)[0], 403)
        persisted = self.request('GET', f'/api/projects/{project["id"]}', admin=False)[2]
        self.assertIsNone(persisted['stages'][0])
        blank = self.create(name='虚构无阶段新项目', resource='虚构无阶段来源', stages=[None] * 11, currentStage=None)
        self.assertIsNone(blank['currentStage'])

    def test_transaction_failure_rolls_back_both_data_and_history(self):
        project=self.create()
        before=self.logs(project)['total']
        import project_write_api
        with patch.object(project_write_api,'record_changes',side_effect=RuntimeError('synthetic failure')):
            with self.assertRaises(RuntimeError): self.edit(project,situation='不可写入')
            with self.assertRaises(RuntimeError): self.create(name='创建必须回滚',resource='创建回滚资源')
        after=self.request('GET',f'/api/projects/{project["id"]}',admin=False)[2]
        self.assertEqual(after['version'],project['version'])
        self.assertEqual(after['situation'],project['situation'])
        self.assertEqual(self.logs(project)['total'],before)
        with closing(self.database.get_db_connection()) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM projects WHERE name_key='创建必须回滚'").fetchone()[0],0)

    def test_two_employees_conflict_history_survives_deactivation_and_paginates(self):
        project = self.create()
        cookie, csrf = self.employee_cookie, self.csrf
        from auth_security import hash_password
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("INSERT OR IGNORE INTO employees(username,name,department,password_hash,must_change_password,can_edit_projects) VALUES(?,?,?,?,0,1)",
                               ('second-fixture', '第二位虚构员工', 'Tests', hash_password('test-only-second-password')))
            original_id = connection.execute("SELECT id FROM employees WHERE username='fixture-employee'").fetchone()[0]
        status, headers, body = asyncio.run(existing.call_app(self.app, 'GET', '/api/employee/csrf'))
        cookies = SimpleCookie(); cookies.load(headers[b'set-cookie'].decode())
        csrf_cookie = '; '.join(f'{k}={v.value}' for k,v in cookies.items())
        status, headers, body = asyncio.run(existing.call_app(self.app, 'POST', '/api/employee/login',
            json.dumps({'username':'second-fixture','password':'test-only-second-password'}).encode(),
            {'cookie':csrf_cookie,'content-type':'application/json','x-csrf-token':json.loads(body)['csrfToken']}))
        self.assertEqual(status,200)
        cookies.load(headers[b'set-cookie'].decode())
        second_cookie = '; '.join(f'{k}={v.value}' for k,v in cookies.items())
        second_csrf = json.loads(body)['csrfToken']
        first = self.edit(project,situation='第一位员工提交')[2]
        try:
            self.__class__.employee_cookie, self.__class__.csrf = second_cookie, second_csrf
            self.assertEqual(self.edit(project,situation='第二位员工旧版本提交')[0],409)
            second = self.edit(first,situation='第二位员工核对后提交')[2]
            self.assertEqual(second['version'],3)
            with closing(self.database.get_db_connection()) as connection,connection:
                connection.execute('UPDATE employees SET is_active=0 WHERE id=?',(original_id,))
            entries = self.logs(project,'situation')['items']
            self.assertEqual(entries[0]['employee_username_snapshot'],'second-fixture')
            self.assertEqual(entries[1]['employee_id'],original_id)
            status,_,page=self.request('GET',f'/api/projects/{project["id"]}/history',admin=False,query='field=situation&limit=1&offset=1')
            self.assertEqual(status,200)
            self.assertEqual(page['total'],3)
            self.assertEqual(page['items'][0]['id'],entries[1]['id'])
            self.assertEqual(self.request('DELETE',f'/api/projects/{project["id"]}/history',admin=False)[0],405)
            self.assertEqual(self.edit(second,changed_at='fake')[0],422)
        finally:
            self.__class__.employee_cookie, self.__class__.csrf = cookie, csrf

    def test_excel_versions_actor_history_and_preview_invalidation(self):
        raw=synthetic_projects()[0]
        self.import_projects([raw])
        project=self.request('GET','/api/projects',admin=False)[2]['projects'][0]
        preview=self.upload(existing.workbook_bytes([{**raw,'situation':'虚构导入更新'}]))[1]
        self.grant()
        updated=self.edit(project,situation='虚构网页内容')[2]
        self.assertEqual(self.confirm(preview['token'])[0],409)
        rejected=self.upload(existing.workbook_bytes([{**raw,'situation':'虚构覆盖网页'}]))[1]
        self.assertFalse(rejected['canConfirm'])
        self.assertIsNone(rejected['token'])
        row=self.request('GET',f'/api/projects/{project["id"]}',admin=False)[2]
        self.assertEqual(row['situation'],updated['situation'])
        self.import_projects([synthetic_projects()[2]])
        other=next(p for p in self.request('GET','/api/projects',admin=False)[2]['projects'] if p['name']==synthetic_projects()[2]['name'])
        self.import_projects([{**synthetic_projects()[2],'situation':'虚构受控导入修改'}])
        event=self.logs(other,'situation')['items'][0]
        self.assertEqual(event['actor_type'],'admin_import')
        self.assertIsNotNone(event['admin_id'])
        self.assertIsNotNone(event['employee_id'])
        self.assertEqual(event['project_version'],2)

    def test_legacy_migration_is_additive_idempotent_and_honest(self):
        raw=synthetic_projects()[0]
        with closing(self.database.get_db_connection()) as connection,connection:
            from project_data import key
            project_id=connection.execute("INSERT INTO projects(name_key,resource_key,data,imported_at,import_id) VALUES(?,?,?,?,?)",(key(raw['name']),key(raw['resource']),json.dumps(raw),'2026-01-02T03:04:05+00:00',0)).lastrowid
        self.database.init_database();self.database.init_database()
        project=self.request('GET',f'/api/projects/{project_id}',admin=False)[2]
        self.assertEqual(project['version'],1)
        entries=self.logs(project,'situation')['items']
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]['change_type'],'baseline')
        self.assertEqual(entries[0]['changed_at'],'2026-01-02T03:04:05+00:00')
        self.assertIsNone(entries[0]['employee_id'])
        self.assertEqual(entries[0]['new_value'],raw['situation'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
