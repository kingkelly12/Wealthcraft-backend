-- =============================================================================
-- Lives: character, age, backgrounds and endings (roguelite runs)
-- =============================================================================
-- Each player plays one life at a time. A life has a background (starting
-- conditions), an avatar and a start age; age comes from the game clock
-- (52 game weeks = 1 year). A life ends with an ending (burnout, debt-free,
-- millionaire...) and a summary, then the player can start a new one.
--
-- Starting a new life resets the run (money, job, home, assets, loans,
-- missions, game clock) and keeps the person (username, follows, Void posts,
-- history). See app/game/life.py in the backend.
-- =============================================================================

create table if not exists public.player_lives (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references public.profiles(user_id) on delete cascade,
  life_number  integer not null check (life_number >= 1),
  background   text not null,
  start_age    integer not null default 18 check (start_age between 14 and 30),
  avatar       jsonb not null default '{}',
  is_current   boolean not null default true,
  started_at   timestamptz not null default now(),
  ended_at     timestamptz,
  ending       text,
  summary      jsonb,
  unique (user_id, life_number)
);
-- At most one current life per player.
create unique index if not exists player_lives_one_current on public.player_lives (user_id) where is_current;
create index if not exists player_lives_user_idx on public.player_lives (user_id, life_number desc);

-- RLS on with no policies: only the Flask backend (service role) uses it.
alter table public.player_lives enable row level security;
