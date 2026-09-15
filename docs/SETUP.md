# KAOW Setup Guide

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Xvfb (Linux) for headless display
- An AI CLI: [Claude CLI](https://docs.anthropic.com/claude/docs/cli) or [OpenDevin](https://github.com/All-Hands-AI/OpenHands)

## Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/aguynamedkent/KAOW.git
cd KAOW

# 2. Install daemon dependencies
cd daemon
uv sync  # or: pip install -e ".[dev]"

# 3. Configure
cp ../.env.example ../.env
# Edit .env with your auth token and CLI adapter settings

# 4. Run the daemon
uv run kaow  # or: python -m kaow.main
```

## Docker

```bash
# Build and run with docker-compose
docker-compose up --build
```

## Mobile App

```bash
# Open in Android Studio or build from CLI
cd mobile
./gradlew :app:installDebug
```

## Configuration

All settings are configured via environment variables (prefix `KAOW_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `KAOW_HOST` | `0.0.0.0` | Server bind address |
| `KAOW_PORT` | `8765` | WebSocket port |
| `KAOW_AUTH_TOKEN` | (required) | Bearer token for auth |
| `KAOW_CLI_ADAPTER` | `claude` | AI CLI to use (`claude` or `opendevin`) |
| `KAOW_CLI_PATH` | `claude` | Path to CLI binary |
| `KAOW_DISPLAY_RESOLUTION` | `1920x1080` | Virtual display resolution |
| `KAOW_SCREENSHOT_INTERVAL` | `5` | Seconds between screenshots |
| `KAOW_LOG_LEVEL` | `INFO` | Logging level |

## Running Tests

```bash
cd daemon
uv run pytest
```

## Linting

```bash
cd daemon
uv run ruff check src/
uv run mypy src/
```
