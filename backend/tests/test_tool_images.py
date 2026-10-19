"""Tool editor regression tests: temporary database/uploads and real cookie auth only."""

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
from test_section_visuals import call_app, image_bytes


class ToolImageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="ai-portal-tool-images-")
        cls.root = Path(cls.temp.name)
        cls.env = patch.dict(os.environ, {
            "DATABASE_PATH": str(cls.root / "test.db"),
            "SESSION_SECRET": "tool-image-tests-only-not-production",
            "SESSION_COOKIE_SECURE": "false",
            "ADMIN_USERNAME": "tool-test-admin", "ADMIN_PASSWORD": "tool-test-password",
        })
        cls.env.start()
        import database
        import upload_api
        cls.db_patch = patch.object(database, "DATABASE_PATH", cls.root / "test.db")
        cls.upload_patch = patch.object(upload_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.db_patch.start()
        cls.upload_patch.start()
        import main
        import tools_api
        cls.tool_patch = patch.object(tools_api, "UPLOAD_ROOT", cls.root / "uploads")
        cls.tool_patch.start()
        cls.database, cls.tools_api, cls.app = database, tools_api, main.app
        status, headers, _ = cls.request("POST", "/api/auth/login", json.dumps({
            "username": "tool-test-admin", "password": "tool-test-password",
        }).encode(), {"content-type": "application/json"})
        assert status == 200
        cookies = SimpleCookie()
        cookies.load(headers[b"set-cookie"].decode())
        cls.cookie = "; ".join(f"{key}={value.value}" for key, value in cookies.items())

    @classmethod
    def tearDownClass(cls):
        cls.tool_patch.stop()
        cls.upload_patch.stop()
        cls.db_patch.stop()
        cls.env.stop()
        cls.temp.cleanup()

    @classmethod
    def request(cls, method, path, body=b"", headers=None, admin=False):
        headers = dict(headers or {})
        if admin:
            headers["cookie"] = cls.cookie
        return asyncio.run(call_app(cls.app, method, path, body, headers))

    def setUp(self):
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("DELETE FROM tools")

    def editor(self, tool_id=None, content=None, mime="image/webp", payload=None, admin=True):
        payload = {"title": "工具示例", "description": "完整说明\n  保留换行和空格  ",
                   "status": "available", "actionType": "route", "actionTarget": "/tools"} if payload is None else payload
        files = None if content is None else {"file": ("../../untrusted.webp", content, mime)}
        prepared = requests.Request("POST", "http://testserver", data={"payload": json.dumps(payload)}, files=files).prepare()
        return self.request("POST" if tool_id is None else "PUT",
                            "/api/admin/tools" + ("" if tool_id is None else f"/{tool_id}"),
                            prepared.body.encode() if isinstance(prepared.body, str) else prepared.body,
                            {"content-type": prepared.headers["Content-Type"]}, admin)

    def row(self, tool_id):
        status, _, body = self.request("GET", f"/api/tools/{tool_id}")
        self.assertEqual(status, 200)
        return json.loads(body)

    def create(self, with_image=True, **fields):
        status, _, body = self.editor(content=image_bytes(size=(800, 400)) if with_image else None,
                                     payload={"title": "工具示例", **fields})
        self.assertEqual(status, 201, body)
        return json.loads(body)

    def test_real_auth_rejects_anonymous_and_inactive_admin(self):
        self.assertEqual(self.editor(content=image_bytes(), admin=False)[0], 401)
        self.assertEqual(self.request("GET", "/api/tools")[2], b"[]")
        first = self.create()
        self.assertEqual(self.editor(first["id"], content=image_bytes(), admin=False)[0], 401)
        self.assertEqual(self.editor(first["id"], payload={"title": "x", "removeImage": True}, admin=False)[0], 401)
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("UPDATE admins SET is_active=0")
        try:
            self.assertEqual(self.editor(first["id"], content=image_bytes())[0], 401)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("UPDATE admins SET is_active=1")
        self.assertEqual(self.row(first["id"]), first)

    def test_create_update_clear_and_public_static_access(self):
        first = self.create(description="第一行\n  第二行  ", icon="QS", status="available",
                            actionType="static", actionTarget="/tools/qstart/index.html", sortOrder=7)
        other = self.create(title="其他工具", sortOrder=1)
        self.assertEqual(first["description"], "第一行\n  第二行  ")
        self.assertRegex(first["coverImageUrl"], r"^/uploads/tools/[a-f0-9]{32}\.webp$")
        self.assertEqual(first["icon"], "QS")
        path = self.root / first["coverImageUrl"].lstrip("/")
        self.assertTrue(path.is_file())
        status, headers, body = self.request("GET", first["coverImageUrl"])
        self.assertEqual(status, 200)
        self.assertIn(b"image/webp", headers[b"content-type"])
        with Image.open(BytesIO(body)) as decoded:
            self.assertEqual(decoded.format, "WEBP")
            decoded.load()
        status, _, body = self.editor(first["id"], content=image_bytes("PNG", (300, 200)), mime="image/png",
                                     payload={"title": "新名称", "description": "  新说明\n完整保存  ",
                                              "status": "available", "actionType": "static",
                                              "actionTarget": "/tools/qstart/index.html", "sortOrder": 7})
        self.assertEqual(status, 200, body)
        updated = json.loads(body)
        self.assertNotEqual(updated["coverImageUrl"], first["coverImageUrl"])
        self.assertEqual(updated["icon"], "QS")
        self.assertEqual(updated["description"], "  新说明\n完整保存  ")
        self.assertEqual(self.row(other["id"]), other)
        self.assertTrue(path.is_file())  # Replacing/clearing never deletes historical media.
        self.assertEqual(self.editor(first["id"], payload={"title": "新名称", "removeImage": True})[0], 200)
        self.assertEqual(self.row(first["id"])["coverImageUrl"], "")
        self.assertEqual(self.row(other["id"]), other)

    def test_legacy_json_updates_preserve_cover_and_all_list_ordering(self):
        first = self.create(sortOrder=8)
        second = self.create(sortOrder=2)
        payload = {"title": "旧客户端编辑", "sortOrder": 8, "isActive": 1}
        result = self.request("PUT", f"/api/tools/{first['id']}", json.dumps(payload).encode(),
                              {"content-type": "application/json"}, True)
        self.assertEqual(result[0], 200)
        self.assertEqual(json.loads(result[2])["coverImageUrl"], first["coverImageUrl"])
        items = json.loads(self.request("GET", "/api/tools")[2])
        self.assertEqual([item["id"] for item in items], [second["id"], first["id"]])

    def test_invalid_images_and_fields_never_replace_old_data(self):
        existing = self.create()
        animated = BytesIO()
        with Image.new("RGB", (40, 40), "red") as a, Image.new("RGB", (40, 40), "blue") as b:
            a.save(animated, format="WEBP", save_all=True, append_images=[b], duration=100, loop=0)
        invalid = [
            (b"not an image", "image/webp"),
            (image_bytes("PNG"), "image/jpeg"),
            (image_bytes()[:15], "image/webp"),
            (b"x" * (5 * 1024 * 1024 + 1), "image/webp"),
            (image_bytes("GIF"), "image/gif"),
            (animated.getvalue(), "image/webp"),
            (image_bytes("PNG", (8193, 1)), "image/png"),
            (image_bytes("PNG", (4001, 4000)), "image/png"),
        ]
        for content, mime in invalid:
            with self.subTest(mime=mime, length=len(content)):
                self.assertEqual(self.editor(existing["id"], content, mime)[0], 400)
                self.assertEqual(self.row(existing["id"]), existing)
        self.assertEqual(self.editor(existing["id"], payload={"title": " "})[0], 422)
        self.assertEqual(self.editor(existing["id"], payload={"title": "a" * 201})[0], 422)
        self.assertEqual(self.editor(existing["id"], payload={"title": "x", "description": "a" * 1001})[0], 422)
        self.assertEqual(self.editor(existing["id"], image_bytes(), payload={"title": "x", "removeImage": True})[0], 422)
        self.assertEqual(self.row(existing["id"]), existing)

    def test_jpeg_png_webp_and_metadata_cleaning(self):
        for fmt, mime in [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")]:
            status, _, body = self.editor(content=image_bytes(fmt, (200, 100)) + b"untrusted trailing payload", mime=mime)
            self.assertEqual(status, 201, body)
            data = json.loads(body)
            saved = (self.root / data["coverImageUrl"].lstrip("/")).read_bytes()
            self.assertNotIn(b"untrusted trailing payload", saved)

    def test_atomic_failure_rolls_back_text_and_new_file(self):
        first = self.create()
        files_before = set((self.root / "uploads" / "tools").iterdir())
        with closing(self.database.get_db_connection()) as connection, connection:
            connection.execute("CREATE TRIGGER fail_tool_cover BEFORE UPDATE OF cover_image_url ON tools "
                               "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END")
        try:
            with self.assertLogs("tools_api", level="ERROR"):
                self.assertEqual(self.editor(first["id"], image_bytes(), payload={"title": "不应保存"})[0], 500)
                self.assertEqual(self.editor(content=image_bytes())[0], 500)
        finally:
            with closing(self.database.get_db_connection()) as connection, connection:
                connection.execute("DROP TRIGGER fail_tool_cover")
        self.assertEqual(self.row(first["id"]), first)
        self.assertEqual(set((self.root / "uploads" / "tools").iterdir()), files_before)
        self.assertEqual(len(json.loads(self.request("GET", "/api/tools")[2])), 1)

    def test_disk_failure_and_unknown_tool_do_not_mutate(self):
        first = self.create()
        blocked = self.root / "not-a-directory"
        blocked.touch()
        with patch.object(self.tools_api, "UPLOAD_ROOT", blocked):
            with self.assertLogs("tools_api", level="ERROR"):
                self.assertEqual(self.editor(first["id"], image_bytes())[0], 500)
        self.assertEqual(self.row(first["id"]), first)
        self.assertEqual(self.editor(999999, image_bytes())[0], 404)

    def test_legacy_and_fresh_database_migration_is_idempotent(self):
        legacy = self.root / "legacy.db"
        with closing(sqlite3.connect(legacy)) as connection, connection:
            connection.execute("CREATE TABLE tools (id INTEGER PRIMARY KEY, icon TEXT, title TEXT, "
                               "description TEXT, status TEXT, action_type TEXT, action_target TEXT, "
                               "button_text TEXT, sort_order INTEGER, is_active INTEGER, created_at TEXT)")
            connection.execute("INSERT INTO tools VALUES (42,'QS','legacy','body','available','route','/tools','open',9,1,'old')")
            before = connection.execute("SELECT * FROM tools").fetchone()
        with patch.object(self.database, "DATABASE_PATH", legacy):
            self.database.init_database()
            with closing(self.database.get_db_connection()) as connection, connection:
                self.assertEqual(tuple(connection.execute("SELECT * FROM tools").fetchone())[:-1], before)
                connection.execute("UPDATE tools SET cover_image_url='/uploads/tools/existing.webp'")
            self.database.init_database()
            with closing(self.database.get_db_connection()) as connection:
                self.assertEqual(connection.execute("SELECT cover_image_url FROM tools").fetchone()[0], '/uploads/tools/existing.webp')
        fresh = self.root / "fresh.db"
        with patch.object(self.database, "DATABASE_PATH", fresh):
            self.database.init_database()
            self.database.init_database()
            with closing(self.database.get_db_connection()) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM tools").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
