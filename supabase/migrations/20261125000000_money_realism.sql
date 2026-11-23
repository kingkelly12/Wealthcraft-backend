-- =============================================================================
-- Money realism: gigs, running costs and leasing, friend loans, bank rates
-- =============================================================================
-- * Gigs: part-time work beside your main job, paid every game WEEK
--   (job_market.kind = 'gig'). One main job, up to two gigs.
-- * Lifestyle items: an annual depreciation rate, monthly running costs broken
--   down (fuel, insurance, crew...), a periodic service bill, and for vehicles,
--   boats and aircraft, income from leasing them out.
-- * Friend loans (P2P): the rate is now per YEAR (like a bank), offers can go
--   to one friend, friends can ask each other for a loan, and each loan keeps a
--   repayment record. Banks are repriced to high rates (13-24% a year)
--   but lend far more.
-- Household bills (groceries, electricity, water, Wi-Fi) are computed by the
-- backend from the home you rent; roommates split them. No schema needed.
-- =============================================================================

-- --- Gigs ---------------------------------------------------------------------------
alter table public.job_market add column if not exists kind text not null default 'job';
alter table public.job_market add column if not exists weekly_pay numeric(12,2) not null default 0;
alter table public.job_market add column if not exists hours_per_week integer;
alter table public.job_market add column if not exists sanity_per_week integer not null default 0;
alter table public.jobs add column if not exists kind text not null default 'job';
alter table public.jobs add column if not exists weekly_pay numeric(12,2) not null default 0;
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

insert into public.job_market (title, industry, company, salary, level, experience_months, description, kind, weekly_pay, hours_per_week, sanity_per_week) values
  ('Rideshare Driver',     'Gig economy', 'Rydr',            0, 'entry', 0, 'Evenings and weekends. Your car, their playlist.',            'gig', 140, 12, -2),
  ('Food Delivery Rider',  'Gig economy', 'ChowNow',         0, 'entry', 0, 'Rain or shine, the fries must arrive warm.',                   'gig', 95,  10, -1),
  ('Weekend Bartender',    'Hospitality', 'The Tipsy Goat',  0, 'entry', 0, 'Friday and Saturday nights. Tips are where the money is.',     'gig', 120, 12, -2),
  ('Freelance Designer',   'Creative',    'Self-employed',   0, 'entry', 0, 'Logos, flyers and clients who want it "more pop".',            'gig', 160, 10, -1),
  ('Online Tutor',         'Education',   'BrightMinds',     0, 'entry', 0, 'Help kids with maths after work. Wholesome, mostly.',          'gig', 85,  6,  0),
  ('Event Photographer',   'Creative',    'Snapshot Events', 0, 'entry', 0, 'Weddings, birthdays, graduations. Smile!',                     'gig', 150, 8,  -1),
  ('Online Reseller',      'Retail',      'Self-employed',   0, 'entry', 0, 'Buy low at thrift stores, sell high online.',                  'gig', 70,  5,  1),
  ('Content Creator',      'Creative',    'Self-employed',   0, 'entry', 0, 'Post daily, pray to the algorithm. Small brand deals.',        'gig', 55,  6,  1)
on conflict (title, company) do update set
  kind = excluded.kind, weekly_pay = excluded.weekly_pay, hours_per_week = excluded.hours_per_week,
  sanity_per_week = excluded.sanity_per_week, description = excluded.description, salary = 0;

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

-- monthly_cost stays the sum of the monthly running costs (older code reads it).
insert into public.liability_items (name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear) values
  ('Latest Smartphone', 'tech',     1200,    40,    'Same apps, better camera, new monthly plan.', 0.35,
     '[{"label":"Phone plan","monthly":40}]', 0, 0, 0, null, 0),
  ('Designer Handbag',  'fashion',  2500,    0,     'Looks rich. Is not an investment.', 0.10,
     '[]', 0, 0, 0, null, 0),
  ('Rolex Submariner',  'fashion',  14000,   15,    'Tells time. Mostly tells everyone else something. Holds its value.', 0.00,
     '[{"label":"Insurance","monthly":15}]', 700, 36, 0, null, 0),
  ('Gym Membership+',   'wellness', 300,     120,   'Premium gym with smoothies you will pay extra for.', 0.60,
     '[{"label":"Membership","monthly":120}]', 0, 0, 0, null, 0),
  ('Used Sedan',        'vehicle',  9000,    180,   'Gets you from A to B. Rent it to a ride-hail driver when you don''t need it.', 0.15,
     '[{"label":"Fuel","monthly":110},{"label":"Insurance","monthly":55},{"label":"Parking","monthly":15}]', 250, 6, 420, 'Rent to a ride-hail driver', 0.10),
  ('Luxury SUV',        'vehicle',  65000,   780,   'Fuel, insurance and the feeling of arrival. Chauffeur companies will hire it.', 0.18,
     '[{"label":"Fuel","monthly":320},{"label":"Insurance","monthly":380},{"label":"Parking","monthly":80}]', 900, 6, 1600, 'Hire it to a chauffeur company', 0.08),
  ('Speedboat',         'boat',     85000,   1050,  'Two best days: buying it and selling it. Weekend charters help.', 0.12,
     '[{"label":"Fuel","monthly":300},{"label":"Insurance","monthly":350},{"label":"Mooring","monthly":400}]', 2500, 6, 2600, 'Charter it out', 0.08),
  ('Superyacht',        'boat',     1200000, 15500, 'Forty metres of status. A full crew lives on it, and so does your money.', 0.10,
     '[{"label":"Fuel","monthly":3000},{"label":"Insurance","monthly":1500},{"label":"Crew","monthly":8500},{"label":"Marina berth","monthly":2500}]', 30000, 12, 42000, 'Charter it to tourists', 0.05),
  ('Helicopter',        'aircraft', 900000,  9500,  'Skip the traffic forever. Pilots, hangars and inspections not included.', 0.08,
     '[{"label":"Fuel","monthly":2500},{"label":"Insurance","monthly":2000},{"label":"Hangar","monthly":1500},{"label":"Pilot","monthly":3500}]', 25000, 6, 32000, 'Lease it for tours and transfers', 0.06),
  ('Private Jet',       'aircraft', 4500000, 38000, 'The ultimate flex. Every hour in the air costs more than most people earn in a week.', 0.07,
     '[{"label":"Fuel","monthly":12000},{"label":"Insurance","monthly":6000},{"label":"Crew","monthly":15000},{"label":"Hangar","monthly":5000}]', 90000, 6, 140000, 'Lease it to a charter operator', 0.05)
on conflict (name) do update set
  category = excluded.category, base_price = excluded.base_price, monthly_cost = excluded.monthly_cost,
  description = excluded.description, depreciation_rate = excluded.depreciation_rate, costs = excluded.costs,
  service_cost = excluded.service_cost, service_every_months = excluded.service_every_months,
  lease_income = excluded.lease_income, lease_label = excluded.lease_label, lease_wear = excluded.lease_wear;

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

-- --- Bank loans: high rates (13-24% a year), much bigger amounts ------------------------------
-- interest_rate is a FRACTION per year; payments are amortised.
insert into public.bank_loans (borrower_id, type, amount, interest_rate, term, monthly_payment, total_interest, credit_required, status, collateral) values
  (null, 'Quick Cash',         1000.00,   0.2400, 3,   346.75,  40.26,     550, 'available', 'none'),
  (null, 'Emergency Fund',     2000.00,   0.2200, 6,   355.05,  130.28,    580, 'available', 'none'),
  (null, 'Personal Loan',      10000.00,  0.1800, 24,  499.24,  1981.78,   600, 'available', 'none'),
  (null, 'Education Loan',     15000.00,  0.1400, 36,  512.66,  3455.92,   640, 'available', 'none'),
  (null, 'Debt Consolidation', 20000.00,  0.1700, 36,  713.05,  5669.96,   650, 'available', 'none'),
  (null, 'Car Loan',           30000.00,  0.1600, 48,  850.21,  10810.00,  660, 'available', 'vehicle'),
  (null, 'Business Starter',   75000.00,  0.1700, 60,  1863.94, 36836.59,  690, 'available', 'business_assets'),
  (null, 'Mortgage',           250000.00, 0.1300, 180, 3163.11, 319358.98, 720, 'available', 'property')
on conflict (type) where borrower_id is null do update set
  amount = excluded.amount, interest_rate = excluded.interest_rate, term = excluded.term,
  monthly_payment = excluded.monthly_payment, total_interest = excluded.total_interest,
  credit_required = excluded.credit_required, collateral = excluded.collateral;
