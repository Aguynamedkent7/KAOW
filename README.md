# KAOW — Kents AI Officiated Workflow

[![daemon-ci](https://github.com/Aguynamedkent7/KAOW/actions/workflows/daemon-ci.yml/badge.svg)](https://github.com/Aguynamedkent7/KAOW/actions/workflows/daemon-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)

Turn any PC into a headless, remote AI workstation. KAOW is a system where your
**phone** controls a **PC daemon** that wraps AI CLIs (Claude, OpenDevin) to run
automation tasks unattended — with live screenshots, streaming output, and full
conversation history.

```
Phone (Kotlin/Compose) → PC Daemon (direct Tailscale WS) → AI CLI → Virtual Display → Screenshots
```

## Why KAOW?

- **Headless automation** — your PC needs no monitor, keyboard, or mouse. A virtual display (Xvfb) gives the AI screen real estate to interact with GUI apps.
- **Remote from anywhere** — trigger tasks from your phone's lock screen. Offline commands queue and execute when the connection returns.
- **AI-agnostic** — pluggable adapters for Claude CLI, OpenDevin, or any future CLI. Swap via one config value.
- **Full history** — every conversation, screenshot, and log is persisted for replay and audit.
- **Privacy-first** — designed with end-to-end encryption between your phone and PC (planned Phase 2).

## Status

> **Phase 1 done; Phase 2 in progress.** The Python daemon core is built and tested
> (43 tests passing). The mobile app now connects directly to the daemon over a
> Tailscale tailnet: QR pairing, streaming chat, live screenshots. Power management,
> encryption, and one-line installers follow.

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Local PoC — daemon-first | **Done** |
| 2 | Mobile app — Tailscale P2P | **In progress** |
| 3 | Power management (Wake-on-LAN) | Planned |
| 4 | Cross-platform packaging | Planned |
| 5 | Zero-touch deployment (one-line installers) | Planned |
| 6 | Secure terminal QR pairing | In progress (base pairing shipped with Phase 2) |

Detailed plans in [`docs/PHASE*.md`](docs/). Roadmap goals and known issues are
tracked in `.agent/CONTINUITY.md`.

## Repository layout

```
KAOW/
├── daemon/                 # The PC agent (Python 3.11+, FastAPI, uv)
│   ├── src/kaow/
│   │   ├── server/         # WebSocket server, auth, message protocol
│   │   ├── adapters/       # AI CLI wrappers (Claude, OpenDevin)
│   │   ├── display/        # Xvfb virtual display + screenshot capture
│   │   ├── telemetry/      # CPU/RAM/disk/process monitoring
│   │   ├── queue/          # Offline command buffering
│   │   ├── transcript/     # Local SQLite conversation history
│   │   ├── security/       # Token auth (AES-GCM planned)
│   │   ├── pair.py         # `kaow pair` QR pairing CLI
│   │   └── main.py         # Entry point (thin)
│   ├── tests/              # Unit + WebSocket integration tests
│   └── Dockerfile
├── mobile/                 # Android app (Kotlin/Jetpack Compose) — Phase 2
├── shared/protocol/        # Cross-language message schema reference
├── docs/                   # Architecture, API, phase plans
└── .agent/CONTINUITY.md    # Agent continuity ledger (goal/state/decisions)
```

## Quick start (daemon)

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Xvfb is needed
on Linux for the virtual display (`sudo pacman -S xorg-server-xvfb`).

```bash
# 1. Clone
git clone https://github.com/Aguynamedkent7/KAOW.git
cd KAOW

# 2. Install
cd daemon
uv sync --dev

# 3. Configure (auth token required)
cp ../.env.example ../.env
# edit KAOW_AUTH_TOKEN — this is what your client uses to connect

# 4. Run
uv run kaow

# 5. Pair your phone (prints a scannable QR code)
uv run kaow-pair
```

Then connect `ws://<tailnet-address>:8765/ws?token=YOUR_TOKEN` — the mobile app
does this for you when you scan the QR — or send a command manually via the
[protocol spec](docs/API.md).

## Verify your setup

```bash
cd daemon
uv run ruff check src/ tests/     # lint
uv run mypy src/                  # typecheck
uv run pytest                     # tests
```

## Docker

```bash
docker-compose up --build
```

The daemon image is also published to GHCR on new `v*` tags
(`ghcr.io/aguynamedkent/kaow-daemon`).

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — system overview and data flow
- [WebSocket API](docs/API.md) — full message protocol reference
- [Setup guide](docs/SETUP.md) — env vars, Docker, mobile
- [Development phases](docs/PHASE1.md) … [PHASE6](docs/PHASE6.md)
- [Agent instructions](AGENTS.md) — conventions for contributors/agents

## Contributing

- **Code conventions:** PEP 8, type hints, ≤300 lines per file, no silent
  error handlers, no default fallbacks in dev. See [`AGENTS.md`](AGENTS.md).
- **Commits:** conventional commits (`feat(daemon): …`, `fix(mobile): …`).
- Please update `.agent/CONTINUITY.md` and the relevant `docs/PHASE*.md` with
  any changes (progress, decisions, blockers).

## License

[MIT](LICENSE) © 2026 Aguynamedkent7