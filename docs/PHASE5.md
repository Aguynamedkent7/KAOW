# Phase 5 — Deployment & Zero-Touch Setup

## Goal
Plug-and-play installation with minimal user input: one command downloads the daemon,
installs Tailscale + Xvfb, generates the auth token, registers a background service,
and prints the pairing QR. "Low user input" is the priority (user directive 2026-09-16).

## Status: PLANNED (design only — no code written yet)

## The One-Line Installer

**Linux/macOS (bash):**
```bash
curl -sSL https://raw.githubusercontent.com/aguynamedkent/kaow/main/daemon/scripts/bootstrap.sh | bash
```
**Windows (PowerShell):** (deferred — Tailscale wire install first, PS installer later)

### Execution Flow (`daemon/scripts/bootstrap.sh`)

1. **Distro detect** — `pacman`/`apt`/`dnf`/`brew`/`apk`; fail loudly on unknown
2. **Install system deps** (single `sudo` prompt, no TTY needed):
   - `tailscale` (+ `tailscaled.service` on Arch — NOT `tailscale.service`)
   - `xorg-server-xvfb` (headless virtual display)
3. **Enable + start daemon service**
   - `sudo systemctl enable --now tailscaled` (Arch) / `tailscale up` otherwise
4. **Tailscale login** — two modes:
   - **Hands-free**: pre-set `TS_AUTHKEY` env → `tailscale up --authkey=$TS_AUTHKEY`
   - **Interactive fallback**: `tailscale up` prints a one-click URL for the user
5. **Generate credentials** — `KAOW_AUTH_TOKEN=$(openssl rand -hex 24)` into `daemon/.env`
6. **Install `kaow.service`** (systemd unit from repo, `WantedBy=multi-user.target`),
   `ExecStart=/usr/bin/bash -lc 'cd <install-dir>/daemon && uv run kaow'`; enable + start
7. **Wait for port 8765**, then run `kaow pair` → prints QR to terminal

### Persistence (Post-Pairing)
- `.env` created with token; no secrets hardcoded (D-block rule)
- Optional Docker variant: `tailscale/tailscale` sidecar + daemon in container,
  HALO/Tailscale peers, `KAOW_*` env passthrough — later phase

## Deliverables (design)
- `daemon/scripts/bootstrap.sh` — main one-liner installer
- `daemon/systemd/kaow.service` — systemd unit
- Optionally `install.sh` at repo root — thin wrapper downloading bootstrap.sh

## Dependencies
- Phase 1 + Phase 2 complete (daemon + direct WS transport). QR pairing already shipped
  via `kaow pair` (Phase 6 pulled forward).
- Phase 4 (cross-platform packaging) partial — daemon runs via `uv`, Dockerfile exists.

## Known Risks
- QR terminal rendering varies by terminal (ANSI block support) — existing `kaow pair`
- `sudo` inside a piped curl|bash cannot prompt for password on some setups — instruct
  user to run with `sudo -E` first, or require TS_AUTHKEY for hands-free
- Docker sidecar on Arch adds complexity; keep bare daemon path primary

## Decisions
- D-P5-001 [USER 2026-09-16]: **bootstrap.sh plan agreed, but CODE IS PLAN-ONLY for now** —
  user asked to document first, implement in a later session
- D-P5-002 [DESIGN]: Tailscale login = TS_AUTHKEY hands-free with interactive URL fallback
- D-P5-003 [DESIGN]: systemd `kaow.service` runs daemon via `uv run`; no host system packages
  beyond tailscale + xvfb (container-first policy otherwise)