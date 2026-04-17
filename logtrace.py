"""Logtrace Python SDK for the developer API."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import json
import urllib.request
import urllib.error

DEFAULT_BASE_URL = "https://api.logtracehq.com/v1/developers"


# --- Types ---


@dataclass
class CreateEventRequest:
    action_name: str
    http_method: str
    http_status: str
    client_ip: str
    client_user_agent: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    http_endpoint: Optional[str] = None
    type: Optional[str] = None
    geo_ip_location: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class CreateSessionRequest:
    login_at: str
    """RFC 3339 timestamp, e.g. '2024-01-15T10:30:00Z'"""
    status: str
    """Must be 'ACTIVE', 'INACTIVE', 'SUCCESSFUL', 'FAILED', or 'EXPIRED'"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    token: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class CreateAuditLogRequest:
    action: str
    timestamp: str
    """ISO 8601 timestamp"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class APIResponse:
    message: str
    status_code: int


class LogtraceError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"logtrace: {status_code} - {message}")


# --- Client ---


class Logtrace:
    """Logtrace developer API client.

    Args:
        api_key: Your Logtrace API key.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key

    def create_event(self, req: CreateEventRequest) -> APIResponse:
        """Send an event to Logtrace."""
        return self._post("/events", req)

    def create_session(self, req: CreateSessionRequest) -> APIResponse:
        """Send a session to Logtrace."""
        return self._post("/sessions", req)

    def create_audit_log(self, req: CreateAuditLogRequest) -> APIResponse:
        """Send an audit log to Logtrace."""
        return self._post("/audit-logs", req)

    def _post(self, path: str, body) -> APIResponse:
        payload = _serialize(body)
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            f"{DEFAULT_BASE_URL}{path}",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self._api_key,
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
                return APIResponse(
                    message=resp_body.get("message", ""),
                    status_code=resp.status,
                )
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                message = err_body.get("message", str(e))
            except Exception:
                message = str(e)
            raise LogtraceError(e.code, message) from e


def _serialize(obj) -> dict:
    """Convert a dataclass to a dict, dropping None values and handling nested dataclasses."""
    d = asdict(obj)
    return {k: v for k, v in d.items() if v is not None}
