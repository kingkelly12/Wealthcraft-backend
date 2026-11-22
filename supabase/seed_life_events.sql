-- Adulting Life Events Seed File (Total: 120; 61-120 also in migration 20261126000000)
-- Generated for "Adulting"
-- Themes: Work, Finance, Social, Domestic, Health, Existential

BEGIN;

-- TRUNCATE existing tables to ensure clean slate (optional, but good for seed)
-- TRUNCATE TABLE life_events CASCADE; 

-- 1. The Dental Gamble (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Dental Gamble', 'You feel a twinge in your molar. Pay now or pray later?', 'challenge', -200.00, 0, 0, -10, 'Smile', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Ignore it and pray', 'You turn up the music to drown out the pain.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Book the Dentist', 'You pay the copay. You survive.', 200, 5, 2 FROM event_insert;

-- 2. The Subscription Vampire (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Subscription Vampire', 'You are paying for a gym you haven''t visited since 2023.', 'neutral', -45.00, 0, 0, -5, 'CreditCard', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'The Great Purge', 'You cancel everything. Silence is free.', 0, 45, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Keep ''em', 'At least you can watch "The Office" again.', 45, 2, 2 FROM event_insert;

-- 3. Therapy vs. Savings (Finance/Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Therapy vs. Savings', 'Existential dread is hitting hard. Budget allows for one.', 'challenge', -150.00, 0, 0, 20, 'Heart', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Go to Therapy', 'You cry for 50 minutes. It helps.', 150, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Raw dog reality', 'You bottle it up. Free but heavy.', 0, -5, 2 FROM event_insert;

-- 4. The Destination Wedding (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Destination Wedding', 'Cousin getting married in Bali. Flight is $2,000.', 'opportunity', -2000.00, 0, 0, 10, 'Plane', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Go (YOLO)', 'Great photos, empty wallet.', 2000, 15, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Decline politely', 'You send a toaster and stay home.', 50, -5, 2 FROM event_insert;

-- 5. The "Buy Now Pay Later" Trap (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The "Buy Now Pay Later" Trap', 'Shiny gadget. 4 easy payments of $50.', 'opportunity', 0, 0, 0, 5, 'ShoppingBag', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Split it up!', 'Future You hates Present You.', 50, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Wait', 'Delayed gratification is boring.', 0, 2, 2 FROM event_insert;

-- 6. The Student Loan Email (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Student Loan Email', 'ACTION REQUIRED. Recertify income plan.', 'neutral', 0, 0, 0, -15, 'FileText', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Do the Paperwork', '3 hours later, you are safe.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Ignore it', 'Future panic awaits.', 0, -10, 2 FROM event_insert;

-- 7. The Avocado Toast Moment (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Avocado Toast Moment', 'Bottomless brunch invites ($50 min).', 'opportunity', -50.00, 0, 0, 10, 'Coffee', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Go to Brunch', 'Mediocre toast, top tier gossip.', 50, 8, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Eat leftovers', 'Responsible but lonely.', 0, -2, 2 FROM event_insert;

-- 8. The Check Engine Light (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Check Engine Light', 'Orange light + weird clunking sound.', 'emergency', -400.00, 0, 0, -20, 'Tool', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Turn up Radio', 'Can''t hear it, not happening.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Go to Mechanic', 'Safe, but expensive.', 400, 0, 2 FROM event_insert;

-- 9. The 9 PM Email (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The 9 PM "Urgent" Email', 'Boss needs this for Monday morning.', 'challenge', 0, 0, 0, -10, 'Mail', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Quiet Quit', 'Reply Monday. Enjoy weekend.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Do it', 'Work late. No bonus.', 0, -5, 2 FROM event_insert;

-- 10. The "Voluntold" Committee (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The "Voluntold" Committee', 'Boss asks for "Office Fun" committee leader.', 'neutral', 0, 0, 0, -5, 'Users', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Accept burden', 'Lose 5 hours/week.', 0, 2, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Stare at floor', 'Avoid eye contact. Freedom!', 0, 5, 2 FROM event_insert;

-- 11. Return to Office Mandate (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Return to Office Mandate', 'CEO misses "hallway collisions". 3 days/week.', 'challenge', -100.00, 0, 0, -10, 'Briefcase', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Buy Train Pass', 'Commute is brutal.', 100, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Fight for Remote', 'Might work or get labeled.', 0, 0, 2 FROM event_insert;

-- 12. The LinkedIn Gloat Post (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The LinkedIn Gloat Post', 'Nemesis made 30 Under 30.', 'neutral', 0, 0, 0, -5, 'Linkedin', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Congratulate', 'Fake smiles.', 0, 2, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Mute and Scroll', 'Inner peace.', 0, 5, 2 FROM event_insert;

-- 13. Pizza Party (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Pizza Party', 'Record profits = Lukewarm pepperoni.', 'neutral', 0, 0, 0, -5, 'Pizza', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Eat pizza', 'Free food.', 0, 2, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Skip it', 'Sad desk salad protest.', 0, 3, 2 FROM event_insert;

-- 14. Spinach Standoff (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Spinach Standoff', 'Rotting spinach judging you.', 'neutral', 0, 0, 0, -2, 'Leaf', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Cook it', 'Health god.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Order Thai', 'Spinach dies.', 40, 3, 2 FROM event_insert;

-- 15. The YouTube Ph.D. (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The YouTube Ph.D.', 'Sink clogged.', 'challenge', -15.00, 0, 0, -5, 'Youtube', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'DIY', 'Feel powerful.', 15, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Call Pro', 'Solved but pricey.', 150, 0, 2 FROM event_insert;

-- 16. IKEA Meltdown (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The IKEA Meltdown', '5,000 parts, no words.', 'challenge', 0, 0, 0, -10, 'Hammer', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Hire TaskRabbit', 'Money well spent.', 100, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'DIY', 'Leans to the left.', 0, 5, 2 FROM event_insert;

-- 17. Laundry Mountain (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Laundry Mountain', 'Out of underwear.', 'neutral', 0, 0, 0, -5, 'Shirt', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Do Wash', 'Accomplished.', 5, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Buy New', 'Lazy but effective.', 20, 0, 2 FROM event_insert;

-- 18. Plant Parent (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Plant Parent', 'Succulent looking sad.', 'neutral', -20.00, 0, 0, 5, 'Flower', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Buy Fake', 'Pragmatic.', 20, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Research', 'Hope it lives.', 0, 2, 2 FROM event_insert;

-- 19. Internet Outage (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Internet Outage', 'WiFi down.', 'emergency', 0, 0, 0, -20, 'WifiOff', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Call Support', 'Hold music.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Hotspot', 'Expensive data.', 20, 0, 2 FROM event_insert;

-- 20. Grocery Tetris (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The Grocery Tetris', '15 bags. One trip?', 'neutral', 0, 0, 0, -5, 'ShoppingBag', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'One Trip', 'Heroic.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Two Trips', 'Shame.', 0, 0, 2 FROM event_insert;

-- 21. Zoom Cat Filter (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Zoom Cat Filter', 'You are stuck as a cat in a serious meeting.', 'challenge', 0, 0, 0, -10, 'Video', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Embrace it', 'Accept your feline fate.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Panic Leave', 'Fake a connection error.', 0, -5, 2 FROM event_insert;

-- 22. "Reply All" Apocalypse (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Reply All Apocalypse', 'You replied all with a snarky comment.', 'emergency', 0, 0, 0, -25, 'AlertTriangle', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Own it', 'Claim it was satire.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Hide', 'Turn off phone.', 0, 0, 2 FROM event_insert;

-- 23. Forgot to Mute (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Forgot to Mute', 'You sighed loudly while the CEO was talking.', 'challenge', 0, 0, 0, -15, 'MicOff', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Pretend it wasn''t you', 'Gaslight the room.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Apologize', 'Awkward silence.', 0, -2, 2 FROM event_insert;

-- 24. Printer Jam (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Printer Jam', 'PC Load Letter? What does that mean?', 'neutral', 0, 0, 0, -5, 'Printer', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Kick it', 'Percussive maintenance.', 0, 2, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Call IT', 'Submit a ticket.', 0, -2, 2 FROM event_insert;

-- 25. Coworker Oversharing (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Coworker Oversharing', 'Dave is talking about his divorce... again.', 'neutral', 0, 0, 0, -10, 'MessageSquare', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Listen knowingly', 'You are now his therapist.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Fake phone call', 'Escape!', 0, 5, 2 FROM event_insert;

-- 26. Performance Review (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Performance Review', 'Time to justify your existence.', 'challenge', 0, 0, 0, -15, 'Clipboard', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Hype yourself', 'Confidence is key.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Panic', 'Sweat through shirt.', 0, -5, 2 FROM event_insert;

-- 27. Free Snacks vs Dignity (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Free Snacks', 'Leftover sandwiches from a client meeting.', 'opportunity', 0, 0, 0, 0, 'Coffee', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Take them all', 'Groceries for the week.', 0, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Abstain', 'Keep your pride.', 0, 0, 2 FROM event_insert;

-- 28. "Quick Sync" (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'The "Quick Sync"', 'Calendar invite with no subject.', 'challenge', 0, 0, 0, -10, 'Calendar', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Prepare for worst', 'Anxiety spike.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Assume it''s fine', 'Ignorance is bliss.', 0, 0, 2 FROM event_insert;

-- 29. Jargon Overload (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Jargon Overload', 'Let''s circle back and synergy the low hanging fruit.', 'neutral', 0, 0, 0, -5, 'Hash', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Nod along', 'Dissociate.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Use more jargon', 'Become the problem.', 0, 5, 2 FROM event_insert;

-- 30. Friday 4PM Meeting (Work)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Friday 4PM Meeting', 'Why does this exist?', 'challenge', 0, 0, 0, -15, 'Clock', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Attend', 'Soul crushing.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Decline', 'Risky move.', 0, 10, 2 FROM event_insert;

-- 31. Forgot Free Trial (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Forgot Free Trial', 'Charged $99 for an app you used once.', 'neutral', -99.00, 0, 0, -10, 'CreditCard', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Beg for refund', 'Customer service hold.', 99, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Accept defeat', 'Expensive lesson.', 0, -5, 2 FROM event_insert;

-- 32. Splitting the Bill (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Splitting the Bill', 'Friend ordered 3 cocktails, you had water.', 'neutral', -20.00, 0, 0, -10, 'Divide', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Pay excess', 'Avoid conflict.', 20, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Itemize it', 'Be "that guy".', 0, 5, 2 FROM event_insert;

-- 33. Impulse Buy Regret (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Impulse Buy Regret', 'You bought a kayak. You live in a desert.', 'neutral', -300.00, 0, 0, -5, 'ShoppingBag', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Return it', 'Hassle.', 300, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Keep it', 'Aspirational decor.', 0, 0, 2 FROM event_insert;

-- 34. Tax Season Panic (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Tax Season Panic', 'Where are your W2s?', 'emergency', 0, 0, 0, -20, 'FileText', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Do it now', 'Get it over with.', 0, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Procrastinate', 'File extension.', 0, -5, 2 FROM event_insert;

-- 35. Overdraft Fee (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Overdraft Fee', 'You have -$4. Bank charges you $35.', 'neutral', -35.00, 0, 0, -15, 'DollarSign', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Call Bank', 'Plead poverty.', 35, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Cry', 'It is unfair.', 0, -5, 2 FROM event_insert;

-- 36. Wedding Gift Inflation (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Wedding Gift Inflation', 'Registry starts at $150.', 'neutral', -150.00, 0, 0, -5, 'Gift', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Buy the blender', 'Standard.', 150, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Cash in card', 'Easy.', 100, 0, 2 FROM event_insert;

-- 37. Gym Cancellation (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Gym Cancellation', 'Requires certified letter and blood sacrifice.', 'challenge', 0, 0, 0, -15, 'Activity', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Do it', 'Freedom.', 0, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Stay member', 'Waste money.', -30, 0, 2 FROM event_insert;

-- 38. Crypto FOMO (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Crypto FOMO', 'Dogecoin is up. Should you buy?', 'opportunity', -100.00, 0, 0, -5, 'TrendingUp', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Buy!', 'Gambling.', 100, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Ignore', 'Safe.', 0, 0, 2 FROM event_insert;

-- 39. Rent Increase (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Rent Increase', 'Landlord wants $200 more.', 'challenge', 0, 0, 200, -20, 'Home', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Pay it', 'No choice.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Move', 'Packing hell.', -500, 0, 2 FROM event_insert;

-- 40. Generic Brand Disappointment (Finance)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Generic Brand Fail', 'The "Oat Circles" taste like cardboard.', 'neutral', -5.00, 0, 0, -2, 'ShoppingCart', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Eat them', 'Sad breakfast.', 0, -2, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Throw away', 'Waste.', 0, 0, 2 FROM event_insert;

-- 41. Ghosted (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Ghosted', 'Three great dates within silence.', 'neutral', 0, 0, 0, -15, 'Ghost', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Check story', 'Stalking.', 0, -5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Move on', 'Healthy.', 0, 5, 2 FROM event_insert;

-- 42. Awkward Date (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Awkward Date', 'They talked about their ex... for 2 hours.', 'neutral', -50.00, 0, 0, -10, 'Heart', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Fake emergency', 'Classic exit.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Endure', 'Polite.', 0, -5, 2 FROM event_insert;

-- 43. Social Battery Drained (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Social Battery Dead', 'You are at a party and want to leave.', 'neutral', 0, 0, 0, -10, 'Battery', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Irish Exit', 'Disappear.', 0, 10, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Stay', 'Suffer.', 0, -5, 2 FROM event_insert;

-- 44. Forgot Name (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Forgot Name', 'Someone says hi. You have no idea who they are.', 'challenge', 0, 0, 0, -5, 'HelpCircle', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Say "Hey You!"', 'Risky.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Admit it', 'Awkward honesty.', 0, 5, 2 FROM event_insert;

-- 45. Ran into Ex (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Ran into Ex', 'You look terrible. They look great.', 'emergency', 0, 0, 0, -20, 'Eye', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Hide in aisle', 'Dignity lost.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Say Hi', 'Painful.', 0, 0, 2 FROM event_insert;

-- 46. Everyone is Engaged (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Everyone is Engaged', 'Your feed is just ring photos.', 'neutral', 0, 0, 0, -5, 'Heart', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Delete App', 'Cleanse.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Compare self', 'Spiral.', 0, -10, 2 FROM event_insert;

-- 47. Cancelled Plans (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Cancelled Plans', 'They cancelled! You can stay in.', 'opportunity', 0, 0, 0, 15, 'Smile', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Order Pizza', 'Celebration.', -20, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Sleep', 'Best night ever.', 0, 10, 2 FROM event_insert;

-- 48. Accidental Like (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Accidental Like', 'You liked a photo from 2016.', 'emergency', 0, 0, 0, -20, 'ThumbsUp', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Unlike immediately', 'They still saw it.', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Move to Nepal', 'Start new life.', 0, 5, 2 FROM event_insert;

-- 49. Bad Haircut (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Bad Haircut', 'You asked for a trim. You got a bowl cut.', 'challenge', -50.00, 0, 0, -15, 'Scissors', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Wear hat', 'For 3 months.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Cry', 'Therapeutic.', 0, 0, 2 FROM event_insert;

-- 50. Same Outfit (Social)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Same Outfit', 'Coworker wearing same shirt.', 'neutral', 0, 0, 0, -2, 'Shirt', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Photo Op', 'Laugh it off.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Go home', 'Change.', 0, 0, 2 FROM event_insert;

-- 51. WebMD Doom (Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'WebMD Doom', 'Headache? Internet says "rare disease".', 'neutral', 0, 0, 0, -15, 'Activity', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Close Tab', 'Denial.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Spiral', 'Write will.', 0, -5, 2 FROM event_insert;

-- 52. Mystery Ailment (Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Mystery Ailment', 'Back hurts. Why? You slept wrong.', 'challenge', 0, 0, 0, -10, 'Frown', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Yoga', 'Effort.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Complain', 'Easy.', 0, 0, 2 FROM event_insert;

-- 53. Dentist Shame (Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Dentist Shame', 'You haven''t flossed. They know.', 'neutral', 0, 0, 0, -5, 'Smile', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Lie', 'I floss daily!', 0, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Accept lecture', 'I am garbage.', 0, 5, 2 FROM event_insert;

-- 54. Hangover at 30 (Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Hangover at 30', 'Two drinks last night. Bedridden today.', 'challenge', 0, 0, 0, -20, 'Frown', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Greasy food', 'Cure.', -20, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Vow sobriety', 'Lie to self.', 0, 0, 2 FROM event_insert;

-- 55. Dehydration (Health)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Dehydration', 'You drank only coffee today.', 'neutral', 0, 0, 0, -5, 'Coffee', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Drink water', 'Self care.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'More coffee', 'Jitters.', 0, -5, 2 FROM event_insert;

-- 56. Package Stolen (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Package Stolen', 'Your porch pirate struck again.', 'emergency', -50.00, 0, 0, -15, 'Box', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Report it', 'Paperwork.', 50, 0, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Seethe', 'Rage.', 0, -5, 2 FROM event_insert;

-- 57. Burnt Dinner (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Burnt Dinner', 'Smoke alarm counts as a timer, right?', 'neutral', -10.00, 0, 0, -5, 'Flame', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Order Pizza', 'Backup plan.', -30, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Eat charcoal', 'Sadness.', 0, -5, 2 FROM event_insert;

-- 58. Noisy Neighbors (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Noisy Neighbors', 'Clogs. Why are they wearing clogs?', 'neutral', 0, 0, 0, -10, 'Speaker', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Bang on ceiling', 'War.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Earplugs', 'Peace.', 0, 0, 2 FROM event_insert;

-- 59. Spider Disappearance (Domestic)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Spider Disappearance', 'It was on the wall. Now it is gone.', 'emergency', 0, 0, 0, -15, 'Bug', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Burn house', 'Logical.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Sleep with one eye open', 'Fear.', 0, -5, 2 FROM event_insert;

-- 60. Sunday Scaries (Existential)
WITH event_insert AS (
    INSERT INTO life_events (id, title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    VALUES (gen_random_uuid(), 'Sunday Scaries', 'The weekend is over. Work looms.', 'neutral', 0, 0, 0, -10, 'Calendar', true) RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order)
SELECT gen_random_uuid(), id, 'Prepare', 'Productive panic.', 0, 5, 1 FROM event_insert
UNION ALL
SELECT gen_random_uuid(), id, 'Denial', 'Stay up late.', 0, -5, 2 FROM event_insert;

-- ---------------------------------------------------------------------------
-- 61-120: everyday adult chaos (skipped if a title already exists)
-- ---------------------------------------------------------------------------

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


-- ---------------------------------------------------------------------------
-- Fixes for events 1-60 (also migration 20261128000000): each choice gets its
-- real cash effect, its own sanity effect and a proper outcome line. Before,
-- sanity sat in `benefit`, which the game pays out as cash.
-- ---------------------------------------------------------------------------

update life_event_choices set outcome_description = 'You turn the music up to drown out the molar. The molar turns it up too.', cost = 0, benefit = 0, impact_sanity = -8, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Dental Gamble');
update life_event_choices set outcome_description = '$200 and a lecture about flossing later, the pain is gone. Worth every cent.', cost = 200, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Dental Gamble');
update life_event_choices set outcome_description = 'You cancel the gym and four streaming apps you forgot about. Your bank statement is suddenly short and beautiful.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Subscription Vampire');
update life_event_choices set outcome_description = 'You keep paying. One day you will go. Probably. Maybe.', cost = 45, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Subscription Vampire');
update life_event_choices set outcome_description = 'You cry for 50 minutes. It helps more than you expected.', cost = 150, benefit = 0, impact_sanity = 10, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Therapy vs. Savings');
update life_event_choices set outcome_description = 'You bottle it up. It''s free, but it''s heavy.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Therapy vs. Savings');
update life_event_choices set outcome_description = 'Great photos, a tan and an empty wallet. The bride cried when she saw you.', cost = 2000, benefit = 0, impact_sanity = 12, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Destination Wedding');
update life_event_choices set outcome_description = 'You send a toaster and watch the whole thing on stories from your couch.', cost = 50, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Destination Wedding');
update life_event_choices set outcome_description = 'Four easy payments! Future you will meet the other three.', cost = 50, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The "Buy Now Pay Later" Trap');
update life_event_choices set outcome_description = 'You wait a week and realise you didn''t need it. Boring. Correct.', cost = 0, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The "Buy Now Pay Later" Trap');
update life_event_choices set outcome_description = 'Three hours of forms later, you''re on a cheaper repayment plan: $40 a month less.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 40
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Student Loan Email');
update life_event_choices set outcome_description = 'You archive it. It will be back, with friends.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Student Loan Email');
update life_event_choices set outcome_description = 'Mediocre toast, top-tier gossip.', cost = 50, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Avocado Toast Moment');
update life_event_choices set outcome_description = 'Responsible, and a little lonely.', cost = 0, benefit = 0, impact_sanity = -1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Avocado Toast Moment');
update life_event_choices set outcome_description = 'You turn up the radio. The light is still on, and now there''s a new noise.', cost = 0, benefit = 0, impact_sanity = -8, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Check Engine Light');
update life_event_choices set outcome_description = 'A loose sensor and a $400 "while we were in there". Safe, at least.', cost = 400, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Check Engine Light');
update life_event_choices set outcome_description = 'You reply on Monday. Nothing caught fire. It never does.', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The 9 PM "Urgent" Email');
update life_event_choices set outcome_description = 'You work until midnight. Nobody says thank you. There is no bonus.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The 9 PM "Urgent" Email');
update life_event_choices set outcome_description = 'You''re on the Fun Committee now. It is not fun. It is five hours a week.', cost = 0, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The "Voluntold" Committee');
update life_event_choices set outcome_description = 'You study the carpet so hard you could draw it from memory. They pick someone else. Freedom.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The "Voluntold" Committee');
update life_event_choices set outcome_description = 'The commute is brutal, but the office has free coffee. Bad coffee.', cost = 100, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Return to Office Mandate');
update life_event_choices set outcome_description = 'You write a passionate email. HR says they will "take it on board".', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Return to Office Mandate');
update life_event_choices set outcome_description = 'You type "Congrats!!" with a smile that doesn''t reach your eyes.', cost = 0, benefit = 0, impact_sanity = -1, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The LinkedIn Gloat Post');
update life_event_choices set outcome_description = 'You mute them and keep scrolling. Inner peace, one tap away.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The LinkedIn Gloat Post');
update life_event_choices set outcome_description = 'Free pizza. It''s not a raise, but it is cheese.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Pizza Party');
update life_event_choices set outcome_description = 'You protest with a sad desk salad. Nobody notices the protest.', cost = 0, benefit = 0, impact_sanity = -1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Pizza Party');
update life_event_choices set outcome_description = 'You cook it. You are a health god for one evening.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Spinach Standoff');
update life_event_choices set outcome_description = 'Pad thai arrives. The spinach dies in the fridge, as was always its destiny.', cost = 40, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Spinach Standoff');
update life_event_choices set outcome_description = 'A $15 drain snake and a nine-minute video later, the sink drains. You feel unstoppable.', cost = 15, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The YouTube Ph.D.');
update life_event_choices set outcome_description = 'A plumber fixes it in ten minutes. You pay for the ten years he spent learning how.', cost = 150, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The YouTube Ph.D.');
update life_event_choices set choice_label = 'Hire a handyman', outcome_description = 'Someone builds it in 40 minutes while you hold one screw.', cost = 100, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The IKEA Meltdown');
update life_event_choices set outcome_description = 'Six hours, one leftover screw, and it leans to the left. Forever.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The IKEA Meltdown');
update life_event_choices set outcome_description = 'Clean sheets, clean socks. You are a functioning adult.', cost = 5, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Laundry Mountain');
update life_event_choices set outcome_description = 'New underwear instead of washing the old ones. The mountain grows.', cost = 20, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Laundry Mountain');
update life_event_choices set outcome_description = 'A plastic plant. It will outlive you.', cost = 20, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Plant Parent');
update life_event_choices set outcome_description = 'An hour of research: you were overwatering it. It might live.', cost = 0, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Plant Parent');
update life_event_choices set outcome_description = 'Ninety minutes of hold music, then: "Have you tried turning it off and on?"', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Internet Outage');
update life_event_choices set outcome_description = 'Your phone becomes the Wi-Fi. Your data plan becomes a memory.', cost = 20, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Internet Outage');
update life_event_choices set outcome_description = 'Eleven bags, one trip, two dead fingers. Heroic.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The Grocery Tetris');
update life_event_choices set outcome_description = 'Two trips. The neighbours saw. Shame.', cost = 0, benefit = 0, impact_sanity = -1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The Grocery Tetris');
update life_event_choices set outcome_description = 'You present the quarterly numbers as a cat. Your boss calls it "refreshing".', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Zoom Cat Filter');
update life_event_choices set outcome_description = 'You fake a connection error. The meeting recording says otherwise.', cost = 0, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Zoom Cat Filter');
update life_event_choices set outcome_description = 'You claim it was satire. Nobody believes you, but some people respect it.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Reply All Apocalypse');
update life_event_choices set outcome_description = 'You turn your phone off for a day. It''s all still there when you turn it back on.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Reply All Apocalypse');
update life_event_choices set outcome_description = 'You gaslight an entire meeting. It almost works.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Forgot to Mute');
update life_event_choices set outcome_description = 'Awkward silence, then someone laughs. You survive.', cost = 0, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Forgot to Mute');
update life_event_choices set outcome_description = 'Percussive maintenance. It works. You tell no one.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Printer Jam');
update life_event_choices set outcome_description = 'Ticket #48213 submitted. Estimated response: next quarter.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Printer Jam');
update life_event_choices set outcome_description = 'You are now Dave''s unpaid therapist. Sessions are Tuesdays, apparently.', cost = 0, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Coworker Oversharing');
update life_event_choices set outcome_description = 'Your "mum" calls at the perfect moment. Escape!', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Coworker Oversharing');
update life_event_choices set outcome_description = 'You list your wins with confidence. They give you a small raise: +$60 a month.', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 60
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Performance Review');
update life_event_choices set outcome_description = 'You sweat through your shirt and agree that you "could communicate more".', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Performance Review');
update life_event_choices set outcome_description = 'Your bag is full of client sandwiches. Lunch is sorted for the week.', cost = 0, benefit = 10, impact_sanity = 2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Free Snacks');
update life_event_choices set outcome_description = 'You keep your pride. Someone else takes the good sandwiches.', cost = 0, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Free Snacks');
update life_event_choices set outcome_description = 'You rehearse a resignation speech. It was about a calendar invite.', cost = 0, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'The "Quick Sync"');
update life_event_choices set outcome_description = 'It was fine. Ignorance is bliss.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'The "Quick Sync"');
update life_event_choices set outcome_description = 'You dissociate through "synergising our deliverables".', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Jargon Overload');
update life_event_choices set outcome_description = 'You say "let''s circle back on bandwidth". You have become the problem. It feels great.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Jargon Overload');
update life_event_choices set outcome_description = 'An hour that could have been an email. It wasn''t even an email.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Friday 4PM Meeting');
update life_event_choices set outcome_description = 'You decline. Nothing happens. You are free at 4pm.', cost = 0, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Friday 4PM Meeting');
update life_event_choices set outcome_description = '45 minutes on hold, but they refund the $99. Persistence pays.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Forgot Free Trial');
update life_event_choices set outcome_description = '$99 for an app you opened once. Expensive lesson.', cost = 99, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Forgot Free Trial');
update life_event_choices set outcome_description = 'You pay $20 more than you ate. Peace has a price.', cost = 20, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Splitting the Bill');
update life_event_choices set outcome_description = 'You split it to the cent. You''re "that guy" now, but a richer one.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Splitting the Bill');
update life_event_choices set outcome_description = 'Forty minutes in the returns queue holding a kayak, but your $300 comes back.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Impulse Buy Regret');
update life_event_choices set outcome_description = 'It''s a beautiful kayak. You live in a desert. It''s decor now.', cost = 300, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Impulse Buy Regret');
update life_event_choices set outcome_description = 'Two painful hours, then done. You feel like a CEO.', cost = 0, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Tax Season Panic');
update life_event_choices set outcome_description = 'You file late and pay a $25 penalty. The panic was free, though.', cost = 25, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Tax Season Panic');
update life_event_choices set outcome_description = 'You plead poverty and they waive the fee. First-time lucky.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Overdraft Fee');
update life_event_choices set outcome_description = 'The $35 fee stays. So do the tears.', cost = 35, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Overdraft Fee');
update life_event_choices set outcome_description = 'It''s on the registry. They''ll use it twice a year.', cost = 150, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Wedding Gift Inflation');
update life_event_choices set outcome_description = 'Simple, appreciated, still $100.', cost = 100, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Wedding Gift Inflation');
update life_event_choices set outcome_description = 'A form, a manager and a sigh, but you''re out. Freedom.', cost = 0, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Gym Cancellation');
update life_event_choices set outcome_description = 'Another $30 for a gym you mostly see from the bus.', cost = 30, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Gym Cancellation');
update life_event_choices set outcome_description = 'You buy $100 right at the top. It''s down 40% by Tuesday.', cost = 100, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Crypto FOMO');
update life_event_choices set outcome_description = 'You miss nothing. It crashes on Tuesday.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Crypto FOMO');
update life_event_choices set outcome_description = 'You pay the extra $200. Your landlord posts a photo of his new car.', cost = 200, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Rent Increase');
update life_event_choices set choice_label = 'Negotiate', outcome_description = 'You show him three cheaper listings nearby. He agrees to no increase this year. Grumpily.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Rent Increase');
update life_event_choices set outcome_description = 'Sad, slightly soggy breakfast.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Generic Brand Fail');
update life_event_choices set choice_label = 'Buy the real ones', outcome_description = 'You bin them and buy the proper brand. A $5 lesson.', cost = 5, benefit = 0, impact_sanity = 1, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Generic Brand Fail');
update life_event_choices set outcome_description = 'They''re at brunch, smiling. You''re fine. Totally fine.', cost = 0, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Ghosted');
update life_event_choices set outcome_description = 'You delete the chat and go for a walk. Healthy. Annoyingly healthy.', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Ghosted');
update life_event_choices set outcome_description = 'Your friend "urgently needs you" before the food arrives. Classic exit.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Awkward Date');
update life_event_choices set outcome_description = 'Two hours about their crypto portfolio, and you pay half.', cost = 50, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Awkward Date');
update life_event_choices set outcome_description = 'You vanish without a goodbye. Nobody notices until Tuesday.', cost = 0, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Social Battery Dead');
update life_event_choices set outcome_description = 'Three more hours of small talk. Your soul leaves before you do.', cost = 0, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Social Battery Dead');
update life_event_choices set outcome_description = '"Heyyy you!" They know. They always know.', cost = 0, benefit = 0, impact_sanity = -1, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Forgot Name');
update life_event_choices set outcome_description = 'You admit it. They forgot yours too. Instant friends.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Forgot Name');
update life_event_choices set outcome_description = 'You hide behind the cereal for nine minutes. Dignity: lost.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Ran into Ex');
update life_event_choices set outcome_description = 'Painful, polite and over in a minute. Growth.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Ran into Ex');
update life_event_choices set outcome_description = 'You delete the app for a week. The world keeps spinning.', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Everyone is Engaged');
update life_event_choices set outcome_description = 'You compare your life to strangers'' best days until 2am.', cost = 0, benefit = 0, impact_sanity = -8, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Everyone is Engaged');
update life_event_choices set outcome_description = 'Pizza, pyjamas, no plans. A celebration.', cost = 20, benefit = 0, impact_sanity = 6, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Cancelled Plans');
update life_event_choices set outcome_description = 'You sleep eleven hours. Best night of the year.', cost = 0, benefit = 0, impact_sanity = 8, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Cancelled Plans');
update life_event_choices set outcome_description = 'You unlike it in 0.3 seconds. They saw. They always see.', cost = 0, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Accidental Like');
update life_event_choices set outcome_description = 'You plan a new life in the mountains, then settle for muting them.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Accidental Like');
update life_event_choices set outcome_description = 'You wear a hat for three months. People think it''s a look.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Bad Haircut');
update life_event_choices set choice_label = 'Pay to fix it', outcome_description = 'A real salon fixes it for $50. You look good. Different, but good.', cost = 50, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Bad Haircut');
update life_event_choices set outcome_description = 'You take a photo together. It gets more likes than either of you ever has.', cost = 0, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Same Outfit');
update life_event_choices set outcome_description = 'You change and come back late. Nobody would have cared.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Same Outfit');
update life_event_choices set outcome_description = 'You close the tab and drink some water. Probably fine.', cost = 0, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'WebMD Doom');
update life_event_choices set outcome_description = 'Forty tabs later, you have six rare diseases and no sleep.', cost = 0, benefit = 0, impact_sanity = -6, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'WebMD Doom');
update life_event_choices set outcome_description = 'Twenty minutes of stretching. Your back pops loud enough for the neighbours.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Mystery Ailment');
update life_event_choices set outcome_description = 'You tell everyone about your back. They tell you about theirs.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Mystery Ailment');
update life_event_choices set outcome_description = '"I floss daily!" The dentist looks at your gums and says nothing. Loudly.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Dentist Shame');
update life_event_choices set outcome_description = 'You promise to floss. You might even do it.', cost = 0, benefit = 0, impact_sanity = 2, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Dentist Shame');
update life_event_choices set outcome_description = 'Fries, a burger and a nap. Medicine.', cost = 20, benefit = 0, impact_sanity = 5, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Hangover at 30');
update life_event_choices set outcome_description = 'You swear you''ll never drink again. Your liver has heard this before.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Hangover at 30');
update life_event_choices set outcome_description = 'A big glass of water. You feel like a plant that got rained on.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Dehydration');
update life_event_choices set outcome_description = 'A fourth coffee. You can hear colours.', cost = 5, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Dehydration');
update life_event_choices set outcome_description = 'Two calls and a form later, the shop sends a replacement.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Package Stolen');
update life_event_choices set outcome_description = 'You rage at the doorbell footage. The package is gone, and so is your $50.', cost = 50, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Package Stolen');
update life_event_choices set outcome_description = 'Pizza saves the night. The smoke alarm gets a rest.', cost = 30, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Burnt Dinner');
update life_event_choices set outcome_description = 'You eat it anyway. It tastes like regret and carbon.', cost = 0, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Burnt Dinner');
update life_event_choices set outcome_description = 'You bang on the ceiling. They bang back. It is war now.', cost = 0, benefit = 0, impact_sanity = -2, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Noisy Neighbors');
update life_event_choices set outcome_description = 'Foam earplugs. Silence. Bliss.', cost = 5, benefit = 0, impact_sanity = 3, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Noisy Neighbors');
update life_event_choices set outcome_description = 'You don''t burn the house down. You do sleep on the sofa.', cost = 0, benefit = 0, impact_sanity = -3, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Spider Disappearance');
update life_event_choices set outcome_description = 'You sleep with one eye open. The spider sleeps soundly.', cost = 0, benefit = 0, impact_sanity = -5, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Spider Disappearance');
update life_event_choices set outcome_description = 'You plan the week and lay out your clothes. Monday you is grateful.', cost = 0, benefit = 0, impact_sanity = 4, impact_income = 0
  where choice_order = 1 and life_event_id in (select id from life_events where title = 'Sunday Scaries');
update life_event_choices set outcome_description = 'You stay up until 2am. Monday arrives anyway.', cost = 0, benefit = 0, impact_sanity = -4, impact_income = 0
  where choice_order = 2 and life_event_id in (select id from life_events where title = 'Sunday Scaries');
-- Each choice now carries its own sanity, so the event-level fallback is off.
update life_events set impact_sanity = 0 where title in (
  'The Dental Gamble',
  'The Subscription Vampire',
  'Therapy vs. Savings',
  'The Destination Wedding',
  'The "Buy Now Pay Later" Trap',
  'The Student Loan Email',
  'The Avocado Toast Moment',
  'The Check Engine Light',
  'The 9 PM "Urgent" Email',
  'The "Voluntold" Committee',
  'Return to Office Mandate',
  'The LinkedIn Gloat Post',
  'Pizza Party',
  'Spinach Standoff',
  'The YouTube Ph.D.',
  'The IKEA Meltdown',
  'The Laundry Mountain',
  'The Plant Parent',
  'The Internet Outage',
  'The Grocery Tetris',
  'Zoom Cat Filter',
  'Reply All Apocalypse',
  'Forgot to Mute',
  'Printer Jam',
  'Coworker Oversharing',
  'Performance Review',
  'Free Snacks',
  'The "Quick Sync"',
  'Jargon Overload',
  'Friday 4PM Meeting',
  'Forgot Free Trial',
  'Splitting the Bill',
  'Impulse Buy Regret',
  'Tax Season Panic',
  'Overdraft Fee',
  'Wedding Gift Inflation',
  'Gym Cancellation',
  'Crypto FOMO',
  'Rent Increase',
  'Generic Brand Fail',
  'Ghosted',
  'Awkward Date',
  'Social Battery Dead',
  'Forgot Name',
  'Ran into Ex',
  'Everyone is Engaged',
  'Cancelled Plans',
  'Accidental Like',
  'Bad Haircut',
  'Same Outfit',
  'WebMD Doom',
  'Mystery Ailment',
  'Dentist Shame',
  'Hangover at 30',
  'Dehydration',
  'Package Stolen',
  'Burnt Dinner',
  'Noisy Neighbors',
  'Spider Disappearance',
  'Sunday Scaries'
);


COMMIT;
