"""Deny-by-default business/attachment gate and synchronizer-token CSRF."""

import hmac

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from employee_security import get_current_employee

AUTH_PATHS = {"/api/employee/csrf", "/api/employee/login", "/api/employee/me",
              "/api/employee/logout", "/api/employee/password", "/api/auth/login", "/api/auth/logout"}


class PortalAccess:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope, receive)
        path = scope["path"].rstrip("/") or "/"
        protected = path.startswith(("/api/", "/uploads/", "/tools/qstart")) or path in {"/uploads", "/api", "/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
        try:
            if protected and path not in AUTH_PATHS and path != "/api/health":
                get_current_employee(request)
            if path.startswith("/api/") and scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
                # A token is mandatory even for login, logout and multipart forms.
                token = request.headers.get("x-csrf-token", "")
                expected = request.session.get("csrf", "")
                origin = request.headers.get("origin")
                allowed = {str(request.base_url).rstrip("/"), "http://localhost:5173", "http://127.0.0.1:5173"}
                if origin and origin not in allowed:
                    raise HTTPException(403, "请求来源不受信任")
                if not isinstance(expected, str) or not expected or not token or not hmac.compare_digest(token.encode(), expected.encode()):
                    raise HTTPException(403, "CSRF 校验失败，请刷新页面后重试")
        except HTTPException as error:
            return await JSONResponse({"detail": error.detail}, error.status_code,
                                      headers={"Cache-Control": "no-store", **(error.headers or {})})(scope, receive, send)

        async def no_cache(message):
            if message["type"] == "http.response.start" and protected:
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"cache-control"]
                headers.append((b"cache-control", b"private, no-store"))
                message = {**message, "headers": headers}
            await send(message)
        return await self.app(scope, receive, no_cache)
