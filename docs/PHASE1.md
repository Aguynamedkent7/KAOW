# Phase 1 — Local PoC (Daemon-First)

## Goal
Build a working Python daemon that accepts WebSocket commands, runs them through an AI CLI adapter, captures screenshots from a headless display, and streams output back.

## Status: IN PROGRESS

## Completed
- [x] Project scaffold: git repo, .gitignore, LICENSE, .env.example
- [x] AGENTS.md with code conventions and development phases
- [x] CONTINUITY.md for agent continuity across sessions
- [x] pyproject.toml with all dependencies and tooling config
- [x] Configuration module (pydantic-settings, env-based)
- [x] WebSocket protocol schemas (Pydantic models, message types)
- [x] WebSocket server with auth middleware (FastAPI)
- [x] CLI adapter abstract base class
- [x] Claude CLI adapter implementation
- [x] OpenDevin CLI adapter implementation
- [x] Xvfb display manager (start/stop/resolution)
- [x] Screenshot capture (ImageMagick/scrot/Pillow fallbacks)
- [x] Telemetry collector (CPU/RAM/disk/process health)
- [x] In-memory task queue (FIFO, max size, cancel/drain)
- [x] Security module (auth, placeholder encryption)
- [x] Entry point (main.py with graceful shutdown)
- [x] Dockerfile + docker-compose.yml
- [x] Unit tests for protocol, adapters, display, queue
- [x] Documentation: ARCHITECTURE.md, SETUP.md, API.md
- [x] Dependencies installed with uv
- [x] Linting passes (ruff + mypy strict, 23 source files)
- [x] Test suite passes (32 tests)

## In Progress
- [ ] Integration test: WebSocket server accepts connection + dispatches command

## To Do (Phase 1 remaining)
- [ ] WebSocket server integration test with real adapter
- [ ] Screenshot integration test with Xvfb
- [ ] End-to-end local test: send command → get output via WebSocket

## Known Issues
- Screenshot capture fallback chain needs real X11 environment to test
- OpenDevin CLI interface may differ from current implementation (needs verification)

## Decisions Made
- D001: Python daemon with FastAPI + WebSockets
- D002: Pluggable adapter pattern for AI CLIs
- D003: 1 phone ↔ 1 daemon model
- D004: Full conversation persistence in Supabase (Phase 2)
- D005: MIT license

## Files Created
```
daemon/src/kaow/
├── __init__.py
├── main.py                    (118 LOC)
├── config.py                  (42 LOC)
├── server/
│   ├── __init__.py
│   ├── app.py                 (237 LOC)
│   ├── protocol.py            (154 LOC)
│   └── middleware.py          (58 LOC)
├── adapters/
│   ├── __init__.py
│   ├── base.py                (63 LOC)
│   ├── claude.py              (118 LOC)
│   └── opendevin.py           (117 LOC)
├── display/
│   ├── __init__.py
│   ├── base.py                (69 LOC)
│   ├── xvfb.py                (151 LOC)
│   └── screenshot.py          (133 LOC)
├── telemetry/
│   ├── __init__.py
│   ├── collector.py           (140 LOC)
│   └── models.py              (39 LOC)
├── queue/
│   ├── __init__.py
│   └── memory.py              (122 LOC)
└── security/
    ├── __init__.py
    ├── auth.py                (23 LOC)
    └── encryption.py          (63 LOC)
```

## Next Phase
Phase 2: Cloud relay + mobile app (Supabase backend, Kotlin/Jetpack Compose mobile)
