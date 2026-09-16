# KAOW WebSocket API

## Connection

```
ws://<host>:<port>/ws?token=<auth_token>
```

Or via Authorization header:
```
Authorization: Bearer <auth_token>
```

## Message Format

All messages are JSON with this envelope:

```json
{
  "type": "string",
  "id": "uuid",
  "payload": {},
  "timestamp": "2026-09-15T12:00:00Z"
}
```

## Client → Daemon Messages

### `command`
Execute a prompt through the AI CLI.

```json
{
  "type": "command",
  "id": "msg-001",
  "payload": {
    "prompt": "List all files in the current directory",
    "task_id": "auto-generated-uuid"
  }
}
```

### `screenshot_request`
Request an immediate screenshot capture.

```json
{
  "type": "screenshot_request",
  "id": "msg-002"
}
```

### `kill`
Terminate a running task.

```json
{
  "type": "kill",
  "id": "msg-003",
  "payload": {
    "task_id": "task-to-kill"
  }
}
```

### `ping`
Health check / keepalive.

```json
{
  "type": "ping",
  "id": "msg-004"
}
```

### `history`
Request the prior chat transcript stored locally on the daemon.

```json
{
  "type": "history",
  "id": "msg-005",
  "payload": {
    "limit": 50
  }
}
```

`limit` is optional (default 50, max 500). The reply is sent only to the
requesting socket as `history_result`; entries are ordered oldest first.

## Daemon → Client Messages

### `command_output`
Streaming output from a command execution.

```json
{
  "type": "command_output",
  "id": "msg-001",
  "payload": {
    "task_id": "task-uuid",
    "stream": "output chunk text",
    "done": false,
    "status": "running"
  }
}
```

### `screenshot`
Screenshot data as base64 PNG.

```json
{
  "type": "screenshot",
  "id": "msg-002",
  "payload": {
    "image": "base64-encoded-png-data",
    "timestamp": "2026-09-15T12:00:05Z",
    "width": 1920,
    "height": 1080
  }
}
```

### `error`
Error response.

```json
{
  "type": "error",
  "id": "msg-003",
  "payload": {
    "message": "Description of what went wrong",
    "code": "ERROR_CODE",
    "task_id": "optional-task-id"
  }
}
```

### `pong`
Response to ping.

```json
{
  "type": "pong",
  "id": "msg-004"
}
```

### `task_queued`
Confirmation that a task was queued for later execution.

```json
{
  "type": "task_queued",
  "id": "msg-005",
  "payload": {
    "task_id": "queued-task-id",
    "queue_position": 0
  }
}
```

### `status`
System telemetry report.

```json
{
  "type": "status",
  "id": "msg-006",
  "payload": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "active_tasks": 2,
    "display_active": true,
    "cli_adapter": "claude"
  }
}
```

### `history_result`
Reply to `history`: prior transcript persisted on the daemon.

```json
{
  "type": "history_result",
  "id": "msg-007",
  "payload": {
    "entries": [
      {
        "task_id": "task-uuid",
        "prompt": "List all files",
        "status": "completed",
        "created_at": "2026-09-16T09:00:00Z",
        "output": "output text"
      }
    ]
  }
}
```

## Pairing

Run `kaow pair` on the PC daemon host. It prints an ASCII QR code plus the
manual-entry values:

```
URL: ws://<tailnet-address>:<port>/ws
Token: <auth_token>
```

The QR encodes `ws://<tailnet-address>:<port>/ws?token=<auth_token>`. The mobile
app scans this and connects straight over the tailnet (WireGuard-encrypted; no
cloud relay).

## Error Codes

| Code | Description |
|------|-------------|
| `AUTH_FAILED` | Authentication token invalid or missing |
| `INVALID_MESSAGE` | Malformed JSON or missing required fields |
| `UNKNOWN_TYPE` | Unrecognized message type |
| `INVALID_PAYLOAD` | Payload validation failed |
| `EXECUTION_FAILED` | AI CLI execution error |
| `SCREENSHOT_FAILED` | Screenshot capture error |
| `PERSISTENCE_FAILED` | Failed to store a transcript chunk locally |

## Task Statuses

| Status | Description |
|--------|-------------|
| `queued` | Task is waiting in queue |
| `running` | Task is currently executing |
| `completed` | Task finished successfully |
| `failed` | Task encountered an error |
| `killed` | Task was terminated by user |
