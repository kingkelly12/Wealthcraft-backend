-- =============================================================================
-- Businesses for every budget, and 60 more life events
-- =============================================================================
-- * 15 businesses from $1.5k (a mobile money kiosk) to $480k (a boutique hotel),
--   so a player can start small, or borrow from a bank or a friend to buy one.
--   Profit swings month to month by risk level (app/game/economy.py).
-- * 10 more cars, motorbikes, boats and aircraft to buy and show off on your profile.
-- * 60 life events: everyday adult chaos, written to be funny.
-- Safe to re-run: businesses and items upsert by name; events are skipped by title.
-- =============================================================================

begin;

insert into public.assets (name, category, price, monthly_income, description, risk_level, roi, time_to_return, availability, total_supply) values
  ('Mobile Money Kiosk', 'business', 1500.00, 55.00, 'A tiny booth, a cash float and a phone. You earn a commission on every deposit and withdrawal.', 'high', 44.0, '2-3 years', 2000, 2000),
  ('Online Thrift Store', 'business', 2000.00, 75.00, 'Second-hand finds, good lighting, nationwide delivery. Depends entirely on the algorithm''s mood.', 'very_high', 45.0, '2 years', 2000, 2000),
  ('Vending Machine', 'business', 2800.00, 85.00, 'Sells sodas and crisps while you sleep. Occasionally eats somebody''s coins.', 'medium', 36.4, '3 years', 1500, 1500),
  ('Poultry Farm', 'business', 5000.00, 160.00, '500 chickens, one caretaker and a lot of eggs. One feed-price hike away from chaos.', 'high', 38.4, '2-3 years', 800, 800),
  ('Car Wash', 'business', 7500.00, 230.00, 'Hoses, sponges and a playlist. Rainy weeks are slow; dusty weeks are gold.', 'medium', 36.8, '3 years', 600, 600),
  ('Cyber Café & Printing', 'business', 9000.00, 220.00, 'Printing, scanning, passport photos and helping people find the "any key".', 'medium', 29.3, '3-4 years', 600, 600),
  ('Barbershop', 'business', 12000.00, 340.00, 'Three chairs, one TV playing football, endless opinions. Regulars pay the bills.', 'medium', 34.0, '3 years', 500, 500),
  ('Beauty Salon', 'business', 18000.00, 480.00, 'Braids, nails and gossip. Booked solid before holidays and weddings.', 'medium', 32.0, '3 years', 400, 400),
  ('Coffee Kiosk', 'business', 22000.00, 520.00, 'Good coffee near a busy office block. Lives and dies by the morning rush.', 'high', 28.4, '3-4 years', 400, 400),
  ('Mini Mart', 'business', 35000.00, 750.00, 'Bread, milk, airtime and everything else people forget. Boring, steady, open late.', 'low', 25.7, '4 years', 300, 300),
  ('Gym', 'business', 85000.00, 1600.00, 'Full in January, quiet by March. Memberships keep paying either way.', 'medium', 22.6, '4-5 years', 150, 150),
  ('Co-working Space', 'business', 150000.00, 2600.00, 'Desks, Wi-Fi and free coffee for freelancers who can''t work from home.', 'medium', 20.8, '5 years', 100, 100),
  ('Event Venue', 'business', 220000.00, 3700.00, 'Weddings, birthdays and corporate end-year parties. Wedding season is a gold rush.', 'high', 20.2, '5 years', 80, 80),
  ('Franchise Restaurant', 'business', 300000.00, 4800.00, 'A known brand with a proven menu. The franchise fee is steep; customers already trust it.', 'low', 19.2, '5-6 years', 60, 60),
  ('Boutique Hotel', 'business', 480000.00, 7400.00, 'Twelve rooms, a rooftop bar and reviews that make or break your month.', 'medium', 18.5, '6 years', 40, 40)
on conflict (name) do update set
  price = excluded.price, monthly_income = excluded.monthly_income, description = excluded.description,
  risk_level = excluded.risk_level, roi = excluded.roi, time_to_return = excluded.time_to_return;

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

-- 61. "Quick call?"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Quick call?"', 'Friday, 4:52pm. Your manager sends "got a sec for a quick call?" with no context.', 'challenge', 0, 0, 0, 0, 'Phone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Quick call?"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Join right away', 'It was about the font on one slide. Your heart rate was not about the font.', 0, 0, 1, -5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, '"Sorry, driving!"', 'You were on your couch. They fixed the font themselves. You never find out what it was about.', 0, 0, 2, 3, 0 FROM e;

-- 62. Reply-All Apocalypse
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Reply-All Apocalypse', 'Someone in HR hits Reply All to the whole company asking for a banana bread recipe. 400 people reply "please remove me".', 'neutral', 0, 0, 0, 0, 'Mail', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Reply-All Apocalypse')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Reply "please remove me"', 'You become part of the problem. IT sends a sternly worded email to everyone.', 0, 0, 1, -2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Grab popcorn', 'You watch 400 adults lose their minds in real time. Best Tuesday in months.', 0, 0, 2, 5, 0 FROM e;

-- 63. Secret Santa
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Secret Santa', 'Office Secret Santa: the limit is $20. You drew the CEO.', 'challenge', 0, 0, 0, 0, 'Gift', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Secret Santa')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Spend the $20', 'A mug that says "World''s Okayest Boss". They laugh. Nervously. So does HR.', 20, 0, 1, -2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Regift last year''s candle', 'The CEO opens it. Your old name tag is still stuck to the bottom. Iconic.', 0, 0, 2, -4, 0 FROM e;

-- 64. The Humblebrag
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Humblebrag', 'An old classmate posts: "Humbled and honoured to announce I''m now Chief Vision Officer" at a startup with two employees.', 'neutral', 0, 0, 0, 0, 'Briefcase', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Humblebrag')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Comment "Congrats!"', 'They reply "Let''s grab coffee!" You both know it will never happen.', 0, 0, 1, 1, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Update your own profile', 'You add "Excel wizard" to your skills. A recruiter messages you. It''s a pyramid scheme.', 0, 0, 2, -2, 0 FROM e;

-- 65. Headhunted
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Headhunted', 'A recruiter says a rival company wants you for weekend contract work. The interview is at 10am on a workday.', 'opportunity', 0, 0, 0, 0, 'TrendingUp', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Headhunted')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Fake a dentist appointment', 'You nail it. They offer a weekend contract worth $150 a month. Your "dentist" was very generous.', 0, 0, 1, -3, 150 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Stay loyal', 'Your manager never finds out you were loyal. Loyalty is free, and also unpaid.', 0, 0, 2, 1, 0 FROM e;

-- 66. Team-Building Weekend
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Team-Building Weekend', 'Mandatory team-building weekend. There will be trust falls. There will be a man called Kevin with a guitar.', 'neutral', 0, 0, 0, 0, 'Tent', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Team-Building Weekend')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Commit fully', 'You win the egg-and-spoon race. Kevin plays the same song twice. Your team trusts you now, sort of.', 0, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Develop a sudden cough', 'A peaceful weekend at home. Monday''s group photo has a suspicious gap where you should be.', 0, 0, 2, -1, 0 FROM e;

-- 67. The Office Fridge
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Office Fridge', 'Something in the office fridge has developed a personality. It''s in your container.', 'emergency', 0, 0, 0, 0, 'AlertTriangle', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Office Fridge')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Bin the container', 'Goodbye, $25 lunchbox. You couldn''t save it. Nobody could have.', 25, 0, 1, 2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Deny it''s yours', 'You watch facilities carry it out in a sealed bag. You''ll take this secret to your grave.', 0, 0, 2, -3, 0 FROM e;

-- 68. Paid Twice
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Paid Twice', 'Payroll accidentally paid you twice this month. HR hasn''t noticed. Yet.', 'opportunity', 0, 0, 0, 0, 'Wallet', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Paid Twice')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Report it', 'HR thanks you and takes it back the next day. Honesty: priceless. Literally, it pays nothing.', 0, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Say nothing', 'Three weeks later HR claws it back plus a $60 "processing fee", in an email cc''d to your boss.', 60, 0, 2, -8, 0 FROM e;

-- 69. Work Bestie Is Leaving
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Work Bestie Is Leaving', 'Your work bestie got a new job. The farewell cake collection is $15, and you have to write something original in the card.', 'challenge', 0, 0, 0, 0, 'Users', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Work Bestie Is Leaving')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Chip in and write from the heart', 'You write "Don''t forget us little people 😭". They cry at the party. So do you, in the bathroom.', 15, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Sign "Best wishes!"', 'You''re the fourth "Best wishes!" in the card. They notice. They notice everything.', 0, 0, 2, -2, 0 FROM e;

-- 70. Promotion, No Raise
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Promotion, No Raise', 'Your boss offers a "promotion": a new title, double the work, same pay. "It''s great exposure!"', 'challenge', 0, 0, 0, 0, 'Award', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Promotion, No Raise')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Accept the exposure', 'You''re now "Senior Associate Lead". Your landlord does not accept exposure.', 0, 0, 1, -6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Ask for money', 'Awkward silence. Then: "+$120 a month, deal?" Turns out asking works.', 0, 0, 2, -2, 120 FROM e;

-- 71. Wrong Group Chat
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Wrong Group Chat', 'You just sent a meme roasting your manager to the team group chat. Your manager is typing...', 'emergency', 0, 0, 0, 0, 'MessageCircle', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Wrong Group Chat')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Delete for everyone', '"This message was deleted." Somehow worse. Everyone saw it. Your manager sends 🙂.', 0, 0, 1, -6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, '"That one''s for you boss 😂"', 'Your manager loves it and makes it the group icon. You are untouchable.', 0, 0, 2, 6, 0 FROM e;

-- 72. Free Pizza (Terms Apply)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Free Pizza (Terms Apply)', 'There''s free pizza in the meeting room after a 90-minute session on "Synergy in the Workplace".', 'opportunity', 0, 0, 0, 0, 'Pizza', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Free Pizza (Terms Apply)')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Sit through the synergy', 'Cold pizza, but you take four slices home. Dinner sorted for two days.', 0, 20, 1, -2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Skip it', 'Everyone says the pizza was actually great. The regret is warmer than the pizza.', 0, 0, 2, -1, 0 FROM e;

-- 73. Your Turn for the Pot
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Your Turn for the Pot', 'It''s finally your turn to collect from the savings group you''ve paid into all year.', 'opportunity', 0, 0, 0, 0, 'PiggyBank', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Your Turn for the Pot')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Take the pot', 'A year of discipline pays out at once. Then the group reminds you next month''s contribution is due.', 0, 800, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Let a friend go first', 'Your friend''s rent is sorted. You''re the group''s favourite now. Your turn comes later.', 0, 0, 2, 5, 0 FROM e;

-- 74. Sent to the Wrong Number
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Sent to the Wrong Number', 'You sent $150 by mobile money to the wrong number. One digit off. The stranger isn''t replying.', 'emergency', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Sent to the Wrong Number')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Call the provider', 'Three calls, two forms and one near-tears moment later, you get it back minus a $10 fee.', 10, 0, 1, -4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Text them "God sees you"', 'Plot twist: they''re honest. The money comes back with a "sorry 🙏🏾".', 0, 0, 2, 3, 0 FROM e;

-- 75. Crypto Bro at Dinner
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Crypto Bro at Dinner', 'Your friend''s new partner explains blockchain for 45 minutes, then offers you "early access" to his coin for $300.', 'challenge', 0, 0, 0, 0, 'Bitcoin', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Crypto Bro at Dinner')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Get in early', 'The coin is called $VIBES. Your stake is now worth $11. He has moved on to selling courses.', 289, 0, 1, -6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Ask what problem it solves', 'He doesn''t know. Long silence. Your friend mouths "thank you" across the table.', 0, 0, 2, 4, 0 FROM e;

-- 76. "You Have an iPhone, Right?"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"You Have an iPhone, Right?"', 'A friend''s cousin needs a photographer for a baby shower. Their entire vetting process was that question.', 'opportunity', 0, 0, 0, 0, 'Camera', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"You Have an iPhone, Right?"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Take the gig', 'You take 600 photos and four are in focus. They pay $180 and call you "the photographer".', 0, 180, 1, -3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Recommend a real one', 'The cousin is less impressed, but the baby shower is spared. You keep your Saturday.', 0, 0, 2, 2, 0 FROM e;

-- 77. "Hey Stranger!! 😊"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Hey Stranger!! 😊"', 'An old friend messages after four years of silence. You know exactly where this is going.', 'challenge', 0, 0, 0, 0, 'Phone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Hey Stranger!! 😊"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Hear them out', 'Supplements. You buy a $60 starter pack to be nice. It tastes like regret.', 60, 0, 1, -5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, '"Not interested in any business 🙏"', '"Wow ok I just wanted to catch up." They did not just want to catch up.', 0, 0, 2, 2, 0 FROM e;

-- 78. Tax Refund
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Tax Refund', 'The tax office says you overpaid last year and are owed $340. The letter is suspiciously polite.', 'opportunity', 0, 0, 0, 0, 'Receipt', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Tax Refund')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Claim it properly', 'Six weeks and an hour on hold later, $340 lands. You feel like a real adult.', 0, 340, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Ignore it, it''s a scam', 'It wasn''t a scam. You find the letter in a drawer two years later.', 0, 0, 2, -3, 0 FROM e;

-- 79. Black Friday
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Black Friday', 'Everything is 70% off. You suddenly "need" an air fryer, a ring light and a massage gun.', 'challenge', 0, 0, 0, 0, 'ShoppingBag', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Black Friday')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Checkout', '$240 later you own three things you''ll use twice. The air fryer is genuinely life-changing though.', 240, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Close the app', 'You save $240. You also refresh the sale page eleven more times out of spite.', 0, 0, 2, -2, 0 FROM e;

-- 80. The Cousin Who Owes You
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Cousin Who Owes You', 'The cousin you lent $200 last year just posted beach holiday photos.', 'neutral', 0, 0, 0, 0, 'Wallet', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Cousin Who Owes You')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Comment "nice! 🙂 btw..."', 'They pay back $120 and blame "the economy" for the rest. Progress.', 0, 120, 1, 2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Let it go', 'You let it go. At the next family lunch, your aunt says he "struggles". Okay.', 0, 0, 2, -2, 0 FROM e;

-- 81. Old Jacket Money
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Old Jacket Money', 'Cleaning out an old jacket, you find an envelope with $75 from a birthday you forgot about.', 'opportunity', 0, 0, 0, 0, 'Mail', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Old Jacket Money')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Brunch on past you', 'Half goes on brunch. Smugness lasts all week.', 0, 35, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Straight to savings', 'Sensible. Somewhere in the future, an older you nods approvingly.', 0, 75, 2, 2, 0 FROM e;

-- 82. A "Loyalty Reward"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'A "Loyalty Reward"', 'Your phone provider calls to "reward your loyalty" with an upgrade. It costs $35 more a month.', 'challenge', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'A "Loyalty Reward"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Upgrade', 'New phone, same scrolling. Your bill is permanently heavier.', 0, 0, 1, 4, -35 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Ask about cheaper plans', 'There''s a plan $15 a month cheaper that they "forgot" to mention.', 0, 0, 2, 3, 15 FROM e;

-- 83. Made in Itlay
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Made in Itlay', 'A guy at the market swears this $50 designer bag is genuine. The label says "Made in Itlay".', 'neutral', 0, 0, 0, 0, 'ShoppingBag', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Made in Itlay')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy it for the plot', 'Your friends call it "the Itlay" with love. Best $50 you ever wasted.', 50, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Walk away', 'He drops it to $15 as you leave. You keep walking. Discipline.', 0, 0, 2, 1, 0 FROM e;

-- 84. Lights Out Mid-Dinner
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Lights Out Mid-Dinner', 'Your prepaid electricity runs out halfway through cooking. The rice is half-cooked. So are you.', 'emergency', 0, 0, 0, 0, 'Zap', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Lights Out Mid-Dinner')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy tokens now', 'Lights back on, rice saved. You vow to top up before it runs out next time. You won''t.', 20, 0, 1, 2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Candlelit dinner', 'Crunchy rice by candlelight. You tell everyone it was "aesthetic".', 0, 0, 2, -3, 0 FROM e;

-- 85. Wedding Season
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Wedding Season', 'Three weddings in one month. Each has a dress code, a gift registry and a "contribution".', 'challenge', 0, 0, 0, 0, 'Heart', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Wedding Season')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Go to all three', 'You dance at all three and eat at all three. Your wallet attends a funeral: its own.', 280, 0, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Send voice-note blessings', 'Heartfelt, free and a little awkward when you see them at Christmas.', 0, 0, 2, -3, 0 FROM e;

-- 86. "Somewhere Chill"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Somewhere Chill"', 'Your date suggested "somewhere chill". It''s a rooftop where cocktails cost $22.', 'neutral', 0, 0, 0, 0, 'Wine', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Somewhere Chill"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Offer to split', 'They let you. Of course they let you. The conversation was great though.', 60, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Suggest a walk instead', 'They love it. Two hours of talking about everything. Cost: zero. Feet: destroyed.', 0, 0, 2, 3, 0 FROM e;

-- 87. Left on Read
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Left on Read', 'The person you''ve been talking to for three weeks hasn''t replied in five days. They posted a story four minutes ago.', 'challenge', 0, 0, 0, 0, 'Ghost', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Left on Read')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Send "hey stranger 👀"', 'Seen 9:42pm. No reply. You have closure now, the hard way.', 0, 0, 1, -5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Delete the chat, hit the gym', 'You lift something heavy and feel something. Growth.', 0, 0, 2, 4, 0 FROM e;

-- 88. "Let's Just Split It"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Let''s Just Split It"', 'The group ordered four bottles of wine and lobster. You had soup. Someone says "let''s just split it evenly".', 'challenge', 0, 0, 0, 0, 'Utensils', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Let''s Just Split It"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Split evenly', '$95 for soup. It was very good soup. It was not $95 soup.', 95, 0, 1, -3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Pay for what you had', '$18. One friend calls you "a calculator". You''re a calculator with $77.', 18, 0, 2, 2, 0 FROM e;

-- 89. Baby Shower Registry
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Baby Shower Registry', 'Your friend is having a baby. The registry has a $300 stroller and a $9 bib.', 'neutral', 0, 0, 0, 0, 'Baby', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Baby Shower Registry')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy the bib', 'With a heartfelt card. The bib says "Mum''s little tax deduction". Massive hit.', 9, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Go in on the stroller', '$60 each with five friends. You are now collectively Godparents of Transportation.', 60, 0, 2, 5, 0 FROM e;

-- 90. Your Ex's Wedding
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Your Ex''s Wedding', 'Your ex invited you to their wedding, plus one included. A revenge outfit is available for $120.', 'challenge', 0, 0, 0, 0, 'Mail', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Your Ex''s Wedding')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Go, in the outfit', 'You look incredible. You dance. The best man asks for your number. Healing.', 120, 0, 1, 8, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Decline gracefully', 'A nice card, a couch, a tub of ice cream. Also healing.', 0, 0, 2, 2, 0 FROM e;

-- 91. Friend's Startup Launch
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Friend''s Startup Launch', 'Your friend''s startup is live. They want you to download the app, rate it 5 stars and "tell ten people".', 'neutral', 0, 0, 0, 0, 'Rocket', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Friend''s Startup Launch')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Hype it hard', 'You post it everywhere. It''s an app for rating other apps. You still believe in them.', 0, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Download, rate, delete', 'Five stars, then gone. Supportive, technically.', 0, 0, 2, 1, 0 FROM e;

-- 92. Forgot the Birthday
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Forgot the Birthday', 'You forgot your best friend''s birthday. It was yesterday. They posted "it''s fine, birthdays don''t matter anyway".', 'emergency', 0, 0, 0, 0, 'Cake', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Forgot the Birthday')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Surprise dinner tonight', '$70 and a lot of grovelling at their favourite place. You''re forgiven.', 70, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Belated meme', 'They reply "lol". A lowercase lol. You are not forgiven.', 0, 0, 2, -6, 0 FROM e;

-- 93. The Plus-One Problem
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Plus-One Problem', 'Your cousin''s wedding is in two weeks. Your mum has already told everyone you''re bringing "someone special".', 'neutral', 0, 0, 0, 0, 'Users', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Plus-One Problem')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Bring a friend as your "date"', 'You buy them a $40 outfit. They charm the aunties so well they''re now invited to Christmas.', 40, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Go solo', 'Seven aunties ask when you''re getting married. You develop a new smile just for this.', 0, 0, 2, -5, 0 FROM e;

-- 94. 3am Party Next Door
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '3am Party Next Door', 'Your neighbour''s party is still going at 3am. Same song, fourth time.', 'neutral', 0, 0, 0, 0, 'Music', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '3am Party Next Door')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Join them', 'You''re best friends with the neighbour now. You know all their business. Sleep is for the weak.', 0, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Call the caretaker', 'No answer. Fifth time. You know every word now.', 0, 0, 2, -5, 0 FROM e;

-- 95. Group Trip Treasurer
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Group Trip Treasurer', 'You''re planning the group trip. Eight people, eight opinions, two people who "will send it tomorrow".', 'challenge', 0, 0, 0, 0, 'Plane', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Group Trip Treasurer')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Front the deposit', 'Six people pay you back. Two send "will sort you out bro". You''re out $100.', 100, 0, 1, -5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Everyone pays first', 'Nobody pays. The trip becomes a group call. The group call becomes "next year".', 0, 0, 2, -2, 0 FROM e;

-- 96. Content Day
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Content Day', 'Your friend needs you to be their photographer for the day. They need 300 photos in front of one wall.', 'neutral', 0, 0, 0, 0, 'Camera', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Content Day')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Do it for love', 'You take 300 photos. They post the blurry one. 12k likes.', 0, 0, 1, 2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Charge them', '$40. They pay and start calling you "my content team". You''re a business now.', 0, 40, 2, 1, 0 FROM e;

-- 97. Family Group Chat
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Family Group Chat', 'Your uncle forwarded a message saying 5G towers can read your thoughts. Fourteen relatives reacted 🙏.', 'neutral', 0, 0, 0, 0, 'MessageCircle', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Family Group Chat')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Correct him with facts', 'You send three links. He replies with a six-minute voice note ending in "you young people".', 0, 0, 1, -4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'React 🙏 too', 'Peace in the family. A small piece of your soul leaves your body.', 0, 0, 2, 2, 0 FROM e;

-- 98. "You're the One With a Job"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"You''re the One With a Job"', 'Your younger sibling needs $250 for fees. Your parents say "you''re the one with a job now".', 'challenge', 0, 0, 0, 0, 'Users', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"You''re the One With a Job"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Pay it', 'Your sibling sends a crying voice note: "thank you". Your bank account sends one too.', 250, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Send job links instead', 'You send three weekend job ads and your old CV template. They reply "ok". Just "ok".', 0, 0, 2, -2, 0 FROM e;

-- 99. Mum Found Instagram
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Mum Found Instagram', 'Your mum just followed you. She''s already commented "my baby 😍" on a photo of you at a club.', 'neutral', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Mum Found Instagram')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Archive the evidence', 'Two hours curating a wholesome feed. Your friends think you''ve been hacked.', 0, 0, 1, -2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Embrace it', 'She comments on everything. Your followers adore her. She gets more likes than you now.', 0, 0, 2, 5, 0 FROM e;

-- 100. Relatives Are Coming
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Relatives Are Coming', 'Relatives from upcountry arrive tomorrow for an "indefinite" stay. Your fridge contains ketchup.', 'emergency', 0, 0, 0, 0, 'Home', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Relatives Are Coming')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Stock up and host', '$150 of groceries. They love you. They also love your Wi-Fi. They''re still here.', 150, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Sudden "work trip"', 'You "travel" to a friend''s couch for four days. Your relatives rearrange your living room.', 0, 0, 2, -4, 0 FROM e;

-- 101. The Ceiling Stain
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Ceiling Stain', 'A brown stain is growing on your ceiling. It''s shaped like your landlord''s face.', 'emergency', 0, 0, 0, 0, 'Droplets', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Ceiling Stain')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Fix it yourself', '$60 of supplies and a video tutorial later, it''s worse, but now it''s shaped like a duck.', 60, 0, 1, -2, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Call the landlord again', 'A plumber turns up three weeks later and fixes it for free. It only cost your patience.', 0, 0, 2, -3, 0 FROM e;

-- 102. "Impossible to Kill"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Impossible to Kill"', 'Your plant is dying. You''ve had it three weeks. The shop said it was "impossible to kill".', 'neutral', 0, 0, 0, 0, 'Leaf', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Impossible to Kill"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy a $30 grow lamp', 'It thrives. You talk to it now. It''s the best listener you know.', 30, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Let nature decide', 'It dies. You keep the pot as a memorial and a warning.', 0, 0, 2, -2, 0 FROM e;

-- 103. Wi-Fi Hostage
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Wi-Fi Hostage', 'Your brother renamed your Wi-Fi "FBI Surveillance Van 4" and changed the password.', 'neutral', 0, 0, 0, 0, 'Wifi', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Wi-Fi Hostage')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Reset the router yourself', 'Two hours on hold with your provider. It''s now called "Mine. Not Yours."', 0, 0, 1, -3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Bribe him with $10 airtime', 'He hands over the password. It was "password". You''re furious.', 10, 0, 2, 2, 0 FROM e;

-- 104. Moving-Out Sale
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Moving-Out Sale', 'You''re moving and have four years of stuff you never use. A neighbour offers $100 for all of it.', 'opportunity', 0, 0, 0, 0, 'Package', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Moving-Out Sale')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Take the $100', 'Easy money. Two days later you realise your favourite hoodie was in there.', 0, 100, 1, 1, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Sell it piece by piece', '$260 over three weeks, and 94 messages asking "is this still available?"', 0, 260, 2, -5, 0 FROM e;

-- 105. Moving Day
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Moving Day', 'Your friends promised to help you move. Two showed up. One brought a dog.', 'challenge', 0, 0, 0, 0, 'Truck', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Moving Day')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Hire movers', '$180 and done in two hours. They dropped one box. It was the plates.', 180, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Make it work', 'Eight hours and a sofa stuck in the stairwell. The dog had a great time.', 0, 0, 2, -6, 0 FROM e;

-- 106. Mum's Birthday
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Mum''s Birthday', 'Your siblings want to split a nice gift for mum. Your share is $60.', 'opportunity', 0, 0, 0, 0, 'Cake', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Mum''s Birthday')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Pay your share', 'She cries, hugs everyone and says you''re her favourite. She says it to all of you.', 60, 0, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Make her a card', 'She frames it. You are an adult. She frames it.', 0, 0, 2, 3, 0 FROM e;

-- 107. New Year, New Gym
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'New Year, New Gym', 'A gym offers a "New You" annual membership for $240. The old you is sceptical.', 'neutral', 0, 0, 0, 0, 'Dumbbell', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'New Year, New Gym')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Sign up', 'You go nine times in January. You are now the gym''s most generous donor.', 240, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Run in the park for free', 'You run twice. The third time you sit on a bench and eat crisps. Progress is progress.', 0, 0, 2, 2, 0 FROM e;

-- 108. 3am Symptom Search
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '3am Symptom Search', 'You looked up a headache at 3am. The internet says you have two weeks to live.', 'challenge', 0, 0, 0, 0, 'Search', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '3am Symptom Search')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'See a doctor', '"Drink water and stop googling." Best $45 you ever spent.', 45, 0, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Keep searching', 'Now you also have a rare tropical disease. You fall asleep at 5am, alive and anxious.', 0, 0, 2, -7, 0 FROM e;

-- 109. 25 Going on 75
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '25 Going on 75', 'You sneezed and pulled a muscle in your back. You''re 25. Your back is 75.', 'challenge', 0, 0, 0, 0, 'Activity', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '25 Going on 75')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'See a physio', '$90 and a stern warning about your posture. You sit up straight for nearly a whole day.', 90, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Lie on the floor', 'Three hours on the floor. It helps, and you reconsider most of your choices.', 0, 0, 2, -2, 0 FROM e;

-- 110. Phone-Free Weekend
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Phone-Free Weekend', 'You read that a weekend without your phone changes your life. Your first try lasted four hours.', 'opportunity', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Phone-Free Weekend')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Try again properly', '48 hours. You read a book, notice birds and miss three memes. Surprisingly lovely.', 0, 0, 1, 8, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Doomscroll instead', 'You watch 500 videos and remember none. Your thumb is in excellent shape.', 0, 0, 2, -4, 0 FROM e;

-- 111. The Spoon Documentary
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Spoon Documentary', 'It''s 2am and you''re watching a documentary about a man who collects spoons. Work starts in six hours.', 'neutral', 0, 0, 0, 0, 'Moon', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Spoon Documentary')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Go to bed', 'You wake up rested and only slightly curious about spoons.', 0, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'One more episode', 'You now know everything about spoons and nothing about the 9am meeting.', 0, 0, 2, -5, 0 FROM e;

-- 112. "Just a Trim"
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT '"Just a Trim"', 'You said "just a trim". The barber heard "start a new chapter".', 'emergency', 0, 0, 0, 0, 'Scissors', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = '"Just a Trim"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Fix it at a fancy salon', '$55 later you look good. Different. But good.', 55, 0, 1, 3, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Hats for a month', 'You become "the hat person". Some people think it''s a style. You let them.', 0, 0, 2, -3, 0 FROM e;

-- 113. Free Sample Festival
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Free Sample Festival', 'A food festival near work is handing out free samples. Your lunch break is 30 minutes.', 'opportunity', 0, 0, 0, 0, 'Utensils', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Free Sample Festival')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Speedrun the samples', 'Fourteen samples in 28 minutes. Free lunch, and a legend is born.', 0, 15, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Stay at your desk', 'Sad desk salad. Four different people tell you about the samples.', 0, 0, 2, -2, 0 FROM e;

-- 114. The 12-Step Skincare
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The 12-Step Skincare', 'A video says you need a 12-step skincare routine. The products come to $180.', 'neutral', 0, 0, 0, 0, 'Sparkles', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The 12-Step Skincare')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy it all', 'Your bathroom looks like a lab. Your skin looks the same. You feel incredibly fancy.', 180, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Water and sleep', 'Cheap, effective, boring. Your skin says thanks.', 0, 0, 2, 2, 0 FROM e;

-- 115. Wrong Ride
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Wrong Ride', 'You got into a car you thought was your ride-hail. It''s a stranger who just let you in. You''ve been chatting for five minutes.', 'emergency', 0, 0, 0, 0, 'Car', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Wrong Ride')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Ask him to drop you anyway', 'He''s going your way and refuses money. You''re invited to his kid''s birthday now.', 0, 0, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Jump out at the lights', 'You run. Your real ride cancelled and charged you a $5 fee.', 5, 0, 2, -3, 0 FROM e;

-- 116. A Bird's Blessing
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'A Bird''s Blessing', 'A bird left a "gift" on your shoulder right before an important meeting. People say it''s good luck.', 'neutral', 0, 0, 0, 0, 'Bird', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'A Bird''s Blessing')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Walk in confidently', 'They notice. You make a joke. They laugh. It goes better than any meeting you''ve had.', 0, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Buy a new shirt nearby', '$30 shirt, two minutes late, meeting fine. The bird got away with it.', 30, 0, 2, 1, 0 FROM e;

-- 117. The Office Jackpot Pool
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Office Jackpot Pool', 'Your office is pooling $10 each for the jackpot. If they win and you''re not in, you''ll be the only one still at work.', 'opportunity', 0, 0, 0, 0, 'Ticket', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Office Jackpot Pool')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Put in $10', 'You win! $46 each. Not life-changing, but lunch is on you and everyone remembers it.', 0, 36, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Skip it', 'They don''t win. You feel smug for exactly one afternoon.', 0, 0, 2, 2, 0 FROM e;

-- 118. Gridlock
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Gridlock', 'The highway is a car park. A vendor walks past selling phone chargers, peanuts and a live chicken.', 'challenge', 0, 0, 0, 0, 'Car', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Gridlock')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Buy the peanuts', 'Best $2 of your week. The chicken guy makes his sale to the car behind you.', 2, 0, 1, 4, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Scream into your sleeve', 'You arrive 90 minutes late and slightly hoarse.', 0, 0, 2, -3, 0 FROM e;

-- 119. Lost Wallet
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Lost Wallet', 'You lost your wallet: ID, cards, $40 and a coffee card one stamp from a free coffee.', 'emergency', 0, 0, 0, 0, 'Wallet', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Lost Wallet')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Retrace your steps', 'A kind lady at the bus stop had it. All there except the coffee card. She needed that coffee.', 0, 0, 1, 5, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Replace everything', '$35 in fees and three queues. Then the wallet turns up in your other jacket.', 35, 0, 2, -5, 0 FROM e;

-- 120. Accidentally Viral
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Accidentally Viral', 'You posted a video of your cat falling off the fridge. It has two million views.', 'opportunity', 0, 0, 0, 0, 'Video', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Accidentally Viral')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), id, 'Do a sponsored post', 'A pet food brand pays $250. Your cat demands a cut, in treats.', 0, 250, 1, 6, 0 FROM e
UNION ALL
SELECT gen_random_uuid(), id, 'Stay humble', 'You do nothing and the video fades. Your cat looks disappointed in you.', 0, 0, 2, 1, 0 FROM e;

commit;
