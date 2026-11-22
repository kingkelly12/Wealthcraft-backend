-- =============================================================================
-- The market moves with game weeks
-- =============================================================================
-- Before: one global price per asset, nudged by up to ±5% (crypto ±10%) every
-- 4 REAL hours, with no upward drift. Players on game time barely saw it move,
-- stocks didn't grow on average, and the "low risk" index fund swung ~±135% a
-- year.
-- Now each player (each life) has their own market that moves one step every
-- game week they finish (app/game/market.py):
-- * assets.annual_drift / annual_volatility: average growth a year and how
--   far it swings (fractions). An index fund: +7% a year, swings ~15%.
-- * Now and then: stock crashes and bull runs, crypto winters and booms, meme
--   squeezes and dumps, currency shocks. Riskier assets take bigger hits.
-- * player_market_prices: each player's current price per traded asset.
-- * player_market_events: the crashes and booms they lived through.
-- The 4-hourly calendar job no longer touches game-time players' holdings.
-- Safe to re-run.
-- =============================================================================

begin;

alter table public.assets add column if not exists annual_drift numeric(6,4);
alter table public.assets add column if not exists annual_volatility numeric(6,4);

update public.assets set annual_drift = v.drift, annual_volatility = v.vol
from (values
  ('Index Fund (VTI)',        0.07,  0.15),
  ('Blue Chip Tech (TECHX)',  0.09,  0.28),
  ('Dividend King (DVK)',     0.05,  0.13),
  ('Meme Stock (YOLO)',      -0.05,  0.90),
  ('Bitcoin',                 0.15,  0.65),
  ('Ethereum',                0.12,  0.80),
  ('DogeMoon',               -0.10,  1.20),
  ('EUR/USD Position',        0.00,  0.08)
) as v(name, drift, vol)
where public.assets.name = v.name;

create table if not exists public.player_market_prices (
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  asset_id   text not null references public.assets(id) on delete cascade,
  price      numeric(18,2) not null check (price > 0),
  prev_price numeric(18,2),
  week       integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, asset_id)
);

create table if not exists public.player_market_events (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  week       integer not null,
  kind       text not null,
  emoji      text,
  title      text not null,
  body       text,
  shock_pct  numeric(6,1),
  assets     text[] not null default '{}',
  created_at timestamptz not null default now()
);
create index if not exists player_market_events_user_week_idx on public.player_market_events (user_id, week desc);

alter table public.player_market_prices enable row level security;
alter table public.player_market_events enable row level security;

commit;
