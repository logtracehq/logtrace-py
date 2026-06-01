from __future__ import annotations

from contextvars import copy_context
from typing import Any, Callable, Iterable

from .context import RequestClient, _request_client_var
from .types import RequestDetails


# ─── Shared helpers ───────────────────────────────────────────────────────────

def real_ip(environ: dict[str, Any]) -> str:
    """Resolve client IP from common proxy headers, then REMOTE_ADDR."""
    for key in ("HTTP_CF_CONNECTING_IP", "HTTP_X_REAL_IP"):
        if ip := environ.get(key, ""):
            return ip
    if xff := environ.get("HTTP_X_FORWARDED_FOR", ""):
        return xff.split(",")[0].strip()
    return environ.get("REMOTE_ADDR", "")


def operating_system(user_agent: str) -> str:
    ua = user_agent.lower()
    if "curl"                              in ua: return "Unknown (curl)"
    if "windows"                           in ua: return "Windows"
    if "mac os" in ua or "macintosh" in ua or "darwin" in ua: return "macOS"
    if "android"                           in ua: return "Android"
    if "iphone" in ua or "ipad" in ua or "ios" in ua: return "iOS"
    if "linux"                             in ua: return "Linux"
    if "cros"                              in ua: return "Chrome OS"
    return "Unknown"


def _headers_from_environ(environ: dict[str, Any]) -> dict[str, str]:
    """Extract HTTP request headers from a WSGI environ dict."""
    headers: dict[str, str] = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].replace("_", "-").title()
            headers[name] = value
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH") and value:
            headers[key.replace("_", "-").title()] = value
    return headers


# ─── WSGI middleware ──────────────────────────────────────────────────────────

class WsgiMiddleware:
    """
    WSGI middleware compatible with Flask, Django, Falcon, and any other
    WSGI framework.

    **Flask example**::

        from logtrace_py import Client
        from logtrace_py.middleware import WsgiMiddleware

        client = Client(api_key=os.environ["LOGTRACE_API_KEY"])
        app.wsgi_app = WsgiMiddleware(app.wsgi_app, client)

    **Django example** (``settings.py``)::

        MIDDLEWARE = [
            "logtrace_py.middleware.DjangoMiddleware",
            ...
        ]

    Then inside any view::

        from logtrace_py import from_context
        rc = from_context(client)
        rc.create_event(CreateEventRequest(...))
    """

    def __init__(self, app: Callable, client: Any) -> None:
        self._app    = app
        self._client = client

    def __call__(
        self,
        environ: dict[str, Any],
        start_response: Callable,
    ) -> Iterable[bytes]:
        user_agent = environ.get("HTTP_USER_AGENT", "")
        status_ref = {"code": 200}

        def capturing_start_response(status: str, headers: list, exc_info=None):
            status_ref["code"] = int(status.split(" ", 1)[0])
            return start_response(status, headers, exc_info)

        rc = RequestClient(
            client=self._client,
            method=environ.get("REQUEST_METHOD", ""),
            endpoint=environ.get("PATH_INFO", ""),
            client_ip=real_ip(environ),
            user_agent=user_agent,
            operating_system=operating_system(user_agent),
            get_status=lambda: status_ref["code"],
        )

        # Run app inside a copied context with rc bound, then capture headers.
        ctx = copy_context()

        def run() -> Iterable[bytes]:
            _request_client_var.set(rc)
            result = self._app(environ, capturing_start_response)
            rc.headers = _headers_from_environ(environ)
            return result

        return ctx.run(run)


# ─── Django-style class-based middleware ──────────────────────────────────────

class DjangoMiddleware:
    """
    Drop-in Django middleware. Add ``"logtrace_py.middleware.DjangoMiddleware"``
    to ``MIDDLEWARE`` in ``settings.py``.

    Requires a ``LOGTRACE_CLIENT`` setting pointing to a ``Client`` instance::

        # settings.py
        import logtrace_py
        LOGTRACE_CLIENT = logtrace_py.Client(api_key=os.environ["LOGTRACE_API_KEY"])
    """

    def __init__(self, get_response: Callable) -> None:
        from django.conf import settings  # type: ignore[import]
        self._get_response = get_response
        self._client = settings.LOGTRACE_CLIENT

    def __call__(self, request: Any) -> Any:
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        status_ref = {"code": 200}

        rc = RequestClient(
            client=self._client,
            method=request.method,
            endpoint=request.path,
            client_ip=self._real_ip_django(request),
            user_agent=user_agent,
            operating_system=operating_system(user_agent),
            get_status=lambda: status_ref["code"],
        )

        ctx = copy_context()

        def run() -> Any:
            _request_client_var.set(rc)
            response = self._get_response(request)
            status_ref["code"] = response.status_code
            rc.headers = {k: v for k, v in request.headers.items()}
            return response

        return ctx.run(run)

    @staticmethod
    def _real_ip_django(request: Any) -> str:
        for attr in ("HTTP_CF_CONNECTING_IP", "HTTP_X_REAL_IP"):
            if ip := request.META.get(attr, ""):
                return ip
        if xff := request.META.get("HTTP_X_FORWARDED_FOR", ""):
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


# ─── ASGI middleware ──────────────────────────────────────────────────────────

class AsgiMiddleware:
    """
    ASGI middleware compatible with FastAPI, Starlette, Django Channels, etc.

    **FastAPI / Starlette example**::

        from logtrace_py.middleware import AsgiMiddleware
        app.add_middleware(AsgiMiddleware, client=client)

    Inside any route::

        from logtrace_py import from_context
        rc = from_context(client)
        await rc.async_create_event(CreateEventRequest(...))
    """

    def __init__(self, app: Callable, client: Any) -> None:
        self._app    = app
        self._client = client

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable,
        send: Callable,
    ) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self._app(scope, receive, send)
            return

        headers_raw: dict[str, str] = {
            k.decode(): v.decode()
            for k, v in scope.get("headers", [])
        }
        user_agent = headers_raw.get("user-agent", "")
        status_ref = {"code": 200}

        async def capturing_send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_ref["code"] = message["status"]
            await send(message)

        rc = RequestClient(
            client=self._client,
            method=scope.get("method", ""),
            endpoint=scope.get("path", ""),
            client_ip=self._real_ip_asgi(scope, headers_raw),
            user_agent=user_agent,
            operating_system=operating_system(user_agent),
            get_status=lambda: status_ref["code"],
            headers=headers_raw,
        )

        token = _request_client_var.set(rc)
        try:
            await self._app(scope, receive, capturing_send)
        finally:
            _request_client_var.reset(token)

    @staticmethod
    def _real_ip_asgi(scope: dict[str, Any], headers: dict[str, str]) -> str:
        for h in ("cf-connecting-ip", "x-real-ip"):
            if ip := headers.get(h, ""):
                return ip
        if xff := headers.get("x-forwarded-for", ""):
            return xff.split(",")[0].strip()
        client = scope.get("client")
        return client[0] if client else ""
