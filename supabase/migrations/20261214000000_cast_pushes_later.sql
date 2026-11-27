-- =============================================================================
-- Cast texts push a few hours later (jobs/cast_pushes.py)
-- * cast_messages.push_due_at: when to push a text (empty = never).
-- * cast_messages.pushed_at: handled (pushed, or no longer worth pushing).
-- * A scheduled job every 15 minutes calls the backend.
-- Run this BEFORE deploying the backend that uses it. Safe to run more than once.
-- =============================================================================
begin;

alter table public.cast_messages add column if not exists push_due_at timestamptz;
alter table public.cast_messages add column if not exists pushed_at timestamptz;
create index if not exists cast_messages_push_due_idx on public.cast_messages (push_due_at) where pushed_at is null;

commit;

-- Uses call_backend_cron() from supabase/cron.sql (already set up if your other jobs run).
do $$
begin
  perform cron.schedule('cast-pushes', '*/15 * * * *', 'select public.call_backend_cron(''/api/cron/cast-pushes/'')');
exception when others then
  raise notice 'cast-pushes not scheduled: run supabase/cron.sql first (%)', sqlerrm;
end $$;

select jobname, schedule from cron.job where jobname = 'cast-pushes';
