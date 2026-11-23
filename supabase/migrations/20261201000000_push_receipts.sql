-- =============================================================================
-- Push receipts: clean up tokens of uninstalled apps
-- =============================================================================
-- Expo answers every push with a *ticket*. "ok" only means Expo accepted it;
-- whether the phone got it arrives minutes later as a *receipt*. On Android,
-- an uninstalled app usually only shows up there (DeviceNotRegistered), so
-- without reading receipts dead tokens were never cleared.
--
-- The backend stores accepted tickets here; /api/cron/push-receipts/ (hourly,
-- see supabase/cron.sql) reads the receipts, clears dead tokens and deletes the
-- tickets. Server-only table: RLS on, no policies.
-- =============================================================================

create table if not exists public.push_tickets (
  ticket_id  text primary key,
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  token      text not null,
  created_at timestamptz not null default now()
);
create index if not exists push_tickets_created_idx on public.push_tickets (created_at);

alter table public.push_tickets enable row level security;

-- A device belongs to one player at a time (enforced by the register endpoint);
-- this index also makes "clear this token" lookups fast.
create index if not exists profiles_expo_push_token_idx on public.profiles (expo_push_token)
  where expo_push_token is not null;
