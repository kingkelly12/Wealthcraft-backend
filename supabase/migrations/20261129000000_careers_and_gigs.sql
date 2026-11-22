-- =============================================================================
-- Careers are ladders, and gigs anyone anywhere would recognise
-- =============================================================================
-- * 12 industries, each with five rungs: entry -> junior -> mid -> senior ->
--   executive (salaries $27k-$260k). Higher rungs need experience in the same
--   industry (6 / 18 / 36 / 60 months); experience elsewhere counts for a third.
--   Rules: app/game/careers.py. Before, experience_months was stored but never
--   checked, so a new player could start as a $130k senior engineer.
-- * jobs.months_worked: a month of experience per payday on a main job.
--   jobs.industry: kept on the job so experience survives listing changes.
-- * 22 gigs, from babysitting and dog walking to DJing weddings and translating.
-- Players who already hold a job keep it. Safe to re-run.
-- =============================================================================

begin;

alter table public.jobs add column if not exists months_worked integer not null default 0;
alter table public.jobs add column if not exists industry text;

-- Existing jobs: industry from the listing, experience from time in the job.
update public.jobs j set industry = m.industry
  from public.job_market m where j.job_market_id = m.id and j.industry is null;
update public.jobs set months_worked = greatest(0, (extract(year from age(coalesce(end_date, now()), start_date)) * 12
                                                   + extract(month from age(coalesce(end_date, now()), start_date)))::int)
  where months_worked = 0 and coalesce(kind, 'job') <> 'gig';

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

commit;
