# Phase 3 — Power Management & Autonomy

## Goal
Enable remote power control: Wake-on-LAN to turn on the PC, and graceful remote shutdown.

## Status: PLANNED

## Planned Tasks
- [ ] Configure PC BIOS for Wake-on-LAN (requires ethernet)
- [ ] Configure OS for WoL (systemd/networkd)
- [ ] Build WoL packet sender in daemon
- [ ] Build mobile trigger to send WoL magic packet
- [ ] Implement graceful remote shutdown commands
- [ ] Build Raspberry Pi WoL bridge for remote boot over internet
- [ ] Document BIOS/OS configuration steps

## Dependencies
- Phase 2 complete (mobile app with power controls)
- Ethernet connection on target PC
- Raspberry Pi (optional, for remote WoL)

## Known Limitations
- WoL requires same local network unless using a bridge
- Remote boot over internet needs Raspberry Pi or smart plug with AC recovery
- Graceful shutdown requires the daemon to be running

## Decisions
(Pending — will be added during Phase 3)
