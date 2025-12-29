# Service API

## Log Streaming (SSE)

Clients MAY reconnect using `Last-Event-ID`.
The server guarantees:
- monotonic event ids starting at 1
- resume from id + 1
- final `event: end`
- Last-Event-ID header overrides last_id query param.
