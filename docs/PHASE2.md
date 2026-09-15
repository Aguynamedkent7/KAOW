# Phase 2 — Cloud Relay + Mobile App

## Goal
Set up Supabase for auth and real-time command routing, build the Kotlin/Jetpack Compose mobile app, and test bidirectional communication over the internet.

## Status: PLANNED

## Planned Tasks
- [ ] Set up Supabase project (auth, database, realtime)
- [ ] Design database schema (users, commands, sessions, screenshots)
- [ ] Implement row-level security policies
- [ ] Build mobile app skeleton (Kotlin + Jetpack Compose)
- [ ] Implement chat interface (text/voice input)
- [ ] Implement live dashboard (screenshots, terminal logs)
- [ ] Connect mobile app to daemon via Supabase relay
- [ ] Test bidirectional communication outside local network
- [ ] Implement conversation history persistence
- [ ] E2E encryption for screenshots and logs

## Dependencies
- Phase 1 complete (daemon with WebSocket server)
- Supabase project created
- Android development environment

## Known Risks
- Supabase realtime subscription latency
- Mobile app WebSocket handling on background/foreground transitions
- Screenshot base64 encoding size over cellular networks

## Decisions
(Pending — will be added during Phase 2)
