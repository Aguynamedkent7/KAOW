-- KAOW seed data for local development.
-- Run after migrations: supabase db reset

-- Note: Supabase auth users are created via the Auth API,
-- not via SQL. Use `supabase auth signup` or the dashboard
-- to create a test user, then replace the UUID below.
--
-- Example:
--   insert into auth.users (id, email, encrypted_password)
--   values ('00000000-0000-0000-0000-000000000001', 'test@kaow.dev', crypt('test1234', gen_salt('bf')));

-- After creating a test user, register a sample device:
-- insert into public.devices (id, user_id, name, status)
-- values (
--   '11111111-1111-1111-1111-111111111111',
--   '00000000-0000-0000-0000-000000000001',
--   'Test Desktop',
--   'online'
-- );
