"""Real TCP import/restart persistence smoke test; independent temporary DB/uploads."""

from contextlib import closing
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_projects import workbook_bytes


def serve(root, port):
    os.environ.update({"DATABASE_PATH": str(root / "http.db"), "SESSION_SECRET": "http-project-test-only",
                       "ADMIN_USERNAME": "http-test", "ADMIN_PASSWORD": "http-test-only-password",
                       "SESSION_COOKIE_SECURE": "false"})
    import upload_api
    upload_api.UPLOAD_ROOT = root / "uploads"
    from main import app
    from auth_support import seed_employee
    seed_employee()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


class ProjectHTTPTest(unittest.TestCase):
    def test_import_restart_repeat_and_protected_reads(self):
        with tempfile.TemporaryDirectory(prefix="ai-portal-project-http-") as directory:
            root = Path(directory)
            with closing(socket.socket()) as probe:
                probe.bind(("127.0.0.1", 0))
                port = probe.getsockname()[1]
            origin = f"http://127.0.0.1:{port}"
            processes = []

            def start():
                child = subprocess.Popen([sys.executable, __file__, "--serve", str(root), str(port)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                processes.append(child)
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if child.poll() is not None:
                        self.fail("Isolated HTTP test server exited")
                    try:
                        if requests.get(origin + "/api/health", timeout=.5).status_code == 200:
                            return child
                    except requests.RequestException:
                        pass
                    time.sleep(.05)
                self.fail("Isolated HTTP test server did not become ready")

            try:
                first = start()
                with requests.Session() as session:
                    self.assertEqual(session.get(origin + "/api/admin/projects", timeout=5).status_code, 401)
                    from auth_support import http_employee_login
                    http_employee_login(session, origin)
                    login = session.post(origin + "/api/auth/login", json={"username": "http-test", "password": "http-test-only-password"}, timeout=5)
                    self.assertEqual(login.status_code, 200)
                    session.headers['X-CSRF-Token'] = login.json()['csrfToken']
                    def preview():
                        response = session.post(origin + "/api/admin/projects/imports/preview", files={"file": (
                            "sample.xlsx", workbook_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}, timeout=10)
                        self.assertEqual(response.status_code, 200, response.text)
                        return response.json()
                    batch = preview()
                    self.assertTrue(batch["canConfirm"])
                    confirmed = session.post(origin + "/api/admin/projects/imports/confirm", json={"token": batch["token"]}, timeout=5)
                    self.assertEqual(confirmed.status_code, 200)
                    first.terminate()
                    first.wait(timeout=10)
                    start()
                    response = session.get(origin + "/api/admin/projects", headers={"Origin": "http://127.0.0.1:5173"}, timeout=5)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.headers.get("access-control-allow-origin"), "http://127.0.0.1:5173")
                    data = response.json()
                    self.assertEqual(data["summary"], {"total": 1, "priority": 1, "coordination": 0, "operational": 0})
                    detail = session.get(origin + f"/api/admin/projects/{data['projects'][0]['id']}", timeout=5).json()
                    self.assertEqual(detail["completedCount"], 3)
                    self.assertEqual(detail["currentStage"], "商务洽谈")
                    repeated = preview()
                    self.assertEqual(repeated["counts"]["new"], 0)
                    self.assertEqual(repeated["counts"]["unchanged"], 1)
                    self.assertEqual(session.post(origin + "/api/admin/projects/imports/confirm", json={"token": repeated["token"]}, timeout=5).status_code, 200)
                    self.assertEqual(session.get(origin + "/api/admin/projects", timeout=5).json()["summary"]["total"], 1)
            finally:
                for child in processes:
                    if child.poll() is None:
                        child.terminate()
                        child.wait(timeout=10)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        serve(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        unittest.main(verbosity=2)
