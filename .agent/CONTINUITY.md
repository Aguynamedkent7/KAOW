# CONTINUITY.md — KAOW

## Snapshot
- **Goal**: Build KAOW — phone-controlled PC daemon wrapping AI CLIs
- **Current Phase**: Phase 1 — Local PoC (daemon-first)
- **Now**: Phase 1 scaffold complete, awaiting dependency install + verification
- **Next**: Install deps, run tests, integration test WebSocket server
- **Constraints**: 300 LOC/file, modular-first, no silent failures, container-first

## Plans Log
- 2026-09-15 [USER]: Full project outline provided, Phase 1 is daemon-first
- 2026-09-15 [USER]: Added Phase X (Deployment/Zero-Touch) and Phase Y (QR Pairing) →
  recorded as Phase 5 and Phase 6 in docs/PHASE5.md, docs/PHASE6.md

## Decisions Log
- D001 ACTIVE: Python daemon with FastAPI + WebSockets [USER] 2026-09-15
- D002 ACTIVE: Pluggable AI CLI adapter (Claude + OpenDevin) [USER] 2026-09-15
- D003 ACTIVE: 1 phone ↔ 1 PC daemon model [USER] 2026-09-15
- D004 ACTIVE: Full conversation persistence in Supabase [USER] 2026-09-15
- D005 ACTIVE: MIT license [USER] 2026-09-15
- D006 ACTIVE: Phase 5 = zero-touch installers (curl/irm one-liner), Phase 6 = QR pairing [USER] 2026-09-15
- D007 ACTIVE: mypy strict mode; add test/type stubs as deps (types-psutil, types-python-xlib) [CODE] 2026-09-15

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

## Discoveries Log
- 2026-09-15 [TOOL]: `loop.run_in_executor(loop, func, kwarg=...)` does NOT forward kwargs —
  fixed with functools.partial (real bug caught by mypy)
- 2026-09-15 [TOOL]: mypy strict requires type stubs: types-psutil, types-python-xlib (now dev deps)
- 2026-09-15 [CODE]: Integration test caught real bug — MessageType(StrEnum) raises ValueError
  before UNKNOWN_TYPE branch could be reached, masking bad-type errors as INVALID_MESSAGE

## Outcomes Log
(empty — populated at phase completion)
