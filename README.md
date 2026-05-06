# logtrace-sdk

Python SDK for the [Logtrace](https://logtracehq.com) developer API. Zero dependencies.

## Install

```bash
pip install logtrace-sdk
```

## Usage

```python
from datetime import datetime, timezone
from logtrace import (
    Logtrace,
    CreateEventRequest,
    CreateSessionRequest,
    CreateAuditLogRequest,
    AuditLogMetadata,
)

client = Logtrace("your-api-key")

# Create an event
client.create_event(CreateEventRequest(
    action_name="user.login",
    username="jane_doe",
    http_method="POST",
    http_status="200",
    client_ip="192.168.1.1",
    client_user_agent="Mozilla/5.0",
))

# Create a session
client.create_session(CreateSessionRequest(
    login_at=datetime.now(timezone.utc).isoformat(),
    status="ACTIVE",
    username="jane_doe",
))

# Create an audit log
client.create_audit_log(CreateAuditLogRequest(
    action="user.deleted",
    timestamp=datetime.now(timezone.utc).isoformat(),
    username="jane_doe",
    metadata=AuditLogMetadata(
        event="deletion",
        type="user",
        description="User account was deleted",
    ),
))
```

