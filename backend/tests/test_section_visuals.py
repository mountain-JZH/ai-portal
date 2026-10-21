"""Run: backend/.venv/Scripts/python.exe backend/tests/test_section_visuals.py.

Uses only a temporary SQLite database and temporary uploads. No real server,
production database, admin credentials or user images are used.
"""

import asyncio
from contextlib import closing
from http.cookies import SimpleCookie
from io import BytesIO
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def call_app(app, method, path, body=b"", headers=None):
    messages = []
    delivered = False

    async def receive():
        nonlocal delivered
        if not delivered:
            delivered = True
            return {"type": "http.request", "body": body, "more_body": False}
        # Keep the request connected while Starlette streams static files.
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1", "method": method, "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "root_path": "", "server": ("testserver", 80), "client": ("127.0.0.1", 1234),
        "headers": [(key.lower().encode(), value.encode()) for key, value in (headers or {}).items()],
    }
    await app(scope, receive, send)
    start = next(item for item in messages if item["type"] == "http.response.start")
    payload = b"".join(item.get("body", b"") for item in messages if item["type"] == "http.response.body")
    return start["status"], dict(start["headers"]), payload


def image_bytes(fmt="WEBP", size=(600, 64)):
    with Image.new("RGB", size, "#708090") as image:
        buffer = BytesIO()
        image.save(buffer, format=fmt)
        return buffer.getvalue()


class SectionVisualsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="ai-portal-sections-")
        cls.root = Path(cls.temp.name)
        cls.environment = patch.dict(os.environ, {
            "DATABASE_PATH": str(cls.root / "test.db"),
            "SESSION_SECRET": "isolated-test-only-not-a-production-secret",
            "SESSION_COOKIE_SECURE": "false",
            "ADMIN_USERNAME": "section-test-admin", "ADMIN_PASSWORD": "section-test-password",
        })
        cls.environment.start()
        import database
        import upload_api
        # Override before main import, including its StaticFiles mount.
        cls.database_patch = patch.object(database, "DATABASE_PATH", cls.root / "test.db")
        cls.database_patch.start()
        cls.upload_patch = patch.object(upload_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.upload_patch.start()
        import main
        import section_visuals_api
        cls.section_upload_patch = patch.object(section_visuals_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.section_upload_patch.start()
        cls.app = main.app
        cls.database = database
        from auth_support import employee_session
        cls.employee_cookie, cls.csrf = employee_session(cls.app, call_app)
        status, headers, login_result = cls.request("POST", "/api/auth/login", body=json.dumps({
            "username": "section-test-admin", "password": "section-test-password",
        }).encode(), headers={"content-type": "application/json"})
        assert status == 200, status
        cookie = SimpleCookie()
        cookie.load(headers.get(b"set-cookie", cls.employee_cookie.encode()).decode())
        cls.cookie = "; ".join(f"{key}={value.value}" for key, value in cookie.items())
        cls.admin_csrf = json.loads(login_result)['csrfToken']
        cls.employee_cookie, cls.csrf = employee_session(cls.app, call_app)

    @classmethod
    def tearDownClass(cls):
        cls.section_upload_patch.stop()
        cls.upload_patch.stop()
        cls.database_patch.stop()
        cls.environment.stop()
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, body=b"", headers=None, admin=False):
        merged = {"cookie": cls.employee_cookie, "x-csrf-token": cls.csrf, **(headers or {})}
        if admin:
            merged["cookie"] = cls.cookie
            merged["x-csrf-token"] = cls.admin_csrf
        return asyncio.run(call_app(cls.app, method, path, body, merged))

    def upload(self, content=None, mime="image/webp", key="home_news", admin=True, text_mode=None):
        prepared = requests.Request("PUT", "http://testserver", files={
            "file": ("../../untrusted-name.webp", image_bytes() if content is None else content, mime),
        }, data={} if text_mode is None else {"textMode": text_mode}).prepare()
        return self.request("PUT", f"/api/admin/section-visuals/{key}", prepared.body,
                            {"content-type": prepared.headers["Content-Type"]}, admin)

    def setUp(self):
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("DELETE FROM section_visuals")

    def update_mode(self, key="home_news", mode="light", admin=True):
        return self.request("PATCH", f"/api/admin/section-visuals/{key}",
                            json.dumps({"textMode": mode}).encode(),
                            {"content-type": "application/json"}, admin)

    def test_color_only_save_and_upload_compatibility(self):
        defaults = json.loads(self.request("GET", "/api/section-visuals")[2])
        self.assertEqual([item["textMode"] for item in defaults], ["dark", "dark"])
        # Can save a colour even when still using the bundled background.
        self.assertEqual(self.update_mode()[0], 200)
        self.assertEqual(json.loads(self.update_mode()[2])["image"], "")
        first = json.loads(self.upload()[2])
        self.assertEqual(first["textMode"], "light")
        files_before = set((self.root / "uploads" / "sections").iterdir())
        changed = json.loads(self.update_mode(mode="dark")[2])
        self.assertEqual(changed["image"], first["image"])
        self.assertEqual(changed["textMode"], "dark")
        self.assertEqual(files_before, set((self.root / "uploads" / "sections").iterdir()))
        self.assertEqual(self.update_mode()[0], 200)
        self.assertEqual(json.loads(self.upload()[2])["textMode"], "light")
        self.assertEqual(json.loads(self.upload(text_mode="dark")[2])["textMode"], "dark")
        self.assertEqual(json.loads(self.upload(key="home_tools", text_mode="light")[2])["textMode"], "light")
        public = json.loads(self.request("GET", "/api/section-visuals")[2])
        self.assertEqual([item["textMode"] for item in public], ["dark", "light"])
        self.database.init_database()
        self.assertEqual(public, json.loads(self.request("GET", "/api/section-visuals")[2]))

    def test_color_validation_auth_and_failed_save(self):
        self.upload(text_mode="light")
        before = self.request("GET", "/api/section-visuals")[2]
        self.assertEqual(self.update_mode(admin=False)[0], 403)
        self.assertEqual(self.update_mode(key="unknown")[0], 400)
        for invalid in ["blue", "", None, 1, ["light"]]:
            self.assertEqual(self.update_mode(mode=invalid)[0], 422)
        self.assertEqual(self.upload(text_mode="invalid")[0], 422)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("""
                CREATE TRIGGER fail_color_update BEFORE UPDATE ON section_visuals
                BEGIN SELECT RAISE(ABORT, 'simulated failure'); END
            """)
        try:
            with self.assertLogs("section_visuals_api", level="ERROR"):
                self.assertEqual(self.update_mode(mode="dark")[0], 500)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("DROP TRIGGER fail_color_update")
        self.assertEqual(before, self.request("GET", "/api/section-visuals")[2])

    def test_legacy_schema_migration_keeps_images_and_timestamps(self):
        legacy = self.root / "legacy.db"
        with closing(sqlite3.connect(legacy)) as connection, connection:
            connection.execute("""
                CREATE TABLE section_visuals (
                    section_key TEXT PRIMARY KEY NOT NULL,
                    image_path TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.execute("INSERT INTO section_visuals VALUES ('home_news', '/uploads/sections/old.webp', '2026-01-01')")
        with patch.object(self.database, "DATABASE_PATH", legacy):
            self.database.init_database()
            self.database.init_database()
            from auth_support import employee_session
            cookie, csrf = employee_session(self.app, call_app)
            row = json.loads(self.request("GET", "/api/section-visuals", headers={"cookie": cookie, "x-csrf-token": csrf})[2])[0]
            self.assertEqual(row["textMode"], "dark")
            self.assertEqual(row["image"], "/uploads/sections/old.webp")
            self.assertEqual(row["updatedAt"], "2026-01-01")
            with closing(self.database.get_db_connection()) as connection, connection:
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE section_visuals SET text_mode='invalid'")

    def test_fresh_and_idempotent_migration(self):
        self.database.init_database()
        with closing(self.database.get_db_connection()) as connection, connection:
            names = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"news", "banners", "announcements", "tools", "section_visuals"} <= names)
        status, _, body = self.request("GET", "/api/section-visuals")
        self.assertEqual(status, 200)
        self.assertEqual([item["image"] for item in json.loads(body)], ["", ""])
        saved = json.loads(self.upload()[2])
        with closing(self.database.get_db_connection()) as connection, connection:
            before = {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
                      for table in ["news", "banners", "announcements", "tools", "admins"]}
        self.database.init_database()
        self.database.init_database()
        self.assertEqual(json.loads(self.request("GET", "/api/section-visuals")[2])[0]["image"], saved["image"])
        with closing(self.database.get_db_connection()) as connection, connection:
            after = {table: [tuple(row) for row in connection.execute(f"SELECT * FROM {table}")]
                     for table in before}
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO section_visuals(section_key,image_path) VALUES ('other','bad')")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("INSERT INTO section_visuals(section_key,image_path) VALUES (NULL,'bad')")
        self.assertEqual(before, after)

    def test_authentication(self):
        self.assertEqual(self.upload(admin=False)[0], 403)
        self.assertEqual(self.request("GET", "/api/admin/section-visuals")[0], 403)
        self.assertEqual(self.request("GET", "/api/admin/section-visuals", admin=True)[0], 200)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE admins SET is_active=0 WHERE username='section-test-admin'")
        try:
            self.assertEqual(self.upload()[0], 401)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("UPDATE admins SET is_active=1 WHERE username='section-test-admin'")

    def test_replacement_independence_and_static_access(self):
        first = self.upload()
        self.assertEqual(first[0], 200)
        first_image = json.loads(first[2])["image"]
        tools = self.upload(key="home_tools")
        self.assertEqual(tools[0], 200)
        second_image = json.loads(self.upload()[2])["image"]
        self.assertNotEqual(first_image, second_image)
        self.assertTrue((self.root / first_image.lstrip('/')).is_file())
        public = json.loads(self.request("GET", "/api/section-visuals")[2])
        self.assertEqual(public[0]["image"], second_image)
        self.assertEqual(public[1]["image"], json.loads(tools[2])["image"])
        status, headers, data = self.request("GET", second_image)
        self.assertEqual(status, 200)
        self.assertEqual(headers[b"content-type"], b"image/webp")
        with Image.open(BytesIO(data)) as image:
            image.load()
            self.assertEqual(image.size, (600, 64))

    def test_invalid_and_corrupt_files_preserve_configuration(self):
        self.upload()
        before = self.request("GET", "/api/section-visuals")[2]
        cases = [
            (b"not an image", "image/webp"),
            (b"<svg></svg>", "image/svg+xml"),
            (image_bytes("PNG"), "image/jpeg"),
            (image_bytes("PNG")[:40], "image/png"),
            (image_bytes("JPEG")[:100], "image/jpeg"),
            (image_bytes()[:30], "image/webp"),
            (b"x" * (5 * 1024 * 1024 + 1), "image/webp"),
            (b"", "image/webp"),
            (image_bytes("PNG", (8193, 1)), "image/png"),
            (image_bytes("PNG", (4001, 4000)), "image/png"),
        ]
        for content, mime in cases:
            with self.subTest(size=len(content), mime=mime):
                self.assertEqual(self.upload(content, mime)[0], 400)
                self.assertEqual(before, self.request("GET", "/api/section-visuals")[2])
        self.assertEqual(self.upload(key="not-a-slot")[0], 400)
        self.assertIn(self.upload(key="..%2Fnews")[0], {400, 404})
        self.assertEqual(self.request("PUT", "/api/admin/section-visuals/home_news", admin=True)[0], 422)

    def test_supported_formats_alpha_and_metadata_cleanup(self):
        for fmt, mime in [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]:
            self.assertEqual(self.upload(image_bytes(fmt), mime)[0], 200)
        with Image.new("RGBA", (600, 64), (255, 10, 10, 0)) as image:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
        status, _, response = self.upload(buffer.getvalue() + b"untrusted trailing data", "image/png")
        self.assertEqual(status, 200)
        data = self.request("GET", json.loads(response)["image"])[2]
        self.assertNotIn(b"untrusted trailing data", data)
        with Image.open(BytesIO(data)) as decoded:
            self.assertEqual(decoded.getpixel((0, 0))[3], 0)

    def test_storage_failure_preserves_configuration(self):
        import section_visuals_api
        self.upload()
        before = self.request("GET", "/api/section-visuals")[2]
        blocked = self.root / "not-a-directory"
        blocked.touch()
        with patch.object(section_visuals_api, "UPLOAD_ROOT", blocked):
            with self.assertLogs("section_visuals_api", level="ERROR"):
                self.assertEqual(self.upload()[0], 500)
        self.assertEqual(before, self.request("GET", "/api/section-visuals")[2])

    def test_database_failure_preserves_old_config_and_files(self):
        self.upload()
        before = self.request("GET", "/api/section-visuals")[2]
        previous_file = self.root / json.loads(before)[0]["image"].lstrip('/')
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("""
                CREATE TRIGGER fail_section_update BEFORE UPDATE ON section_visuals
                BEGIN SELECT RAISE(ABORT, 'simulated storage failure'); END
            """)
        try:
            with self.assertLogs("section_visuals_api", level="ERROR"):
                self.assertEqual(self.upload()[0], 500)
            self.assertEqual(before, self.request("GET", "/api/section-visuals")[2])
            self.assertTrue(previous_file.is_file())
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("DROP TRIGGER fail_section_update")

    def test_bomb_warning_and_animated_image_rejected(self):
        with patch.object(Image, "MAX_IMAGE_PIXELS", 1000):
            self.assertEqual(self.upload()[0], 400)
        buffer = BytesIO()
        with Image.new("RGB", (600, 64), "red") as first, Image.new("RGB", (600, 64), "blue") as second:
            first.save(buffer, format="WEBP", save_all=True, append_images=[second], duration=100)
        self.assertEqual(self.upload(buffer.getvalue())[0], 400)

    def test_banner_endpoints_still_available(self):
        self.assertEqual(self.request("GET", "/api/banners")[0], 200)
        self.assertEqual(self.request("GET", "/api/admin/banners", admin=True)[0], 200)
        self.assertEqual(self.request("GET", "/api/admin/banners")[0], 403)


if __name__ == "__main__":
    unittest.main(verbosity=2)
