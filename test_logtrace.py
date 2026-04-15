"""Tests for the Logtrace Python SDK."""

import json
import unittest
from http.client import HTTPResponse
from io import BytesIO
from unittest.mock import patch, MagicMock

from logtrace import (
    Logtrace,
    LogtraceError,
    APIResponse,
    CreateEventRequest,
    CreateSessionRequest,
    CreateAuditLogRequest,
    AuditLogMetadata,
    _serialize,
)

EXPECTED_BASE = "https://api.logtracehq.com/v1/developers"


def _mock_response(status: int, body: dict) -> MagicMock:
    """Create a mock urllib response."""
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestCreateEvent(unittest.TestCase):
    @patch("logtrace.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "Event created"})
        client = Logtrace("test-api-key")

        resp = client.create_event(CreateEventRequest(
            action_name="user.login",
            http_method="POST",
            http_status="200",
            client_ip="192.168.1.1",
            client_user_agent="TestAgent/1.0",
        ))

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.message, "Event created")

    @patch("logtrace.urllib.request.urlopen")
    def test_sends_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_event(CreateEventRequest(
            action_name="test",
            http_method="GET",
            http_status="200",
            client_ip="0.0.0.0",
            client_user_agent="t",
        ))

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, f"{EXPECTED_BASE}/events")

    @patch("logtrace.urllib.request.urlopen")
    def test_sends_correct_headers(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("my-secret-key")

        client.create_event(CreateEventRequest(
            action_name="test",
            http_method="GET",
            http_status="200",
            client_ip="0.0.0.0",
            client_user_agent="t",
        ))

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertEqual(req.get_header("X-api-key"), "my-secret-key")

    @patch("logtrace.urllib.request.urlopen")
    def test_sends_correct_body(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_event(CreateEventRequest(
            action_name="user.signup",
            http_method="POST",
            http_status="201",
            client_ip="10.0.0.1",
            client_user_agent="Mozilla/5.0",
            user_id="usr_123",
        ))

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["action_name"], "user.signup")
        self.assertEqual(body["user_id"], "usr_123")
        self.assertNotIn("username", body)  # None values should be omitted

    @patch("logtrace.urllib.request.urlopen")
    def test_with_all_optional_fields(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_event(CreateEventRequest(
            action_name="user.login",
            http_method="GET",
            http_status="200",
            client_ip="1.2.3.4",
            client_user_agent="Agent",
            user_id="usr_123",
            username="john",
            http_endpoint="/api/login",
            type="auth",
            geo_ip_location="US",
        ))

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["user_id"], "usr_123")
        self.assertEqual(body["username"], "john")
        self.assertEqual(body["geo_ip_location"], "US")
        self.assertEqual(body["http_endpoint"], "/api/login")


class TestCreateSession(unittest.TestCase):
    @patch("logtrace.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "Session created"})
        client = Logtrace("key")

        resp = client.create_session(CreateSessionRequest(
            login_at="2025-01-15T10:30:00Z",
            status="ACTIVE",
        ))

        self.assertEqual(resp.message, "Session created")
        self.assertEqual(resp.status_code, 200)

    @patch("logtrace.urllib.request.urlopen")
    def test_sends_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_session(CreateSessionRequest(
            login_at="2025-01-01T00:00:00Z",
            status="ACTIVE",
        ))

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, f"{EXPECTED_BASE}/sessions")

    @patch("logtrace.urllib.request.urlopen")
    def test_with_all_fields(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_session(CreateSessionRequest(
            login_at="2025-06-01T08:00:00Z",
            status="ACTIVE",
            user_id="usr_456",
            username="jane",
            device_info="Chrome on macOS",
            ip_address="10.0.0.5",
            location="New York, US",
        ))

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["user_id"], "usr_456")
        self.assertEqual(body["device_info"], "Chrome on macOS")
        self.assertEqual(body["ip_address"], "10.0.0.5")


class TestCreateAuditLog(unittest.TestCase):
    @patch("logtrace.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "Audit log created"})
        client = Logtrace("key")

        resp = client.create_audit_log(CreateAuditLogRequest(
            action="user.deleted",
            timestamp="2025-03-10T14:00:00Z",
        ))

        self.assertEqual(resp.message, "Audit log created")

    @patch("logtrace.urllib.request.urlopen")
    def test_sends_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_audit_log(CreateAuditLogRequest(
            action="t",
            timestamp="2025-01-01T00:00:00Z",
        ))

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, f"{EXPECTED_BASE}/audit-logs")

    @patch("logtrace.urllib.request.urlopen")
    def test_with_metadata(self, mock_urlopen):
        mock_urlopen.return_value = _mock_response(200, {"message": "ok"})
        client = Logtrace("key")

        client.create_audit_log(CreateAuditLogRequest(
            action="user.role_change",
            timestamp="2025-03-10T14:00:00Z",
            user_id="usr_789",
            request_id="req_abc",
            metadata=AuditLogMetadata(
                event="role_change",
                description="Promoted to admin",
            ),
        ))

        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["metadata"]["event"], "role_change")
        self.assertEqual(body["metadata"]["description"], "Promoted to admin")


class TestErrorHandling(unittest.TestCase):
    @patch("logtrace.urllib.request.urlopen")
    def test_400_bad_request(self, mock_urlopen):
        import urllib.error
        err_resp = MagicMock()
        err_resp.read.return_value = json.dumps({"message": "Bad request: missing action_name"}).encode()
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=400, msg="Bad Request", hdrs=None, fp=err_resp
        )

        client = Logtrace("key")
        with self.assertRaises(LogtraceError) as ctx:
            client.create_event(CreateEventRequest(
                action_name="",
                http_method="GET",
                http_status="200",
                client_ip="0.0.0.0",
                client_user_agent="t",
            ))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("missing action_name", ctx.exception.message)

    @patch("logtrace.urllib.request.urlopen")
    def test_401_unauthorized(self, mock_urlopen):
        import urllib.error
        err_resp = MagicMock()
        err_resp.read.return_value = json.dumps({"message": "Invalid API key"}).encode()
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=401, msg="Unauthorized", hdrs=None, fp=err_resp
        )

        client = Logtrace("bad-key")
        with self.assertRaises(LogtraceError) as ctx:
            client.create_event(CreateEventRequest(
                action_name="t",
                http_method="GET",
                http_status="200",
                client_ip="0.0.0.0",
                client_user_agent="t",
            ))

        self.assertEqual(ctx.exception.status_code, 401)

    @patch("logtrace.urllib.request.urlopen")
    def test_500_server_error(self, mock_urlopen):
        import urllib.error
        err_resp = MagicMock()
        err_resp.read.return_value = json.dumps({"message": "Internal server error"}).encode()
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=500, msg="Internal Server Error", hdrs=None, fp=err_resp
        )

        client = Logtrace("key")
        with self.assertRaises(LogtraceError) as ctx:
            client.create_audit_log(CreateAuditLogRequest(
                action="t",
                timestamp="2025-01-01T00:00:00Z",
            ))

        self.assertEqual(ctx.exception.status_code, 500)

    @patch("logtrace.urllib.request.urlopen")
    def test_non_json_error_response(self, mock_urlopen):
        import urllib.error
        err_resp = MagicMock()
        err_resp.read.return_value = b"Bad Gateway"
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=502, msg="Bad Gateway", hdrs=None, fp=err_resp
        )

        client = Logtrace("key")
        with self.assertRaises(LogtraceError) as ctx:
            client.create_event(CreateEventRequest(
                action_name="t",
                http_method="GET",
                http_status="200",
                client_ip="0.0.0.0",
                client_user_agent="t",
            ))

        self.assertEqual(ctx.exception.status_code, 502)


class TestLogtraceError(unittest.TestCase):
    def test_error_properties(self):
        err = LogtraceError(404, "Not found")
        self.assertEqual(err.status_code, 404)
        self.assertEqual(err.message, "Not found")
        self.assertIn("404", str(err))
        self.assertIn("Not found", str(err))

    def test_is_exception(self):
        err = LogtraceError(500, "fail")
        self.assertIsInstance(err, Exception)


class TestSerialize(unittest.TestCase):
    def test_omits_none_values(self):
        req = CreateEventRequest(
            action_name="test",
            http_method="GET",
            http_status="200",
            client_ip="0.0.0.0",
            client_user_agent="t",
        )
        result = _serialize(req)
        self.assertNotIn("user_id", result)
        self.assertNotIn("username", result)
        self.assertEqual(result["action_name"], "test")

    def test_includes_set_values(self):
        req = CreateEventRequest(
            action_name="test",
            http_method="GET",
            http_status="200",
            client_ip="0.0.0.0",
            client_user_agent="t",
            user_id="usr_1",
        )
        result = _serialize(req)
        self.assertEqual(result["user_id"], "usr_1")

    def test_serializes_nested_metadata(self):
        req = CreateAuditLogRequest(
            action="test",
            timestamp="2025-01-01T00:00:00Z",
            metadata=AuditLogMetadata(event="role_change"),
        )
        result = _serialize(req)
        self.assertEqual(result["metadata"]["event"], "role_change")


if __name__ == "__main__":
    unittest.main()
