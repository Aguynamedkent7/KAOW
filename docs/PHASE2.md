# Phase 2 — P2P Mobile App (Tailscale Direct)

## Goal
Build the Kotlin/Jetpack Compose mobile app and connect it **directly** to the PC
daemon over a Tailscale tailnet (WireGuard / DERP fallback). No cloud relay, no
operator-hosted project: user data stays entirely on the user's phone + PC.

## Status: IN PROGRESS (daemon relay removed, direct WS transport + QR pairing done, E2E pending)

## Completed Tasks
- [x] Design database schema (devices, commands, command_outputs, screenshots) — superseeded, DB unused
- [x] Write SQL migrations: `supabase/migrations/*.sql` — superseeded, DB unused
- [x] Supabase relay removed from daemon (`config.py`, `relay/`, `main.py`, `server/app.py`,
      deps, `.env.example`) [D-207]
- [x] Local transcript persistence: `kaow/transcript/sqlite.py` (SQLite in `~/.kaow`),
      append-only; persisted on every chunk + terminal status [D-208]
- [x] `history` / `history_result` WS messages (limit 1..500; reply to requesting socket only)
- [x] `kaow pair` CLI: detects Tailscale IP, prints `ws://<addr>:<port>/ws?token=...` QR code [D-209]
- [x] Install Android toolchain (see `mobile/SETUP_TOOLCHAIN.md`) — JDK 17, adb,
      platform-36, build-tools 34 on Arch; env vars in fish config
- [x] Build mobile app skeleton (Kotlin + Jetpack Compose) — auth, chat, dashboard,
      power tabs; `./gradlew :app:assembleDebug` GREEN (`app-debug.apk`)
- [x] Mobile data layer rewritten: Supabase removed; direct Tailscale WS transport
      (`net/DirectRelay` + `DaemonProtocol`, ktor websockets) [D-207]
- [x] QR pairing screen (scan or manual entry) + settings persistence
      (`net/ConnectionStore`); connection status banner + Re-pair/Retry on failure
- [x] Daemon test suite green (43 tests), ruff + mypy clean; mobile `assembleDebug` green

## Planned Tasks
- [ ] Test bidirectional communication over the internet (tailnet roam / DERP)
- [ ] E2E encryption for screenshots and logs
- [ ] Power management screen wired to real daemon endpoints
- [ ] Real-device round trip: `kaow pair` → scan → chat → screenshot

## Dependencies
- Phase 1 complete (daemon with WebSocket server)
- Tailscale tailnet with phone + PC enrolled (free tier: 3 devices)
- Android development environment (see `mobile/SETUP_TOOLCHAIN.md`)
- Daemon bound to tailnet interface (plain `ws` — encrypted by WireGuard itself)

## Known Risks
- Mobile app WebSocket handling on background/foreground transitions
- Screenshot payload size over DERP relay (Tailscale fallback) on cellular
- TLS for the daemon WS (`wss`) not needed over WireGuard; cert provisioning for
  tailnet addresses left for a later phase if the user wants it
- First-run: user must install + sign into Tailscale (extra install step)

## Decisions
- D-201 SUPERSEDED: connection modes now `local` (WS only) is the product; the
  `cloud`/`both` Supabase relay modes stay dormant behind `KAOW_RELAY_MODE` [CODE] 2026-09-15
- D-202 SUPERSEDED: no cloud relay — user data never leaves phone/PC tailnet.
  Supabase not used for user data. [CODE] 2026-09-15
- D-203 SUPERSEDED: screenshots/transcripts are streamed or stored on the PC, not
  in a cloud DB. [CODE] 2026-09-15
- D-204 SUPERSEDED: no server-side device registry — device identity is the
  daemon token + tailnet address. [CODE] 2026-09-15
- D-205 SUPERSEDED: pairing lands via Tailscale + daemon token (QR pairing pulled
  forward as the intended UX, see Phase 6). [CODE] 2026-09-15
- D-206 ACTIVE: Mobile pins Compose BOM 2026.06.01 (ui 1.11.x) + core-ktx 1.18.0 +
  lifecycle 2.10.0 to stay within AGP 8.13.2 / compileSdk 36 (newer androidx
  artifacts require AGP 9.1 + compileSdk 37). [CODE] 2026-09-16
- D-207 ACTIVE: full Tailscale (P2P) transport — dedicated WS connection from the
  phone straight to the PC daemon; Supabase relay code removed from daemon config
  and the mobile app entirely. [DESIGN] 2026-09-16
- D-208 ACTIVE: conversation history is a daemon-local SQLite transcript
  (`~/.kaow/transcript.db`); the mobile app fetches it via `history_result` on
  connect, no cloud DB. [DESIGN] 2026-09-16
- D-209 ACTIVE: pairing is a QR code printed by `kaow pair` on the PC containing
  `ws://<tailnet-address>:<port>/ws?token=<auth_token>`; mobile scans it and
  stores the pairing locally (reconnectable until user re-pairs). [DESIGN] 2026-09-16