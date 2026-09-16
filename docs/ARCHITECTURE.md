# KAOW Architecture

## System Overview

```
┌─────────────────────┐
│   Mobile App        │
│   (Kotlin/Compose)  │
└─────────┬───────────┘
          │ WebSocket over Tailscale
          │ (WireGuard-encrypted, no relay)
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
│  └───────┬────────┘ │
│          │           │
│  ┌───────▼────────┐ │
│  │ Transcript     │ │
│  │ (SQLite)       │ │
│  └────────────────┘ │
└─────────────────────┘
```

Pairing: `kaow pair` prints a QR code containing
`ws://<tailnet-address>:8765/ws?token=<auth_token>`; the phone scans it and
connects directly over the tailnet.

## Data Flow

1. **User sends prompt** → Mobile app sends WebSocket message straight to the PC daemon
2. **Daemon processes** → Adapter executes prompt via AI CLI subprocess
3. **Output streams** → Chunks sent back through the same WebSocket to mobile
4. **Screenshots captured** → Periodic or on-demand from Xvfb framebuffer
5. **Telemetry reported** → CPU/RAM/process health pushed to clients
6. **Transcript persisted** → Prompt, chunks, and terminal status stored in local SQLite

Transport is a dedicated WebSocket over the user's Tailscale tailnet (WireGuard /
DERP fallback). There is no cloud relay: user data never leaves the phone/PC pair.

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

- **Authentication**: Bearer token on WebSocket connect (printed as QR by `kaow pair`)
- **Transport encryption**: WireGuard via Tailscale (no application TLS needed)
- **Isolation**: Each daemon is independently authenticated by its own token
- **Transcript**: stored on the daemon host in SQLite (`~/.kaow`); fetched by
  clients via `history` / `history_result`

## Phase Breakdown

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Local PoC (daemon-first) | DONE |
| 2 | Mobile app — Tailscale P2P | IN PROGRESS |
| 3 | Power management (WoL) | PLANNED |
| 4 | Cross-platform packaging | PLANNED |
| 5 | Zero-touch deployment (one-command installers) | PLANNED |
| 6 | Secure terminal QR pairing | IN PROGRESS (base pairing shipped) |
