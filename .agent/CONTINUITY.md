# CONTINUITY.md — KAOW

## Snapshot
- **Goal**: Build KAOW — phone-controlled PC daemon wrapping AI CLIs
- **Current Phase**: Phase 2 — Cloud Relay + Mobile App
- **Now**: Phase 2 daemon relay shipped; mobile app deferred until Android toolchain installed
- **Next**: Install Android SDK/JDK (`mobile/SETUP_TOOLCHAIN.md`), scaffold mobile project, run compile verification
- **Constraints**: 300 LOC/file, modular-first, no silent failures, container-first

## Plans Log
- 2026-09-15 [USER]: Full project outline provided, Phase 1 is daemon-first
- 2026-09-15 [USER]: Added Phase X (Deployment/Zero-Touch) and Phase Y (QR Pairing) →
  recorded as Phase 5 and Phase 6 in docs/PHASE5.md, docs/PHASE6.md
- 2026-09-15 [USER]: "go for current phase 2" — approved Phase 2 execution
- 2026-09-15 [USER]: Deferred mobile skeleton; requested `mobile/SETUP_TOOLCHAIN.md` install guide for next session

## Decisions Log
- D001 ACTIVE: Python daemon with FastAPI + WebSockets [USER] 2026-09-15
- D002 ACTIVE: Pluggable AI CLI adapter (Claude + OpenDevin) [USER] 2026-09-15
- D003 ACTIVE: 1 phone ↔ 1 PC daemon model [USER] 2026-09-15
- D004 ACTIVE: Full conversation persistence in Supabase [USER] 2026-09-15
- D005 ACTIVE: MIT license [USER] 2026-09-15
- D006 ACTIVE: Phase 5 = zero-touch installers (curl/irm one-liner), Phase 6 = QR pairing [USER] 2026-09-15
- D007 ACTIVE: mypy strict mode; add test/type stubs as deps (types-psutil, types-python-xlib) [CODE] 2026-09-15
- D008 ACTIVE: Git flow per task = feature branch → staging → main (promote to main only on release) [USER] 2026-09-15
- D-201 ACTIVE: Three relay modes: local/cloud/both via KAOW_RELAY_MODE [CODE] 2026-09-15
- D-202 ACTIVE: Daemon uses service_role key to bypass RLS; mobile uses anon key [CODE] 2026-09-15
- D-203 ACTIVE: Screenshots stored as base64 in command_outputs/supabase; revisit Storage in Phase 3+ [CODE] 2026-09-15
- D-204 ACTIVE: register_device RPC is SECURITY DEFINER (upsert by user_id + name) [CODE] 2026-09-15

## Progress Log
- 2026-09-15 [CODE]: Git repo initialized, .gitignore, LICENSE, .env.example
- 2026-09-15 [CODE]: AGENTS.md and CONTINUITY.md created
- 2026-09-15 [CODE]: pyproject.toml with FastAPI/WebSockets/Pydantic/psutil deps
- 2026-09-15 [CODE]: config.py — pydantic-settings, env-based config
- 2026-09-15 [CODE]: server/protocol.py — WS message schemas (10 message types)
- 2026-09-15 [CODE]: server/middleware.py — Bearer token auth with constant-time compare
- 2026-09-15 [CODE]: server/app.py — FastAPI WS server, ConnectionManager, KAOWServer
- 2026-09-15 [CODE]: adapters/base.py — CLIAdapter ABC (execute/kill/health_check)
- 2026-09-15 [CODE]: adapters/claude.py — Claude CLI subprocess wrapper
- 2026-09-15 [CODE]: adapters/opendevin.py — OpenDevin CLI subprocess wrapper
- 2026-09-15 [CODE]: display/base.py — DisplayManager ABC (start/stop/capture)
- 2026-09-15 [CODE]: display/xvfb.py — Xvfb lifecycle, auto display number, resolution
- 2026-09-15 [CODE]: display/screenshot.py — Multi-method capture (import/scrot/Pillow)
- 2026-09-15 [CODE]: telemetry/collector.py — Async periodic CPU/RAM/disk collection
- 2026-09-15 [CODE]: telemetry/models.py — SystemMetrics, ProcessInfo, TelemetrySnapshot
- 2026-09-15 [CODE]: queue/memory.py — FIFO queue with max_size, cancel, drain
- 2026-09-15 [CODE]: security/auth.py — Token validation
- 2026-09-15 [CODE]: security/encryption.py — XOR placeholder (Phase 2: AES-GCM)
- 2026-09-15 [CODE]: main.py — Entry point, adapter/display factory, uvicorn, graceful shutdown
- 2026-09-15 [CODE]: Dockerfile + docker-compose.yml
- 2026-09-15 [CODE]: Tests: test_server.py, test_adapters.py, test_display.py
- 2026-09-15 [CODE]: Docs: ARCHITECTURE.md, SETUP.md, API.md, PHASE1-4.md
- 2026-09-15 [CODE]: uv installed by user; deps synced; ruff/mypy/pytest all GREEN (32 tests)
- 2026-09-15 [CODE]: Docs: PHASE5.md (zero-touch installers), PHASE6.md (QR pairing) added
- 2026-09-15 [CODE]: test_integration.py — full WS server integration tests (auth, command streaming, screenshots)
- 2026-09-15 [CODE]: Server bug fix: message-type parsing now properly separates INVALID_MESSAGE vs UNKNOWN_TYPE
- 2026-09-15 [CODE]: httpx2 added as dev dep for starlette TestClient
- 2026-09-15 [CODE]: Phase 2 Supabase schema + RLS: 001_initial_schema.sql, 002_rls_policies.sql,
  003_realtime_publications.sql, 004_register_device_function.sql, seed.sql
- 2026-09-15 [CODE]: config.py extended with RelayMode enum, Supabase creds, device identity fields
- 2026-09-15 [CODE]: relay/ package: SupabaseClient (async wrapper), RealtimeSubscription,
  RelayCoordinator, factory helpers (create_relay, validate_relay_settings)
- 2026-09-15 [CODE]: KAOWServer + main.py wired for relay; bridge hook streams cloud events to local WS
- 2026-09-15 [CODE]: .env.example updated with KAOW_RELAY_MODE / KAOW_SUPABASE_* / KAOW_DEVICE_* vars
- 2026-09-15 [CODE]: test_relay.py added (48 total tests passing, ruff + mypy clean)
- 2026-09-15 [CODE]: mobile/SETUP_TOOLCHAIN.md created — Android SDK + JDK install steps for Arch Linux

## Discoveries Log
- 2026-09-15 [TOOL]: `loop.run_in_executor(loop, func, kwarg=...)` does NOT forward kwargs —
  fixed with functools.partial (real bug caught by mypy)
- 2026-09-15 [TOOL]: mypy strict requires type stubs: types-psutil, types-python-xlib (now dev deps)
- 2026-09-15 [CODE]: Integration test caught real bug — MessageType(StrEnum) raises ValueError
  before UNKNOWN_TYPE branch could be reached, masking bad-type errors as INVALID_MESSAGE
- 2026-09-15 [TOOL]: `supabase` v2.31+ async API: use `acreate_client()` (returns `AsyncClient`),
  not sync `create_client()`. The runtime event parameter for `on_postgres_changes` is
  `RealtimePostgresChangesListenEvent.Insert` (capitalized), and the TypedDict payload is
  accessed via `payload.get("data", {}).get("record", {})` rather than attribute access.

## Outcomes Log
- 2026-09-15 [CODE]: Phase 1 daemon complete — shipped as `5ca360c` + `56e4164`
  (initial scaffold + CI/README). CI passes (ruff, mypy, pytest). Published on GitHub.
- 2026-09-15 [CODE]: Phase 2 daemon relay complete — schema written, relay module built and tested,
  ready to apply migrations to a live Supabase project. Mobile deferred pending toolchain.