-- =============================================================================
-- Showroom: wishlists, "since you passed on it", and deals (app/game/showroom.py)
-- =============================================================================
-- showroom_wishlist   things a player saved; notified_at = when we last pushed
--                     "you can afford it now" (cleared when it slips out of reach)
-- showroom_seen       the game week a player first scrolled past an item, per life
-- showroom_deals      a few discounts per two game weeks; redeemed_at once the
--                     discount has been paid back after the purchase
-- Server-only: RLS on, no policies. Safe to run more than once.
-- =============================================================================

create table if not exists public.showroom_wishlist (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  kind        text not null check (kind in ('home', 'business', 'item')),
  item_id     text not null,
  added_at    timestamptz not null default now(),
  notified_at timestamptz,
  unique (user_id, kind, item_id)
);
create index if not exists showroom_wishlist_user_idx on public.showroom_wishlist (user_id);
alter table public.showroom_wishlist enable row level security;

create table if not exists public.showroom_seen (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.profiles(user_id) on delete cascade,
  life_number     integer not null default 1,
  kind            text not null check (kind in ('home', 'business', 'item')),
  item_id         text not null,
  first_seen_week integer not null,
  price           numeric not null,
  seen_at         timestamptz not null default now(),
  unique (user_id, life_number, kind, item_id)
);
create index if not exists showroom_seen_user_idx on public.showroom_seen (user_id, life_number);
alter table public.showroom_seen enable row level security;

create table if not exists public.showroom_deals (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references public.profiles(user_id) on delete cascade,
  life_number       integer not null default 1,
  window_start_week integer not null,
  ends_week         integer not null,
  kind              text not null check (kind in ('home', 'item')),
  item_id           text not null,
  discount_pct      numeric not null check (discount_pct > 0 and discount_pct < 0.5),
  label             text,
  emoji             text,
  created_at        timestamptz not null default now(),
  redeemed_at       timestamptz,
  saving            numeric,
  unique (user_id, life_number, kind, item_id)
);
create index if not exists showroom_deals_window_idx on public.showroom_deals (user_id, life_number, window_start_week);
alter table public.showroom_deals enable row level security;
