"""Unified login acceptance: all accounts/data belong to a temporary SQLite database."""
from contextlib import closing
import json
import unittest

import test_employee_auth as existing
from auth_security import hash_password, verify_password


class SingleLoginTests(unittest.TestCase):
    setUpClass = classmethod(existing.EmployeeAuthTests.setUpClass.__func__)
    tearDownClass = classmethod(existing.EmployeeAuthTests.tearDownClass.__func__)
    sql = existing.EmployeeAuthTests.sql

    def setUp(self):
        existing.EmployeeAuthTests.setUp(self)
        from scripts.set_admin_password import set_password
        with closing(self.db.get_db_connection()) as connection, connection:
            self.admin_id, self.employee_id = set_password(connection, 'adminMO', hash_password('synthetic-admin-password'))

    def admin(self):
        status, identity = self.client.login('adminMO', 'synthetic-admin-password')
        self.assertEqual(status, 200, identity)
        return identity

    def test_admin_one_login_read_manage_edit_history_and_logout(self):
        identity = self.admin()
        self.assertTrue(identity['isAdmin']); self.assertTrue(identity['canEditProjects'])
        self.assertFalse(identity['mustChangePassword'])
        self.assertEqual(identity['admin']['id'], self.admin_id)
        for path in ['/api/news', '/api/banners', '/api/tools', '/api/projects', '/api/admin/employees', '/api/admin/news']:
            self.assertEqual(self.client.request('GET', path)[0], 200, path)
        status, project = self.client.request('POST', '/api/projects', {'name':'虚构管理员维护项目', 'storageCapacity':'尚不能确定'})
        self.assertEqual(status,201)
        status, history = self.client.request('GET',f'/api/projects/{project["id"]}/history')
        self.assertEqual(status,200)
        self.assertEqual(history['items'][0]['employee_id'],identity['id'])
        old = self.client.cookie
        self.assertEqual(self.client.request('POST','/api/employee/logout')[0],200)
        self.client.cookie=old
        self.assertEqual(self.client.request('GET','/api/admin/employees')[0],401)
        self.assertEqual(self.client.request('GET','/api/projects')[0],401)

    def test_market_and_reader_permissions_no_frontend_bypass(self):
        self.client.login()
        self.assertEqual(self.client.request('GET','/api/projects')[0],200)
        self.assertEqual(self.client.request('POST','/api/projects',{'name':'不允许新增'})[0],403)
        self.sql("UPDATE employees SET can_edit_projects=1 WHERE username='employee'")
        self.assertEqual(self.client.request('POST','/api/projects',{'name':'虚构市场部项目'})[0],201)
        self.assertEqual(self.client.request('GET','/api/admin/employees')[0],403)
        self.assertEqual(self.client.request('POST','/api/tools',{'title':'不能管理'})[0],403)
        self.sql("UPDATE employees SET can_edit_projects=0 WHERE username='employee'")
        self.assertEqual(self.client.request('POST','/api/projects',{'name':'撤权后禁止'})[0],403)

    def test_admin_password_change_updates_legacy_hash_and_revokes_other_sessions(self):
        self.admin()
        other=existing.Client(self.app);other.login('adminMO','synthetic-admin-password')
        status,identity=self.client.request('POST','/api/employee/password',{'currentPassword':'synthetic-admin-password','newPassword':'changed-admin-test-password'})
        self.assertEqual(status,200);self.assertTrue(identity['isAdmin'])
        self.assertEqual(other.request('GET','/api/news')[0],401)
        encoded=self.sql('SELECT password_hash FROM admins WHERE id=?',(self.admin_id,))[0][0]
        self.assertTrue(verify_password('changed-admin-test-password',encoded))
        self.assertEqual(self.client.login('adminMO','synthetic-admin-password')[0],401)
        self.assertEqual(self.client.login('adminMO','changed-admin-test-password')[0],200)

    def test_local_password_tool_preserves_ids_business_and_revokes_old_cookie(self):
        from scripts.set_admin_password import set_password
        self.admin();old=self.client.cookie
        before=self.sql('SELECT * FROM news')
        with closing(self.db.get_db_connection()) as connection,connection:
            actual=set_password(connection,'adminMO',hash_password('reset-admin-test-password'))
        self.assertEqual(actual,(self.admin_id,self.employee_id))
        self.assertEqual(before,self.sql('SELECT * FROM news'))
        self.client.cookie=old
        self.assertEqual(self.client.request('GET','/api/admin/news')[0],401)
        self.assertEqual(self.client.login('adminMO','reset-admin-test-password')[0],200)

    def test_existing_admin_bootstraps_only_after_valid_password_and_no_collision(self):
        self.sql('DELETE FROM employees WHERE id=?',(self.employee_id,))
        self.assertEqual(self.client.login('adminMO','wrong')[0],401)
        self.assertFalse(self.sql('SELECT id FROM employees WHERE admin_id=?',(self.admin_id,)))
        self.assertEqual(self.admin()['admin']['id'],self.admin_id)
        self.sql('DELETE FROM employee_sessions')
        self.sql('UPDATE employees SET admin_id=NULL,password_hash=? WHERE admin_id=?',(hash_password('unrelated-employee-password'),self.admin_id))
        self.assertEqual(self.client.login('adminMO','synthetic-admin-password')[0],409)
        result=self.client.login('adminMO','unrelated-employee-password')
        self.assertEqual(result[0],200);self.assertFalse(result[1]['isAdmin'])
        self.assertEqual(self.client.request('GET','/api/admin/news')[0],403)

    def test_old_elevated_session_fields_cannot_grant_admin_and_role_is_live(self):
        self.client.login()
        self.sql('UPDATE employee_sessions SET admin_id=?,admin_expires_at=9999999999',(self.admin_id,))
        self.assertEqual(self.client.request('GET','/api/admin/news')[0],403)
        self.admin()
        self.sql('UPDATE employees SET admin_id=NULL WHERE id=?',(self.employee_id,))
        self.assertEqual(self.client.request('GET','/api/admin/news')[0],403)
        self.assertEqual(self.client.request('POST','/api/projects',{'name':'不继承管理员维护'})[0],403)

    def test_rate_limit_shared_between_login_aliases_and_csrf_required(self):
        self.assertEqual(self.client.request('POST','/api/auth/login',{'username':'adminMO','password':'synthetic-admin-password'},csrf=False)[0],403)
        self.client.request('GET','/api/employee/csrf')
        for index in range(8):
            endpoint='/api/auth/login' if index%2 else '/api/employee/login'
            self.assertEqual(self.client.request('POST',endpoint,{'username':'adminMO','password':'wrong'})[0],401)
        self.assertEqual(self.client.login('adminMO','synthetic-admin-password')[0],429)

    def test_no_role_injection_and_admin_reset_remains_usable_without_forced_change(self):
        self.admin()
        status,employee=self.client.request('POST','/api/admin/employees',{'username':'market-test','name':'虚构维护人员','department':'Market','temporaryPassword':'initial-market-password','canEditProjects':True})
        self.assertEqual(status,201)
        user=existing.Client(self.app);result=user.login('market-test','initial-market-password')
        self.assertFalse(result[1]['mustChangePassword'])
        self.assertEqual(user.request('GET','/api/admin/employees')[0],403)
        self.assertEqual(self.client.request('PUT',f'/api/admin/employees/{employee["id"]}',{'name':'Name','department':'Market','admin_id':self.admin_id})[0],422)
        self.assertEqual(self.client.request('POST',f'/api/admin/employees/{employee["id"]}/reset-password',{'temporaryPassword':'reset-market-password'})[0],200)
        self.assertEqual(user.request('GET','/api/projects')[0],401)
        self.assertFalse(user.login('market-test','reset-market-password')[1]['mustChangePassword'])


if __name__=='__main__':
    unittest.main(verbosity=2)
