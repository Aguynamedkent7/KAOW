# Phase 4 — Modularity & Cross-Platform Packaging

## Goal
Make KAOW a one-click install on any platform with automated setup, containerized dependencies, and auto-start on boot.

## Status: PLANNED

## Planned Tasks
- [ ] Write cross-platform install script (Bash for Linux/Mac, PowerShell for Windows)
- [ ] Auto-detect OS and install dependencies
- [ ] Containerize AI CLI + virtual display tools in Docker
- [ ] Multi-stage Docker build for minimal image size
- [ ] Set daemon to auto-start on boot (systemd for Linux, Task Scheduler for Windows)
- [ ] Create uninstall script
- [ ] Package mobile app for distribution (APK signing, Play Store?)
- [ ] End-to-end testing across platforms

## Dependencies
- Phases 1-3 complete
- Docker installed on target machine
- Platform-specific: Xvfb (Linux), virtual display driver (Windows/Mac)

## Known Challenges
- Windows virtual display (no Xvfb equivalent — need WinAPI or third-party)
- macOS virtual display (need CoreGraphics or third-party)
- AI CLI installation varies by platform
- Docker on Windows requires WSL2

## Decisions
(Pending — will be added during Phase 4)
