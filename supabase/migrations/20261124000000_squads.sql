-- =============================================================================
-- Squads: a named crew of up to 8 players who play together
-- =============================================================================
-- * squads: name, emoji, a join code, the squad streak and last week's MVP.
-- * squad_members: one squad per player (user_id is the primary key).
-- * squad_member_weeks: each member's real calendar week (Monday UTC) in the
--   squad: net worth at the start of the week (for the "growth" race) and how
--   many game weeks they played (for the co-op squad goal).
-- * squad_feed / squad_reactions: what happened in the squad, and emoji reacts.
--
-- Squads run on the real calendar because every player's game clock is
-- different. Weekly settlement (MVP, streak) is done lazily by the backend the
-- first time anyone touches the squad in a new week, so there is no cron.
-- =============================================================================

create table if not exists public.squads (
  id             uuid primary key default gen_random_uuid(),
  name           text not null check (char_length(name) between 2 and 24),
  emoji          text not null default '🔥',
  code           text not null unique,
  owner_id       uuid references public.profiles(user_id) on delete set null,
  created_at     timestamptz not null default now(),
  settled_week   date not null,                         -- Monday of the last week whose MVP was decided
  goal_hit_week  date not null default '2000-01-03',    -- Monday of the last week the squad goal was hit
  streak         integer not null default 0,            -- consecutive weeks the goal was hit
  last_mvp       jsonb                                  -- {user_id, username, growth, week_start}
);

create table if not exists public.squad_members (
  user_id    uuid primary key references public.profiles(user_id) on delete cascade,
  squad_id   uuid not null references public.squads(id) on delete cascade,
  role       text not null default 'member' check (role in ('owner', 'member')),
  joined_at  timestamptz not null default now()
);
create index if not exists squad_members_squad_idx on public.squad_members (squad_id);

-- At most 8 members, enforced in the database so two people joining at once
-- can't make it 9.
create or replace function public.squad_members_limit() returns trigger
language plpgsql as $$
begin
  perform 1 from public.squads where id = new.squad_id for update;
  if (select count(*) from public.squad_members where squad_id = new.squad_id) >= 8 then
    raise exception 'SQUAD_FULL' using errcode = 'P0001';
  end if;
  return new;
end $$;
drop trigger if exists squad_members_limit on public.squad_members;
create trigger squad_members_limit before insert on public.squad_members
  for each row execute function public.squad_members_limit();

create table if not exists public.squad_member_weeks (
  squad_id         uuid not null references public.squads(id) on delete cascade,
  user_id          uuid not null references public.profiles(user_id) on delete cascade,
  week_start       date not null,
  start_net_worth  numeric(14,2) not null default 0,
  end_net_worth    numeric(14,2),                 -- set when the week is settled
  weeks_played     integer not null default 0,
  rewarded         boolean not null default false,  -- got the squad-goal reward this week
  primary key (squad_id, user_id, week_start)
);
create index if not exists squad_member_weeks_user_idx on public.squad_member_weeks (user_id, week_start);

create table if not exists public.squad_feed (
  id          uuid primary key default gen_random_uuid(),
  squad_id    uuid not null references public.squads(id) on delete cascade,
  user_id     uuid references public.profiles(user_id) on delete set null,  -- null for squad-wide posts
  kind        text not null,
  emoji       text not null,
  body        text not null,
  created_at  timestamptz not null default now()
);
create index if not exists squad_feed_squad_idx on public.squad_feed (squad_id, created_at desc);

create table if not exists public.squad_reactions (
  feed_id     uuid not null references public.squad_feed(id) on delete cascade,
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  emoji       text not null,
  created_at  timestamptz not null default now(),
  primary key (feed_id, user_id)
);

-- RLS on with no policies: only the Flask backend (service role) uses these.
alter table public.squads enable row level security;
alter table public.squad_members enable row level security;
alter table public.squad_member_weeks enable row level security;
alter table public.squad_feed enable row level security;
alter table public.squad_reactions enable row level security;
