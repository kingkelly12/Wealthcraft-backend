-- =============================================================================
-- The cast (characters who text you) and roommate co-op
-- =============================================================================
-- * player_relationships: how each cast member (mom, bestie, roommate, ex)
--   feels about the player, 0..100. Reset with every new life.
-- * cast_messages: texts from the cast, written when a week ends based on what
--   happened. A text can offer two quick replies with small effects.
-- * roommates: a real friend moves into your rental and pays a share of the
--   rent on each of their game months.
-- * player_game_clock.last_nudged_on: at most one "your week is ready" push a day.
-- =============================================================================

create table if not exists public.player_relationships (
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  character   text not null,
  score       integer not null default 50 check (score between 0 and 100),
  updated_at  timestamptz not null default now(),
  primary key (user_id, character)
);

create table if not exists public.cast_messages (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references public.profiles(user_id) on delete cascade,
  character    text not null,
  week         integer,
  body         text not null,
  from_player  boolean not null default false,
  replies      jsonb,          -- [{id, label, ...effects}] or null
  replied_with text,           -- the reply id chosen, once
  read_at      timestamptz,
  created_at   timestamptz not null default now()
);
create index if not exists cast_messages_thread_idx on public.cast_messages (user_id, character, created_at desc);

create table if not exists public.roommates (
  id              uuid primary key default gen_random_uuid(),
  leaseholder_id  uuid not null references public.profiles(user_id) on delete cascade,
  roommate_id     uuid not null references public.profiles(user_id) on delete cascade,
  rental_id       uuid references public.player_rentals(id) on delete set null,
  status          text not null default 'pending' check (status in ('pending', 'active', 'declined', 'ended')),
  rent_share      numeric(4,3) not null default 0.5 check (rent_share > 0 and rent_share < 1),
  created_at      timestamptz not null default now(),
  accepted_at     timestamptz,
  ended_at        timestamptz,
  check (leaseholder_id <> roommate_id)
);
-- One active arrangement per person, on either side.
create unique index if not exists roommates_active_leaseholder on public.roommates (leaseholder_id) where status = 'active';
create unique index if not exists roommates_active_roommate on public.roommates (roommate_id) where status = 'active';
create unique index if not exists roommates_one_pending_pair on public.roommates (leaseholder_id, roommate_id) where status = 'pending';

alter table public.player_game_clock add column if not exists last_nudged_on date;

-- RLS on with no policies: only the Flask backend (service role) uses these.
alter table public.player_relationships enable row level security;
alter table public.cast_messages enable row level security;
alter table public.roommates enable row level security;
