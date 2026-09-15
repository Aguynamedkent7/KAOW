-- KAOW Phase 2: Core schema
-- Run in Supabase SQL Editor or via `supabase db push`

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ============================================================
-- DEVICES
-- Each PC daemon registers as a device belonging to a user.
-- ============================================================
create table public.devices (
  id         uuid primary key default uuid_generate_v4(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  name       text not null default 'My PC',
  status     text not null default 'offline'
             check (status in ('offline', 'online', 'busy')),
  public_key text,                         -- E2E encryption key (Phase 2+)
  last_seen  timestamptz,
  created_at timestamptz not null default now()
);

create index idx_devices_user_id on public.devices(user_id);

comment on table public.devices is 'PC daemons registered to a user.';

-- ============================================================
-- COMMANDS
-- Phone sends a prompt; daemon picks it up and executes.
-- ============================================================
create table public.commands (
  id           uuid primary key default uuid_generate_v4(),
  device_id    uuid not null references public.devices(id) on delete cascade,
  user_id      uuid not null references auth.users(id) on delete cascade,
  prompt       text not null,
  status       text not null default 'queued'
               check (status in ('queued', 'running', 'completed', 'failed', 'killed')),
  error_message text,
  created_at   timestamptz not null default now(),
  started_at   timestamptz,
  completed_at timestamptz
);

create index idx_commands_device_id on public.commands(device_id);
create index idx_commands_user_id   on public.commands(user_id);
create index idx_commands_status    on public.commands(status)
  where status in ('queued', 'running');

comment on table public.commands is 'Command queue: phone → daemon.';

-- ============================================================
-- COMMAND_OUTPUTS
-- Streaming output chunks from daemon back to phone.
-- ============================================================
create table public.command_outputs (
  id         bigserial primary key,
  command_id uuid not null references public.commands(id) on delete cascade,
  chunk      text not null,
  seq        integer not null,             -- ordering within a command
  created_at timestamptz not null default now()
);

create index idx_command_outputs_command_id on public.command_outputs(command_id, seq);

comment on table public.command_outputs is 'Streaming output chunks for a command.';

-- ============================================================
-- SCREENSHOTS
-- Captured by daemon, stored as base64 (Phase 2).
-- Phase 3+: consider Supabase Storage for binary blobs.
-- ============================================================
create table public.screenshots (
  id           uuid primary key default uuid_generate_v4(),
  device_id    uuid not null references public.devices(id) on delete cascade,
  command_id   uuid references public.commands(id) on delete set null,
  image_base64 text not null,
  width        integer not null default 1920,
  height       integer not null default 1080,
  created_at   timestamptz not null default now()
);

create index idx_screenshots_device_id on public.screenshots(device_id, created_at desc);

comment on table public.screenshots is 'Screenshots captured by daemon.';
