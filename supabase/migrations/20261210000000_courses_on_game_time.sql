-- =============================================================================
-- Courses on game time, matched to the job market (app/game/courses.py)
-- =============================================================================
-- 48 career courses: 4 per industry, each leading to the next job on that ladder
--   (target_job). They take game weeks, count as experience in the industry, and pay a
--   bonus on paydays while your main job is in it (capped at 20%).
-- 22 side-hustle courses: one per gig (target_gig), raising its weekly pay (capped at 50%).
-- 4 money-skills courses (Finance): small experience credit, no bonus.
-- The old flat salary boost is retired (salary_boost = 0). Safe to run more than once.
-- =============================================================================
begin;

alter table public.courses add column if not exists industry text;
alter table public.courses add column if not exists tier text not null default 'certificate';
alter table public.courses add column if not exists emoji text;
alter table public.courses add column if not exists weeks integer not null default 4;
alter table public.courses add column if not exists experience_months integer not null default 0;
alter table public.courses add column if not exists pay_bonus_pct numeric not null default 0;
alter table public.courses add column if not exists min_months integer not null default 0;
alter table public.courses add column if not exists target_job text;
alter table public.courses add column if not exists target_gig text;
alter table public.courses add column if not exists gig_bonus_pct numeric not null default 0;
alter table public.user_courses add column if not exists started_week integer;

-- Renamed: no trademarked exam names.
update public.courses set title = 'Investment Analyst Prep' where title = 'CFA Level I Prep'
  and not exists (select 1 from public.courses c where c.title = 'Investment Analyst Prep');

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
on conflict (title) do update set salary_boost = 0, description = excluded.description, category = excluded.category, difficulty = excluded.difficulty, duration_hours = excluded.duration_hours, cost = excluded.cost, industry = excluded.industry, tier = excluded.tier, emoji = excluded.emoji, weeks = excluded.weeks, experience_months = excluded.experience_months, pay_bonus_pct = excluded.pay_bonus_pct, min_months = excluded.min_months, target_job = excluded.target_job, target_gig = excluded.target_gig, gig_bonus_pct = excluded.gig_bonus_pct;

commit;

-- Check: every course should point at a real job or gig (no rows here):
--   select title, target_job, target_gig from public.courses c
--   where (target_job is not null and not exists (select 1 from public.job_market j where j.title = c.target_job and coalesce(j.kind, 'job') = 'job'))
--      or (target_gig is not null and not exists (select 1 from public.job_market j where j.title = c.target_gig and j.kind = 'gig'));
