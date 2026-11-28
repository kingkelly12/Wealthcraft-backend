-- =============================================================================
-- Land: buy a plot and maybe a company comes for it (app/game/land.py)
-- * player_land: plots players own, with any open offer or lease.
-- * Row level security is on with NO policies: `fate` says whether an offer is
--   coming, so only the backend (service role) may read this table.
-- * One row per player and plot: a sold plot can't be bought again this life.
-- Run this BEFORE deploying the backend that uses it. Safe to run more than once.
-- =============================================================================
begin;

create table if not exists public.player_land (
  id             uuid primary key default gen_random_uuid(),
  player_id      uuid not null references public.profiles(user_id) on delete cascade,
  plot_key       text not null,
  purchase_price numeric(15,2) not null,
  current_value  numeric(15,2) not null,
  months_held    integer not null default 0,
  status         text not null default 'owned' check (status in ('owned', 'leased', 'sold')),
  fate           jsonb not null default '{}',
  offer          jsonb,
  lease          jsonb,
  version        integer not null default 0,
  is_active      boolean not null default true,
  purchased_at   timestamptz not null default now(),
  sold_at        timestamptz,
  unique (player_id, plot_key)
);

alter table public.player_land enable row level security;

commit;
