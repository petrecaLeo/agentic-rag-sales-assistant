import asyncio

import pytest

from backend.security import SECURITY_HEADERS, SecurityMiddleware

JSON = {"content-type": "application/json", "content-length": "20"}


async def ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b"{}"})


def call(middleware, method="POST", path="/api/chat", headers=None, client="10.0.0.1"):
    scope = {
        "type": "http", "method": method, "path": path, "raw_path": path.encode(), "query_string": b"",
        "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (client, 5000), "server": ("127.0.0.1", 8000), "scheme": "http", "http_version": "1.1", "root_path": "",
    }
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(middleware(scope, receive, send))
    start = sent[0]
    headers = {k.decode().lower(): v.decode() for k, v in start["headers"]}
    body = b"".join(m.get("body", b"") for m in sent[1:])
    return start["status"], headers, body


def test_valid_json_post_passes_and_gets_security_headers():
    status, headers, _ = call(SecurityMiddleware(ok_app), headers=JSON)
    assert status == 200
    for name in SECURITY_HEADERS:
        assert name.lower() in headers


def test_pages_get_security_headers_too():
    status, headers, _ = call(SecurityMiddleware(ok_app), method="GET", path="/")
    assert status == 200
    assert "default-src 'self'" in headers["content-security-policy"]


@pytest.mark.parametrize(
    ("headers", "status"),
    [
        ({"content-type": "text/plain", "content-length": "20"}, 415),
        ({"content-length": "20"}, 415),
        ({"content-type": "application/json"}, 411),
        ({"content-type": "application/json", "content-length": "2000000"}, 413),
        ({"content-type": "application/json", "content-length": "20000"}, 413),
        ({**JSON, "origin": "https://evil.example"}, 403),
    ],
)
def test_rejects_unsafe_posts(headers, status):
    code, _, body = call(SecurityMiddleware(ok_app), headers=headers)
    assert code == status
    assert body.startswith(b'{"code"')


def test_same_site_origin_and_charset_are_fine():
    headers = {**JSON, "content-type": "application/json; charset=utf-8", "origin": "http://localhost:8000"}
    assert call(SecurityMiddleware(ok_app), headers=headers)[0] == 200


def test_rate_limit_is_per_client():
    middleware = SecurityMiddleware(ok_app, rate_limit=3)
    assert [call(middleware, headers=JSON)[0] for _ in range(4)] == [200, 200, 200, 429]
    assert call(middleware, headers=JSON, client="10.0.0.2")[0] == 200
