# Phase 5 — Deployment & Zero-Touch Setup

## Goal
Plug-and-play installation on any OS without manual configuration. User runs one command per platform.

## Status: PLANNED

## The One-Line Installer

**Linux/macOS:**
```bash
curl -sSL https://raw.githubusercontent.com/aguynamedkent/kaow/main/install.sh | bash
```

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/aguynamedkent/kaow/main/install.ps1 | iex
```

### Execution Flow (install.sh / install.ps1)

1. **Environment Check**
   - Detects OS, architecture
   - Checks for required dependencies: Docker, Python/Node, virtual display drivers
     (Xvfb for Linux headless rendering)
   - Fails loudly on missing requirements — no silent partial installs

2. **Fetch Payload**
   - Downloads the latest KAOW PC Daemon binary or Docker image

3. **Generate Credentials**
   - Generates a unique `device_id` (UUID) and temporary `pairing_secret` on the local machine

4. **Initiate Pairing Mode**
   - Temporarily launches a lightweight setup process that prints a QR code to the terminal and waits
   - See Phase 6 for the full pairing handshake protocol

5. **Persistence (Post-Pairing)**
   - Creates `.env` file with generated credentials
   - Registers daemon as a background service:
     - Linux: systemd
     - Windows: Task Scheduler
   - Starts the headless agent

## Deliverables
- `scripts/install.sh` — Linux/macOS installer
- `scripts/install.ps1` — Windows installer
- `scripts/uninstall.sh` / `scripts/uninstall.ps1`
- `daemon/scripts/pairing.py` — QR display + pairing socket listener
- systemd unit file (`kaow.service`)
- Task Scheduler XML template

## Dependencies
- Phase 1 complete (daemon core)
- Phase 2 complete (cloud auth + pairing backend)
- Phase 4 complete (Docker packaging + OS detection)

## Known Risks
- QR terminal rendering varies by terminal (ANSI block support)
- Windows PowerShell execution policy restrictions for `irm | iex`
- Docker availability on Windows requires WSL2 backend

## Decisions
(Pending — will be added during Phase 5 implementation)