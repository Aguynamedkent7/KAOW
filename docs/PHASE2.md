# Phase 2 — Cloud Relay + Mobile App

## Goal
Set up Supabase for auth and real-time command routing, build the Kotlin/Jetpack
Compose mobile app, and test bidirectional communication over the internet.

## Status: IN PROGRESS (daemon relay shipped, mobile skeleton compiles)

## Completed Tasks
- [x] Design database schema (devices, commands, command_outputs, screenshots)
- [x] Write SQL migrations: `supabase/migrations/001_initial_schema.sql`
- [x] RLS policies: `supabase/migrations/002_rls_policies.sql`
- [x] Realtime publications: `supabase/migrations/003_realtime_publications.sql`
- [x] Device registration function: `supabase/migrations/004_register_device_function.sql`
- [x] Seed template: `supabase/seed.sql`
- [x] Add `supabase` Python client to daemon deps
- [x] Daemon settings: `relay_mode`, `KAOW_SUPABASE_*`, `KAOW_DEVICE_*` (config.py)
- [x] Relay module (`daemon/src/kaow/relay/`): SupabaseClient, RealtimeSubscription,
      RelayCoordinator, factory
- [x] Wire relay into `KAOWServer` + `main.py` (modes: local / cloud / both)
- [x] Bridge hook: cloud commands stream to local WebSocket clients (BOTH mode)
- [x] Tests: `tests/test_relay.py` (48 total passing, ruff + mypy clean)
- [x] Install Android toolchain (see `mobile/SETUP_TOOLCHAIN.md`) — JDK 17, adb,
      platform-36, build-tools 34 on Arch; env vars in fish config
- [x] Build mobile app skeleton (Kotlin + Jetpack Compose) — auth, chat, dashboard,
      power tabs; `./gradlew :app:assembleDebug` GREEN (`app-debug.apk`, 16 MB)

## Planned Tasks
- [ ] Implement chat interface (text/voice input) in Supabase-connected run
- [ ] Implement live dashboard (screenshots, terminal logs) in Supabase-connected run
- [ ] Connect mobile app to daemon via Supabase relay (real project creds)
- [ ] Test bidirectional communication outside local network
- [ ] Implement conversation history persistence
- [ ] E2E encryption for screenshots and logs

## Dependencies
- Phase 1 complete (daemon with WebSocket server)
- Supabase project created (apply migrations 001–004)
- Android development environment (see `mobile/SETUP_TOOLCHAIN.md`)

## Known Risks
- Supabase realtime subscription latency
- Mobile app WebSocket handling on background/foreground transitions
- Screenshot base64 encoding size over cellular networks
- `supabase` py client pulls a large dep tree (pyjwt, realtime, storage3, yarl)

## Decisions
- D-201 ACTIVE: Three connection modes via `KAOW_RELAY_MODE` — `local` (WS only,
  Phase 1 behavior), `cloud` (Supabase only), `both` (WS + relay bridged)
  [CODE] 2026-09-15
- D-202 ACTIVE: Daemon uses `service_role` key to bypass RLS; mobile uses anon key
  scoped by RLS. Service key never ships in mobile app. [CODE] 2026-09-15
- D-203 ACTIVE: `commands`/`command_outputs`/`screenshots` tables take base64 for
  now; revisit Supabase Storage for large blobs in Phase 3+ [CODE] 2026-09-15
- D-204 ACTIVE: `register_device` is a SECURITY DEFINER RPC (upsert by user_id+name)
  [CODE] 2026-09-15
- D-205 ACTIVE: Relay integration reuses the same CLI adapter + display; local WS
  path unchanged. Device pairing (device_user_id) lands with QR pairing (Phase 6).
  [CODE] 2026-09-15
- D-206 ACTIVE: Mobile pins Compose BOM 2026.06.01 (ui 1.11.x) + core-ktx 1.18.0 +
  lifecycle 2.10.0 to stay within AGP 8.13.2 / compileSdk 36 (newer androidx
  artifacts require AGP 9.1 + compileSdk 37). [CODE] 2026-09-16