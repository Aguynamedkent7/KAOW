-- KAOW Supabase helper: register_device function
-- Called by daemon on startup to upsert its device record.

create or replace function public.register_device(
  p_user_id uuid,
  p_device_name text default 'My PC',
  p_public_key text default null
)
returns uuid
language plpgsql
security definer  -- runs as the function owner, bypasses RLS
as $$
declare
  v_device_id uuid;
begin
  insert into public.devices (user_id, name, public_key, status, last_seen)
  values (p_user_id, p_device_name, p_public_key, 'online', now())
  on conflict (user_id, name)
  do update set
    status = 'online',
    last_seen = now(),
    public_key = excluded.public_key
  returning id into v_device_id;

  return v_device_id;
end;
$$;

comment on function public.register_device is 'Upsert a device by user_id + name. Returns the device UUID.';
