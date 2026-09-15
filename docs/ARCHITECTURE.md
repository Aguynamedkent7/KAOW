# KAOW Architecture

## System Overview

```
┌─────────────────────┐
│   Mobile App        │
│   (Kotlin/Compose)  │
└─────────┬───────────┘
          │ WebSocket
          ▼
┌─────────────────────┐
│   Supabase          │
│   (Auth + Relay)    │
│   PostgreSQL        │
│   Realtime DB       │
└─────────┬───────────┘
          │ WebSocket
          ▼
┌─────────────────────┐
│   PC Daemon         │
│   (Python/FastAPI)  │
│                     │
│  ┌────────────────┐ │
│  │ WebSocket Srv  │ │◄── Client commands
│  └───────┬────────┘ │
│          │           │
│  ┌───────▼────────┐ │
│  │ CLI Adapter    │ │
│  │ (Claude/OD)    │ │
│  └───────┬────────┘ │
│          │           │
│  ┌───────▼────────┐ │
│  │ Virtual Display│ │
│  │ (Xvfb)         │ │
│  └───────┬────────┘ │
│          │           │
│  ┌───────▼────────┐ │
│  │ Screenshot     │ │
│  │ Capture        │ │
│  └───────┬────────┘ │
│          │           │
│  ┌───────▼────────┐ │
│  │ Telemetry      │ │
│  │ Collector      │ │
│  └────────────────┘ │
└─────────────────────┘
```

## Data Flow

1. **User sends prompt** → Mobile app sends WebSocket message to Supabase
2. **Supabase relays** → Real-time subscription pushes to daemon
3. **Daemon processes** → Adapter executes prompt via AI CLI subprocess
4. **Output streams** → Chunks sent back through WebSocket to mobile
5. **Screenshots captured** → Periodic or on-demand from Xvfb framebuffer
6. **Telemetry reported** → CPU/RAM/process health pushed to clients

## Message Protocol

All WebSocket messages use JSON envelopes:

```json
{
  "type": "<message_type>",
  "id": "<uuid>",
  "payload": { ... },
  "timestamp": "<ISO8601>"
}
```

See [docs/API.md](API.md) for full protocol specification.

## Security Model

- **Authentication**: Bearer token on WebSocket connect (Phase 1)
- **Encryption**: Placeholder XOR in Phase 1, AES-GCM in Phase 2
- **Isolation**: Each daemon is independently authenticated
- **RLS**: Supabase row-level security in Phase 2

## Phase Breakdown

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Local PoC (daemon-first) | IN PROGRESS |
| 2 | Cloud relay + mobile app | PLANNED |
| 3 | Power management (WoL) | PLANNED |
| 4 | Cross-platform packaging | PLANNED |
| 5 | Zero-touch deployment (one-command installers) | PLANNED |
| 6 | Secure terminal QR pairing | PLANNED |
