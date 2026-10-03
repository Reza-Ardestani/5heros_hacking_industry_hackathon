"""Deployed entrypoint: the API plus the built frontend, behind shared-password Basic auth.

Local development keeps using app.api:app; this module wraps it without modifying it.
Auth is enforced when BB_AUTH_PASSWORD is set. BB_REQUIRE_AUTH=1 (set in the Dockerfile)
refuses to serve anything if the password is missing, so a misconfigured deploy fails closed.
"""

import base64
import binascii
import os
import secrets
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse

from app.api import app as api_app

ROOT = Path(__file__).resolve().parents[2]
API_PREFIXES = ("/api", "/docs", "/redoc", "/openapi.json")
OPEN_PATHS = {"/api/health"}


class BasicAuth:
    def __init__(self, inner, user: str, password: str, required: bool):
        self.inner, self.user, self.password = inner, user, password
        self.enabled = bool(password) or required

    def _authorized(self, header: str) -> bool:
        scheme, _, encoded = header.partition(" ")
        if scheme.lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(encoded, validate=True).decode()
        except (binascii.Error, UnicodeDecodeError):
            return False
        user, _, password = decoded.partition(":")
        # Evaluate both comparisons so timing does not reveal which field was wrong.
        user_ok = secrets.compare_digest(user.encode(), self.user.encode())
        password_ok = secrets.compare_digest(password.encode(), self.password.encode())
        return user_ok and password_ok

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.enabled or scope["path"] in OPEN_PATHS:
            return await self.inner(scope, receive, send)
        if not self.password:
            response = PlainTextResponse("Access password is not configured", status_code=503)
        elif self._authorized(Headers(scope=scope).get("authorization", "")):
            return await self.inner(scope, receive, send)
        else:
            response = PlainTextResponse(
                "Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Bottleneck Busters", charset="UTF-8"'},
            )
        await response(scope, receive, send)


def with_frontend(api, dist: Path):
    """Route API paths (and lifespan events) to the API; everything else to the built SPA."""
    if not dist.is_dir():
        return api
    static = StaticFiles(directory=dist, html=True)

    async def router(scope, receive, send):
        if scope["type"] == "http" and not scope["path"].startswith(API_PREFIXES):
            return await static(scope, receive, send)
        return await api(scope, receive, send)

    return router


app = BasicAuth(
    with_frontend(api_app, Path(os.environ.get("BB_FRONTEND_DIST", ROOT / "frontend" / "dist"))),
    user=os.environ.get("BB_AUTH_USER", "bottleneck"),
    password=os.environ.get("BB_AUTH_PASSWORD", ""),
    required=os.environ.get("BB_REQUIRE_AUTH") == "1",
)
