# CONTINUITY.md — KAOW

## Snapshot
- **Goal**: Build KAOW — phone-controlled PC daemon wrapping AI CLIs
- **Current Phase**: Phase 2 — P2P Mobile App; transport + pairing shipped, capture mode added
- **Now**: Daemon + mobile live on Tailscale tailnet (real-device pairing verified; `544fe00`).
  Capture mode auto tries real X11 desktop first, Xvfb fallback — but real capture fails on
  Wayland (user's session: `XDG_SESSION_TYPE=wayland`, `DISPLAY=:1` XWayland). `import` (ImageMagick)
  can't capture Wayland surfaces. `grim` not installed. daemon/.env currently has
  `KAOW_CAPTURE_MODE=auto` but user may want `virtual` to suppress noise until Wayland support added.
  opencode is now the default CLI adapter. 53 tests green, lint clean.
- **Next**:
  1. Fix Wayland capture: install `grim` (`sudo pacman -S grim`), add `_capture_with_grim()` to screenshot.py
     (needs Wayland socket path `$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY`)
  2. Round-trip test: pair → scan → chat → opencode run execution
  3. DirectRelay keepalive/robustness (ping, recoverable DISCONNECTED state, backoff cap)
  4. Phase 5 zero-touch bootstrap (plan only — write to docs/PHASE5.md)
  5. E2E encryption; power management wiring
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
- D002a ACTIVE: opencode added as third CLI adapter; now the DEFAULT (opencode run) [CODE] 2026-09-16
- D003 ACTIVE: 1 phone ↔ 1 PC daemon model [USER] 2026-09-15
- D004 SUPERSEDED: Supabase conversation persistence replaced by daemon-local SQLite transcript (D-208) [SUPERSEDED]
- D005 ACTIVE: MIT license [USER] 2026-09-15
- D006 ACTIVE: Phase 5 = zero-touch installers (curl/irm one-liner), Phase 6 = QR pairing [USER] 2026-09-15
- D007 ACTIVE: mypy strict mode; add test/type stubs as deps (types-psutil, types-python-xlib) [CODE] 2026-09-15
- D008 ACTIVE: Git flow per task = feature branch → staging → main (promote to main only on release) [USER] 2026-09-15
- D-201 SUPERSEDED: relay modes no longer exist; code removed. [SUPERSEDED by D-207]
- D-202 SUPERSEDED: relay code removed; no Supabase auth flow. [SUPERSEDED by D-207]
- D-203 SUPERSEDED: screenshots/transcripts live on the daemon. [SUPERSEDED by D-207]
- D-204 SUPERSEDED: no server-side device registry. [SUPERSEDED by D-207]
- D-205 SUPERSEDED: pairing is a daemon-paired QR over tailnet. [SUPERSEDED by D-207]
- D-206 ACTIVE: Mobile pins Compose BOM 2026.06.01, core-ktx 1.18.0, lifecycle 2.10.0,
  compileSdk 36 (newer androidx needs AGP 9.1 + compileSdk 37) [CODE] 2026-09-16
- D-207 ACTIVE: FULL TAILSCALE TRANSPORT — phone connects directly to PC daemon over
  a tailnet (magic DNS + WS + Bearer token). No user data in any cloud project.
  Supersedes D-201..D-205. D-201..D-204 now marked SUPERSEDED (relay code removed).
  [USER] 2026-09-16
- D-208 ACTIVE: conversation history is a daemon-local SQLite transcript
  (`~/.kaow/transcript.db`, `KAOW_DATA_DIR`); mobile fetches it via `history_result`.
  [DESIGN] 2026-09-16
- D-209 ACTIVE: pairing is a QR code printed by `kaow pair` containing
  `ws://<tailnet-address>:<port>/ws?token=<auth_token>`; mobile scans/stores it
  locally (zxing ScanContract). [DESIGN] 2026-09-16
- D-210 ACTIVE: capture mode (`KAOW_CAPTURE_MODE=auto|virtual|real`) — auto reads
  from the user's real X11 display (`:0` etc.) when detected, falling back to the
  Xvfb virtual framebuffer; real mode enforces real display only. [CODE] 2026-09-16

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
- 2026-09-16 [CODE]: Android toolchain installed/verified — JDK 17, adb, platform-35, build-tools 34
- 2026-09-16 [CODE]: SETUP_TOOLCHAIN.md §4 updated for fish shell (user's shell is fish, not bash)
- 2026-09-16 [CODE]: Android platform-36 installed; tools + `mobile/` scaffold. Wrapper gen with
  Gradle 8.14.2. libs.versions.toml pinned: AGP 8.13.2, Kotlin 2.4.20, BOM 2026.06.01,
  core-ktx 1.18.0, lifecycle 2.10.0, supabase-kt 3.8.0, ktor 3.5.2
- 2026-09-16 [CODE]: mobile/ build files (settings/build/gradle.properties), manifest, res
  (M3 dark theme, adaptive launcher), data layer (Dtos, UiModels, KaowSupabase,
  Auth/Device/Chat/Dashboard repos), UI (KaowRoot auth gate + 3-tab shell, Login,
  Chat (VM+screen), Dashboard (VM+screen), Power placeholder, shared screens)
- 2026-09-16 [CODE]: First build failed on androidx/compileSdk mismatch (BOM 2026.09.00 →
  ui 1.12.1 needs AGP 9.1/compileSdk 37); pinned down to BOM 2026.06.01 (ui 1.11.x).
  Fixed supabase-kt 3.8.0 API drift: Email → providers.builtin.Email,
  decodeList/decodeSingle are `PostgrestResult` members (drop imports),
  realtime via `client.realtime` + `channel(...)` imports, `HasRecord.decodeRecord<T>()`
- 2026-09-16 [CODE]: `:app:assembleDebug` GREEN — app-debug.apk (16 MB). BUILT against
  empty Supabase creds; app shows ConfigErrorScreen until -P vars provided.
- 2026-09-16 [USER]: Full Tailscale pivot (D-207) — phone↔PC direct over tailnet,
  no user data in operator Supabase; Supabase relay code kept dormant. PHASE2.md superseded.
- 2026-09-16 [CODE]: Relay removed from daemon — deleted `relay/` + test_relay.py,
  stripped RelayMode/KAOW_SUPABASE_*/KAOW_DEVICE_* from config.py, relay wiring from
  main.py/server/app.py (incl. bridge + task_queued), `supabase` dep dropped from
  pyproject (uv.lock relocked). pyproject cleanup: unified dev deps into
  [dependency-groups] (pytest/ruff/mypy/httpx2/types-*) — `uv sync --dev` installs all.
- 2026-09-16 [CODE]: daemon/src/kaow/transcript/ — SqliteTranscriptStore (thread-local
  sqlite3, tables tasks/outputs, record_command/append_output/update_status/history).
- 2026-09-16 [CODE]: protocol.py + app.py — `history`/`history_result` messages
  (limit 1..500, reply to requesting socket), commands persisted + every chunk
  persisted (seq counter), terminal status updates (completed/killed/failed).
- 2026-09-16 [CODE]: daemon/src/kaow/pair.py — `kaow-pair` CLI: Tailscale IP detect
  (psutil, 100.64.0.0/10), builds ws URL + token, prints ASCII QR via `qrcode`.
- 2026-09-16 [CODE]: Daemon verification — 43 tests pass, ruff + mypy clean.
  Added tests: test_transcript.py (store CRUD/history) + history e2e in test_integration.py.
- 2026-09-16 [CODE]: Mobile deps — dropped supabase-bom/auth/postgrest/realtime;
  added ktor-client-websockets + zxing-android-embedded 4.3.0; removed BuildConfig
  SUPABASE fields.
- 2026-09-16 [CODE]: mobile net/ — DaemonProtocol (envelope parse/build), DirectRelay
  (ktor WS client, reconnect w/ backoff, status + events flows), ConnectionStore
  (SharedPreferences base_url + token).
- 2026-09-16 [CODE]: Mobile UI — PairScreen (zxing ScanContract QR + manual entry,
  PairingCode parse of ws://…?token=), KaowRoot pairing gate + FAILED connection bar
  (Retry/Re-pair), Chat/Dashboard VMs rewired to relay events, banners show
  connection status. `:app:assembleDebug` GREEN, no warnings.
- 2026-09-16 [CODE]: Docs — README/ARCHITECTURE/AGENTS/PHASE1/PHASE2/PHASE6/API updated to
  Tailscale-direct model; `supabase/` migrations + seed deleted (dead after D-207).
- 2026-09-16 [CODE]: Capture mode (D-210) — `KAOW_CAPTURE_MODE=auto|virtual|real` added
  to config; `XvfbDisplay` detects ambient DISPLAY before clobbering; in `auto` mode
  screenshots come from the real X11 desktop when present, Xvfb virtual fallback.
  opencode now the default CLI adapter. 53 tests, ruff + mypy clean.
- 2026-09-16 [CODE]: opencode adapter — `adapters/opencode.py` (opencode run, kill all,
  health_check via --version), registered in config/main factory. 53 tests pass.
- 2026-09-16 [TEST]: Live Tailscale test on user's machine — phone (100.113.131.8) scanned QR,
  connected, persisted pairing across force-quit. Dashboard shows Xvfb :99 (blue root).
  No live chat command sent yet — opencode round-trip is next.

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
- 2026-09-16 [TOOL]: User shell is fish; `sudo pacman -S ` needs a terminal, cannot run from agent
  (no TTY) — user must install packages. Arch has no `tailscale.service`, only `tailscaled.service`.
- 2026-09-16 [TOOL]: User session is WAYLAND (`XDG_SESSION_TYPE=wayland`) — `import`/`scrot` (X11)
  cannot capture Wayland surfaces; need `grim` (wlroots) + Wayland socket path. `import` IS installed.
- 2026-09-16 [TOOL]: Xvfb display is :99 (1920x1080x24); real X display is :0 (native) and :1
  (XWayland); `pgrep -a Xvfb` confirms. `xsetroot -solid <color>` on :99 proves Dashboard renders.
- 2026-09-16 [TOOL]: Mobile app can't stay paired after scanning — pairing persists on disk but
  UI reverted to Pair screen mid-session; direct WS reconnect churn observed. Needs keepalive fix.

## Outcomes Log
- 2026-09-15 [CODE]: Phase 1 daemon complete — shipped as `5ca360c` + `56e4164`
  (initial scaffold + CI/README). CI passes (ruff, mypy, pytest). Published on GitHub.
- 2026-09-15 [CODE]: Phase 2 daemon relay complete — schema written, relay module built and tested,
  ready to apply migrations to a live Supabase project. Mobile deferred pending toolchain.

## Uncommitted Work (as of session end 2026-09-16)
- **Not yet committed**: opencode adapter (`adapters/opencode.py`, config default change),
  capture mode (D-210), `.env.example` capture-mode entry, test additions, PHASE5.md full
  plan-only rewrite, PHASE2.md status/risks update. Work is on branch
  `feat/mobile-skeleton`. Last commit `544fe00` was the Tailscale route. Need to commit these.
- **Pending user action**: `sudo pacman -S grim` for Wayland capture support.
- **daemon/.env**: created from `.env.example` copy, has real auth token (d661e2...); adapter set
  to `opencode`, capture mode still `auto` (may want `virtual` to silence warnings until grim).