-- =============================================================================
-- Adulting / Wealthcraft — consolidated Supabase schema
-- =============================================================================
-- Run this ONCE on a brand-new Supabase project (SQL Editor → paste → Run),
-- then run supabase/seed.sql, supabase/seed_mentors.sql and
-- supabase/seed_life_events.sql.
--
-- Design rules this schema enforces:
--   * Every per-player table keys on auth.users.id (stored as `user_id` /
--     `player_id`) and has a FK to profiles(user_id). No more "auth uid vs
--     profile id" ambiguity, and PostgREST embeds like
--     profiles!user_follows_follower_id_fkey(...) resolve.
--   * Money only moves through public.adjust_balance(), which is atomic,
--     refuses to overdraw and always writes a transactions row.
--   * The Flask backend uses the service_role key (bypasses RLS). The mobile
--     app uses the anon key + user JWT, so RLS below only grants what the app
--     reads/writes directly: catalogue reads, follow lists, chat, own push token.
--   * Players can NOT write their own balance, net worth, sanity or credit score.
-- =============================================================================

create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- Helpers
-- -----------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- -----------------------------------------------------------------------------
-- Players
-- -----------------------------------------------------------------------------
create table public.profiles (
  id                           uuid primary key default gen_random_uuid(),
  user_id                      uuid not null unique references auth.users(id) on delete cascade,
  username                     text not null unique check (char_length(username) between 3 and 50),
  net_worth                    numeric(15,2) not null default 0,
  base_monthly_income          numeric(15,2) not null default 0,   -- permanent boosts (courses, life events)
  monthly_income               numeric(15,2) not null default 0,   -- cached: base + job salaries/12 + asset yield
  credit_score                 integer not null default 650 check (credit_score between 300 and 850),
  wealth_level                 text not null default 'Beginner',
  experience_points            integer not null default 0,
  profile_picture_url          text,
  trading_profits              numeric(15,2) not null default 0,
  income_sources_count         integer not null default 1,
  monthly_savings              numeric(15,2) not null default 0,
  engagement_days              integer not null default 0,
  sanity                       integer not null default 100 check (sanity between 0 and 100),
  has_completed_onboarding     boolean not null default false,
  expo_push_token              text,
  push_token_updated_at        timestamptz,
  last_active_at               timestamptz not null default now(),
  last_inactivity_ping_sent_at timestamptz,
  last_free_recovery_at        timestamptz,                         -- daily cooldown for free 'touch grass'
  created_at                   timestamptz not null default now(),
  updated_at                   timestamptz not null default now()
);
create index profiles_net_worth_idx on public.profiles (net_worth desc);
create index profiles_last_active_idx on public.profiles (last_active_at);
create trigger profiles_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();

create table public.user_balances (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null unique references public.profiles(user_id) on delete cascade,
  current_balance numeric(15,2) not null default 0 check (current_balance >= 0),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create trigger user_balances_updated_at before update on public.user_balances
  for each row execute function public.set_updated_at();

create table public.transactions (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references public.profiles(user_id) on delete cascade,
  type             text not null check (type in ('income', 'expense')),
  category         text not null default 'balance_adjustment',
  amount           numeric(15,2) not null check (amount >= 0),
  description      text,
  transaction_date timestamptz not null default now(),
  created_at       timestamptz not null default now()
);
create index transactions_user_created_idx on public.transactions (user_id, created_at desc);

-- -----------------------------------------------------------------------------
-- Market: assets
-- -----------------------------------------------------------------------------
create table public.assets (
  id                      text primary key default gen_random_uuid()::text,
  name                    text not null unique,          -- code looks assets up by name
  category                text not null,                 -- stocks | crypto | forex | real_estate | business
  price                   numeric(14,2) not null check (price > 0),
  price_change            numeric(14,2) not null default 0,
  price_change_percent    numeric(7,2) not null default 0,
  monthly_income          numeric(14,2) not null default 0,  -- yield per unit per month
  description             text,
  risk_level              text not null default 'medium' check (risk_level in ('low', 'medium', 'high', 'very_high')),
  roi                     numeric(7,2) not null default 0,
  time_to_return          text default 'unknown',
  availability            integer not null default 0,
  total_supply            integer not null default 0,
  mission_prerequisites   text[] not null default '{}',
  recommended_for_mission text[] not null default '{}',
  risk_education          text,
  educational_tier        text not null default 'beginner',
  mission_only            boolean not null default false,
  unlocks_on_purchase     text[] not null default '{}',
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);
create index assets_category_idx on public.assets (category);
create trigger assets_updated_at before update on public.assets
  for each row execute function public.set_updated_at();

create table public.user_assets (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null references public.profiles(user_id) on delete cascade,
  asset_id       text references public.assets(id) on delete set null,
  asset_type     text not null,                 -- stocks | crypto | forex | property
  name           text not null,
  value          numeric(15,2) not null default 0,
  quantity       numeric(15,4) not null default 1 check (quantity > 0),
  purchase_price numeric(15,2),                 -- per-unit cost basis
  purchase_date  timestamptz not null default now(),
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);
create index user_assets_user_idx on public.user_assets (user_id);
create index user_assets_name_idx on public.user_assets (name);
create trigger user_assets_updated_at before update on public.user_assets
  for each row execute function public.set_updated_at();

create table public.market_news (
  id               uuid primary key default gen_random_uuid(),
  headline         text not null,
  body             text,
  analyst_tip      text,
  category         text not null default 'market',  -- market | profile | jobs | rentals | lifestyle | banking | education
  sentiment        text,
  asset_name       text,
  price_change_pct numeric(7,2) not null default 0,
  created_at       timestamptz not null default now()
);
create index market_news_category_created_idx on public.market_news (category, created_at desc);
create index market_news_created_idx on public.market_news (created_at desc);

-- -----------------------------------------------------------------------------
-- Jobs & education
-- -----------------------------------------------------------------------------
create table public.job_market (
  id                uuid primary key default gen_random_uuid(),
  title             text not null,
  industry          text not null,
  company           text not null,
  salary            numeric(15,2) not null check (salary > 0),   -- ANNUAL salary
  level             text not null default 'entry',
  experience_months integer not null default 0,
  description       text,
  created_at        timestamptz not null default now(),
  unique (title, company)
);

create table public.jobs (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references public.profiles(user_id) on delete cascade,
  job_market_id       uuid references public.job_market(id) on delete set null,
  title               text not null,
  company             text,
  salary              numeric(15,2) not null default 0,         -- ANNUAL salary
  level               text not null default 'entry',
  experience_months   integer not null default 0,
  promotion_progress  integer not null default 0,
  is_current          boolean not null default true,
  work_hours_per_week integer default 40,
  start_date          timestamptz not null default now(),
  end_date            timestamptz,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
create index jobs_user_current_idx on public.jobs (user_id) where is_current;
create unique index jobs_one_current_per_listing on public.jobs (user_id, job_market_id) where is_current;
create trigger jobs_updated_at before update on public.jobs
  for each row execute function public.set_updated_at();

create table public.courses (
  id                    uuid primary key default gen_random_uuid(),
  title                 text not null unique,
  description           text,
  category              text not null,
  difficulty            text not null default 'beginner',
  duration_hours        integer not null default 1,
  cost                  numeric(10,2) not null default 0 check (cost >= 0),
  salary_boost          numeric(10,2) not null default 0,   -- permanent MONTHLY income boost
  mission_prerequisites text[] not null default '{}',
  unlocks_assets        text[] not null default '{}',
  mission_only          boolean not null default false,
  difficulty_rating     integer not null default 1,
  learning_path         text,
  created_at            timestamptz not null default now()
);

create table public.user_courses (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references public.profiles(user_id) on delete cascade,
  course_id    uuid not null references public.courses(id) on delete cascade,
  progress     integer not null default 0 check (progress between 0 and 100),
  started_at   timestamptz not null default now(),
  completed_at timestamptz,
  created_at   timestamptz not null default now(),
  unique (user_id, course_id)
);

-- -----------------------------------------------------------------------------
-- Housing & lifestyle
-- -----------------------------------------------------------------------------
create table public.rental_properties (
  id            uuid primary key default gen_random_uuid(),
  name          text not null unique,
  property_type text not null,
  monthly_rent  integer not null check (monthly_rent > 0),
  location      text not null,
  amenities     text[] not null default '{}',
  image_url     text,
  created_at    timestamptz not null default now()
);

create table public.player_rentals (
  id           uuid primary key default gen_random_uuid(),
  player_id    uuid not null references public.profiles(user_id) on delete cascade,
  property_id  uuid not null references public.rental_properties(id) on delete restrict,
  monthly_rent integer not null,
  is_active    boolean not null default true,
  rented_at    timestamptz not null default now(),
  ended_at     timestamptz
);
create unique index player_rentals_one_active on public.player_rentals (player_id) where is_active;

-- Homes for sale, and homes players own (app/game/homes.py). Living in one you
-- own ends your lease: no rent, just upkeep and bills.
create table public.home_listings (
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

create table public.player_homes (
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
create index player_homes_player_idx on public.player_homes (player_id) where is_active;
-- You live in at most one home you own.
create unique index player_homes_one_lived_in on public.player_homes (player_id) where is_active and lives_in;

create table public.liability_items (
  id           uuid primary key default gen_random_uuid(),
  name         text not null unique,
  category     text not null,
  base_price   numeric(15,2) not null check (base_price > 0),
  monthly_cost numeric(15,2) not null default 0,
  description  text,
  image_url    text,
  created_at   timestamptz not null default now()
);

create table public.player_liabilities (
  id                     uuid primary key default gen_random_uuid(),
  player_id              uuid not null references public.profiles(user_id) on delete cascade,
  liability_id           uuid not null references public.liability_items(id) on delete restrict,
  purchase_price         numeric(15,2) not null,
  monthly_cost           numeric(15,2) not null default 0,
  current_value          numeric(15,2),                  -- depreciated resale value
  purchase_date          timestamptz not null default now(),
  is_active              boolean not null default true,
  last_depreciation_date date,
  months_owned           integer not null default 0
);
create index player_liabilities_player_active_idx on public.player_liabilities (player_id) where is_active;

-- -----------------------------------------------------------------------------
-- Credit: bank loans, P2P loans, and the unified `liabilities` debt ledger
-- -----------------------------------------------------------------------------
create table public.bank_loans (
  id              uuid primary key default gen_random_uuid(),
  borrower_id     uuid references public.profiles(user_id) on delete cascade,  -- NULL = loan product template
  type            text not null,
  amount          numeric(15,2) not null check (amount > 0),
  interest_rate   numeric(6,4) not null,               -- fraction, e.g. 0.05 = 5%
  term            integer not null check (term > 0),   -- months
  monthly_payment numeric(15,2) not null,
  total_interest  numeric(15,2) not null default 0,
  credit_required integer not null default 300,
  status          text not null default 'available' check (status in ('available', 'active', 'completed', 'defaulted')),
  collateral      text not null default 'none',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  funded_at       timestamptz,
  due_date        timestamptz
);
create index bank_loans_borrower_idx on public.bank_loans (borrower_id, status);
create unique index bank_loans_product_type on public.bank_loans (type) where borrower_id is null;
create trigger bank_loans_updated_at before update on public.bank_loans
  for each row execute function public.set_updated_at();

create table public.p2p_loans (
  id                uuid primary key default gen_random_uuid(),
  lender_id         uuid not null,
  borrower_id       uuid,
  amount            numeric(15,2) not null check (amount > 0),
  interest_rate     numeric(6,2) not null check (interest_rate between 0 and 100),  -- percent, simple interest
  term_months       integer not null check (term_months between 1 and 120),
  purpose           text not null default 'General Loan',
  status            text not null default 'pending' check (status in ('pending', 'active', 'completed', 'cancelled', 'defaulted')),
  monthly_payment   numeric(15,2),
  collateral_amount numeric(15,2),
  next_payment_date timestamptz,
  remaining_balance numeric(15,2),
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  funded_at         timestamptz,
  due_date          timestamptz,
  constraint p2p_loans_lender_id_fkey   foreign key (lender_id)   references public.profiles(user_id) on delete cascade,
  constraint p2p_loans_borrower_id_fkey foreign key (borrower_id) references public.profiles(user_id) on delete set null
);
create index p2p_loans_status_idx on public.p2p_loans (status);
create trigger p2p_loans_updated_at before update on public.p2p_loans
  for each row execute function public.set_updated_at();

create table public.liabilities (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references public.profiles(user_id) on delete cascade,
  name              text not null,
  liability_type    text not null check (liability_type in ('bank_loan', 'p2p_loan', 'luxury')),
  amount            numeric(15,2) not null,          -- original principal
  interest_rate     numeric(6,2) not null default 0, -- percent
  monthly_payment   numeric(15,2) not null default 0,
  remaining_balance numeric(15,2),                   -- principal + interest still owed
  remaining_term    integer,
  due_date          timestamptz,
  p2p_loan_id       uuid references public.p2p_loans(id) on delete set null,
  bank_loan_id      uuid references public.bank_loans(id) on delete set null,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create index liabilities_user_idx on public.liabilities (user_id);
create trigger liabilities_updated_at before update on public.liabilities
  for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- Social
-- -----------------------------------------------------------------------------
create table public.user_follows (
  id           uuid primary key default gen_random_uuid(),
  follower_id  uuid not null,
  following_id uuid not null,
  created_at   timestamptz not null default now(),
  constraint user_follows_follower_id_fkey  foreign key (follower_id)  references public.profiles(user_id) on delete cascade,
  constraint user_follows_following_id_fkey foreign key (following_id) references public.profiles(user_id) on delete cascade,
  constraint user_follows_unique unique (follower_id, following_id),
  constraint user_follows_not_self check (follower_id <> following_id)
);
create index user_follows_following_idx on public.user_follows (following_id);

create table public.chat_messages (
  id           uuid primary key default gen_random_uuid(),
  sender_id    uuid not null,
  recipient_id uuid not null,
  content      text not null check (char_length(content) between 1 and 2000),
  timestamp    timestamptz not null default now(),
  status       text not null default 'sent' check (status in ('sent', 'delivered', 'read')),
  type         text not null default 'text' check (type in ('text', 'file', 'image')),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint chat_messages_sender_id_fkey    foreign key (sender_id)    references public.profiles(user_id) on delete cascade,
  constraint chat_messages_recipient_id_fkey foreign key (recipient_id) references public.profiles(user_id) on delete cascade
);
create index chat_messages_pair_idx on public.chat_messages (sender_id, recipient_id, timestamp);
create index chat_messages_recipient_idx on public.chat_messages (recipient_id, status);
create trigger chat_messages_updated_at before update on public.chat_messages
  for each row execute function public.set_updated_at();

create table public.notifications (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.profiles(user_id) on delete cascade,
  type            text not null,
  title           text not null,
  message         text not null,
  asset_id        text,
  related_user_id uuid,
  read            boolean not null default false,
  created_at      timestamptz not null default now()
);
create index notifications_user_created_idx on public.notifications (user_id, created_at desc);
create index notifications_user_unread_idx on public.notifications (user_id) where not read;

create table public.void_posts (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  content     text not null check (char_length(content) between 1 and 280),
  ai_analysis jsonb,
  oof_count   integer not null default 0,
  same_count  integer not null default 0,
  created_at  timestamptz not null default now()
);
create index void_posts_created_idx on public.void_posts (created_at desc);

create table public.void_reactions (
  id            uuid primary key default gen_random_uuid(),
  post_id       uuid not null references public.void_posts(id) on delete cascade,
  user_id       uuid not null references public.profiles(user_id) on delete cascade,
  reaction_type text not null check (reaction_type in ('oof', 'same')),
  created_at    timestamptz not null default now(),
  unique (post_id, user_id)
);

-- -----------------------------------------------------------------------------
-- Life events
-- -----------------------------------------------------------------------------
create table public.life_events (
  id                 uuid primary key default gen_random_uuid(),
  title              text not null,
  description        text not null,
  event_type         text not null,
  impact_cash        numeric(15,2) not null default 0,
  impact_income      numeric(15,2) not null default 0,
  impact_expenses    numeric(15,2) not null default 0,
  impact_sanity      integer not null default 0,
  impact_assets      text,
  time_limit_seconds integer not null default 604800,
  icon_name          text not null default 'Zap',
  is_active          boolean not null default true,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);
create trigger life_events_updated_at before update on public.life_events
  for each row execute function public.set_updated_at();

create table public.life_event_choices (
  id                  uuid primary key default gen_random_uuid(),
  life_event_id       uuid not null references public.life_events(id) on delete cascade,
  choice_label        text not null,
  outcome_description text not null,
  cost                numeric(15,2) not null default 0,
  benefit             numeric(15,2) not null default 0,
  choice_order        integer not null default 0,
  impact_sanity       integer not null default 0,
  impact_income       numeric(15,2) not null default 0,
  created_at          timestamptz not null default now()
);
create index life_event_choices_event_idx on public.life_event_choices (life_event_id, choice_order);

create table public.user_life_events (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references public.profiles(user_id) on delete cascade,
  life_event_id     uuid not null references public.life_events(id) on delete cascade,
  choice_id         uuid references public.life_event_choices(id) on delete set null,
  was_auto_selected boolean not null default false,
  created_at        timestamptz not null default now()
);
create index user_life_events_user_created_idx on public.user_life_events (user_id, created_at desc);
create index user_life_events_pending_idx on public.user_life_events (user_id, life_event_id) where choice_id is null;

-- -----------------------------------------------------------------------------
-- Missions
-- -----------------------------------------------------------------------------
create table public.integrated_missions (
  id                      uuid primary key default gen_random_uuid(),
  name                    text not null unique,
  description             text not null,
  short_description       text,
  icon                    text not null default '🎯',
  category                text not null,
  difficulty              text not null default 'beginner' check (difficulty in ('beginner', 'intermediate', 'advanced')),
  duration_months         integer not null default 12 check (duration_months > 0),
  learning_objectives     text[] not null default '{}',
  affects_main_game       boolean not null default true,
  income_multiplier       double precision not null default 1.0,
  expense_multiplier      double precision not null default 1.0,
  can_change_job          boolean not null default true,
  can_buy_assets          boolean not null default true,
  can_take_loans          boolean not null default true,
  can_rent_property       boolean not null default true,
  can_sell_assets         boolean not null default true,
  can_buy_lifestyle_items boolean not null default true,
  allowed_asset_types     text[],
  max_loan_amount         numeric(15,2),
  allowed_loan_types      text[],
  max_monthly_spending    numeric(15,2),
  completion_reward       numeric(15,2) not null default 0,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);
create trigger integrated_missions_updated_at before update on public.integrated_missions
  for each row execute function public.set_updated_at();

create table public.mission_decision_points (
  id                      uuid primary key default gen_random_uuid(),
  mission_id              uuid not null references public.integrated_missions(id) on delete cascade,
  month                   integer not null check (month >= 1),
  is_required             boolean not null default true,
  auto_resolve_after_days integer,
  auto_resolve_option_id  uuid,
  title                   text not null,
  description             text not null,
  context                 text,
  learning_lesson         text,
  created_at              timestamptz not null default now(),
  unique (mission_id, month)
);

create table public.mission_decision_options (
  id                     uuid primary key default gen_random_uuid(),
  decision_point_id      uuid not null references public.mission_decision_points(id) on delete cascade,
  label                  text not null,
  description            text not null,
  game_action_type       text,
  game_action_data       jsonb not null default '{}',
  immediate_cash         numeric(15,2) not null default 0,
  monthly_income_change  numeric(15,2) not null default 0,
  monthly_expense_change numeric(15,2) not null default 0,
  asset_impact           numeric(15,2) not null default 0,
  debt_impact            numeric(15,2) not null default 0,
  happiness_change       integer not null default 0,
  stress_change          integer not null default 0,
  motivation_change      integer not null default 0,
  risk_level             text not null default 'medium',
  success_probability    double precision,
  unlocks_decision_id    uuid references public.mission_decision_points(id) on delete set null,
  blocks_decision_id     uuid references public.mission_decision_points(id) on delete set null,
  affects_story          boolean not null default false,
  hidden                 boolean not null default false,
  condition              text,
  option_order           integer not null default 0,
  created_at             timestamptz not null default now()
);

create table public.mission_success_criteria (
  id                    uuid primary key default gen_random_uuid(),
  mission_id            uuid not null references public.integrated_missions(id) on delete cascade,
  metric                text not null check (metric in ('net_worth', 'monthly_income', 'debt_ratio', 'credit_score',
                                                        'asset_value', 'passive_income', 'business_value', 'custom')),
  target                numeric(15,2) not null,
  comparison            text not null check (comparison in ('greater_than', 'less_than', 'equals', 'between')),
  target_min            numeric(15,2),
  custom_metric_formula text,
  label                 text not null,
  description           text,
  icon                  text,
  created_at            timestamptz not null default now(),
  unique (mission_id, metric)
);

create table public.mission_story_events (
  id                uuid primary key default gen_random_uuid(),
  mission_id        uuid not null references public.integrated_missions(id) on delete cascade,
  title             text not null,
  emoji             text not null default '📖',
  narrative         text not null,
  financial_context text,
  story_type        text not null,
  trigger_type      text not null,     -- e.g. 'month'
  trigger_value     integer,
  trigger_condition text,
  probability       double precision not null default 1.0,
  audio_cue         text,
  background_image  text,
  mood_color        text,
  happiness_change  integer not null default 0,
  stress_change     integer not null default 0,
  motivation_change integer not null default 0,
  immediate_cash    numeric(15,2) not null default 0,
  display_order     integer not null default 0,
  is_active         boolean not null default true,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (mission_id, display_order)
);

create table public.player_mission_progress (
  id                  uuid primary key default gen_random_uuid(),
  player_id           uuid not null references public.profiles(user_id) on delete cascade,
  mission_id          uuid not null references public.integrated_missions(id) on delete cascade,
  is_active           boolean not null default false,
  is_completed        boolean not null default false,
  is_failed           boolean not null default false,
  current_month       integer not null default 1,
  started_at          timestamptz not null default now(),
  completed_at        timestamptz,
  failed_at           timestamptz,
  abandoned_at        timestamptz,
  constraints_applied jsonb not null default '{}',
  game_state_snapshot jsonb not null default '{}',
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);
-- One active mission per player; abandoned missions can be retried later.
create unique index player_mission_progress_one_active on public.player_mission_progress (player_id) where is_active;
create trigger player_mission_progress_updated_at before update on public.player_mission_progress
  for each row execute function public.set_updated_at();

create table public.player_mission_decisions (
  id                uuid primary key default gen_random_uuid(),
  player_mission_id uuid not null references public.player_mission_progress(id) on delete cascade,
  decision_point_id uuid not null references public.mission_decision_points(id) on delete cascade,
  chosen_option_id  uuid not null references public.mission_decision_options(id) on delete cascade,
  month_made        integer not null,
  decision_data     jsonb not null default '{}',
  created_at        timestamptz not null default now(),
  unique (player_mission_id, decision_point_id)   -- a decision can only be made once
);

create table public.player_mission_success_tracking (
  id                uuid primary key default gen_random_uuid(),
  player_mission_id uuid not null references public.player_mission_progress(id) on delete cascade,
  criteria_id       uuid not null references public.mission_success_criteria(id) on delete cascade,
  current_value     numeric(15,2) not null default 0,
  is_met            boolean not null default false,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (player_mission_id, criteria_id)
);

create table public.player_story_progress (
  id                  uuid primary key default gen_random_uuid(),
  player_mission_id   uuid not null references public.player_mission_progress(id) on delete cascade,
  story_event_id      uuid not null references public.mission_story_events(id) on delete cascade,
  has_triggered       boolean not null default false,
  has_been_viewed     boolean not null default false,
  triggered_at        timestamptz,
  viewed_at           timestamptz,
  game_state_snapshot jsonb not null default '{}',
  mission_month       integer,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  unique (player_mission_id, story_event_id)
);

create table public.mission_completion_results (
  id                  uuid primary key default gen_random_uuid(),
  mission_id          uuid not null references public.integrated_missions(id) on delete cascade,
  player_mission_id   uuid not null unique references public.player_mission_progress(id) on delete cascade,
  player_id           uuid not null references public.profiles(user_id) on delete cascade,
  completed           boolean not null default false,
  failed              boolean not null default false,
  abandoned           boolean not null default false,
  duration_months     integer not null,
  net_worth_change    numeric(15,2) not null default 0,
  income_change       numeric(15,2) not null default 0,
  credit_score_change integer not null default 0,
  criteria_met        integer not null default 0,
  criteria_total      integer not null default 0,
  success_percentage  double precision not null default 0,
  rewards_earned      jsonb not null default '[]',
  total_cash_reward   numeric(15,2) not null default 0,
  learning_score      integer,
  financial_iq_gain   integer,
  completion_message  text,
  completed_at        timestamptz not null default now(),
  created_at          timestamptz not null default now()
);
create index mission_completion_results_player_idx on public.mission_completion_results (player_id, completed_at desc);

-- -----------------------------------------------------------------------------
-- Mentors & AI
-- -----------------------------------------------------------------------------
create table public.mentors (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  role              text not null,
  personality       text not null,
  avatar_url        text,
  greeting_template text not null,
  created_at        timestamptz not null default now()
);

create table public.mentor_messages (
  id                 uuid primary key default gen_random_uuid(),
  mentor_id          uuid not null references public.mentors(id) on delete cascade,
  trigger_type       text not null,
  message_template   text not null,
  cta_text           text,
  cta_action         text,
  trigger_conditions jsonb not null default '{}',
  min_net_worth      numeric(15,2),
  max_net_worth      numeric(15,2),
  priority           integer not null default 1,
  points_reward      integer not null default 10,
  is_active          boolean not null default true,
  created_at         timestamptz not null default now()
);

create table public.player_mentor_interactions (
  id                    uuid primary key default gen_random_uuid(),
  player_id             uuid not null references public.profiles(user_id) on delete cascade,
  mentor_id             uuid not null references public.mentors(id) on delete cascade,
  message_id            uuid references public.mentor_messages(id) on delete set null,
  message_content       text not null,
  trigger_type          text not null,
  player_data_snapshot  jsonb not null default '{}',
  sent_at               timestamptz not null default now(),
  read_at               timestamptz,
  action_taken          boolean not null default false,
  action_taken_at       timestamptz,
  points_earned         integer not null default 0,
  relationship_score    integer not null default 0,
  is_player_message     boolean not null default false,
  parent_interaction_id uuid references public.player_mentor_interactions(id) on delete set null,
  ai_metadata           jsonb not null default '{}',
  created_at            timestamptz not null default now()
);
create index player_mentor_interactions_player_idx on public.player_mentor_interactions (player_id, mentor_id, sent_at desc);

create table public.ai_response_cache (
  cache_key  text primary key,
  response   jsonb not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

-- Scheduler bookkeeping: monthly jobs insert (job_name, 'YYYY-MM') first and
-- skip if it already exists, so retries never double-charge players.
create table public.cron_runs (
  job_name text not null,
  period   text not null,
  ran_at   timestamptz not null default now(),
  primary key (job_name, period)
);

-- Turn-based time ("This Week"): one row per player on game time, one row per
-- dealt week. See migrations/20261121000000_game_clock.sql.
create table public.player_game_clock (
  user_id          uuid primary key references public.profiles(user_id) on delete cascade,
  week             integer not null default 1 check (week >= 1),   -- the week being played
  banked_weeks     integer not null default 1 check (banked_weeks >= 0),
  bank_updated_on  date not null default (now() at time zone 'utc')::date,
  last_nudged_on   date,                                            -- max one "week ready" push a day
  started_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create trigger player_game_clock_updated_at before update on public.player_game_clock
  for each row execute function public.set_updated_at();

create table public.player_weeks (
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
create index player_weeks_user_week_idx on public.player_weeks (user_id, week desc);

-- Lives: character, age, background and ending per run. See migrations/20261122000000_player_lives.sql.
create table public.player_lives (
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
create unique index player_lives_one_current on public.player_lives (user_id) where is_current;
create index player_lives_user_idx on public.player_lives (user_id, life_number desc);

-- The cast and roommates. See migrations/20261123000000_cast_and_roommates.sql.
create table public.player_relationships (
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  character   text not null,
  score       integer not null default 50 check (score between 0 and 100),
  updated_at  timestamptz not null default now(),
  primary key (user_id, character)
);

create table public.cast_messages (
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
create index cast_messages_thread_idx on public.cast_messages (user_id, character, created_at desc);

create table public.roommates (
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
create unique index roommates_active_leaseholder on public.roommates (leaseholder_id) where status = 'active';
create unique index roommates_active_roommate on public.roommates (roommate_id) where status = 'active';
create unique index roommates_one_pending_pair on public.roommates (leaseholder_id, roommate_id) where status = 'pending';

-- Money realism (gigs, item running costs & leasing, friend loans). See migrations/20261125000000_money_realism.sql.
-- --- Gigs ---------------------------------------------------------------------------
alter table public.job_market add column if not exists kind text not null default 'job';
alter table public.job_market add column if not exists weekly_pay numeric(12,2) not null default 0;
alter table public.job_market add column if not exists hours_per_week integer;
alter table public.job_market add column if not exists sanity_per_week integer not null default 0;
alter table public.jobs add column if not exists kind text not null default 'job';
alter table public.jobs add column if not exists weekly_pay numeric(12,2) not null default 0;
-- Careers (app/game/careers.py): months of experience earned on this job, and its industry.
alter table public.jobs add column if not exists months_worked integer not null default 0;
alter table public.jobs add column if not exists industry text;
alter table public.jobs add column if not exists sanity_per_week integer not null default 0;
do $$ begin
  alter table public.job_market add constraint job_market_kind_check check (kind in ('job', 'gig'));
exception when duplicate_object then null; end $$;
do $$ begin
  alter table public.jobs add constraint jobs_kind_check check (kind in ('job', 'gig'));
exception when duplicate_object then null; end $$;
-- Gigs have no annual salary (they pay weekly_pay).
alter table public.job_market drop constraint if exists job_market_salary_check;
alter table public.job_market add constraint job_market_salary_check check (salary > 0 or kind = 'gig');
-- --- Lifestyle items: running costs, depreciation, leasing -------------------------
alter table public.liability_items add column if not exists depreciation_rate numeric(5,4) not null default 0.125;  -- per year
alter table public.liability_items add column if not exists costs jsonb not null default '[]';                       -- [{"label","monthly"}]
alter table public.liability_items add column if not exists service_cost numeric(12,2) not null default 0;
alter table public.liability_items add column if not exists service_every_months integer not null default 0;
alter table public.liability_items add column if not exists lease_income numeric(12,2) not null default 0;           -- monthly, fully booked
alter table public.liability_items add column if not exists lease_label text;
alter table public.liability_items add column if not exists lease_wear numeric(5,4) not null default 0;              -- extra depreciation a year while leased
alter table public.player_liabilities add column if not exists is_leased boolean not null default false;
alter table public.player_liabilities add column if not exists leased_since timestamptz;
-- --- Assets: game months held (property and businesses grow on game months) -------
alter table public.user_assets add column if not exists months_held integer not null default 0;
-- --- Friend loans (P2P) -------------------------------------------------------------
alter table public.p2p_loans add column if not exists offered_to uuid references public.profiles(user_id) on delete cascade;
alter table public.p2p_loans add column if not exists requested boolean not null default false;
alter table public.p2p_loans add column if not exists rate_basis text not null default 'total';   -- older loans: flat total %
alter table public.p2p_loans add column if not exists payments_made integer not null default 0;
alter table public.p2p_loans add column if not exists payments_missed integer not null default 0;
alter table public.p2p_loans alter column rate_basis set default 'annual';
alter table public.p2p_loans drop constraint if exists p2p_loans_status_check;
alter table public.p2p_loans add constraint p2p_loans_status_check
  check (status in ('requested', 'pending', 'active', 'completed', 'cancelled', 'declined', 'defaulted'));
create index if not exists p2p_loans_offered_to_idx on public.p2p_loans (offered_to) where status in ('pending', 'requested');

-- Squads. See migrations/20261124000000_squads.sql.
create table public.squads (
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

create table public.squad_members (
  user_id    uuid primary key references public.profiles(user_id) on delete cascade,
  squad_id   uuid not null references public.squads(id) on delete cascade,
  role       text not null default 'member' check (role in ('owner', 'member')),
  joined_at  timestamptz not null default now()
);
create index squad_members_squad_idx on public.squad_members (squad_id);

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

create table public.squad_member_weeks (
  squad_id         uuid not null references public.squads(id) on delete cascade,
  user_id          uuid not null references public.profiles(user_id) on delete cascade,
  week_start       date not null,
  start_net_worth  numeric(14,2) not null default 0,
  end_net_worth    numeric(14,2),                 -- set when the week is settled
  weeks_played     integer not null default 0,
  rewarded         boolean not null default false,  -- got the squad-goal reward this week
  primary key (squad_id, user_id, week_start)
);
create index squad_member_weeks_user_idx on public.squad_member_weeks (user_id, week_start);

create table public.squad_feed (
  id          uuid primary key default gen_random_uuid(),
  squad_id    uuid not null references public.squads(id) on delete cascade,
  user_id     uuid references public.profiles(user_id) on delete set null,  -- null for squad-wide posts
  kind        text not null,
  emoji       text not null,
  body        text not null,
  created_at  timestamptz not null default now()
);
create index squad_feed_squad_idx on public.squad_feed (squad_id, created_at desc);

create table public.squad_reactions (
  feed_id     uuid not null references public.squad_feed(id) on delete cascade,
  user_id     uuid not null references public.profiles(user_id) on delete cascade,
  emoji       text not null,
  created_at  timestamptz not null default now(),
  primary key (feed_id, user_id)
);

-- =============================================================================
-- Functions
-- =============================================================================

-- New auth user → profile + wallet. Username collisions get a numeric suffix
-- instead of aborting the sign-up (the old trigger failed sign-up with a 500).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = ''
as $$
declare
  v_base     text;
  v_username text;
  v_try      integer := 0;
  -- Starting cash for a new player. Tune to taste.
  c_starting_balance constant numeric := 5000;
begin
  v_base := coalesce(
    nullif(new.raw_user_meta_data ->> 'username', ''),
    nullif(split_part(coalesce(new.email, ''), '@', 1), ''),
    'player'
  );
  v_base := left(regexp_replace(v_base, '[^A-Za-z0-9_.]', '', 'g'), 40);
  if char_length(v_base) < 3 then
    v_base := v_base || 'player';
  end if;
  v_username := v_base;

  while exists (select 1 from public.profiles where username = v_username) loop
    v_try := v_try + 1;
    v_username := v_base || (floor(random() * 9000) + 1000)::int::text;
    if v_try > 20 then
      v_username := v_base || replace(gen_random_uuid()::text, '-', '');
      exit;
    end if;
  end loop;

  insert into public.profiles (user_id, username, profile_picture_url)
  values (new.id, v_username, new.raw_user_meta_data ->> 'avatar_url');

  insert into public.user_balances (user_id, current_balance)
  values (new.id, c_starting_balance);

  insert into public.transactions (user_id, type, category, amount, description)
  values (new.id, 'income', 'starting_balance', c_starting_balance, 'Starting cash');

  return new;
end $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- The ONLY way money moves. Positive amount = credit, negative = debit.
-- Atomic (single UPDATE with a guard), never overdraws, always logs.
create or replace function public.adjust_balance(
  p_user_id  uuid,
  p_amount   numeric,
  p_reason   text,
  p_category text default 'balance_adjustment'
) returns numeric
language plpgsql
security definer set search_path = public
as $$
declare
  v_new numeric;
begin
  if p_amount is null or p_amount = 0 then
    raise exception 'Amount must be non-zero';
  end if;

  insert into user_balances (user_id, current_balance)
  values (p_user_id, 0)
  on conflict (user_id) do nothing;

  update user_balances
     set current_balance = current_balance + p_amount
   where user_id = p_user_id
     and (p_amount > 0 or current_balance + p_amount >= 0)
  returning current_balance into v_new;

  if v_new is null then
    raise exception 'Insufficient funds' using errcode = 'P0001';
  end if;

  insert into transactions (user_id, type, category, amount, description)
  values (p_user_id,
          case when p_amount > 0 then 'income' else 'expense' end,
          coalesce(p_category, 'balance_adjustment'),
          abs(p_amount),
          p_reason);

  return v_new;
end $$;

-- Atomic sanity change, clamped to 0..100. Returns the new value.
create or replace function public.adjust_sanity(p_user_id uuid, p_delta integer)
returns integer
language sql
security definer set search_path = public
as $$
  update profiles
     set sanity = greatest(0, least(100, sanity + p_delta))
   where user_id = p_user_id
  returning sanity;
$$;

-- Recount void reaction counters from the source of truth (no lost updates).
create or replace function public.refresh_void_post_counts(p_post_id uuid)
returns void
language sql
security definer set search_path = public
as $$
  update void_posts p
     set oof_count  = (select count(*) from void_reactions r where r.post_id = p.id and r.reaction_type = 'oof'),
         same_count = (select count(*) from void_reactions r where r.post_id = p.id and r.reaction_type = 'same')
   where p.id = p_post_id;
$$;

create or replace function public.get_top_players(limit_count integer default 5)
returns table (id uuid, user_id uuid, username text, net_worth numeric, profile_picture_url text)
language sql stable
security definer set search_path = public
as $$
  select p.id, p.user_id, p.username, p.net_worth, p.profile_picture_url
    from profiles p
   order by p.net_worth desc
   limit greatest(1, least(limit_count, 100));
$$;

create or replace function public.start_integrated_mission(p_player_id uuid, p_mission_id uuid)
returns uuid
language plpgsql
security definer set search_path = public
as $$
declare
  v_id      uuid;
  v_mission integrated_missions%rowtype;
  v_profile profiles%rowtype;
begin
  select * into v_mission from integrated_missions where id = p_mission_id;
  if not found then
    raise exception 'Mission not found: %', p_mission_id;
  end if;

  select * into v_profile from profiles where user_id = p_player_id;
  if not found then
    raise exception 'Player not found: %', p_player_id;
  end if;

  insert into player_mission_progress (player_id, mission_id, is_active, current_month,
                                       constraints_applied, game_state_snapshot)
  values (
    p_player_id, p_mission_id, true, 1,
    jsonb_build_object(
      'income_multiplier',       v_mission.income_multiplier,
      'expense_multiplier',      v_mission.expense_multiplier,
      'can_change_job',          v_mission.can_change_job,
      'can_buy_assets',          v_mission.can_buy_assets,
      'can_take_loans',          v_mission.can_take_loans,
      'can_rent_property',       v_mission.can_rent_property,
      'can_sell_assets',         v_mission.can_sell_assets,
      'can_buy_lifestyle_items', v_mission.can_buy_lifestyle_items,
      'allowed_asset_types',     v_mission.allowed_asset_types,
      'max_loan_amount',         v_mission.max_loan_amount,
      'allowed_loan_types',      v_mission.allowed_loan_types,
      'max_monthly_spending',    v_mission.max_monthly_spending
    ),
    jsonb_build_object(
      'net_worth',      v_profile.net_worth,
      'monthly_income', v_profile.monthly_income,
      'credit_score',   v_profile.credit_score,
      'started_at',     now()
    )
  )
  returning id into v_id;   -- unique index rejects a second active mission

  insert into player_mission_success_tracking (player_mission_id, criteria_id, current_value, is_met)
  select v_id, sc.id,
         case sc.metric
           when 'net_worth'      then v_profile.net_worth
           when 'monthly_income' then v_profile.monthly_income
           when 'credit_score'   then v_profile.credit_score
           else 0
         end,
         false
    from mission_success_criteria sc
   where sc.mission_id = p_mission_id;

  return v_id;
end $$;

-- Server-only functions: never callable with the anon/authenticated key.
revoke execute on function public.adjust_balance(uuid, numeric, text, text)   from public, anon, authenticated;
revoke execute on function public.adjust_sanity(uuid, integer)                from public, anon, authenticated;
revoke execute on function public.refresh_void_post_counts(uuid)              from public, anon, authenticated;
revoke execute on function public.start_integrated_mission(uuid, uuid)        from public, anon, authenticated;
revoke execute on function public.handle_new_user()                           from public, anon, authenticated;
grant  execute on function public.adjust_balance(uuid, numeric, text, text)   to service_role;
grant  execute on function public.adjust_sanity(uuid, integer)                to service_role;
grant  execute on function public.refresh_void_post_counts(uuid)              to service_role;
grant  execute on function public.start_integrated_mission(uuid, uuid)        to service_role;
grant  execute on function public.get_top_players(integer)                    to anon, authenticated, service_role;

-- =============================================================================
-- The market on game time (app/game/market.py): each player's own prices.
-- =============================================================================
alter table public.assets add column if not exists annual_drift numeric(6,4);
alter table public.assets add column if not exists annual_volatility numeric(6,4);


create table public.player_market_prices (
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  asset_id   text not null references public.assets(id) on delete cascade,
  price      numeric(18,2) not null check (price > 0),
  prev_price numeric(18,2),
  week       integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (user_id, asset_id)
);

create table public.player_market_events (
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
create index player_market_events_user_week_idx on public.player_market_events (user_id, week desc);


-- =============================================================================
-- Row Level Security
-- =============================================================================
-- RLS on everywhere. No policy = no access for anon/authenticated
-- (the Flask backend's service_role key bypasses RLS).
do $$
declare t record;
begin
  for t in select tablename from pg_tables where schemaname = 'public' loop
    execute format('alter table public.%I enable row level security', t.tablename);
  end loop;
end $$;

-- Catalogue / reference data: readable by any signed-in player.
create policy "catalogue read" on public.assets                   for select to anon, authenticated using (true);
create policy "catalogue read" on public.job_market               for select to authenticated using (true);
create policy "catalogue read" on public.courses                  for select to authenticated using (true);
create policy "catalogue read" on public.rental_properties        for select to authenticated using (true);
create policy "catalogue read" on public.home_listings            for select to authenticated using (true);
create policy "catalogue read" on public.liability_items          for select to authenticated using (true);
create policy "catalogue read" on public.life_events              for select to authenticated using (true);
create policy "catalogue read" on public.life_event_choices       for select to authenticated using (true);
create policy "catalogue read" on public.integrated_missions      for select to authenticated using (true);
create policy "catalogue read" on public.mission_decision_points  for select to authenticated using (true);
create policy "catalogue read" on public.mission_decision_options for select to authenticated using (true);
create policy "catalogue read" on public.mission_success_criteria for select to authenticated using (true);
create policy "catalogue read" on public.mission_story_events     for select to authenticated using (true);
create policy "catalogue read" on public.mentors                  for select to authenticated using (true);
create policy "catalogue read" on public.market_news              for select to authenticated using (true);
create policy "catalogue read" on public.bank_loans               for select to authenticated using (borrower_id is null or borrower_id = auth.uid());

-- Profiles: public game stats are readable, private columns are not.
create policy "profiles readable" on public.profiles for select to authenticated using (true);
create policy "own push token"    on public.profiles for update to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());
revoke select, insert, update, delete on public.profiles from anon, authenticated;
grant select (id, user_id, username, net_worth, monthly_income, credit_score, wealth_level,
              experience_points, profile_picture_url, trading_profits, sanity,
              has_completed_onboarding, created_at)
  on public.profiles to authenticated;
-- The app writes its own Expo push token directly; nothing else.
grant update (expo_push_token, push_token_updated_at) on public.profiles to authenticated;

-- Social graph: readable (follower lists, counts). Writes go through the API.
create policy "follows readable" on public.user_follows for select to authenticated using (true);

-- Chat: participants can read; only the recipient can flip status to 'read'.
create policy "chat participants read" on public.chat_messages for select to authenticated
  using (auth.uid() in (sender_id, recipient_id));
create policy "chat recipient marks read" on public.chat_messages for update to authenticated
  using (recipient_id = auth.uid()) with check (recipient_id = auth.uid());
revoke update on public.chat_messages from anon, authenticated;
grant update (status) on public.chat_messages to authenticated;

-- Own data (read-only from the app).
create policy "own life events" on public.user_life_events for select to authenticated using (user_id = auth.uid());
create policy "own notifications" on public.notifications for select to authenticated using (user_id = auth.uid());

-- The Void feed (realtime subscription needs SELECT).
create policy "void readable"           on public.void_posts     for select to authenticated using (true);
create policy "void reactions readable" on public.void_reactions for select to authenticated using (true);

-- =============================================================================
-- Realtime (the app subscribes to these)
-- =============================================================================
alter publication supabase_realtime add table public.void_posts;
alter publication supabase_realtime add table public.chat_messages;
alter publication supabase_realtime add table public.assets;

-- =============================================================================
-- Storage: avatars bucket (profile pictures)
-- =============================================================================
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

create policy "avatars public read" on storage.objects for select
  using (bucket_id = 'avatars');
create policy "avatars owner write" on storage.objects for insert to authenticated
  with check (bucket_id = 'avatars' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "avatars owner update" on storage.objects for update to authenticated
  using (bucket_id = 'avatars' and auth.uid()::text = (storage.foldername(name))[1]);
create policy "avatars owner delete" on storage.objects for delete to authenticated
  using (bucket_id = 'avatars' and auth.uid()::text = (storage.foldername(name))[1]);
