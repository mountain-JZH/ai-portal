"""Real ASGI + SQLite + image tests, exclusively in temporary directories."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import socket
import sys
import tempfile
import unittest
from threading import Thread
from time import monotonic, sleep
from unittest.mock import patch
from urllib.parse import urlsplit

from PIL import Image
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def call(app, method, path, body=b"", headers=None):
    messages, delivered = [], False

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    url = urlsplit(path)
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": method, "scheme": "http",
        "path": url.path, "raw_path": url.path.encode(), "query_string": url.query.encode(),
        "root_path": "", "server": ("testserver", 80), "client": ("127.0.0.1", 1234),
        "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
    }
    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    data = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), data


def image_bytes(fmt="WEBP", size=(132, 120)):
    with Image.new("RGBA" if fmt != "JPEG" else "RGB", size, "#89ab70") as image:
        stream = BytesIO()
        image.save(stream, format=fmt)
        return stream.getvalue()


class ExchangeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="ai-portal-exchange-")
        cls.root = Path(cls.temp.name)
        cls.env = patch.dict(os.environ, {
            "DATABASE_PATH": str(cls.root / "test.db"), "EXCHANGE_ENABLED": "true",
            "SESSION_SECRET": "exchange-isolated-test-secret", "SESSION_COOKIE_SECURE": "false",
            "ADMIN_USERNAME": "exchange-test-admin", "ADMIN_PASSWORD": "exchange-test-password",
        })
        cls.env.start()
        import database
        import upload_api
        cls.db_patch = patch.object(database, "DATABASE_PATH", cls.root / "test.db")
        cls.upload_patch = patch.object(upload_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.db_patch.start()
        cls.upload_patch.start()
        import main
        import exchange_api
        cls.api_upload = patch.object(exchange_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.api_upload.start()
        cls.database, cls.api, cls.app = database, exchange_api, main.app
        status, headers, _ = cls.request("POST", "/api/auth/login", json.dumps({
            "username": "exchange-test-admin", "password": "exchange-test-password",
        }).encode(), {"content-type": "application/json"})
        assert status == 200
        cookie = SimpleCookie()
        cookie.load(headers[b"set-cookie"].decode())
        cls.cookie = "; ".join(f"{key}={value.value}" for key, value in cookie.items())

    @classmethod
    def tearDownClass(cls):
        cls.api_upload.stop()
        cls.upload_patch.stop()
        cls.db_patch.stop()
        cls.env.stop()
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, body=b"", headers=None, admin=False):
        headers = dict(headers or {})
        if admin:
            headers["cookie"] = cls.cookie
        return asyncio.run(call(cls.app, method, path, body, headers))

    def setUp(self):
        self.api.submission_limiter = self.api.SubmissionLimiter(per_peer=1000, total=1000)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("DELETE FROM exchange_resources")

    def fields(self, **updates):
        return {"title": "分享示例", "description": "第一段\n\n第二段", "reason": "", "domain": "工作方法", "type": "文章", **updates}

    def post(self, fields=None, image=None, mime="image/webp", headers=None):
        prepared = requests.Request("POST", "http://testserver", data={
            "payload": json.dumps(self.fields() if fields is None else fields),
        }, files=None if image is None else {"file": ("../../unsafe.webp", image, mime)}).prepare()
        body = prepared.body.encode() if isinstance(prepared.body, str) else prepared.body
        return self.request("POST", "/api/exchange", body, {"content-type": prepared.headers["Content-Type"], **(headers or {})})

    def create(self, image=None, **fields):
        status, _, body = self.post(self.fields(**fields), image)
        self.assertEqual(status, 201, body)
        return json.loads(body)

    def public(self, query=""):
        status, _, body = self.request("GET", "/api/exchange" + query)
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def test_empty_plain_submission_persistence_and_utc(self):
        self.assertEqual(self.public(), [])
        before = datetime.now(timezone.utc)
        saved = self.create(tags=["测试", "测试", "方法"])
        self.assertEqual(saved["displayNumber"], str(saved["id"]).zfill(3))
        self.assertEqual(saved["tags"], ["测试", "方法"])
        self.assertEqual(saved["description"], "第一段\n\n第二段")
        self.assertEqual(saved["imageUrl"], "")
        self.assertEqual(saved["externalUrl"], "")
        self.assertLessEqual(before, datetime.fromisoformat(saved["createdAt"].replace("Z", "+00:00")))
        self.assertEqual(self.public(), [saved])
        with closing(sqlite3.connect(self.root / "test.db")) as connection:
            self.assertEqual(connection.execute("SELECT title FROM exchange_resources WHERE id=?", (saved["id"],)).fetchone()[0], saved["title"])
        self.database.init_database()
        self.assertEqual(self.public(), [saved])

    def test_valid_image_formats_are_reencoded_and_statically_accessible(self):
        for fmt, mime in [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]:
            status, _, body = self.post(image=image_bytes(fmt) + b"extra metadata", mime=mime)
            self.assertEqual(status, 201, body)
            item = json.loads(body)
            self.assertRegex(item["imageUrl"], r"^/uploads/exchange/[a-f0-9]{32}\.webp$")
            status, headers, content = self.request("GET", item["imageUrl"])
            self.assertEqual(status, 200)
            self.assertEqual(headers[b"content-type"], b"image/webp")
            self.assertNotIn(b"extra metadata", content)
            with Image.open(BytesIO(content)) as decoded:
                decoded.load()
                self.assertEqual(decoded.size, (132, 120))

    def test_fields_and_dangerous_protocols_are_rejected(self):
        for fields in [{}, self.fields(title=" "), self.fields(description=" "), self.fields(title="x"*91),
                       self.fields(description="x"*1501), self.fields(reason="x"*601), self.fields(domain="invalid"),
                       self.fields(type="invalid"), self.fields(id=7), self.fields(createdAt="today"),
                       self.fields(tags=["x"*41]), self.fields(tags=[str(i) for i in range(9)])]:
            with self.subTest(fields=fields):
                self.assertEqual(self.post(fields)[0], 422)
        for url in ["javascript:alert(1)", "data:text/plain,a", "file:///etc/passwd", "ftp://host/file", "https://", "https://a/b\n", "http://a:invalid", "https://user:pass@host/"]:
            # Trailing whitespace is intentionally normalized, as for other text fields.
            if url.endswith("\n"):
                url = "https://a/b\nx"
            self.assertEqual(self.post(self.fields(externalUrl=url))[0], 422)
        self.assertEqual(self.public(), [])
        self.create(externalUrl="https://example.com/resource", description="一句话也可以")

    def test_invalid_images_and_oversize_never_create_rows(self):
        animated = BytesIO()
        with Image.new("RGB", (20, 20), "red") as a, Image.new("RGB", (20, 20), "blue") as b:
            a.save(animated, format="WEBP", save_all=True, append_images=[b], duration=100)
        cases = [(b"not image", "image/webp"), (image_bytes("PNG"), "image/jpeg"),
                 (image_bytes()[:15], "image/webp"), (b"", "image/webp"),
                 (b"<svg/>", "image/svg+xml"), (animated.getvalue(), "image/webp"),
                 (b"x"*(5*1024*1024+1), "image/webp"),
                 (image_bytes("PNG", (8193, 1)), "image/png"), (image_bytes("PNG", (4001, 4000)), "image/png")]
        for content, mime in cases:
            with self.subTest(size=len(content), mime=mime):
                self.assertEqual(self.post(image=content, mime=mime)[0], 400)
        self.assertEqual(self.public(), [])

    def test_auth_admin_detail_delete_file_cleanup_and_number_nonreuse(self):
        first = self.create(image=image_bytes())
        other = self.create(image=image_bytes())
        first_path = self.root / first["imageUrl"].lstrip("/")
        other_path = self.root / other["imageUrl"].lstrip("/")
        for method, path in [("GET", "/api/admin/exchange"), ("GET", f"/api/admin/exchange/{first['id']}"), ("DELETE", f"/api/admin/exchange/{first['id']}")]:
            self.assertEqual(self.request(method, path)[0], 401)
        listing = json.loads(self.request("GET", "/api/admin/exchange?limit=1&offset=0", admin=True)[2])
        self.assertEqual(listing["total"], 2)
        self.assertEqual(listing["items"], [other])
        self.assertEqual(json.loads(self.request("GET", f"/api/admin/exchange/{first['id']}", admin=True)[2]), first)
        self.assertEqual(self.request("DELETE", f"/api/admin/exchange/{other['id']}", admin=True)[0], 200)
        self.assertFalse(other_path.exists())
        self.assertTrue(first_path.exists())
        self.assertGreater(self.create()["id"], other["id"])
        self.assertEqual(self.request("GET", f"/api/admin/exchange/{other['id']}", admin=True)[0], 404)
        self.assertEqual(self.request("DELETE", f"/api/admin/exchange/{other['id']}", admin=True)[0], 404)
        self.assertNotIn(other["id"], [r["id"] for r in self.public()])

    def test_transaction_failure_cleans_only_new_image_and_delete_failure_keeps_media(self):
        original = self.create(image=image_bytes())
        files = set((self.root / "uploads" / "exchange").iterdir())
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("CREATE TRIGGER fail_exchange BEFORE INSERT ON exchange_resources BEGIN SELECT RAISE(ABORT, 'test'); END")
        try:
            with self.assertLogs("exchange_api", level="ERROR"):
                self.assertEqual(self.post(image=image_bytes())[0], 500)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("DROP TRIGGER fail_exchange")
        self.assertEqual(set((self.root / "uploads" / "exchange").iterdir()), files)
        self.assertEqual(self.public(), [original])
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("CREATE TRIGGER fail_delete BEFORE DELETE ON exchange_resources BEGIN SELECT RAISE(ABORT, 'test'); END")
        try:
            with self.assertLogs("exchange_api", level="WARNING"):
                self.assertEqual(self.request("DELETE", f"/api/admin/exchange/{original['id']}", admin=True)[0], 500)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("DROP TRIGGER fail_delete")
        self.assertTrue((self.root / original["imageUrl"].lstrip("/")).is_file())

    def test_disk_failure_and_controlled_deletion_paths(self):
        blocked = self.root / "blocked"
        blocked.touch(exist_ok=True)
        with patch.object(self.api, "UPLOAD_ROOT", blocked), self.assertLogs("exchange_api", level="ERROR"):
            self.assertEqual(self.post(image=image_bytes())[0], 500)
        outside = self.root / "uploads" / "news" / "keep.webp"
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_bytes(b"do not delete")
        for path in ["/uploads/news/keep.webp", "/uploads/exchange/../../news/keep.webp", str(outside)]:
            item = self.create()
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("UPDATE exchange_resources SET image_path=? WHERE id=?", (path, item["id"]))
            self.assertEqual(self.request("DELETE", f"/api/admin/exchange/{item['id']}", admin=True)[0], 200)
            self.assertTrue(outside.is_file())

    def test_concurrent_ids_and_bounded_pagination(self):
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(lambda _: self.post(), range(8)))
        self.assertTrue(all(r[0] == 201 for r in results), results)
        ids = [json.loads(r[2])["id"] for r in results]
        self.assertEqual(len(set(ids)), 8)
        first_page = self.public("?limit=3")
        next_page = self.public(f"?limit=3&beforeId={first_page[-1]['id']}")
        self.assertFalse({r["id"] for r in first_page} & {r["id"] for r in next_page})
        self.assertEqual(self.request("GET", "/api/exchange?limit=201")[0], 422)

    def test_rate_body_limit_and_feature_gate(self):
        self.api.submission_limiter = self.api.SubmissionLimiter(per_peer=2, total=20)
        self.assertEqual(self.post()[0], 201)
        self.assertEqual(self.post(headers={"x-forwarded-for": "different-client"})[0], 201)
        status, headers, _ = self.post(headers={"x-forwarded-for": "another-client"})
        self.assertEqual(status, 429)
        self.assertEqual(headers[b"retry-after"], b"60")
        self.api.submission_limiter = self.api.SubmissionLimiter()
        self.assertEqual(self.request("POST", "/api/exchange", b"", {"content-length": str(self.api.MAX_REQUEST_BYTES+1)})[0], 413)
        self.assertEqual(self.request("POST", "/api/exchange", b"x"*(self.api.MAX_REQUEST_BYTES+1))[0], 413)
        with patch.dict(os.environ, {"EXCHANGE_ENABLED": "false"}):
            self.assertEqual(self.request("GET", "/api/exchange")[0], 503)
            self.assertEqual(self.post()[0], 503)
            self.assertEqual(self.request("GET", "/api/admin/exchange", admin=True)[0], 200)

    def test_migration_is_idempotent_and_keeps_other_content(self):
        self.create()
        with closing(self.database.get_db_connection()) as connection:
            before = {name: [tuple(r) for r in connection.execute(f"SELECT * FROM {name}")]
                      for name in ["news", "tools", "banners", "announcements", "admins", "exchange_resources"]}
        self.database.init_database()
        self.database.init_database()
        with closing(self.database.get_db_connection()) as connection:
            after = {name: [tuple(r) for r in connection.execute(f"SELECT * FROM {name}")] for name in before}
            schema = connection.execute("SELECT sql FROM sqlite_master WHERE name='exchange_resources'").fetchone()[0]
        self.assertEqual(before, after)
        self.assertIn("AUTOINCREMENT", schema)
        fresh = self.root / "fresh.db"
        with patch.object(self.database, "DATABASE_PATH", fresh):
            self.database.init_database()
            self.database.init_database()
            with closing(self.database.get_db_connection()) as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM exchange_resources").fetchone()[0], 0)

    def test_inactive_admin_and_cleanup_failure_are_explicit(self):
        resource = self.create(image=image_bytes())
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE admins SET is_active=0")
        try:
            self.assertEqual(self.request("DELETE", f"/api/admin/exchange/{resource['id']}", admin=True)[0], 401)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("UPDATE admins SET is_active=1")
        with patch.object(Path, "unlink", side_effect=OSError("test permission denied")), self.assertLogs("exchange_api", level="ERROR"):
            status, _, body = self.request("DELETE", f"/api/admin/exchange/{resource['id']}", admin=True)
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["imageCleanupPending"])
        self.assertEqual(self.public(), [])

    def test_http_create_reload_login_detail_delete_closed_loop(self):
        import uvicorn
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(self.app, host="127.0.0.1", port=port,
                                             log_level="error", proxy_headers=False))
        thread = Thread(target=lambda: server.run(sockets=[sock]), daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{port}"
        try:
            deadline = monotonic() + 5
            while not server.started and monotonic() < deadline:
                sleep(.02)
            self.assertTrue(server.started)
            response = requests.post(origin + "/api/exchange", data={"payload": json.dumps(self.fields())},
                                     files={"file": ("untrusted-name.webp", image_bytes(), "image/webp")}, timeout=5)
            self.assertEqual(response.status_code, 201, response.text)
            resource = response.json()
            self.assertIn(resource, requests.get(origin + "/api/exchange", timeout=5).json())
            self.assertEqual(requests.get(origin + resource["imageUrl"], timeout=5).status_code, 200)
            with closing(sqlite3.connect(self.root / "test.db")) as connection:
                self.assertEqual(connection.execute("SELECT title FROM exchange_resources WHERE id=?", (resource["id"],)).fetchone()[0], resource["title"])
            self.assertEqual(requests.delete(origin + f"/api/admin/exchange/{resource['id']}", timeout=5).status_code, 401)
            with requests.Session() as admin:
                self.assertEqual(admin.post(origin + "/api/auth/login", json={"username": "exchange-test-admin", "password": "exchange-test-password"}, timeout=5).status_code, 200)
                self.assertEqual(admin.get(origin + f"/api/admin/exchange/{resource['id']}", timeout=5).json(), resource)
                self.assertEqual(admin.delete(origin + f"/api/admin/exchange/{resource['id']}", timeout=5).status_code, 200)
            self.assertEqual(requests.get(origin + "/api/exchange", timeout=5).json(), [])
            self.assertEqual(requests.get(origin + resource["imageUrl"], timeout=5).status_code, 404)
        finally:
            server.should_exit = True
            thread.join(timeout=5)
            sock.close()
            self.assertFalse(thread.is_alive())

    def test_existing_news_endpoints_keep_their_auth_and_payload(self):
        data = {"title": "独立测试新闻", "content": "news content", "is_published": 1}
        headers = {"content-type": "application/json"}
        self.assertEqual(self.request("POST", "/api/news", json.dumps(data).encode(), headers)[0], 401)
        status, _, body = self.request("POST", "/api/news", json.dumps(data).encode(), headers, True)
        self.assertEqual(status, 201)
        news = json.loads(body)
        try:
            self.assertEqual(self.request("GET", f"/api/news/{news['id']}")[0], 200)
            self.assertEqual(self.request("GET", "/api/admin/news", admin=True)[0], 200)
            status, _, body = self.request("PUT", f"/api/news/{news['id']}", json.dumps({**data, "title": "修改测试新闻"}).encode(), headers, True)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["title"], "修改测试新闻")
        finally:
            self.assertEqual(self.request("DELETE", f"/api/news/{news['id']}", admin=True)[0], 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
