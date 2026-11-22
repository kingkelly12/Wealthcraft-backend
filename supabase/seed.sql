-- =============================================================================
-- Adulting — starter catalogue data
-- =============================================================================
-- The original catalogue (assets, jobs, courses, rentals, lifestyle items,
-- missions) only ever existed inside the deleted Supabase project; it was never
-- committed. This file is a STARTER set so the game is playable on a fresh
-- database. Prices and numbers are game-balance placeholders: tune them.
--
-- Run after schema.sql. Safe to re-run (ON CONFLICT DO NOTHING on natural keys).
-- Then also run my_flask_app/seed_mentors.sql and my_flask_app/seed_life_events.sql.
-- =============================================================================

-- ---------------------------------------------------------------- Assets -----
-- monthly_income = yield per unit per month (dividends / rent / profit share).
insert into public.assets (name, category, price, monthly_income, description, risk_level, roi, time_to_return, availability, total_supply) values
  ('Index Fund (VTI)',         'stocks',      250.00,    0.75, 'Broad market index fund. Slow, steady, boring — in a good way.', 'low',       6.0,  '5+ years',  100000, 100000),
  ('Blue Chip Tech (TECHX)',   'stocks',      180.00,    0.30, 'Large-cap tech giant. Grows with the economy, dips with the hype.', 'medium',  9.0,  '3-5 years', 100000, 100000),
  ('Dividend King (DVK)',      'stocks',       60.00,    0.25, 'Consumer staples company with 50 years of rising dividends.', 'low',            5.0,  '5+ years',  100000, 100000),
  ('Meme Stock (YOLO)',        'stocks',       15.00,    0.00, 'Driven by vibes and forums. Can 10x. Can go to zero.', 'very_high',           0.0,  'unknown',   100000, 100000),
  ('Bitcoin',                  'crypto',    60000.00,    0.00, 'Digital gold. Wild swings, no yield.', 'high',                                0.0,  'unknown',   1000,   21000000),
  ('Ethereum',                 'crypto',     3000.00,    6.00, 'Smart-contract platform; staking pays a small yield.', 'high',                 2.4,  'unknown',   10000,  120000000),
  ('DogeMoon',                 'crypto',        0.20,    0.00, 'A joke that became a coin. Pure speculation.', 'very_high',                   0.0,  'unknown',   10000000, 10000000),
  ('EUR/USD Position',         'forex',      1000.00,    0.00, 'Leveraged currency position. Small moves, real consequences.', 'high',         0.0,  'days',      10000,  10000),
  ('Studio Apartment Unit',    'real_estate', 85000.00, 650.00, 'Rent it out. Tenants pay your mortgage... in theory.', 'medium',              9.2,  '10+ years', 500,    500),
  ('Duplex',                   'real_estate',240000.00,1900.00, 'Two units, two rent cheques, twice the plumbing calls.', 'medium',            9.5,  '10+ years', 200,    200),
  ('Food Truck',               'business',   45000.00, 900.00, 'Taco Tuesday every day. Long hours, real cash flow.', 'high',               24.0,  '4-5 years', 300,    300),
  ('Laundromat',               'business',  120000.00,2200.00, 'The classic boring business that quietly prints money.', 'medium',          22.0,  '5 years',   150,    150)
on conflict (name) do nothing;

-- ------------------------------------------------------------ Job market -----
-- salary is ANNUAL. The monthly job pays salary/12 on payday.
insert into public.job_market (title, industry, company, salary, level, experience_months, description) values
  ('Barista',                 'Hospitality', 'Bean There Café',      28000, 'entry',  0,  'Early mornings, latte art, and the occasional rude customer.'),
  ('Retail Associate',        'Retail',      'MegaMart',             30000, 'entry',  0,  'Restock, upsell, repeat.'),
  ('Delivery Driver',         'Logistics',   'ZoomDrop',             34000, 'entry',  0,  'Your car, their packages.'),
  ('Customer Support Rep',    'Tech',        'HelpDesk Inc.',        38000, 'entry',  0,  'Have you tried turning it off and on again?'),
  ('Junior Accountant',       'Finance',     'Ledger & Co.',         52000, 'junior', 6,  'Spreadsheets with consequences.'),
  ('Junior Developer',        'Tech',        'ByteForge',            65000, 'junior', 6,  'Ship features, fix bugs, learn fast.'),
  ('Registered Nurse',        'Healthcare',  'City General',         72000, 'mid',    12, 'Long shifts, real impact.'),
  ('Marketing Manager',       'Marketing',   'Hype Labs',            85000, 'mid',    24, 'Own the brand, own the budget.'),
  ('Senior Software Engineer','Tech',        'CloudNine Systems',   130000, 'senior', 48, 'Architecture, mentoring, on-call.'),
  ('Investment Analyst',      'Finance',     'Summit Capital',      110000, 'senior', 36, 'Model the market before it models you.')
on conflict (title, company) do nothing;

-- --------------------------------------------------------------- Courses -----
-- salary_boost is a permanent MONTHLY income increase on completion.
insert into public.courses (title, description, category, difficulty, duration_hours, cost, salary_boost, difficulty_rating) values
  ('Budgeting 101',               'Track every dollar and stop wondering where it went.',           'personal_finance', 'beginner',     2,   0,    50, 1),
  ('Excel for Everyone',          'Formulas, pivot tables and the confidence to use them.',         'skills',           'beginner',     6,   150,  150, 1),
  ('Intro to Investing',          'Stocks, bonds, index funds and compounding.',                    'investing',        'beginner',     8,   300,  100, 2),
  ('Digital Marketing Certificate','SEO, ads and analytics employers actually pay for.',            'skills',           'intermediate', 20,  900,  400, 2),
  ('Full-Stack Coding Bootcamp',  'Twelve intense weeks that change your salary bracket.',          'tech',             'advanced',     120, 6000, 1500, 4),
  ('Real Estate Fundamentals',    'Cap rates, cash flow and how not to buy a money pit.',           'investing',        'intermediate', 16,  1200, 250, 3),
  ('CFA Level I Prep',            'The first step to a finance career that pays.',                  'finance',          'advanced',     200, 3500, 1200, 5)
on conflict (title) do nothing;

-- ----------------------------------------------------- Rental properties -----
insert into public.rental_properties (name, property_type, monthly_rent, location, amenities) values
  ('Shared Room',             'room',      450,  'Student Quarter', '{"Wi-Fi","Shared kitchen"}'),
  ('Studio Apartment',        'studio',    950,  'Downtown Edge',   '{"Wi-Fi","Gym"}'),
  ('One-Bedroom Apartment',   'apartment', 1400, 'Midtown',         '{"Balcony","Gym","Parking"}'),
  ('Two-Bedroom Condo',       'condo',     2200, 'Riverside',       '{"Pool","Concierge","Parking"}'),
  ('Penthouse',               'penthouse', 6500, 'Skyline District','{"Rooftop terrace","Doorman","Private elevator"}')
on conflict (name) do nothing;

-- ------------------------------------------------- Lifestyle (liabilities) ---
insert into public.liability_items (name, category, base_price, monthly_cost, description) values
  ('Latest Smartphone',  'tech',      1200,   40,   'Same apps, better camera, new monthly plan.'),
  ('Designer Handbag',   'fashion',   2500,   0,    'Looks rich. Is not an investment.'),
  ('Used Sedan',         'vehicle',   9000,   180,  'Gets you from A to B. Insurance included in monthly.'),
  ('Luxury SUV',         'vehicle',   65000,  950,  'Fuel, insurance and the feeling of arrival.'),
  ('Gym Membership+',    'wellness',  300,    120,  'Premium gym with smoothies you will pay extra for.'),
  ('Speedboat',          'vehicle',   85000,  1200, 'Two best days: buying it and selling it.'),
  ('Rolex Submariner',   'fashion',   14000,  0,    'Tells time. Mostly tells everyone else something.')
on conflict (name) do nothing;

-- ------------------------------------------------------ Bank loan products ---
-- borrower_id NULL = product template. interest_rate is a FRACTION.
-- monthly_payment * term = amount + total_interest.
insert into public.bank_loans (borrower_id, type, amount, interest_rate, term, monthly_payment, total_interest, credit_required, status, collateral) values
  (null, 'Quick Cash',         1000.00,  0.0800, 3,  338.00,  14.00,   550, 'available', 'none'),
  (null, 'Emergency Fund',     2000.00,  0.1200, 6,  345.00,  70.00,   580, 'available', 'none'),
  (null, 'Personal Loan',      5000.00,  0.0500, 12, 428.00,  136.00,  600, 'available', 'none'),
  (null, 'Education Loan',     8000.00,  0.0400, 24, 347.00,  328.00,  640, 'available', 'none'),
  (null, 'Debt Consolidation', 10000.00, 0.0600, 36, 304.00,  944.00,  650, 'available', 'none'),
  (null, 'Business Starter',   25000.00, 0.0700, 24, 1119.00, 1856.00, 680, 'available', 'business_assets')
on conflict (type) where borrower_id is null do nothing;

-- ---------------------------------------------------------------- Missions ---
with m as (
  insert into public.integrated_missions
    (name, description, short_description, icon, category, difficulty, duration_months,
     learning_objectives, can_buy_lifestyle_items, completion_reward)
  values
    ('Emergency Fund Builder',
     'Build a cash cushion worth three months of expenses without buying any lifestyle items.',
     'Save up a safety net.', '🛟', 'wealth_preservation', 'beginner', 3,
     '{"Pay yourself first","Separate wants from needs","Why emergency funds beat credit cards"}',
     false, 1000)
  on conflict (name) do nothing
  returning id
),
c as (
  insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
  select id, 'net_worth', 10000, 'greater_than', 'Net worth above $10,000', 'Grow your net worth past $10k.', '💰' from m
  returning mission_id
),
d as (
  insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
  select id, 1, 'Paycheck Day', 'Your paycheck just landed. What do you do first?', 'Automate savings before you see the money.' from m
  returning id
)
insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, risk_level, option_order)
select d.id, x.label, x.description, x.cash, x.risk, x.ord
from d, (values
  ('Auto-transfer 20% to savings', 'Boring. Effective.',                0,    'low',  1),
  ('Treat yourself first',         'You deserve it... right?',          -300, 'high', 2),
  ('Pick up a weekend side gig',   'Tired, but your fund grows faster.', 250, 'medium', 3)
) as x(label, description, cash, risk, ord);

with m as (
  insert into public.integrated_missions
    (name, description, short_description, icon, category, difficulty, duration_months,
     learning_objectives, can_take_loans, completion_reward)
  values
    ('First Investment Portfolio',
     'Start investing without touching debt. Grow your portfolio and your monthly passive income.',
     'Invest without borrowing.', '📈', 'investment', 'intermediate', 6,
     '{"Diversification","Dollar-cost averaging","Why you never invest borrowed money you can''t lose"}',
     false, 2500)
  on conflict (name) do nothing
  returning id
)
insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
select id, 'monthly_income', 4000, 'greater_than', 'Monthly income above $4,000', 'Salary + passive income above $4k/month.', '📊' from m;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, immediate_cash, display_order)
select id, 'The Market Dips', '📉',
       'Headlines scream "CRASH". Your portfolio is red. Your group chat is panicking. Do you?',
       'market_event', 'month', 2, 0, 1
from public.integrated_missions where name = 'First Investment Portfolio'
on conflict (mission_id, display_order) do nothing;

-- ------------------------------------------- Gigs, item costs, bank rates -----
-- Same as migrations/20261125000000_money_realism.sql (safe to re-run).
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

-- --- Bank loans: Kenyan-style rates, much bigger amounts ------------------------------
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
