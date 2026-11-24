-- =============================================================================
-- Player activity: the timeline on a player's profile ("Bought the Lakehouse · 3d")
-- =============================================================================
-- Written by the backend whenever a player makes a move their followers hear about
-- (ExpoPushService.notify_followers_of_financial_move), and shown by
-- /api/profile/overview/. Server-only: RLS on, no policies. Safe to run more than once.
-- =============================================================================

create table if not exists public.player_activity (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  kind       text not null,
  emoji      text,
  text       text not null,
  item_name  text,
  amount     numeric,
  profit     numeric,
  created_at timestamptz not null default now()
);
create index if not exists player_activity_user_idx on public.player_activity (user_id, created_at desc);
alter table public.player_activity enable row level security;
