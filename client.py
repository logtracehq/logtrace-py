from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .exceptions import LogtraceError
from .types import (
    ApiResponse,
    CreateAuditLogRequest,
    CreateEventRequest,
    CreateSessionRequest,
)

_DEFAULT_BASE_URL = "https://logtracehq.com/v1/developers"
_DEFAULT_TIMEOUT  = 10.0  # seconds


class Client:
    """
    Synchronous Logtrace API client backed by the stdlib ``urllib``.
    No third-party dependencies required.

    Usage::

        client = Client(api_key=os.environ["LOGTRACE_API_KEY"])
        client.create_event(CreateEventRequest(...))
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("logtrace: API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout


    def create_event(self, req: CreateEventRequest) -> ApiResponse:
        return self._post("/events", req.to_dict())

    def create_session(self, req: CreateSessionRequest) -> ApiResponse:
        return self._post("/sessions", req.to_dict())

    def create_audit_log(self, req: CreateAuditLogRequest) -> ApiResponse:
        return self._post("/audit-logs", req.to_dict())


    def _post(self, path: str, body: dict[str, Any]) -> ApiResponse:
        url     = self._base_url + path
        payload = json.dumps(body).encode()

        http_req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key":    self._api_key,
            },
        )

        try:
            with urllib.request.urlopen(http_req, timeout=self._timeout) as resp:
                raw         = resp.read().decode()
                status_code = resp.status
        except urllib.error.HTTPError as exc:
            raw         = exc.read().decode()
            status_code = exc.code
            message     = raw
            try:
                message = json.loads(raw).get("message", raw)
            except json.JSONDecodeError:
                pass
            raise LogtraceError(status_code, message) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"logtrace: request failed: {exc.reason}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("logtrace: failed to parse response") from exc

        return ApiResponse(
            message=data.get("message", ""),
            status_code=status_code,
        )
