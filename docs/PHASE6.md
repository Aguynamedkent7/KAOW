# Phase 6 — Secure Terminal QR Pairing

## Goal
Link a physical PC to the mobile app without typing credentials on the headless
machine. The base version shipped early (with Phase 2) because no cloud backend
exists to broker pairing — the tailnet IS the trust boundary.

## Status: IN PROGRESS (base pairing shipped; hardening pending)

## Problem
Headless PCs have no easy way to input credentials. Typing a token over SSH is
tedious and insecure. QR pairing solves both problems.

## The Handshake Protocol (shipped)

### Actors
| Actor | Role |
|-------|------|
| PC (daemon) | Generates QR, serves the WebSocket |
| Mobile app | Scans QR, stores the pairing, connects over the tailnet |

### Sequence

```
 PC (terminal)          Mobile App
     |                      |
     |  1. `kaow pair`      |
     |  print QR:           |
     |  ws://<addr>:<port>/ws?token=<auth_token>
     |                      |
     |                      |  2. Scan QR
     |                      |  parse URL + token
     |                      |
     |                      |  3. Connect ws://...
     |  <---- WebSocket ----|  (WireGuard-encrypted)
     |                      |
     |  4. Daemon serves     |
     |  chat/screenshots     |
```

### Step Details

1. **Terminal QR Generation**
   - `kaow pair` (daemon/src/kaow/pair.py) detects the Tailscale IP local
     interface (100.64.0.0/10, iface name "tailscale"), builds
     `ws://<address>:<port>/ws?token=<auth_token>`, prints an ASCII QR via the
     `qrcode` Python lib plus the manual URL/token.
2. **Mobile Scan**
   - Mobile app PairScreen uses ZXing (`ScanContract`) to read the QR.
   - Manual entry fallback (base URL + token) for remote SSH users.
3. **Store & Connect**
   - App saves `{base_url, auth_token}` in SharedPreferences and connects the
     WebSocket directly over the tailnet; status banner shows connecting /
     connected / unreachable with Retry + Re-pair.

## Hardening Pending (future)
- Single-use rotation: `kaow pair` rotates the auth token on each run and the
  mobile app re-pairs (rather than reconnecting forever).
- Pairing attestation: prove the token holder also controls the tailnet before
  the token can be crossed with another device.
- Out-of-band confirmation: PSK-derived proof presented on both ends of pairing.
- QR must degrade gracefully if the pairing command itself is a risk to run
  unattended.

## Deliverables
- `daemon/src/kaow/pair.py` — QR render + tailnet address detection
- `mobile` PairScreen — camera scanner + manual entry + persisted pairing
- Mobile `net/DirectRelay` — token-authenticated WebSocket with reconnect/backoff

## Dependencies
- Tailscale tailnet (free tier: 3 devices) enrolled on phone + PC
- Phase 2 direct-WS transport (WireGuard replaces the cloud broker entirely)