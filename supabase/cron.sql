-- =============================================================================
-- Schedule the Flask cron endpoints from Supabase (pg_cron + pg_net)
-- =============================================================================
-- 1. Store the backend URL and CRON_SECRET in Vault (Dashboard → Vault, or SQL):
--      select vault.create_secret('https://YOUR-CLOUD-RUN-URL', 'backend_url');
--      select vault.create_secret('YOUR_CRON_SECRET',         'cron_secret');
--    (no trailing slash on the URL; the value must match the backend's CRON_SECRET)
-- 2. Run this file. It enables pg_cron and pg_net itself, and is safe to re-run
--    (cron.schedule with an existing job name updates that job).
--
-- Do NOT also schedule the old Supabase Edge Functions in adulting/supabase/functions
-- (monthly-loan-deductions, monthly-appreciation, daily-volatility, ...). They
-- duplicate these jobs and would charge loans/rent twice.
-- =============================================================================

-- pg_net creates the `net` schema (net.http_post); pg_cron creates the `cron` schema.
-- Both must exist before the function below can be created.
create extension if not exists pg_net;
create extension if not exists pg_cron with schema pg_catalog;

create or replace function public.call_backend_cron(p_path text)
returns bigint
language sql
security definer set search_path = public
as $$
  select net.http_post(
    url     := (select decrypted_secret from vault.decrypted_secrets where name = 'backend_url') || p_path,
    headers := jsonb_build_object(
      'Content-Type',  'application/json',
      'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name = 'cron_secret')
    ),
    body    := '{}'::jsonb,
    timeout_milliseconds := 300000
  );
$$;
revoke execute on function public.call_backend_cron(text) from public, anon, authenticated;

select cron.schedule('mentor-analysis',  '0 6 * * *',   $$select public.call_backend_cron('/api/cron/mentor-analysis/')$$);
select cron.schedule('random-events',    '0 9 * * *',   $$select public.call_backend_cron('/api/cron/random-events/')$$);
select cron.schedule('inactive-users',   '0 10 * * *',  $$select public.call_backend_cron('/api/cron/inactive-users-monitor/')$$);
-- At most one "your week is ready" push per player per day, from a cast member.
select cron.schedule('week-ready',       '0 16 * * *',  $$select public.call_backend_cron('/api/cron/week-ready/')$$);
select cron.schedule('push-receipts',    '20 * * * *',  $$select public.call_backend_cron('/api/cron/push-receipts/')$$);
select cron.schedule('market-monitor',   '0 */4 * * *', $$select public.call_backend_cron('/api/cron/market-monitor/')$$);
select cron.schedule('depreciation',     '0 2 1 * *',   $$select public.call_backend_cron('/api/cron/depreciation/')$$);
select cron.schedule('appreciation',     '0 3 1 * *',   $$select public.call_backend_cron('/api/cron/appreciation/')$$);
-- monthly-payday only covers players still on calendar time. Players on game
-- time (This Week, table player_game_clock) get their month every 4th game week.
select cron.schedule('monthly-payday',   '0 4 1 * *',   $$select public.call_backend_cron('/api/cron/loan-deductions/')$$);

-- Inspect:   select * from cron.job;   select * from cron.job_run_details order by start_time desc limit 20;
-- Remove:    select cron.unschedule('monthly-payday');
