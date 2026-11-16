"""News access regression: fresh SQLite and uploads only, no production imports."""
import asyncio
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_exchange import call

class NewsAccessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='news-access-')
        cls.root = Path(cls.temp.name)
        cls.env = patch.dict(os.environ, {
            'DATABASE_PATH': str(cls.root / 'test.db'), 'SESSION_SECRET': 'isolated-news-test-secret',
            'SESSION_COOKIE_SECURE': 'false', 'ADMIN_USERNAME': 'news-test',
            'ADMIN_PASSWORD': 'isolated-password', 'EXCHANGE_ENABLED': 'false',
        })
        cls.env.start()
        import upload_api
        cls.upload_patch = patch.object(upload_api, 'UPLOAD_ROOT', cls.root / 'uploads')
        cls.upload_patch.start()
        import main
        cls.app = main.app
        status, headers, _ = cls.request('POST', '/api/auth/login', {
            'username': 'news-test', 'password': 'isolated-password',
        })
        assert status == 200
        cookie = SimpleCookie()
        cookie.load(headers[b'set-cookie'].decode())
        cls.cookie = '; '.join(f'{k}={v.value}' for k, v in cookie.items())

    @classmethod
    def tearDownClass(cls):
        cls.upload_patch.stop()
        cls.env.stop()
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, payload=None, admin=False):
        headers = {'content-type': 'application/json'}
        if admin:
            headers['cookie'] = cls.cookie
        status, headers, body = asyncio.run(call(cls.app, method, path,
            json.dumps(payload).encode() if payload is not None else b'', headers))
        return status, headers, json.loads(body)

    def create(self, published=0):
        payload = dict(title='Test news', content='Private draft', summary='Summary', source='Test',
            source_type='行业资讯', publish_date='2026-11-16', keywords='one,two',
            url='https://example.com/news', is_published=published)
        status, _, news = self.request('POST', '/api/news', payload, True)
        self.assertEqual(status, 201)
        self.assertEqual(set(news), set(payload) | {'id', 'created_at'})
        self.addCleanup(self.request, 'DELETE', f"/api/news/{news['id']}", None, True)
        return news

    def test_published_and_missing(self):
        news = self.create(1)
        self.assertEqual(self.request('GET', f"/api/news/{news['id']}")[0], 200)
        self.assertEqual(self.request('GET', '/api/news/999999')[0], 404)

    def test_private_draft_and_admin_access(self):
        news = self.create()
        path = f"/api/news/{news['id']}"
        self.assertEqual(self.request('GET', path)[2], self.request('GET', '/api/news/999999')[2])
        self.assertEqual(self.request('GET', path)[0], 404)
        self.assertEqual(self.request('GET', f"/api/admin/news/{news['id']}")[0], 401)
        self.assertEqual(self.request('GET', f"/api/admin/news/{news['id']}", admin=True)[2], news)
        self.assertEqual(self.request('GET', '/api/admin/news/999999', admin=True)[0], 404)

    def test_edit_publish_withdraw_and_delete(self):
        news = self.create()
        path = f"/api/news/{news['id']}"
        payload = {k: v for k, v in news.items() if k not in {'id', 'created_at'}}
        payload['content'] = 'Edited draft'
        status, _, edited = self.request('PUT', path, payload, True)
        self.assertEqual(status, 200)
        self.assertEqual(edited['content'], 'Edited draft')
        self.assertEqual(edited['is_published'], 0)
        self.assertEqual(self.request('GET', path)[0], 404)
        for value, expected in [(1, 200), (0, 404)]:
            self.assertEqual(self.request('PATCH', path + '/publish', {'is_published': value}, True)[0], 200)
            self.assertEqual(self.request('GET', path)[0], expected)
        self.assertEqual(self.request('DELETE', path, admin=True)[0], 200)
        self.assertEqual(self.request('GET', path)[0], 404)

    def test_public_feed_excludes_drafts(self):
        draft, public = self.create(), self.create(1)
        status, _, feed = self.request('GET', '/api/news')
        self.assertEqual(status, 200)
        self.assertNotIn(draft['id'], [n['id'] for n in feed])
        self.assertIn(public['id'], [n['id'] for n in feed])
        admin_feed = self.request('GET', '/api/admin/news', admin=True)[2]
        self.assertIn(draft['id'], [n['id'] for n in admin_feed])

    def test_mutations_require_admin(self):
        news = self.create()
        path = f"/api/news/{news['id']}"
        for method, url, payload in [('POST', '/api/news', {'title': 'x'}),
                ('PUT', path, {'title': 'x'}), ('DELETE', path, None),
                ('PATCH', path + '/publish', {'is_published': 1})]:
            self.assertEqual(self.request(method, url, payload)[0], 401)
        self.assertEqual(self.request('POST', '/api/news', {'title': '  '}, True)[0], 422)

if __name__ == '__main__':
    unittest.main()
