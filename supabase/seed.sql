-- =============================================================================
-- Adulting — starter catalogue data
-- =============================================================================
-- The original catalogue (assets, jobs, courses, rentals, lifestyle items,
-- missions) only ever existed inside the deleted Supabase project; it was never
-- committed. This file is a STARTER set so the game is playable on a fresh
-- database. Prices and numbers are game-balance placeholders: tune them.
--
-- Run after schema.sql. Safe to re-run (ON CONFLICT DO NOTHING on natural keys).
-- Then also run supabase/seed_mentors.sql and supabase/seed_life_events.sql.
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

-- Market behaviour: average growth a year and how far it swings (app/game/market.py).
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

-- Businesses for every budget (also in migration 20261126000000). Profit swings by risk level.
insert into public.assets (name, category, price, monthly_income, description, risk_level, roi, time_to_return, availability, total_supply) values
  ('Phone Repair Kiosk', 'business', 1500.00, 55.00, 'Cracked screens, dead batteries and chargers. Everyone breaks their phone eventually.', 'high', 44.0, '2-3 years', 2000, 2000),
  ('Online Thrift Store', 'business', 2000.00, 75.00, 'Second-hand finds, good lighting, nationwide delivery. Depends entirely on the algorithm''s mood.', 'very_high', 45.0, '2 years', 2000, 2000),
  ('Vending Machine', 'business', 2800.00, 85.00, 'Sells sodas and crisps while you sleep. Occasionally eats somebody''s coins.', 'medium', 36.4, '3 years', 1500, 1500),
  ('Small Farm', 'business', 5000.00, 160.00, 'Eggs, honey and vegetables for the farmers'' market and local restaurants. One bad season away from chaos.', 'high', 38.4, '2-3 years', 800, 800),
  ('Car Wash', 'business', 7500.00, 230.00, 'Hoses, sponges and a playlist. Rainy weeks are slow; dusty weeks are gold.', 'medium', 36.8, '3 years', 600, 600),
  ('Print & Copy Shop', 'business', 9000.00, 220.00, 'Printing, scanning, passport photos and helping people find the "any key".', 'medium', 29.3, '3-4 years', 600, 600),
  ('Barbershop', 'business', 12000.00, 340.00, 'Three chairs, one TV playing football, endless opinions. Regulars pay the bills.', 'medium', 34.0, '3 years', 500, 500),
  ('Beauty Salon', 'business', 18000.00, 480.00, 'Braids, nails and gossip. Booked solid before holidays and weddings.', 'medium', 32.0, '3 years', 400, 400),
  ('Coffee Kiosk', 'business', 22000.00, 520.00, 'Good coffee near a busy office block. Lives and dies by the morning rush.', 'high', 28.4, '3-4 years', 400, 400),
  ('Convenience Store', 'business', 35000.00, 750.00, 'Bread, milk, phone top-ups and everything else people forget. Boring, steady, open late.', 'low', 25.7, '4 years', 300, 300),
  ('Gym', 'business', 85000.00, 1600.00, 'Full in January, quiet by March. Memberships keep paying either way.', 'medium', 22.6, '4-5 years', 150, 150),
  ('Co-working Space', 'business', 150000.00, 2600.00, 'Desks, Wi-Fi and free coffee for freelancers who can''t work from home.', 'medium', 20.8, '5 years', 100, 100),
  ('Event Venue', 'business', 220000.00, 3700.00, 'Weddings, birthdays and corporate end-year parties. Wedding season is a gold rush.', 'high', 20.2, '5 years', 80, 80),
  ('Franchise Restaurant', 'business', 300000.00, 4800.00, 'A known brand with a proven menu. The franchise fee is steep; customers already trust it.', 'low', 19.2, '5-6 years', 60, 60),
  ('Boutique Hotel', 'business', 480000.00, 7400.00, 'Twelve rooms, a rooftop bar and reviews that make or break your month.', 'medium', 18.5, '6 years', 40, 40)
on conflict (name) do update set
  price = excluded.price, monthly_income = excluded.monthly_income, description = excluded.description,
  risk_level = excluded.risk_level, roi = excluded.roi, time_to_return = excluded.time_to_return;

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
-- Matched to job_market (app/game/courses.py): career courses lead to the next job on a ladder
-- (count as experience + a pay bonus while you work in that industry); side-hustle courses
-- raise a gig's weekly pay; money-skills courses are small life skills.
insert into public.courses (title, description, category, difficulty, duration_hours, cost, salary_boost, industry, tier, emoji, weeks, experience_months, pay_bonus_pct, min_months, target_job, target_gig, gig_bonus_pct)
values
  ('Electrical Apprenticeship Certificate', 'Wiring, safety and the regs. Your way off labouring and onto the tools.', 'construction', 'beginner', 30, 600, 0, 'Construction', 'certificate', '🔌', 3, 3, 0.03, 0, 'Apprentice Electrician', null, 0),
  ('Licensed Electrician Course', 'Pass the licence and sign off your own work.', 'construction', 'intermediate', 80, 3500, 0, 'Construction', 'diploma', '⚡', 8, 4, 0.05, 6, 'Electrician', null, 0),
  ('Site Management Diploma', 'Schedules, budgets and keeping twenty contractors happy.', 'construction', 'intermediate', 100, 7500, 0, 'Construction', 'diploma', '📐', 10, 6, 0.06, 18, 'Site Manager', null, 0),
  ('Construction Leadership Program', 'Big builds and big budgets. For experienced site leads.', 'construction', 'advanced', 120, 18000, 0, 'Construction', 'executive', '🏗️', 12, 9, 0.06, 36, 'Construction Director', null, 0),
  ('Graphic Design Certificate', 'Type, colour and layout that clients pay for.', 'creative', 'beginner', 30, 500, 0, 'Creative', 'certificate', '🖌️', 3, 3, 0.03, 0, 'Graphic Designer', null, 0),
  ('UX & Product Design Program', 'Design apps people love to use. Portfolio included.', 'creative', 'intermediate', 80, 4000, 0, 'Creative', 'diploma', '🎨', 8, 4, 0.05, 6, 'UX Designer', null, 0),
  ('Art Direction Diploma', 'Lead shoots, campaigns and other creatives.', 'creative', 'intermediate', 100, 6500, 0, 'Creative', 'diploma', '🎬', 10, 6, 0.06, 18, 'Creative Director', null, 0),
  ('Creative Leadership Masterclass', 'Own the vision for a whole company. For senior creatives.', 'creative', 'advanced', 120, 15000, 0, 'Creative', 'executive', '👁️', 12, 9, 0.06, 36, 'Chief Creative Officer', null, 0),
  ('Teaching Certificate', 'Plan lessons, manage a classroom, get qualified.', 'education', 'beginner', 30, 350, 0, 'Education', 'certificate', '🍎', 3, 3, 0.03, 0, 'Teacher', null, 0),
  ('Curriculum Leadership Diploma', 'Design what a whole department teaches.', 'education', 'intermediate', 80, 3000, 0, 'Education', 'diploma', '📚', 8, 4, 0.05, 6, 'Head of Department', null, 0),
  ('School Management Diploma', 'Timetables, staff and budgets of a whole school.', 'education', 'intermediate', 100, 5000, 0, 'Education', 'diploma', '🗂️', 10, 6, 0.06, 18, 'Deputy Principal', null, 0),
  ('Principal Leadership Program', 'Run a school. For experienced school leaders.', 'education', 'advanced', 120, 12000, 0, 'Education', 'executive', '🏫', 12, 9, 0.06, 36, 'School Principal', null, 0),
  ('Solar & Field Technician Certificate', 'Panels, turbines and fixing things out in the field.', 'energy', 'beginner', 30, 900, 0, 'Energy', 'certificate', '☀️', 3, 3, 0.03, 0, 'Field Technician', null, 0),
  ('Process Engineering Diploma', 'Make plants safer, cleaner and more efficient.', 'energy', 'intermediate', 80, 4500, 0, 'Energy', 'diploma', '⚙️', 8, 4, 0.05, 6, 'Process Engineer', null, 0),
  ('Plant Operations Management Diploma', 'Run a plant, its people and its numbers.', 'energy', 'intermediate', 100, 8000, 0, 'Energy', 'diploma', '🏭', 10, 6, 0.06, 18, 'Operations Manager', null, 0),
  ('Energy Executive Program', 'Strategy for power companies in a changing world.', 'energy', 'advanced', 120, 25000, 0, 'Energy', 'executive', '🔋', 12, 9, 0.06, 36, 'Chief Executive Officer', null, 0),
  ('Bookkeeping & Accounting Certificate', 'Ledgers, reconciliations and month-end, done right.', 'finance', 'beginner', 30, 450, 0, 'Finance', 'certificate', '🧾', 3, 3, 0.03, 0, 'Junior Accountant', null, 0),
  ('Financial Modelling Diploma', 'Build the spreadsheets that decide where money goes.', 'finance', 'intermediate', 80, 3500, 0, 'Finance', 'diploma', '📊', 8, 4, 0.05, 6, 'Financial Analyst', null, 0),
  ('Investment Analyst Prep', 'Valuation, markets and portfolio theory. Long nights, big payoff.', 'finance', 'intermediate', 100, 6000, 0, 'Finance', 'diploma', '🏦', 10, 6, 0.06, 18, 'Investment Analyst', null, 0),
  ('Finance Executive Program', 'Capital, strategy and leading a finance team.', 'finance', 'advanced', 120, 28000, 0, 'Finance', 'executive', '💼', 12, 9, 0.06, 36, 'Chief Financial Officer', null, 0),
  ('Pharmacy Technician Certificate', 'Dispensing, stock and patient safety.', 'healthcare', 'beginner', 30, 450, 0, 'Healthcare', 'certificate', '💊', 3, 3, 0.03, 0, 'Pharmacy Technician', null, 0),
  ('Nursing Degree Program', 'Patient care, clinical skills and your nursing licence.', 'healthcare', 'intermediate', 80, 4500, 0, 'Healthcare', 'diploma', '🩺', 8, 4, 0.05, 6, 'Registered Nurse', null, 0),
  ('Nurse Leadership Diploma', 'Run a ward: rotas, standards and people.', 'healthcare', 'intermediate', 100, 5500, 0, 'Healthcare', 'diploma', '📋', 10, 6, 0.06, 18, 'Nurse Manager', null, 0),
  ('Healthcare Executive Program', 'Lead a hospital. For experienced clinical managers.', 'healthcare', 'advanced', 120, 20000, 0, 'Healthcare', 'executive', '🏥', 12, 9, 0.06, 36, 'Hospital Director', null, 0),
  ('Supervisor & Food Safety Certificate', 'Run a shift and keep the kitchen out of the news.', 'hospitality', 'beginner', 30, 300, 0, 'Hospitality', 'certificate', '🍳', 3, 3, 0.03, 0, 'Shift Supervisor', null, 0),
  ('Restaurant Management Diploma', 'Menus, margins and a full house on Friday.', 'hospitality', 'intermediate', 80, 2500, 0, 'Hospitality', 'diploma', '🍽️', 8, 4, 0.05, 6, 'Restaurant Manager', null, 0),
  ('Hotel Operations Diploma', 'Rooms, revenue and five-star reviews.', 'hospitality', 'intermediate', 100, 4500, 0, 'Hospitality', 'diploma', '🛎️', 10, 6, 0.06, 18, 'Hotel Operations Manager', null, 0),
  ('Hospitality Leadership Program', 'Run hotels and restaurants at scale.', 'hospitality', 'advanced', 120, 14000, 0, 'Hospitality', 'executive', '🍾', 12, 9, 0.06, 36, 'General Manager', null, 0),
  ('Warehouse & Forklift Certificate', 'Safe lifting, stock control and leading a crew.', 'logistics', 'beginner', 30, 400, 0, 'Logistics', 'certificate', '📦', 3, 3, 0.03, 0, 'Warehouse Team Lead', null, 0),
  ('Logistics Coordination Diploma', 'Routes, carriers and on-time deliveries.', 'logistics', 'intermediate', 80, 3000, 0, 'Logistics', 'diploma', '🗺️', 8, 4, 0.05, 6, 'Logistics Coordinator', null, 0),
  ('Supply Chain Management Diploma', 'From factory to front door, end to end.', 'logistics', 'intermediate', 100, 6000, 0, 'Logistics', 'diploma', '🚚', 10, 6, 0.06, 18, 'Supply Chain Manager', null, 0),
  ('Operations Executive Program', 'Fleets, warehouses and global routes.', 'logistics', 'advanced', 120, 20000, 0, 'Logistics', 'executive', '🌍', 12, 9, 0.06, 36, 'VP of Supply Chain', null, 0),
  ('Digital Marketing Certificate', 'Ads, social and analytics that move sales.', 'marketing', 'beginner', 30, 900, 0, 'Marketing', 'certificate', '📣', 3, 3, 0.03, 0, 'Marketing Coordinator', null, 0),
  ('Marketing Management Diploma', 'Plans, budgets and a team to run them.', 'marketing', 'intermediate', 80, 3500, 0, 'Marketing', 'diploma', '📈', 8, 4, 0.05, 6, 'Marketing Manager', null, 0),
  ('Brand Strategy Diploma', 'Positioning and campaigns people remember.', 'marketing', 'intermediate', 100, 6500, 0, 'Marketing', 'diploma', '🎯', 10, 6, 0.06, 18, 'Head of Brand', null, 0),
  ('Chief Marketing Officer Program', 'Budgets, agencies and the boardroom.', 'marketing', 'advanced', 120, 22000, 0, 'Marketing', 'executive', '👑', 12, 9, 0.06, 36, 'Chief Marketing Officer', null, 0),
  ('Public Administration Certificate', 'How government works, and how to work in it.', 'public_service', 'beginner', 30, 500, 0, 'Public Service', 'certificate', '🏛️', 3, 3, 0.03, 0, 'Policy Officer', null, 0),
  ('Programme Management Diploma', 'Deliver public programmes on time and on budget.', 'public_service', 'intermediate', 80, 3000, 0, 'Public Service', 'diploma', '📁', 8, 4, 0.05, 6, 'Programme Manager', null, 0),
  ('Policy & Governance Diploma', 'Lead policy and the people who write it.', 'public_service', 'intermediate', 100, 4500, 0, 'Public Service', 'diploma', '📜', 10, 6, 0.06, 18, 'Department Head', null, 0),
  ('Public Leadership Program', 'Run a city. For senior officials.', 'public_service', 'advanced', 120, 12000, 0, 'Public Service', 'executive', '🎖️', 12, 9, 0.06, 36, 'City Manager', null, 0),
  ('Retail Supervisor Certificate', 'Rotas, tills and keeping the floor running.', 'retail', 'beginner', 30, 300, 0, 'Retail', 'certificate', '🏷️', 3, 3, 0.03, 0, 'Assistant Store Manager', null, 0),
  ('Store Management Diploma', 'Targets, stock and a team of your own.', 'retail', 'intermediate', 80, 2500, 0, 'Retail', 'diploma', '🏬', 8, 4, 0.05, 6, 'Store Manager', null, 0),
  ('Multi-Store Management Diploma', 'Run ten shops at once without losing your mind.', 'retail', 'intermediate', 100, 5000, 0, 'Retail', 'diploma', '🗺️', 10, 6, 0.06, 18, 'Regional Manager', null, 0),
  ('Retail Executive Program', 'Chains, buying and brand.', 'retail', 'advanced', 120, 15000, 0, 'Retail', 'executive', '🛒', 12, 9, 0.06, 36, 'Head of Retail Operations', null, 0),
  ('Full-Stack Coding Bootcamp', 'Build real apps end to end. Intense, and it pays.', 'tech', 'beginner', 100, 6000, 0, 'Tech', 'certificate', '💻', 10, 3, 0.03, 0, 'Junior Developer', null, 0),
  ('Software Engineering Diploma', 'Clean code, testing and working in a real team.', 'tech', 'intermediate', 80, 4000, 0, 'Tech', 'diploma', '🧑‍💻', 8, 4, 0.05, 6, 'Software Engineer', null, 0),
  ('Systems Design & Cloud Program', 'Architecture, scale and keeping systems up.', 'tech', 'intermediate', 100, 8000, 0, 'Tech', 'diploma', '☁️', 10, 6, 0.06, 18, 'Senior Software Engineer', null, 0),
  ('Engineering Leadership Program', 'Teams, roadmaps and budgets.', 'tech', 'advanced', 120, 25000, 0, 'Tech', 'executive', '🚀', 12, 9, 0.06, 36, 'Chief Technology Officer', null, 0),
  ('Budgeting 101', 'Where your money goes, and how to tell it where to go instead. Free, and it shows.', 'money_skills', 'beginner', 10, 0, 0, 'Finance', 'skill', '🧾', 1, 1, 0, 0, null, null, 0),
  ('Excel for Everyone', 'Formulas and pivot tables: useful in every office job.', 'money_skills', 'beginner', 20, 150, 0, 'Finance', 'skill', '📊', 2, 1, 0, 0, null, null, 0),
  ('Intro to Investing', 'Stocks, funds, risk and compound interest, minus the hype.', 'money_skills', 'beginner', 20, 300, 0, 'Finance', 'skill', '📈', 2, 1, 0, 0, null, null, 0),
  ('Real Estate Fundamentals', 'Valuations, mortgages and how property deals really work.', 'money_skills', 'beginner', 30, 1200, 0, 'Finance', 'skill', '🏘️', 3, 1, 0, 0, null, null, 0),
  ('Fast Typing & Data Entry Course', 'Faster fingers, better-paid tasks.', 'side_hustle', 'beginner', 10, 120, 0, null, 'skill', '⌨️', 1, 0, 0, 0, null, 'Online Microtasks', 0.2),
  ('Video Editing & Storytelling Course', 'Hooks, cuts and stories people watch to the end.', 'side_hustle', 'beginner', 20, 300, 0, null, 'skill', '🎥', 2, 0, 0, 0, null, 'Content Creator', 0.3),
  ('Product Photography & Listings Course', 'Listings that sell first time.', 'side_hustle', 'beginner', 10, 250, 0, null, 'skill', '📸', 1, 0, 0, 0, null, 'Online Reseller', 0.25),
  ('Pet First Aid & Care Course', 'Owners pay more for someone certified.', 'side_hustle', 'beginner', 10, 200, 0, null, 'skill', '🐾', 1, 0, 0, 0, null, 'Dog Walker & Pet Sitter', 0.2),
  ('Online Tutoring Certificate', 'Better lessons, better reviews, higher rates.', 'side_hustle', 'beginner', 20, 300, 0, null, 'skill', '🎧', 2, 0, 0, 0, null, 'Online Tutor', 0.25),
  ('Childcare & Paediatric First Aid', 'The certificate every parent asks about.', 'side_hustle', 'beginner', 10, 250, 0, null, 'skill', '🧸', 1, 0, 0, 0, null, 'Babysitter', 0.2),
  ('Safe Riding & Route Planning Course', 'More drops per hour, fewer close calls.', 'side_hustle', 'beginner', 10, 150, 0, null, 'skill', '🛵', 1, 0, 0, 0, null, 'Food Delivery Rider', 0.15),
  ('Music Teaching Method Course', 'Teach beginners properly and keep them coming back.', 'side_hustle', 'beginner', 20, 500, 0, null, 'skill', '🎹', 2, 0, 0, 0, null, 'Music Teacher', 0.25),
  ('Market Selling & Pricing Course', 'Display, pricing and the art of the upsell.', 'side_hustle', 'beginner', 10, 250, 0, null, 'skill', '🧺', 1, 0, 0, 0, null, 'Weekend Market Stall', 0.2),
  ('Professional Cleaning Certificate', 'Faster, better, and clients who book weekly.', 'side_hustle', 'beginner', 10, 250, 0, null, 'skill', '🧽', 1, 0, 0, 0, null, 'House Cleaner', 0.2),
  ('Tour Guiding & Storytelling Course', 'Make a simple walk the highlight of their trip. Tips follow.', 'side_hustle', 'beginner', 20, 400, 0, null, 'skill', '🗺️', 2, 0, 0, 0, null, 'Tour Guide', 0.25),
  ('Bartending & Mixology Course', 'Cocktails, speed and charm. The tip jar notices.', 'side_hustle', 'beginner', 20, 450, 0, null, 'skill', '🍸', 2, 0, 0, 0, null, 'Weekend Bartender', 0.25),
  ('Safe Lifting & Moving Course', 'Lift smart, move faster, break nothing.', 'side_hustle', 'beginner', 10, 150, 0, null, 'skill', '📦', 1, 0, 0, 0, null, 'Moving Helper', 0.15),
  ('Professional Translation Certificate', 'Certified work pays double what casual work does.', 'side_hustle', 'beginner', 30, 700, 0, null, 'skill', '🌐', 3, 0, 0, 0, null, 'Translator', 0.3),
  ('Personal Training Certification', 'Get certified and charge like a pro.', 'side_hustle', 'beginner', 30, 800, 0, null, 'skill', '🏋️', 3, 0, 0, 0, null, 'Personal Trainer', 0.3),
  ('Barbering & Braiding Course', 'Fades, braids and a full weekend diary.', 'side_hustle', 'beginner', 30, 700, 0, null, 'skill', '💇', 3, 0, 0, 0, null, 'Mobile Hairdresser', 0.25),
  ('Advanced Driving & Rideshare Course', 'Five-star rides and smarter hours.', 'side_hustle', 'beginner', 10, 300, 0, null, 'skill', '🚗', 1, 0, 0, 0, null, 'Rideshare Driver', 0.15),
  ('Social Media Strategy Course', 'Strategy, not just posting. Clients pay for results.', 'side_hustle', 'beginner', 20, 500, 0, null, 'skill', '📱', 2, 0, 0, 0, null, 'Social Media Manager', 0.25),
  ('Plumbing & Electrical Basics Course', 'Take the jobs other handymen turn down.', 'side_hustle', 'beginner', 30, 700, 0, null, 'skill', '🔧', 3, 0, 0, 0, null, 'Handyman', 0.25),
  ('Photography & Editing Course', 'Light, composition and editing that gets you rebooked.', 'side_hustle', 'beginner', 20, 600, 0, null, 'skill', '📷', 2, 0, 0, 0, null, 'Event Photographer', 0.25),
  ('Freelance Design Business Course', 'Pricing, contracts and clients who pay on time.', 'side_hustle', 'beginner', 20, 600, 0, null, 'skill', '🖥️', 2, 0, 0, 0, null, 'Freelance Designer', 0.25),
  ('DJing & MC Skills Course', 'Read the room, fill the floor, book the next wedding.', 'side_hustle', 'beginner', 20, 650, 0, null, 'skill', '🎤', 2, 0, 0, 0, null, 'Wedding DJ / MC', 0.25)
on conflict (title) do nothing;

-- ----------------------------------------------------- Rental properties -----
insert into public.rental_properties (name, property_type, monthly_rent, location, amenities) values
  ('Shared Room',             'room',      450,  'Student Quarter', '{"Wi-Fi","Shared kitchen"}'),
  ('Studio Apartment',        'studio',    950,  'Downtown Edge',   '{"Wi-Fi","Gym"}'),
  ('One-Bedroom Apartment',   'apartment', 1400, 'Midtown',         '{"Balcony","Gym","Parking"}'),
  ('Two-Bedroom Condo',       'condo',     2200, 'Riverside',       '{"Pool","Concierge","Parking"}'),
  ('Penthouse',               'penthouse', 6500, 'Skyline District','{"Rooftop terrace","Doorman","Private elevator"}')
on conflict (name) do nothing;

-- Homes for sale (also in migration 20261127000000).
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

-- Career ladders (12 industries x 5 rungs) and gigs (also migration 20261129000000).
insert into public.job_market (title, industry, company, salary, level, experience_months, description, kind, weekly_pay, hours_per_week, sanity_per_week) values
  ('Barista', 'Hospitality', 'Bean There Café', 28000, 'entry', 0, 'Early mornings, latte art, and the occasional rude customer.', 'job', 0, null, 0),
  ('Shift Supervisor', 'Hospitality', 'Bean There Café', 35000, 'junior', 6, 'Keys to the shop, the rota and every complaint.', 'job', 0, null, 0),
  ('Restaurant Manager', 'Hospitality', 'The Copper Pot', 52000, 'mid', 18, 'Fully booked Fridays, a chef with opinions and a tight margin.', 'job', 0, null, 0),
  ('Hotel Operations Manager', 'Hospitality', 'Grand Meridian Hotels', 78000, 'senior', 36, 'Two hundred rooms, one broken lift and a VIP arriving at noon.', 'job', 0, null, 0),
  ('General Manager', 'Hospitality', 'Grand Meridian Hotels', 125000, 'executive', 60, 'The whole hotel answers to you. So do the reviews.', 'job', 0, null, 0),
  ('Retail Associate', 'Retail', 'MegaMart', 30000, 'entry', 0, 'Restock, upsell, repeat.', 'job', 0, null, 0),
  ('Assistant Store Manager', 'Retail', 'MegaMart', 40000, 'junior', 6, 'Open, close, count the till, cover every sick day.', 'job', 0, null, 0),
  ('Store Manager', 'Retail', 'MegaMart', 58000, 'mid', 18, 'Your store, your targets, your team of forty.', 'job', 0, null, 0),
  ('Regional Manager', 'Retail', 'MegaMart', 92000, 'senior', 36, 'Twelve stores, a company car and a lot of motorway.', 'job', 0, null, 0),
  ('Head of Retail Operations', 'Retail', 'MegaMart', 165000, 'executive', 60, 'Every store in the country, and the board on speed dial.', 'job', 0, null, 0),
  ('Delivery Driver', 'Logistics', 'ZoomDrop', 34000, 'entry', 0, 'Your van, their packages, and a route that changes daily.', 'job', 0, null, 0),
  ('Warehouse Team Lead', 'Logistics', 'ZoomDrop', 42000, 'junior', 6, 'Forklifts, scanners and keeping twelve people on schedule.', 'job', 0, null, 0),
  ('Logistics Coordinator', 'Logistics', 'Atlas Freight', 56000, 'mid', 18, 'Ships, trucks and spreadsheets. Something is always late.', 'job', 0, null, 0),
  ('Supply Chain Manager', 'Logistics', 'Atlas Freight', 90000, 'senior', 36, 'When a port closes on the other side of the world, you get the call.', 'job', 0, null, 0),
  ('VP of Supply Chain', 'Logistics', 'Atlas Freight', 170000, 'executive', 60, 'Everything that moves, everywhere, on time. In theory.', 'job', 0, null, 0),
  ('Customer Support Rep', 'Tech', 'HelpDesk Inc.', 38000, 'entry', 0, 'Have you tried turning it off and on again?', 'job', 0, null, 0),
  ('Junior Developer', 'Tech', 'ByteForge', 65000, 'junior', 6, 'Ship features, fix bugs, learn fast.', 'job', 0, null, 0),
  ('Software Engineer', 'Tech', 'ByteForge', 95000, 'mid', 18, 'You own a whole service now. And its pager.', 'job', 0, null, 0),
  ('Senior Software Engineer', 'Tech', 'CloudNine Systems', 135000, 'senior', 36, 'Architecture, mentoring, on-call.', 'job', 0, null, 0),
  ('Chief Technology Officer', 'Tech', 'CloudNine Systems', 230000, 'executive', 60, 'Every system, every engineer, every outage. Ultimately, you.', 'job', 0, null, 0),
  ('Bank Teller', 'Finance', 'First Harbour Bank', 32000, 'entry', 0, 'Deposits, withdrawals and smiling through the lunchtime queue.', 'job', 0, null, 0),
  ('Junior Accountant', 'Finance', 'Ledger & Co.', 52000, 'junior', 6, 'Spreadsheets with consequences.', 'job', 0, null, 0),
  ('Financial Analyst', 'Finance', 'Summit Capital', 75000, 'mid', 18, 'Models, forecasts and a manager who wants it "by end of day".', 'job', 0, null, 0),
  ('Investment Analyst', 'Finance', 'Summit Capital', 112000, 'senior', 36, 'Model the market before it models you.', 'job', 0, null, 0),
  ('Chief Financial Officer', 'Finance', 'Summit Capital', 220000, 'executive', 60, 'Every dollar in and out, and the auditors at your door.', 'job', 0, null, 0),
  ('Care Assistant', 'Healthcare', 'Sunrise Care Homes', 29000, 'entry', 0, 'Long shifts, small kindnesses, residents who become family.', 'job', 0, null, 0),
  ('Pharmacy Technician', 'Healthcare', 'City General', 40000, 'junior', 6, 'Counting pills precisely while the queue grows impatiently.', 'job', 0, null, 0),
  ('Registered Nurse', 'Healthcare', 'City General', 72000, 'mid', 18, 'Long shifts, real impact.', 'job', 0, null, 0),
  ('Nurse Manager', 'Healthcare', 'City General', 98000, 'senior', 36, 'A whole ward, its rota and its emergencies.', 'job', 0, null, 0),
  ('Hospital Director', 'Healthcare', 'City General', 195000, 'executive', 60, 'Budgets, boards and a building that never sleeps.', 'job', 0, null, 0),
  ('Social Media Assistant', 'Marketing', 'Hype Labs', 33000, 'entry', 0, 'Scheduling posts, replying to comments, chasing trends.', 'job', 0, null, 0),
  ('Marketing Coordinator', 'Marketing', 'Hype Labs', 45000, 'junior', 6, 'Campaigns, calendars and a lot of "quick tweaks".', 'job', 0, null, 0),
  ('Marketing Manager', 'Marketing', 'Hype Labs', 85000, 'mid', 18, 'Own the brand, own the budget.', 'job', 0, null, 0),
  ('Head of Brand', 'Marketing', 'Northstar Media', 122000, 'senior', 36, 'The logo, the voice and the billboard everyone talks about.', 'job', 0, null, 0),
  ('Chief Marketing Officer', 'Marketing', 'Northstar Media', 205000, 'executive', 60, 'Growth targets with your name on them.', 'job', 0, null, 0),
  ('Teaching Assistant', 'Education', 'Riverside Academy', 27000, 'entry', 0, 'Glue sticks, playground duty and the occasional breakthrough.', 'job', 0, null, 0),
  ('Teacher', 'Education', 'Riverside Academy', 46000, 'junior', 6, 'Thirty students, one plan, endless marking.', 'job', 0, null, 0),
  ('Head of Department', 'Education', 'Riverside Academy', 62000, 'mid', 18, 'Your subject, your team, your exam results.', 'job', 0, null, 0),
  ('Deputy Principal', 'Education', 'Riverside Academy', 82000, 'senior', 36, 'Timetables, discipline and parents at the gate.', 'job', 0, null, 0),
  ('School Principal', 'Education', 'Riverside Academy', 110000, 'executive', 60, 'The whole school, its budget and its reputation.', 'job', 0, null, 0),
  ('Construction Labourer', 'Construction', 'BuildRight', 31000, 'entry', 0, 'Early starts, heavy lifting and a very good lunch.', 'job', 0, null, 0),
  ('Apprentice Electrician', 'Construction', 'BuildRight', 38000, 'junior', 6, 'Learning which wire is which. Carefully.', 'job', 0, null, 0),
  ('Electrician', 'Construction', 'BuildRight', 64000, 'mid', 18, 'Licensed, in demand and always booked.', 'job', 0, null, 0),
  ('Site Manager', 'Construction', 'BuildRight', 92000, 'senior', 36, 'A whole building site, its safety and its deadline.', 'job', 0, null, 0),
  ('Construction Director', 'Construction', 'BuildRight', 165000, 'executive', 60, 'Towers, bridges and contracts worth millions.', 'job', 0, null, 0),
  ('Production Assistant', 'Creative', 'Lumen Studios', 29000, 'entry', 0, 'Coffee runs, call sheets and holding the reflector.', 'job', 0, null, 0),
  ('Graphic Designer', 'Creative', 'Lumen Studios', 44000, 'junior', 6, 'Logos, layouts and clients who want it "more pop".', 'job', 0, null, 0),
  ('UX Designer', 'Creative', 'Lumen Studios', 74000, 'mid', 18, 'Make apps people actually understand.', 'job', 0, null, 0),
  ('Creative Director', 'Creative', 'Lumen Studios', 118000, 'senior', 36, 'The big idea, the pitch and the final say.', 'job', 0, null, 0),
  ('Chief Creative Officer', 'Creative', 'Lumen Studios', 185000, 'executive', 60, 'The studio''s whole look and feel, and its biggest clients.', 'job', 0, null, 0),
  ('Administrative Clerk', 'Public Service', 'City Council', 30000, 'entry', 0, 'Forms, stamps and the queue that never ends.', 'job', 0, null, 0),
  ('Policy Officer', 'Public Service', 'City Council', 44000, 'junior', 6, 'Research, reports and meetings about meetings.', 'job', 0, null, 0),
  ('Programme Manager', 'Public Service', 'City Council', 62000, 'mid', 18, 'A public project, a budget and a lot of stakeholders.', 'job', 0, null, 0),
  ('Department Head', 'Public Service', 'City Council', 96000, 'senior', 36, 'Hundreds of staff and every decision on the evening news.', 'job', 0, null, 0),
  ('City Manager', 'Public Service', 'City Council', 155000, 'executive', 60, 'Runs the city day to day. The mayor gets the credit.', 'job', 0, null, 0),
  ('Plant Operator Trainee', 'Energy', 'Solaris Power', 36000, 'entry', 0, 'Dials, safety checks and night shifts at the plant.', 'job', 0, null, 0),
  ('Field Technician', 'Energy', 'Solaris Power', 48000, 'junior', 6, 'Solar farms, wind turbines and a very sturdy pair of boots.', 'job', 0, null, 0),
  ('Process Engineer', 'Energy', 'Solaris Power', 82000, 'mid', 18, 'Squeeze more power out of every panel and turbine.', 'job', 0, null, 0),
  ('Operations Manager', 'Energy', 'Solaris Power', 118000, 'senior', 36, 'Keep the lights on for a million homes.', 'job', 0, null, 0),
  ('Chief Executive Officer', 'Energy', 'Solaris Power', 260000, 'executive', 60, 'The whole company, its shareholders and its future.', 'job', 0, null, 0),
  ('Rideshare Driver', 'Gig economy', 'Rydr', 0, 'entry', 0, 'Evenings and weekends. Your car, their playlist.', 'gig', 140, 12, -2),
  ('Food Delivery Rider', 'Gig economy', 'ChowNow', 0, 'entry', 0, 'Rain or shine, the fries must arrive warm.', 'gig', 95, 10, -1),
  ('Weekend Bartender', 'Hospitality', 'The Tipsy Goat', 0, 'entry', 0, 'Friday and Saturday nights. Tips are where the money is.', 'gig', 120, 12, -2),
  ('Freelance Designer', 'Creative', 'Self-employed', 0, 'entry', 0, 'Logos, flyers and clients who want it "more pop".', 'gig', 160, 10, -1),
  ('Online Tutor', 'Education', 'BrightMinds', 0, 'entry', 0, 'Help kids with maths after work. Wholesome, mostly.', 'gig', 85, 6, 0),
  ('Event Photographer', 'Creative', 'Snapshot Events', 0, 'entry', 0, 'Weddings, birthdays, graduations. Smile!', 'gig', 150, 8, -1),
  ('Online Reseller', 'Retail', 'Self-employed', 0, 'entry', 0, 'Buy low at thrift shops and markets, sell high online.', 'gig', 70, 5, 1),
  ('Content Creator', 'Creative', 'Self-employed', 0, 'entry', 0, 'Post daily, pray to the algorithm. Small brand deals.', 'gig', 55, 6, 1),
  ('Babysitter', 'Care', 'Self-employed', 0, 'entry', 0, 'Friday nights with someone else''s kids, a fridge full of snacks and cartoons.', 'gig', 90, 8, -1),
  ('Dog Walker & Pet Sitter', 'Care', 'Self-employed', 0, 'entry', 0, 'Paid to hang out with dogs. Honestly the dream.', 'gig', 80, 7, 2),
  ('House Cleaner', 'Home services', 'Self-employed', 0, 'entry', 0, 'Other people''s kitchens, your playlist, cash at the end.', 'gig', 110, 10, -1),
  ('Handyman', 'Home services', 'Self-employed', 0, 'entry', 0, 'Shelves, leaky taps and flat-pack furniture nobody else can build.', 'gig', 150, 10, -1),
  ('Weekend Market Stall', 'Retail', 'Self-employed', 0, 'entry', 0, 'Food, crafts or second-hand clothes at the weekend market.', 'gig', 100, 9, 0),
  ('Translator', 'Language', 'Self-employed', 0, 'entry', 0, 'Documents and subtitles in your second language. Every bilingual friend''s side hustle.', 'gig', 120, 6, 0),
  ('Online Microtasks', 'Gig economy', 'TaskHive', 0, 'entry', 0, 'Tag photos and rate search results. Mind-numbing, but it adds up.', 'gig', 45, 5, -1),
  ('Wedding DJ / MC', 'Events', 'Self-employed', 0, 'entry', 0, 'One microphone, two hundred guests and the cha-cha slide.', 'gig', 170, 8, -1),
  ('Personal Trainer', 'Fitness', 'Self-employed', 0, 'entry', 0, 'Early-morning clients and a lot of "one more rep".', 'gig', 130, 8, 2),
  ('Social Media Manager', 'Marketing', 'Self-employed', 0, 'entry', 0, 'Run the accounts of three small businesses that "just need more followers".', 'gig', 140, 8, -1),
  ('Music Teacher', 'Education', 'Self-employed', 0, 'entry', 0, 'Guitar, piano or voice lessons in the evenings. Occasionally, a natural.', 'gig', 100, 6, 1),
  ('Tour Guide', 'Tourism', 'CityWalks', 0, 'entry', 0, 'Weekend walking tours. You know which stories to exaggerate.', 'gig', 110, 8, 1),
  ('Mobile Hairdresser', 'Beauty', 'Self-employed', 0, 'entry', 0, 'Braids, cuts and colour in clients'' homes. Booked out before holidays.', 'gig', 130, 8, 0),
  ('Moving Helper', 'Gig economy', 'LiftLoad', 0, 'entry', 0, 'Sofas, stairs and boxes labelled "misc". Your back will remember.', 'gig', 120, 8, -2)
on conflict (title, company) do update set
  industry = excluded.industry, salary = excluded.salary, level = excluded.level,
  experience_months = excluded.experience_months, description = excluded.description, kind = excluded.kind,
  weekly_pay = excluded.weekly_pay, hours_per_week = excluded.hours_per_week, sanity_per_week = excluded.sanity_per_week;


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

-- More things to show off: cars, motorbikes, boats and aircraft (each player's showcase).
insert into public.liability_items (name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear) values
  ('Superbike',           'vehicle',  22000,  160,  'Zero to "please slow down" in three seconds. Your mum has opinions.', 0.15,
     '[{"label":"Fuel","monthly":60},{"label":"Insurance","monthly":85},{"label":"Parking","monthly":15}]', 400, 6, 0, null, 0),
  ('Adventure Motorbike', 'vehicle',  14000,  120,  'Built for dirt roads and road trips. Tour companies rent them by the week.', 0.13,
     '[{"label":"Fuel","monthly":50},{"label":"Insurance","monthly":55},{"label":"Parking","monthly":15}]', 300, 6, 650, 'Rent it to a motorbike tour company', 0.12),
  ('Cruiser Motorbike',   'vehicle',  32000,  210,  'Chrome, leather and a rumble the whole street hears. Mostly ridden on Sundays.', 0.10,
     '[{"label":"Fuel","monthly":70},{"label":"Insurance","monthly":110},{"label":"Garage","monthly":30}]', 500, 12, 0, null, 0),
  ('Classic Convertible', 'vehicle',  48000,  420,  'Older than you and in better shape. Classics hold their value; wedding hires pay well.', 0.00,
     '[{"label":"Fuel","monthly":150},{"label":"Classic insurance","monthly":120},{"label":"Garage","monthly":150}]', 600, 12, 1500, 'Hire it out for weddings', 0.05),
  ('Electric Saloon',     'vehicle',  55000,  270,  'Silent, fast and smug. Charging is cheap; insurance is not.', 0.16,
     '[{"label":"Charging","monthly":90},{"label":"Insurance","monthly":160},{"label":"Parking","monthly":20}]', 300, 12, 1300, 'Rent it to a ride-hail driver', 0.10),
  ('Sports Coupe',        'vehicle',  140000, 1100, 'Two doors, no back seat, every head turns. Shoots and weddings pay to borrow it.', 0.14,
     '[{"label":"Fuel","monthly":350},{"label":"Insurance","monthly":650},{"label":"Parking","monthly":100}]', 2500, 6, 3800, 'Rent it for weddings and shoots', 0.08),
  ('Supercar',            'vehicle',  380000, 2600, 'Scissor doors and a fuel tank that empties when you look at it.', 0.10,
     '[{"label":"Fuel","monthly":600},{"label":"Insurance","monthly":1800},{"label":"Garage","monthly":200}]', 8000, 6, 9500, 'Rent it for music videos', 0.06),
  ('Jet Ski',             'boat',     16000,  230,  'The fun part of boating without the crew. Beach rentals pay for the fuel.', 0.14,
     '[{"label":"Fuel","monthly":80},{"label":"Insurance","monthly":70},{"label":"Storage","monthly":80}]', 500, 6, 900, 'Rent it out at the beach', 0.12),
  ('Sailing Catamaran',   'boat',     420000, 5200, 'Two hulls, sunset cruises, and a skipper who calls you "captain" ironically.', 0.08,
     '[{"label":"Insurance","monthly":1200},{"label":"Marina berth","monthly":1800},{"label":"Skipper","monthly":2200}]', 9000, 12, 14000, 'Charter it for island trips', 0.05),
  ('Light Aircraft',      'aircraft', 320000, 3400, 'A four-seater propeller plane. Flight schools are always short of planes.', 0.06,
     '[{"label":"Fuel","monthly":900},{"label":"Insurance","monthly":1100},{"label":"Hangar","monthly":600},{"label":"Maintenance reserve","monthly":800}]', 7000, 6, 9000, 'Rent it to a flight school', 0.06)
on conflict (name) do update set
  category = excluded.category, base_price = excluded.base_price, monthly_cost = excluded.monthly_cost,
  description = excluded.description, depreciation_rate = excluded.depreciation_rate, costs = excluded.costs,
  service_cost = excluded.service_cost, service_every_months = excluded.service_every_months,
  lease_income = excluded.lease_income, lease_label = excluded.lease_label, lease_wear = excluded.lease_wear;

-- --- Bank loans: high rates (13-24% a year), much bigger amounts ------------------------------
-- interest_rate is a FRACTION per year; payments are amortised.
insert into public.bank_loans (borrower_id, type, amount, interest_rate, term, monthly_payment, total_interest, credit_required, status, collateral) values
  (null, 'Quick Cash',         1000.00,   0.2400, 3,   346.75,  40.26,     550, 'available', 'none'),
  (null, 'Emergency Fund',     2000.00,   0.2200, 6,   355.05,  130.28,    580, 'available', 'none'),
  (null, 'Personal Loan',      10000.00,  0.1800, 24,  499.24,  1981.78,   600, 'available', 'none'),
  (null, 'Education Loan',     15000.00,  0.1400, 36,  512.66,  3455.92,   640, 'available', 'none'),
  (null, 'Debt Consolidation', 20000.00,  0.1700, 36,  713.05,  5669.96,   650, 'available', 'none'),
  (null, 'Car Loan',           30000.00,  0.1600, 48,  850.21,  10810.00,  660, 'available', 'vehicle'),
  (null, 'Business Starter',   75000.00,  0.1700, 60,  1863.94, 36836.59,  690, 'available', 'business_assets')
on conflict (type) where borrower_id is null do update set
  amount = excluded.amount, interest_rate = excluded.interest_rate, term = excluded.term,
  monthly_payment = excluded.monthly_payment, total_interest = excluded.total_interest,
  credit_required = excluded.credit_required, collateral = excluded.collateral;
-- Mortgages come with buying a home (homes.py), not from this list.
delete from public.bank_loans where type = 'Mortgage' and borrower_id is null;

-- ===== Lifestyle categories (migration 20261213000000) =====
update public.liability_items set category = 'motorbikes' where category = 'vehicle' and name ~* '(bike|motorcycle|scooter)';
update public.liability_items set category = 'cars' where category = 'vehicle';
update public.liability_items set category = 'boats' where category = 'boat';
update public.liability_items set category = 'accessories' where category = 'fashion';
update public.liability_items set category = 'gadgets' where category = 'tech';

-- Wellness: drop saved showroom deals and wishlist entries for it, then the item itself.
delete from public.showroom_deals d using public.liability_items l
 where d.kind = 'item' and d.item_id::text = l.id::text and l.category = 'wellness';
delete from public.showroom_wishlist w using public.liability_items l
 where w.kind = 'item' and w.item_id::text = l.id::text and l.category = 'wellness';
delete from public.showroom_seen s using public.liability_items l
 where s.kind = 'item' and s.item_id::text = l.id::text and l.category = 'wellness';
delete from public.liability_items l
 where l.category = 'wellness' and not exists (select 1 from public.player_liabilities p where p.liability_id = l.id);

-- Luxury: 42 rows (existing names are skipped)
insert into public.liability_items (name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear, image_url, image_credit)
select v.name, v.category, v.base_price::numeric, v.monthly_cost::numeric, v.description, v.depreciation_rate::numeric, v.costs::jsonb, v.service_cost::numeric, v.service_every_months::int, v.lease_income::numeric, v.lease_label, v.lease_wear::numeric, v.image_url, v.image_credit
from (values
  ('Gold Hoop Earrings', 'accessories', 320, 5, 'Small hoops with big opinions.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Silk Scarf', 'accessories', 380, 5, 'Wear it as a scarf, a headband or a personality.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Designer Sunglasses', 'accessories', 420, 5, 'Instantly 40% more mysterious.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Limited Edition Sneakers', 'accessories', 450, 5, 'You will walk around puddles like they are lava.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Leather Wallet', 'accessories', 480, 5, 'A beautiful home for very little money.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Statement Jacket', 'accessories', 950, 10, 'People will ask where you got it. You will enjoy this far too much.', 0.35, '[{"label": "Cleaning", "monthly": 10}]', 50, 12, 0, null, 0, null, null),
  ('Leather Boots', 'accessories', 680, 5, 'Break them in for a month. Then they love you forever.', 0.35, '[{"label": "Cleaning", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Tailored Suit', 'accessories', 1400, 15, 'You look like you have a plan. You do not need a plan in this suit.', 0.35, '[{"label": "Cleaning", "monthly": 15}]', 70, 12, 0, null, 0, null, null),
  ('Evening Gown', 'accessories', 1800, 20, 'For galas, weddings and dramatic exits.', 0.35, '[{"label": "Cleaning", "monthly": 20}]', 90, 12, 0, null, 0, null, null),
  ('Cashmere Overcoat', 'accessories', 2200, 25, 'So soft strangers want to touch it. Please do not let them.', 0.35, '[{"label": "Cleaning", "monthly": 25}]', 110, 12, 0, null, 0, null, null),
  ('Weekend Leather Duffel', 'accessories', 1100, 5, 'Packed for a getaway you have not booked.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Everyday Designer Tote', 'accessories', 1900, 5, 'Holds your whole life and three old receipts.', 0.1, '[{"label": "Care & cleaning", "monthly": 5}]', 55, 12, 0, null, 0, null, null),
  ('Silver Signet Ring', 'accessories', 650, 5, 'Instant old money. The money is not included.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Pearl Necklace', 'accessories', 1600, 5, 'Your grandma will approve. Loudly.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 30, 24, 0, null, 0, null, null),
  ('Gold Chain', 'accessories', 3200, 5, 'Heavy enough to count as a workout.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 65, 24, 0, null, 0, null, null),
  ('Diamond Stud Earrings', 'accessories', 4800, 5, 'Tiny, sparkly and not tiny in price.', 0.05, '[{"label": "Insurance", "monthly": 5}]', 95, 24, 0, null, 0, null, null),
  ('Diamond Tennis Bracelet', 'accessories', 9500, 15, 'You will wave at people for no reason.', 0.05, '[{"label": "Insurance", "monthly": 15}]', 190, 24, 0, null, 0, null, null),
  ('Automatic Dress Watch', 'accessories', 2800, 5, 'Tells the time and also that you made it.', 0.0, '[{"label": "Insurance", "monthly": 5}]', 85, 36, 0, null, 0, null, null),
  ('Dive Watch', 'accessories', 8500, 10, 'Waterproof to depths you will never visit.', 0.0, '[{"label": "Insurance", "monthly": 10}]', 255, 36, 0, null, 0, null, null),
  ('Gold Chronograph Watch', 'accessories', 24000, 35, 'Three little dials. You use none of them.', 0.0, '[{"label": "Insurance", "monthly": 35}]', 720, 36, 0, null, 0, null, null),
  ('Skeleton Tourbillon Watch', 'accessories', 85000, 125, 'You can see every gear spending your money.', 0.0, '[{"label": "Insurance", "monthly": 125}]', 2550, 36, 0, null, 0, null, null),
  ('Wireless Earbuds', 'gadgets', 220, 5, 'Lose one within a month. It is tradition.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Smart Ring', 'gadgets', 350, 5, 'Tracks your sleep and silently judges it.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Mechanical Keyboard', 'gadgets', 260, 5, 'Loud enough that coworkers know you are working.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Noise-cancelling Headphones', 'gadgets', 420, 5, 'Cancels noise, small talk and your flatmate.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Portable Speaker', 'gadgets', 280, 5, 'Every park is now your personal party.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Smartwatch', 'gadgets', 480, 5, 'Tells you to stand up. Frequently.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Handheld Gaming Console', 'gadgets', 550, 5, 'Just one more level. It is 3am.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('E-reader', 'gadgets', 200, 5, 'Carries a thousand books you intend to read.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Home Games Console', 'gadgets', 600, 5, 'Ruins sleep schedules since the first level.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 30, 12, 0, null, 0, null, null),
  ('Drawing Tablet', 'gadgets', 900, 5, 'Draw masterpieces. Mostly draw cats.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 35, 12, 40, 'Rent it out for shoots', 0.08, null, null),
  ('Camera Drone', 'gadgets', 1300, 5, 'Cinematic shots of your own roof.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 50, 12, 60, 'Rent it out for shoots', 0.08, null, null),
  ('Mirrorless Camera', 'gadgets', 2100, 10, 'Makes even your lunch look expensive.', 0.2, '[{"label": "Insurance", "monthly": 10}]', 85, 12, 90, 'Rent it out for shoots', 0.08, null, null),
  ('Studio Podcast Kit', 'gadgets', 1100, 5, 'Your hot takes, now in high definition.', 0.2, '[{"label": "Insurance", "monthly": 5}]', 45, 12, 45, 'Rent it out for shoots', 0.08, null, null),
  ('Cinema Camera', 'gadgets', 8500, 35, 'For when your phone is just not serious enough.', 0.2, '[{"label": "Insurance", "monthly": 35}]', 340, 12, 385, 'Rent it out for shoots', 0.08, null, null),
  ('Foldable Smartphone', 'gadgets', 1800, 60, 'A phone that becomes a slightly bigger phone.', 0.3, '[{"label": "Phone plan", "monthly": 45}, {"label": "Insurance", "monthly": 15}]', 215, 12, 0, null, 0, null, null),
  ('Flagship Smartphone Pro', 'gadgets', 1500, 45, 'Three cameras, so every blurry photo is blurry from three angles.', 0.3, '[{"label": "Phone plan", "monthly": 35}, {"label": "Insurance", "monthly": 10}]', 180, 12, 0, null, 0, null, null),
  ('Ultrabook Laptop', 'gadgets', 1700, 15, 'Thin, fast and perfect for looking busy in cafes.', 0.25, '[{"label": "Subscriptions", "monthly": 15}]', 85, 12, 0, null, 0, null, null),
  ('Gaming PC', 'gadgets', 2800, 25, 'Glows in six colours. Runs everything. Heats the room.', 0.25, '[{"label": "Subscriptions", "monthly": 25}]', 140, 12, 0, null, 0, null, null),
  ('Giant OLED Television', 'gadgets', 3200, 25, 'So big your neighbours can watch too.', 0.25, '[{"label": "Subscriptions", "monthly": 25}]', 160, 12, 0, null, 0, null, null),
  ('VR Headset', 'gadgets', 700, 5, 'Punch walls in a whole new world.', 0.25, '[{"label": "Subscriptions", "monthly": 5}]', 35, 12, 0, null, 0, null, null),
  ('Home Cinema System', 'gadgets', 6500, 55, 'Surround sound so good the pizza feels nervous.', 0.25, '[{"label": "Subscriptions", "monthly": 55}]', 325, 12, 0, null, 0, null, null)
) as v(name, category, base_price, monthly_cost, description, depreciation_rate, costs, service_cost, service_every_months, lease_income, lease_label, lease_wear, image_url, image_credit)
on conflict (name) do nothing;

