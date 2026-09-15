-- KAOW Phase 2: Enable Supabase Realtime on tables
-- The mobile app subscribes to these for live updates.

-- Enable realtime for commands (phone watches for status changes)
alter publication supabase_realtime add table public.commands;

-- Enable realtime for command_outputs (phone watches streaming output)
alter publication supabase_realtime add table public.command_outputs;

-- Enable realtime for screenshots (phone watches for new screenshots)
alter publication supabase_realtime add table public.screenshots;
