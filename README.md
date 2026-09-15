# KAOW — Kents AI Officiated Workflow

Phone-controlled PC daemon that wraps AI CLIs (Claude, OpenDevin) for headless automation.

## Architecture

```
Phone (Kotlin/Compose) → Supabase (Cloud Relay) → PC Daemon (Python/FastAPI) → AI CLI → Virtual Display → Screenshots
```

## Quick Start

```bash
# Clone
git clone https://github.com/aguynamedkent/KAOW.git
cd KAOW

# Configure
cp .env.example .env

# Run daemon
cd daemon
pip install -e ".[dev]"
kaow

# Run tests
uv run pytest
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [API Reference](docs/API.md)
- [Phase 1 Progress](docs/PHASE1.md)

## License

MIT
