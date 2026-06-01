from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

Metadata = dict[str, Any]


@dataclass
class RequestDetails:
    timestamp: str
    http_method: str
    http_endpoint: str
    http_status_code: int
    ip_address: str
    operating_system: str
    client_user_agent: str
    request_headers: dict[str, str] = field(default_factory=dict)
    geo_ip_location: str = ""
    request_duration: str = ""
    request_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp":         self.timestamp,
            "http_method":       self.http_method,
            "http_endpoint":     self.http_endpoint,
            "http_status_code":  self.http_status_code,
            "ip_address":        self.ip_address,
            "operating_system":  self.operating_system,
            "client_user_agent": self.client_user_agent,
            "request_headers":   self.request_headers,
            "geo_ip_location":   self.geo_ip_location,
            "request_duration":  self.request_duration,
            "request_id":        self.request_id,
        }


@dataclass
class CreateEventRequest:
    action_name: str
    http_method: str
    http_status: int
    client_ip: str
    client_user_agent: str
    user_id: str = ""
    user_name: str = ""
    http_endpoint: str = ""
    type: str = ""
    geo_ip_location: str = ""
    metadata: Metadata = field(default_factory=dict)
    request_details: RequestDetails | None = field(default=None, init=False)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "action_name":        self.action_name,
            "http_method":        self.http_method,
            "http_status":        self.http_status,
            "client_ip":          self.client_ip,
            "client_user_agent":  self.client_user_agent,
        }
        if self.user_id:         data["user_id"]          = self.user_id
        if self.user_name:       data["username"]         = self.user_name
        if self.http_endpoint:   data["http_endpoint"]    = self.http_endpoint
        if self.type:            data["type"]             = self.type
        if self.geo_ip_location: data["geo_ip_location"]  = self.geo_ip_location
        if self.metadata:        data["metadata"]         = self.metadata
        if self.request_details: data["request_details"]  = self.request_details.to_dict()
        return data


@dataclass
class CreateSessionRequest:
    login_at: str
    status: str
    user_id: str = ""
    user_name: str = ""
    device_info: str = ""
    ip_address: str = ""
    location: str = ""
    token: str = ""
    metadata: Metadata = field(default_factory=dict)
    request_details: RequestDetails | None = field(default=None, init=False)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "login_at": self.login_at,
            "status":   self.status,
        }
        if self.user_id:     data["user_id"]     = self.user_id
        if self.user_name:   data["username"]    = self.user_name
        if self.device_info: data["device_info"] = self.device_info
        if self.ip_address:  data["ip_address"]  = self.ip_address
        if self.location:    data["location"]    = self.location
        if self.token:       data["token"]       = self.token
        if self.metadata:    data["metadata"]    = self.metadata
        if self.request_details: data["request_details"] = self.request_details.to_dict()
        return data


@dataclass
class CreateAuditLogRequest:
    action: str
    timestamp: str
    user_id: str = ""
    user_name: str = ""
    ip_address: str = ""
    request_id: str = ""
    metadata: Metadata = field(default_factory=dict)
    request_details: RequestDetails | None = field(default=None, init=False)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "action":    self.action,
            "timestamp": self.timestamp,
        }
        if self.user_id:    data["user_id"]    = self.user_id
        if self.user_name:  data["username"]   = self.user_name
        if self.ip_address: data["ip_address"] = self.ip_address
        if self.request_id: data["request_id"] = self.request_id
        if self.metadata:   data["metadata"]   = self.metadata
        if self.request_details: data["request_details"] = self.request_details.to_dict()
        return data


@dataclass(frozen=True)
class ApiResponse:
    message: str
    status_code: int
