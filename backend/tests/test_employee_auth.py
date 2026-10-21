"""Single login with server-side role checks; temporary SQLite and files only."""
import asyncio
from contextlib import closing
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_section_visuals import call_app
from auth_security import hash_password


class Client:
    def __init__(self, app):
        self.app, self.cookie, self.csrf = app, '', ''

    def request(self, method, path, payload=None, headers=None, csrf=True):
        merged = {'cookie': self.cookie}
        if csrf and self.csrf:
            merged['x-csrf-token'] = self.csrf
        body = b''
        if payload is not None:
            body = json.dumps(payload).encode()
            merged['content-type'] = 'application/json'
        merged.update(headers or {})
        status, returned, content = asyncio.run(call_app(self.app, method, path, body, merged))
        if b'set-cookie' in returned:
            cookies = SimpleCookie(); cookies.load(returned[b'set-cookie'].decode())
            self.cookie = '; '.join(f'{k}={v.value}' for k, v in cookies.items())
        try:
            data = json.loads(content)
        except (ValueError, UnicodeDecodeError):
            data = content
        if isinstance(data, dict) and 'csrfToken' in data:
            self.csrf = data['csrfToken']
        return status, data

    def login(self, username='employee', password='initial-test-password'):
        self.request('GET', '/api/employee/csrf')
        return self.request('POST', '/api/employee/login', {'username': username, 'password': password})

    def admin(self):
        return self.request('POST', '/api/auth/login', {'username': 'independent-admin', 'password': 'independent-admin-test-password'})


class EmployeeAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='employee-security-')
        cls.root = Path(cls.temp.name)
        cls.env = patch.dict(os.environ, {'DATABASE_PATH': str(cls.root/'test.db'), 'SESSION_SECRET': 'isolated-employee-tests-only',
            'SESSION_COOKIE_SECURE': 'false', 'ADMIN_USERNAME': 'independent-admin',
            'ADMIN_PASSWORD': 'independent-admin-test-password', 'EXCHANGE_ENABLED': 'false'})
        cls.env.start()
        import database, upload_api
        cls.dbpatch = patch.object(database, 'DATABASE_PATH', cls.root/'test.db'); cls.dbpatch.start()
        cls.uploadpatch = patch.object(upload_api, 'UPLOAD_ROOT', cls.root/'uploads'); cls.uploadpatch.start()
        import main
        from employee_security import require_project_editor
        from fastapi import Depends
        # Test-only route exercises the future permission dependency, not project business APIs.
        @main.app.post('/api/test-project-permission', dependencies=[Depends(require_project_editor)])
        def permission_probe():
            return {'allowed': True}
        cls.app, cls.db = main.app, database
        cls.password_hash = hash_password('initial-test-password')
        (cls.root/'uploads/news').mkdir(parents=True)
        (cls.root/'uploads/news/sample.txt').write_text('protected test attachment')

    @classmethod
    def tearDownClass(cls):
        cls.uploadpatch.stop(); cls.dbpatch.stop(); cls.env.stop(); cls.temp.cleanup()

    def setUp(self):
        with closing(self.db.get_db_connection()) as c, c:
            c.execute('DELETE FROM employee_sessions'); c.execute('DELETE FROM employees'); c.execute('DELETE FROM auth_login_attempts')
            c.execute("INSERT INTO employees(username,name,department,password_hash,must_change_password) VALUES('employee','Test employee','Test department',?,0)", (self.password_hash,))
        self.client = Client(self.app)

    def sql(self, query, values=()):
        with closing(self.db.get_db_connection()) as c, c:
            return c.execute(query, values).fetchall()

    def test_deny_all_anonymous_registered_business_routes_and_attachments(self):
        for path in ['/api/news', '/api/banners', '/api/announcements', '/api/tools', '/api/section-visuals',
                     '/api/exchange', '/api/admin/projects', '/api/hello', '/api/auth/me',
                     '/api/admin/employees', '/uploads/news/sample.txt', '/tools/qstart/index.html', '/api/projects']:
            self.assertEqual(self.client.request('GET', path)[0], 401, path)
        self.assertEqual(self.client.request('GET', '/api/health')[0], 200)
        self.assertEqual(self.client.request('POST', '/api/chat', {'message': 'test'})[0], 401)

    def test_employee_login_bad_password_disabled_and_logout_replay(self):
        self.assertEqual(self.client.login(password='wrong')[0], 401)
        self.assertEqual(self.client.login()[0], 200)
        old = self.client.cookie
        self.assertEqual(self.client.request('GET', '/api/news')[0], 200)
        self.assertEqual(self.client.request('GET', '/uploads/news/sample.txt')[0], 200)
        self.assertEqual(self.client.request('POST', '/api/employee/logout')[0], 200)
        self.client.cookie = old
        self.assertEqual(self.client.request('GET', '/api/news')[0], 401)
        self.sql('UPDATE employees SET is_active=0')
        self.assertEqual(self.client.login()[0], 401)

    def test_first_password_change_rotates_and_revokes_other_sessions(self):
        self.sql('UPDATE employees SET must_change_password=1')
        self.assertFalse(self.client.login()[1]['mustChangePassword'])
        self.assertEqual(self.client.request('GET', '/api/news')[0], 200)
        old = self.client.cookie
        result = self.client.request('POST', '/api/employee/password', {'currentPassword': 'initial-test-password', 'newPassword': 'changed-test-password'})
        self.assertEqual(result[0], 200); self.assertFalse(result[1]['mustChangePassword'])
        self.assertNotEqual(self.client.cookie, old)
        self.assertEqual(self.client.request('GET', '/api/news')[0], 200)
        self.client.cookie = old
        self.assertEqual(self.client.request('GET', '/api/news')[0], 401)
        self.assertEqual(self.client.login()[0], 401)
        self.assertEqual(self.client.login(password='changed-test-password')[0], 200)

    def test_admin_single_login_and_unified_logout(self):
        self.assertEqual(self.client.login('independent-admin', 'independent-admin-test-password')[0], 200)
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 200)
        other = Client(self.app); other.login()
        self.assertEqual(other.request('GET', '/api/admin/news')[0], 403)
        elevated = self.client.cookie
        self.assertEqual(self.client.request('POST', '/api/auth/logout')[0], 200)
        self.client.cookie = elevated
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 401)
        self.assertEqual(self.client.request('GET', '/api/news')[0], 401)
        self.client.login('independent-admin', 'independent-admin-test-password'); elevated = self.client.cookie
        self.client.request('POST', '/api/employee/logout'); self.client.cookie = elevated
        self.assertEqual(self.client.request('GET', '/api/auth/me')[0], 401)

    def test_admin_management_permissions_disable_and_password_reset(self):
        self.client.login(); self.client.admin()
        fields = {'username': 'another', 'name': 'Another', 'department': 'Market', 'temporaryPassword': 'temporary-test-password', 'canEditProjects': True}
        status, created = self.client.request('POST', '/api/admin/employees', fields)
        self.assertEqual(status, 201); self.assertNotIn('password_hash', created)
        self.assertEqual(self.client.request('POST', '/api/admin/employees', fields)[0], 409)
        other = Client(self.app); self.assertEqual(other.login('another', 'temporary-test-password')[0], 200)
        other.request('POST', '/api/employee/password', {'currentPassword': 'temporary-test-password', 'newPassword': 'personal-test-password'})
        self.assertEqual(other.request('POST', '/api/test-project-permission')[0], 200)
        self.assertEqual(other.request('GET', '/api/admin/employees')[0], 403)
        self.assertEqual(other.request('POST', '/api/admin/employees', fields)[0], 403)
        self.assertEqual(self.client.request('POST', '/api/test-project-permission')[0], 200)
        self.client.request('PUT', f"/api/admin/employees/{created['id']}", {'name': 'Renamed', 'department': 'Market', 'canEditProjects': False, 'isActive': True})
        self.assertEqual(other.request('POST', '/api/test-project-permission')[0], 403)
        self.assertEqual(self.client.request('POST', f"/api/admin/employees/{created['id']}/reset-password", {'temporaryPassword': 'reset-test-password'})[0], 200)
        self.assertEqual(other.request('GET', '/api/news')[0], 401)
        self.assertFalse(other.login('another', 'reset-test-password')[1]['mustChangePassword'])
        self.client.request('PUT', f"/api/admin/employees/{created['id']}", {'name': 'Another', 'department': 'Market', 'canEditProjects': False, 'isActive': False})
        self.assertEqual(other.request('GET', '/api/employee/me')[0], 401)

    def test_csrf_login_and_multipart_origin_checks(self):
        self.assertEqual(self.client.request('POST', '/api/employee/login', {'username': 'employee', 'password': 'initial-test-password'}, csrf=False)[0], 403)
        self.client.login()
        self.assertEqual(self.client.request('POST', '/api/employee/logout', csrf=False)[0], 403)
        self.assertEqual(self.client.request('POST', '/api/employee/logout', headers={'origin': 'https://attacker.invalid'})[0], 403)
        self.assertEqual(self.client.request('POST', '/api/employee/logout', headers={'origin': 'https://[invalid'})[0], 403)
        self.assertEqual(self.client.request('POST', '/api/employee/logout', headers={'x-csrf-token': '\u00e4'})[0], 403)
        self.assertEqual(self.client.request('POST', '/api/admin/uploads/banners', csrf=False)[0], 403)
        self.assertEqual(self.client.request('GET', '/api/news')[0], 200)

    def test_bruteforce_limits_and_cookie_properties(self):
        for _ in range(8):
            self.assertEqual(self.client.login(password='bad')[0], 401)
        self.assertEqual(self.client.login()[0], 429)
        self.sql('DELETE FROM auth_login_attempts'); self.client.login()
        self.assertTrue(self.sql('SELECT last_login_at FROM employees')[0][0])
        self.assertTrue(self.sql('SELECT attempts FROM auth_login_attempts'))
        self.assertNotEqual(self.sql('SELECT token_hash FROM employee_sessions')[0][0], self.client.cookie)
        self.sql('UPDATE employee_sessions SET expires_at=?', (time.time()-1,))
        self.assertEqual(self.client.request('GET', '/api/news')[0], 401)

    def test_admin_has_no_short_second_expiry_but_session_and_disable_still_apply(self):
        self.client.login(); self.client.admin()
        self.sql('UPDATE employee_sessions SET admin_expires_at=?', (time.time()-1,))
        self.assertEqual(self.client.request('GET', '/api/auth/me')[0], 200)
        self.assertEqual(self.client.request('GET', '/api/employee/me')[0], 200)
        self.client.admin(); self.sql('UPDATE employees SET is_active=0')
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 401)

    def test_no_registration_no_plaintext_or_invalid_password_echo(self):
        self.assertEqual(self.client.request('POST', '/api/register')[0], 401)
        self.client.login(); self.client.admin()
        status, data = self.client.request('POST', '/api/admin/employees', {'username': 'invalid', 'name': 'Name', 'department': 'Dept', 'temporaryPassword': 'tiny123'})
        self.assertEqual(status, 422); self.assertNotIn('tiny123', json.dumps(data))
        stored = self.sql('SELECT password_hash FROM employees')[0][0]
        self.assertTrue(stored.startswith('$argon2id$')); self.assertNotIn('initial-test-password', stored)

    def test_legacy_admin_crud_requires_admin_role(self):
        self.client.login()
        self.assertEqual(self.client.request('POST', '/api/news', {'title': 'test'})[0], 403)
        self.client.admin()
        for path, payload in [('/api/banners', {'title': 'isolated standard'}),
                              ('/api/announcements', {'title': 'isolated announcement'}),
                              ('/api/tools', {'title': 'isolated tool'}),
                              ('/api/news', {'title': 'isolated news'})]:
            status, item = self.client.request('POST', path, payload)
            self.assertEqual(status, 201, (path, item))
            self.assertEqual(self.client.request('DELETE', f"{path}/{item['id']}")[0], 200)

    def test_cookie_flags_tamper_and_account_switch(self):
        status, headers, _ = asyncio.run(call_app(self.app, 'GET', '/api/employee/csrf'))
        self.assertEqual(status, 200)
        cookie = headers[b'set-cookie'].decode().lower()
        self.assertIn('httponly', cookie); self.assertIn('samesite=lax', cookie)
        self.client.login(); self.client.admin()
        self.sql("INSERT INTO employees(username,name,department,password_hash,must_change_password) VALUES('switch','Switch','Tests',?,0)", (self.password_hash,))
        self.assertEqual(self.client.login('switch')[0], 200)
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 403)
        self.client.cookie += 'tampered'
        self.assertEqual(self.client.request('GET', '/api/news')[0], 401)

    def test_idempotent_migration_and_old_admin_cookie_cannot_bypass(self):
        import base64
        from itsdangerous import TimestampSigner
        self.client.cookie = 'ai_portal_admin_session=' + TimestampSigner('isolated-employee-tests-only').sign(
            base64.b64encode(json.dumps({'admin_id': 1}).encode())).decode()
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 401)
        self.client.login(); self.client.admin()
        tables = ['employees', 'employee_sessions', 'admins']
        before = {name: [tuple(row) for row in self.sql(f'SELECT * FROM {name}')] for name in tables}
        self.db.init_database(); self.db.init_database()
        self.assertEqual(before, {name: [tuple(row) for row in self.sql(f'SELECT * FROM {name}')] for name in tables})
        self.assertEqual(self.client.request('GET', '/api/admin/news')[0], 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
