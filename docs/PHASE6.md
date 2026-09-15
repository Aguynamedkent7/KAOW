# Phase 6 — Secure Terminal QR Pairing

## Goal
Securely link a physical PC to the authenticated mobile app WITHOUT requiring the user to type credentials on the headless machine.

## Status: PLANNED

## Problem
Headless PCs have no easy way to input credentials. Typing a token over SSH is
tedious and insecure. QR code pairing solves both problems.

## The Handshake Protocol

### Actors
| Actor | Role |
|-------|------|
| PC (installer) | Generates QR, listens for authorization |
| Mobile app | Scans QR, sends pairing request |
| Supabase backend | Validates + registers the binding |

### Sequence

```
 PC (terminal)          Mobile App             Supabase
     |                      |                     |
     |  1. Generate QR      |                     |
     |  {device_id,        |                     |
     |   pairing_secret}    |                     |
     |  print to terminal   |                     |
     |                      |  2. Scan QR        |
     |                      |  open app,         |
     |                      |  tap "Add Device"  |
     |                      |                     |
     |                      |  3. POST pairing   |
     |                      |  {device_id,        |
     |                      |   secret,           |
     |                      |   user_id} -------->|
     |                      |                     |  4. Verify secret
     |                      |                     |  register device
     |                      |                     |  to user account
     |<-- 5. Realtime -----|  broadcast "success" |
     |    "success" event   |                     |
     |    receive user_id   |                     |
     |                      |                     |
     |  6. Cleanup          |                     |
     |  clear QR output     |                     |
     |  save user_id to     |                     |
     |  local config        |                     |
     |  restart into        |                     |
     |  headless worker     |                     |
     |        mode          |                     |
```

### Step Details

1. **Terminal QR Generation**
   - Installer script uses a CLI QR library (e.g., `qrcode-terminal` using ANSI blocks)
   - Payload: `{"device_id": "uuid-here", "secret": "temp-secret-here"}`

2. **Socket Listen**
   - PC daemon temporarily connects to a Supabase Realtime channel keyed by `device_id`
   - Listens for an authorization payload

3. **Mobile Scan**
   - User opens the KAOW Jetpack Compose app
   - Taps "Add Device"
   - Scans the terminal screen

4. **Cloud Handshake**
   - Mobile app sends `device_id`, `pairing_secret`, and the authenticated `user_id` to Supabase backend

5. **Validation & Lock**
   - Backend verifies the secret matches
   - If valid: registers the PC to the user's account in the database
   - Broadcasts a "success" event down the realtime socket to the waiting PC
   - Mobile app shows paired state

6. **Cleanup & Boot**
   - PC receives success signal containing `user_id`
   - Clears QR code from terminal
   - Saves `user_id` to local config
   - Restarts into silent headless worker mode

## Security Considerations
- `pairing_secret` is single-use — expires after first successful (or failed) handshake
- Binding is one-to-one: a PC pairs to exactly one authenticated user
- QR must degrade gracefully if the pairing command itself is a risk to run unattended
- Backend must rate-limit pairing attempts to prevent brute-force of the secret

## Deliverables
- `daemon/scripts/pairing.py` — QR render + realtime listener + lifecycle
- Supabase table `devices` + RLS policies + pairing RPC
- Mobile "Add Device" screen with camera/scanner integration

## Dependencies
- Phase 2 complete (Supabase auth + realtime)
- Phase 5 complete (installer invokes pairing mode)

## Decisions
(Pending — will be added during Phase 6 implementation)