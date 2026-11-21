-- =============================================================================
-- Turn-based time: "This Week"
-- =============================================================================
-- Game time is decoupled from the calendar. One turn = one in-game week, played
-- as a short deck of swipe cards. Every 4th week the player's month runs
-- (salary, loans, rent, living costs, asset income, missions).
--
-- Weeks unlock one per real day; up to 2 can be banked, so a missed day leaves
-- a catch-up deck instead of a broken streak.
--
-- A player with a row in player_game_clock is "on game time": the calendar
-- monthly job (/api/cron/loan-deductions) and the daily random life events
-- skip them. Players without a row stay on the calendar until they first open
-- This Week, so nobody is ever paid or charged twice.
-- =============================================================================

create table if not exists public.player_game_clock (
  user_id          uuid primary key references public.profiles(user_id) on delete cascade,
  week             integer not null default 1 check (week >= 1),   -- the week being played
  banked_weeks     integer not null default 1 check (banked_weeks >= 0),
  bank_updated_on  date not null default (now() at time zone 'utc')::date,
  started_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
drop trigger if exists player_game_clock_updated_at on public.player_game_clock;
create trigger player_game_clock_updated_at before update on public.player_game_clock
  for each row execute function public.set_updated_at();

create table if not exists public.player_weeks (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references public.profiles(user_id) on delete cascade,
  week          integer not null,
  cards         jsonb not null default '[]',
  version       integer not null default 0,     -- optimistic lock for card choices
  status        text not null default 'open' check (status in ('open', 'completed')),
  receipt       jsonb,
  created_at    timestamptz not null default now(),
  completed_at  timestamptz,
  unique (user_id, week)
);
create index if not exists player_weeks_user_week_idx on public.player_weeks (user_id, week desc);

-- RLS on with no policies, like the rest of the schema: only the Flask
-- backend (service role) reads or writes these.
alter table public.player_game_clock enable row level security;
alter table public.player_weeks enable row level security;
