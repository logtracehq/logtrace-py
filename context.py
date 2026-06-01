
from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Callable

from .types import (
    ApiResponse,
    CreateAuditLogRequest,
    CreateEventRequest,
    CreateSessionRequest,
    RequestDetails,
)

_request_client_var: ContextVar[RequestClient] = ContextVar("logtrace_request_client")


class RequestClient:
    """
    A wrapper around a ``Client`` or ``AsyncClient`` that automatically
    populates ``request_details`` on every outgoing request.

    Obtain one from the middleware rather than constructing directly.
    """

    def __init__(
        self,
        client: object, 
        method: str = "",
        endpoint: str = "",
        client_ip: str = "",
        user_agent: str = "",
        operating_system: str = "",
        get_status: Callable[[], int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._client           = client
        self._method           = method
        self._endpoint         = endpoint
        self._client_ip        = client_ip
        self._user_agent       = user_agent
        self._operating_system = operating_system
        self._get_status       = get_status
        self.headers: dict[str, str] = headers or {}


    def _build_request_details(self) -> RequestDetails:
        return RequestDetails(
            timestamp=datetime.now(timezone.utc).isoformat(),
            http_method=self._method,
            http_endpoint=self._endpoint,
            http_status_code=self._get_status() if self._get_status else 0,
            ip_address=self._client_ip,
            operating_system=self._operating_system,
            client_user_agent=self._user_agent,
            request_headers=dict(self.headers),
        )


    def create_event(self, req: CreateEventRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return self._client.create_event(req)  # type: ignore[union-attr]

    def create_session(self, req: CreateSessionRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return self._client.create_session(req)  # type: ignore[union-attr]

    def create_audit_log(self, req: CreateAuditLogRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return self._client.create_audit_log(req)  # type: ignore[union-attr]


    async def async_create_event(self, req: CreateEventRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return await self._client.create_event(req)  # type: ignore[union-attr]

    async def async_create_session(self, req: CreateSessionRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return await self._client.create_session(req)  # type: ignore[union-attr]

    async def async_create_audit_log(self, req: CreateAuditLogRequest) -> ApiResponse:
        req.request_details = self._build_request_details()
        return await self._client.create_audit_log(req)  # type: ignore[union-attr]


def from_context(fallback: object) -> RequestClient:
    """
    Return the ``RequestClient`` bound to the current context, or a bare one
    wrapping ``fallback`` if no middleware has run (workers, tests, etc.).
    """
    try:
        return _request_client_var.get()
    except LookupError:
        return RequestClient(fallback)
