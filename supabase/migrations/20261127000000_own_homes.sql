-- =============================================================================
-- Own your home: buy a place, move in, stop paying rent
-- =============================================================================
-- * home_listings: homes for sale, from a studio flat to a country manor.
--   Each has a market rent (what renting it would cost, and what tenants pay
--   you if you let it out), itemised monthly upkeep (rates, insurance, service
--   charge, staff...) and a bills_type for electricity, water and Wi-Fi.
-- * player_homes: homes a player owns. Living in one ends your lease, so rent
--   stops; you pay upkeep and bills instead. A home you own but don't live in
--   is let out for rent. Homes gain value on game months and count towards
--   net worth. Selling costs 5% in agent and legal fees.
-- Rules live in app/game/homes.py. Safe to re-run.
-- =============================================================================

begin;

create table if not exists public.home_listings (
  id           uuid primary key default gen_random_uuid(),
  name         text not null unique,
  home_type    text not null,              -- studio | apartment | townhouse | bungalow | lakehouse | villa | penthouse | mansion | manor
  bills_type   text,                       -- a key of economy.HOME_BILLS; null = bills scale with market_rent
  price        numeric(14,2) not null check (price > 0),
  market_rent  numeric(12,2) not null default 0 check (market_rent >= 0),
  bedrooms     integer not null default 1,
  location     text not null,
  description  text,
  upkeep       jsonb not null default '[]', -- [{"label": "Insurance", "monthly": 40}, ...]
  image_url    text,
  created_at   timestamptz not null default now()
);

create table if not exists public.player_homes (
  id             uuid primary key default gen_random_uuid(),
  player_id      uuid not null references public.profiles(user_id) on delete cascade,
  home_id        uuid not null references public.home_listings(id) on delete restrict,
  purchase_price numeric(15,2) not null,
  current_value  numeric(15,2) not null,
  lives_in       boolean not null default false,
  months_held    integer not null default 0,
  is_active      boolean not null default true,
  purchased_at   timestamptz not null default now(),
  sold_at        timestamptz
);
create index if not exists player_homes_player_idx on public.player_homes (player_id) where is_active;
-- You live in at most one home you own.
create unique index if not exists player_homes_one_lived_in on public.player_homes (player_id) where is_active and lives_in;

alter table public.home_listings enable row level security;
alter table public.player_homes enable row level security;
do $$ begin
  create policy "catalogue read" on public.home_listings for select to authenticated using (true);
exception when duplicate_object then null; end $$;

insert into public.home_listings (name, home_type, bills_type, price, market_rent, bedrooms, location, description, upkeep) values
  ('Studio Flat',            'studio',    'studio',     95000,   950,   0, 'Downtown Edge',  'One room, one window, one hundred percent yours. Your first set of keys.',
     '[{"label":"Service charge","monthly":70},{"label":"Insurance","monthly":20},{"label":"Property rates","monthly":30}]'),
  ('One-Bedroom Apartment',  'apartment', 'apartment',  150000,  1400,  1, 'Midtown',        'A real bedroom door you can close. Gym in the basement, lift that works most days.',
     '[{"label":"Service charge","monthly":110},{"label":"Insurance","monthly":30},{"label":"Property rates","monthly":45}]'),
  ('Two-Bedroom Apartment',  'apartment', 'condo',      220000,  1900,  2, 'Riverside',      'A spare room for guests, a home office, or a very organised shoe collection.',
     '[{"label":"Service charge","monthly":150},{"label":"Insurance","monthly":40},{"label":"Property rates","monthly":65}]'),
  ('Townhouse',              'townhouse', 'house',      300000,  2500,  3, 'Greenview Estate','Three floors, a small garden and an estate WhatsApp group with very strong opinions.',
     '[{"label":"Estate fees","monthly":120},{"label":"Insurance","monthly":55},{"label":"Property rates","monthly":90},{"label":"Maintenance","monthly":100}]'),
  ('Bungalow',               'bungalow',  'house',      340000,  2700,  3, 'Leafy Suburbs',  'Everything on one floor, a big garden and a dog-shaped hole in your life.',
     '[{"label":"Insurance","monthly":60},{"label":"Property rates","monthly":100},{"label":"Garden & maintenance","monthly":180}]'),
  ('Lakehouse',              'lakehouse', null,         650000,  5000,  4, 'Lakeside',       'Wake up to mist on the water. Has a dock, so friends now "pop by" every weekend.',
     '[{"label":"Insurance","monthly":120},{"label":"Property rates","monthly":190},{"label":"Dock & maintenance","monthly":350}]'),
  ('Beach Villa',            'villa',     null,         850000,  6200,  4, 'The Coast',      'Pool, ocean view, sand in absolutely everything. Holiday lets pay very well.',
     '[{"label":"Insurance","monthly":160},{"label":"Property rates","monthly":250},{"label":"Pool & garden","monthly":400},{"label":"Caretaker","monthly":300}]'),
  ('Penthouse',              'penthouse', 'penthouse',  1100000, 6500,  3, 'Skyline District','The whole top floor, a rooftop terrace and a lift that opens right in your living room.',
     '[{"label":"Service charge","monthly":900},{"label":"Insurance","monthly":200},{"label":"Property rates","monthly":320}]'),
  ('Mansion',                'mansion',   null,         2200000, 14000, 7, 'The Hills',      'Gates, a fountain and more bathrooms than you will ever use. Staff included in the bills, not the price.',
     '[{"label":"Insurance","monthly":400},{"label":"Property rates","monthly":650},{"label":"Staff","monthly":2500},{"label":"Maintenance","monthly":1200}]'),
  ('Country Manor',          'manor',     null,         3800000, 20000, 10,'Old Estates',    'A hundred acres, a library with a ladder, and a groundskeeper who calls you "the young master".',
     '[{"label":"Insurance","monthly":700},{"label":"Property rates","monthly":1100},{"label":"Staff","monthly":4000},{"label":"Grounds","monthly":2500}]')
on conflict (name) do update set
  home_type = excluded.home_type, bills_type = excluded.bills_type, price = excluded.price,
  market_rent = excluded.market_rent, bedrooms = excluded.bedrooms, location = excluded.location,
  description = excluded.description, upkeep = excluded.upkeep;

commit;
