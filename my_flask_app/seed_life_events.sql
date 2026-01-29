-- Adulting Life Events Seed File (Total: 60)
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

COMMIT;
