# Service API

## Log Streaming (SSE)

Clients MAY reconnect using `Last-Event-ID`.
The server guarantees:
- monotonic event ids starting at 1
- resume from id + 1
- final `event: end`
- Last-Event-ID header overrides last_id query param.

### Edge Cases
- **Garbage Last-Event-ID**: If the `Last-Event-ID` header contains non-numeric values, the server responds with **HTTP 400**.
- **Future ID**: If `Last-Event-ID` > `len(logs)`, the stream returns only `event: end`.
- **Reconnect after completion**: If the job is already finished and `Last-Event-ID` matches the total log count, the stream returns only `event: end`.
