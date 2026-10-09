import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from backend.config import ALLOWED_HOSTS, MAX_BODY_BYTES, RATE_LIMIT_PER_MINUTE

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

WINDOW_SECONDS = 60


class SecurityMiddleware:
    def __init__(self, app: ASGIApp, rate_limit: int = RATE_LIMIT_PER_MINUTE) -> None:
        self.app = app
        self.rate_limit = rate_limit
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
            await send(message)

        if scope["method"] == "POST" and scope["path"].startswith("/api/"):
            problem = self.reject_reason(scope)
            if problem:
                code, status = problem
                await JSONResponse({"code": code}, status_code=status)(scope, receive, send_with_headers)
                return

        await self.app(scope, receive, send_with_headers)

    def reject_reason(self, scope: Scope) -> tuple[str, int] | None:
        headers = Headers(scope=scope)

        if headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            return "invalid_request", 415
        length = headers.get("content-length", "")
        if not length.isdigit():
            return "invalid_request", 411
        if int(length) > MAX_BODY_BYTES:
            return "invalid_request", 413
        # O navegador manda Origin em todo POST: barra pedidos vindos de outro site.
        origin = headers.get("origin")
        if origin and urlsplit(origin).hostname not in ALLOWED_HOSTS:
            return "forbidden", 403
        client = scope["client"][0] if scope.get("client") else "unknown"
        if self.too_many_requests(client):
            return "rate_limited", 429
        return None

    def too_many_requests(self, client: str) -> bool:
        now = time.monotonic()
        hits = self.hits[client]
        while hits and now - hits[0] > WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self.rate_limit:
            return True
        hits.append(now)
        return False
