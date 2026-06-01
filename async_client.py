
from __future__ import annotations

import asyncio
import json
from typing import Any

from .exceptions import LogtraceError
from .types import (
    ApiResponse,
    CreateAuditLogRequest,
    CreateEventRequest,
    CreateSessionRequest,
)

_DEFAULT_BASE_URL = "https://logtracehq.com/v1/developers"
_DEFAULT_TIMEOUT  = 10.0


class AsyncClient:
    """
    Async Logtrace API client using ``asyncio`` streams — no third-party
    dependencies required.

    Usage::

        async with AsyncClient(api_key=os.environ["LOGTRACE_API_KEY"]) as client:
            await client.create_event(CreateEventRequest(...))

    Or without the context manager::

        client = AsyncClient(api_key=os.environ["LOGTRACE_API_KEY"])
        await client.create_event(...)
        await client.close()
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("logtrace: API key is required")
        self._api_key  = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout  = timeout

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def close(self) -> None:
        """No persistent connections to clean up; kept for API symmetry."""

    async def create_event(self, req: CreateEventRequest) -> ApiResponse:
        return await self._post("/events", req.to_dict())

    async def create_session(self, req: CreateSessionRequest) -> ApiResponse:
        return await self._post("/sessions", req.to_dict())

    async def create_audit_log(self, req: CreateAuditLogRequest) -> ApiResponse:
        return await self._post("/audit-logs", req.to_dict())

    async def _post(self, path: str, body: dict[str, Any]) -> ApiResponse:
        from urllib.parse import urlparse

        url     = self._base_url + path
        payload = json.dumps(body).encode()
        parsed  = urlparse(url)

        host   = parsed.hostname or ""
        port   = parsed.port or (443 if parsed.scheme == "https" else 80)
        use_tls = parsed.scheme == "https"
        request_path = parsed.path or "/"
        if parsed.query:
            request_path += "?" + parsed.query

        headers = (
            f"POST {request_path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Type: application/json\r\n"
            f"X-API-Key: {self._api_key}\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode()

        try:
            open_conn = asyncio.open_connection(host, port, ssl=use_tls)
            reader, writer = await asyncio.wait_for(open_conn, timeout=self._timeout)
        except (OSError, asyncio.TimeoutError) as exc:
            raise RuntimeError(f"logtrace: request failed: {exc}") from exc

        try:
            writer.write(headers + payload)
            await writer.drain()

            raw_response = await asyncio.wait_for(
                reader.read(65536),
                timeout=self._timeout,
            )
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

        # Parse the raw HTTP response
        try:
            header_section, _, body_bytes = raw_response.partition(b"\r\n\r\n")
            status_line = header_section.split(b"\r\n")[0].decode()
            status_code = int(status_line.split(" ")[1])
        except (ValueError, IndexError) as exc:
            raise RuntimeError("logtrace: failed to parse response") from exc

        raw_body = body_bytes.decode(errors="replace")

        if status_code >= 400:
            message = raw_body
            try:
                message = json.loads(raw_body).get("message", raw_body)
            except json.JSONDecodeError:
                pass
            raise LogtraceError(status_code, message)

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError("logtrace: failed to parse response") from exc

        return ApiResponse(
            message=data.get("message", ""),
            status_code=status_code,
        )
