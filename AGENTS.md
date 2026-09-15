# KAOW — Agent Instructions

## Project Overview
KAOW (Kents AI Officiated Workflow) is a multi-user system where a phone app
remotely controls a PC daemon wrapping AI CLIs (Claude, OpenDevin) for
headless automation.

**Flow**: Phone → Supabase (auth + relay) → PC Daemon → AI CLI → Virtual Display → Screenshots

## Tech Stack
- **Daemon**: Python 3.11+, FastAPI, WebSockets, Pydantic, uv
- **Mobile**: Kotlin, Jetpack Compose, Supabase Kotlin SDK
- **Database**: Supabase (PostgreSQL + realtime)
- **Infra**: Docker, docker-compose, systemd

## Code Conventions (REQUIRED)
- PEP 8, type hints everywhere, max 100 chars/line
- **MAX 300 lines per code file** — split into modules/functions if approaching limit
- Docstrings on all public APIs
- No secrets in code — env vars / .env only
- No empty try-except blocks — fail loudly
- No default fallbacks during development — explicit errors only
- Don't reinvent the wheel — use established libraries
- Design mobile UI for end-user mental model, not DB schema

## Git Workflow
- Conventional commits: `type(scope): description`
  - Types: feat, fix, docs, refactor, test, ci, chore
  - Scopes: daemon, mobile, shared, infra, docs
- Branch flow (every task): feature branch → staging → main (eventually)
  1. Create a new branch per task: `git switch -c feat/<scope>-<desc>`
  2. Commit the task's work on that branch
  3. Merge into `staging`: `git switch staging && git merge <branch>`
  4. Promote `staging` to `main` only when deliberately releasing (not automatically)
- No commits without user permission
- No force-push, no interactive rebase unless asked
- Small, reviewable commits

## File Organization
- Abstract base classes for all swappable components (adapters, display, telemetry)
- Entry points stay thin — delegate to modules
- Tests colocated with package (tests/ in each package)
- All config via environment variables

## Development Phases
- Phase 1: Local PoC (daemon-first) → docs/PHASE1.md
- Phase 2: Cloud relay + mobile → docs/PHASE2.md
- Phase 3: Power management → docs/PHASE3.md
- Phase 4: Cross-platform packaging → docs/PHASE4.md
- Phase 5: Deployment & zero-touch setup (one-command installers) → docs/PHASE5.md
- Phase 6: Secure terminal QR pairing (device↔user handshake) → docs/PHASE6.md

## Running & Testing
- Daemon: `cd daemon && uv run kaow`
- Tests: `cd daemon && uv run pytest`
- Lint: `cd daemon && uv run ruff check src/ && uv run mypy src/`
- Mobile: `./gradlew :app:installDebug`

## Container-First Policy
- Daemon runs in Docker by default
- No system packages installed on host unless explicitly told
- Dockerfile lives in daemon/
- docker-compose.yml at project root orchestrates full stack

## Definition of Done
A task is done when:
- Change is implemented
- Linting passes (ruff + mypy for Python)
- Documentation updated (PHASE*.md, ARCHITECTURE.md, etc.)
- CONTINUITY.md updated if goal/state/decisions changed
- No empty error handlers, no silent failures

## IMPORTANT
- Read docs/PHASE*.md before starting any task
- Read .agent/CONTINUITY.md at start of every turn
- Never commit without user permission
- Document ALL progress, decisions, and blockers
- Prefer editing existing files over creating new ones
- Keep code modular and under 300 LOC per file
