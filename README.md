# logtrace-py

Python client for the Logtrace API. Requires Python ≥ 3.11, no dependencies.

## Install

```bash
pip install logtrace-py
```

## Usage

```python
from logtrace_py import Client, CreateEventRequest

client = Client(api_key=os.environ["LOGTRACE_API_KEY"])

client.create_event(CreateEventRequest(
    action_name="user.signup",
    http_method="POST",
    http_status=201,
    client_ip="203.0.113.42",
    client_user_agent=request.headers.get("User-Agent", ""),
))

client.create_session(CreateSessionRequest(...))
client.create_audit_log(CreateAuditLogRequest(...))
```

### Async

```python
from logtrace_py import AsyncClient

async with AsyncClient(api_key=os.environ["LOGTRACE_API_KEY"]) as client:
    await client.create_event(CreateEventRequest(...))
```

## Middleware

Automatically attaches request context (IP, method, endpoint, headers, status code) to every call made inside a handler.

**WSGI (Flask)**

```python
from logtrace_py import WsgiMiddleware

app.wsgi_app = WsgiMiddleware(app.wsgi_app, client)
```

**ASGI (FastAPI / Starlette)**

```python
from logtrace_py import AsgiMiddleware

app.add_middleware(AsgiMiddleware, client=client)
```

**Django** — add to `settings.py`:

```python
import logtrace_py
LOGTRACE_CLIENT = logtrace_py.Client(api_key=os.environ["LOGTRACE_API_KEY"])

MIDDLEWARE = [
    "logtrace_py.middleware.DjangoMiddleware",
    ...
]
```

Inside any handler:

```python
from logtrace_py import from_context

rc = from_context(client)
rc.create_event(CreateEventRequest(...))              # sync
await rc.async_create_event(CreateEventRequest(...))  # async
```

## Error handling

```python
from logtrace_py import LogtraceError

try:
    client.create_event(req)
except LogtraceError as e:
    print(e.status_code, e)
```

## Options

```python
Client(
    api_key="...",
    base_url="https://api.logtrace.dev/v1/developers",  # default: http://localhost:8080/v1/developers
    timeout=5.0,                                         # default: 10.0
)
```
