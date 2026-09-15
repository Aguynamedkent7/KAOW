-- KAOW Phase 2: Row-Level Security policies
-- Requires 001_initial_schema.sql to be applied first.

-- Enable RLS on all tables
alter table public.devices         enable row level security;
alter table public.commands        enable row level security;
alter table public.command_outputs enable row level security;
alter table public.screenshots     enable row level security;

-- ============================================================
-- DEVICES policies
-- ============================================================
-- Users can see their own devices
create policy "Users see own devices"
  on public.devices for select
  using (auth.uid() = user_id);

-- Users can register new devices
create policy "Users create own devices"
  on public.devices for insert
  with check (auth.uid() = user_id);

-- Users can update their own devices (name, status)
create policy "Users update own devices"
  on public.devices for update
  using (auth.uid() = user_id);

-- Daemon service role can update any device (for heartbeat/status)
create policy "Service role updates devices"
  on public.devices for update
  using (auth.role() = 'service_role');

-- ============================================================
-- COMMANDS policies
-- ============================================================
-- Users see commands they sent
create policy "Users see own commands"
  on public.commands for select
  using (auth.uid() = user_id);

-- Users can insert commands for their own devices
create policy "Users create commands for own devices"
  on public.commands for insert
  with check (
    auth.uid() = user_id
    and exists (
      select 1 from public.devices
      where devices.id = device_id
        and devices.user_id = auth.uid()
    )
  );

-- Daemon service role can update command status + output
create policy "Service role manages commands"
  on public.commands for all
  using (auth.role() = 'service_role');

-- ============================================================
-- COMMAND_OUTPUTS policies
-- ============================================================
-- Users see outputs for their own commands
create policy "Users see own command outputs"
  on public.command_outputs for select
  using (
    exists (
      select 1 from public.commands
      where commands.id = command_id
        and commands.user_id = auth.uid()
    )
  );

-- Daemon service role inserts output chunks
create policy "Service role inserts outputs"
  on public.command_outputs for insert
  with check (auth.role() = 'service_role');

-- ============================================================
-- SCREENSHOTS policies
-- ============================================================
-- Users see screenshots for their own devices
create policy "Users see own device screenshots"
  on public.screenshots for select
  using (
    exists (
      select 1 from public.devices
      where devices.id = device_id
        and devices.user_id = auth.uid()
    )
  );

-- Daemon service role inserts screenshots
create policy "Service role inserts screenshots"
  on public.screenshots for insert
  with check (auth.role() = 'service_role');
