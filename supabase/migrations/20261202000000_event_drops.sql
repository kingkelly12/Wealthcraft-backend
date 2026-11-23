-- =============================================================================
-- New events, regularly: seasonal events and scheduled weekly drops
-- =============================================================================
-- * life_events.released_at: dealt only from this time on. Events written ahead
--   go live by themselves, with no deploy. Empty = available now (all older
--   events), and only events with a date get the "✨ New" badge (for 14 days).
-- * life_events.season_start / season_end ('MM-DD', may wrap the new year):
--   dealt only inside that window, every year, for every player at once.
--   season_label / season_emoji: the badge on the card ("🛍️ Black Friday").
-- * life_events.pack: which drop or season an event belongs to.
-- New and in-season events are dealt first (app/game/week_service.py).
-- Content: 18 seasonal events (Black Friday, festive season, New Year,
-- Valentine's, April Fools, halfway through the year) and 18 events in six
-- weekly drops, live each Monday from 30 Nov 2026 to 4 Jan 2027.
-- To add more later: insert events with a future released_at.
-- Safe to re-run: events are skipped by title.
-- =============================================================================

begin;

alter table public.life_events add column if not exists released_at timestamptz;
alter table public.life_events add column if not exists season_start text check (season_start ~ '^[0-1][0-9]-[0-3][0-9]$');
alter table public.life_events add column if not exists season_end text check (season_end ~ '^[0-1][0-9]-[0-3][0-9]$');
alter table public.life_events add column if not exists season_label text;
alter table public.life_events add column if not exists season_emoji text;
alter table public.life_events add column if not exists pack text;

-- 1. Doorbuster Deal (season: Black Friday (11-20 to 12-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Doorbuster Deal', 'A TV is 60% off for the first 20 people in the queue. The queue started at 4am. It is 3:50am and you are, for some reason, awake.', 'challenge', 0, 0, 0, 0, 'ShoppingBag', true, '11-20', '12-02', 'Black Friday', '🛍️', 'Black Friday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Doorbuster Deal')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Join the queue', 'You''re person nineteen. You carry a 65-inch TV home on the bus. Your arms will never forgive you.', 350, 0, 1, 3, 0),
    ('Go back to sleep', 'You sleep until 10. The same TV is on sale online at 9:58. Nice try, capitalism.', 0, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 2. Abandoned Cart (season: Black Friday (11-20 to 12-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Abandoned Cart', 'You left $180 of things in your cart. The shop emails: "Still thinking? Here''s 10% off ❤️".', 'neutral', 0, 0, 0, 0, 'ShoppingCart', true, '11-20', '12-02', 'Black Friday', '🛍️', 'Black Friday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Abandoned Cart')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Fine. Checkout.', 'It arrives in four boxes, one of them for a single candle. You feel seen, and slightly manipulated.', 162, 0, 1, 2, 0),
    ('Delete the email', 'Three more emails follow, each sadder. By Friday they offer 25% off and a short poem.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 3. Cyber Monday Laptop (season: Black Friday (11-20 to 12-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Cyber Monday Laptop', 'Your laptop is held together with tape. A good one is $300 off today only.', 'opportunity', 0, 0, 0, 0, 'Laptop', true, '11-20', '12-02', 'Black Friday', '🛍️', 'Black Friday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Cyber Monday Laptop')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Upgrade', 'Everything opens instantly. You finish freelance work faster: about $40 more a month.', 600, 0, 1, 5, 40),
    ('Tape it again', 'The hinge squeaks like a haunted door. It is fine. It is fine.', 0, 0, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 4. End-of-Year Party (season: Festive season (12-10 to 12-30))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'End-of-Year Party', 'Open bar, karaoke, and your manager has the microphone.', 'neutral', 0, 0, 0, 0, 'PartyPopper', true, '12-10', '12-30', 'Festive season', '🎄', 'Festive season'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'End-of-Year Party')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Duet with your boss', 'You crush a power ballad together. Your next review already feels warmer.', 0, 0, 1, 6, 0),
    ('Leave after one drink', 'You miss the moment accounting did the worm. People talk about it until March.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 5. Gift List Spiral (season: Festive season (12-10 to 12-30))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Gift List Spiral', 'The family gift list is now 14 people, including a cousin''s new partner you''ve met once.', 'challenge', 0, 0, 0, 0, 'Gift', true, '12-10', '12-30', 'Festive season', '🎄', 'Festive season'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Gift List Spiral')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy for everyone', 'Fourteen gifts and one wiped-out weekend. The new partner gets you nothing. Noted.', 280, 0, 1, 4, 0),
    ('Propose a name draw', 'Everyone buys one gift. Your aunt calls it "cold". Everyone else calls it genius.', 40, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 6. Flights Home (season: Festive season (12-10 to 12-30))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Flights Home', 'Flights home cost three times the usual price this month. Your mum texts: "so when do you land?"', 'challenge', 0, 0, 0, 0, 'Plane', true, '12-10', '12-30', 'Festive season', '🎄', 'Festive season'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Flights Home')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Book it', 'Expensive, crowded, delayed, and worth every minute when you see the food.', 450, 0, 1, 8, 0),
    ('Video call instead', 'You watch the family dinner on a phone propped against the salad. Someone forgets to unmute.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 7. Eleven Resolutions (season: New Year (12-31 to 01-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Eleven Resolutions', 'New year, new you. You''ve written eleven resolutions. It''s January 1st and you''re eating cold pizza.', 'neutral', 0, 0, 0, 0, 'Target', true, '12-31', '01-10', 'New Year', '🎆', 'New Year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Eleven Resolutions')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Pick one and keep it', 'Just one: save a little every week. Weirdly, it sticks.', 0, 0, 1, 5, 0),
    ('Keep all eleven', 'By January 4th you have broken nine. Two survive: "drink water" and "be mysterious".', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 8. New Year's Eve (season: New Year (12-31 to 01-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'New Year''s Eve', 'Tickets to the big countdown party cost $90. Your friends are staying in with board games.', 'challenge', 0, 0, 0, 0, 'Sparkles', true, '12-31', '01-10', 'New Year', '🎆', 'New Year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'New Year''s Eve')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Party', 'Fireworks, strangers hugging, a shoe lost somewhere. Iconic.', 90, 0, 1, 6, 0),
    ('Board games', 'Someone flips the board at 11:58pm. Best New Year in ages.', 15, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 9. The Longest Month (season: New Year (12-31 to 01-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'The Longest Month', 'December''s payday came early. January''s comes late. This month has 47 days.', 'challenge', 0, 0, 0, 0, 'CalendarClock', true, '12-31', '01-10', 'New Year', '🎆', 'New Year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Longest Month')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Live on pantry food', 'Rice, a tin of beans and heroic creativity. You invent three dishes. None of them are good.', 0, 0, 1, -4, 0),
    ('Pick up an extra shift', 'Long shift, sore feet, full fridge. January blinks first.', 0, 120, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 10. Valentine's Set Menu (season: Valentine's (02-07 to 02-15))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Valentine''s Set Menu', 'Every restaurant has a "special set menu" at double the price. Your date wants something romantic.', 'neutral', 0, 0, 0, 0, 'Heart', true, '02-07', '02-15', 'Valentine''s', '💘', 'Valentine''s'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Valentine''s Set Menu')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Book the set menu', 'Seven tiny courses and a violinist who will not leave. Very romantic. You are still hungry.', 160, 0, 1, 5, 0),
    ('Cook at home', 'You burn the first attempt and nail the second. Candles hide everything.', 30, 0, 2, 6, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 11. Anti-Valentine Party (season: Valentine's (02-07 to 02-15))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Anti-Valentine Party', 'Your single friends are throwing an anti-Valentine party. Dress code: "emotionally available".', 'neutral', 0, 0, 0, 0, 'Users', true, '02-07', '02-15', 'Valentine''s', '💘', 'Valentine''s'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Anti-Valentine Party')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go', 'Breakup-song karaoke until 2am. The healthiest thing you have done all year.', 20, 0, 1, 6, 0),
    ('Judge couples online', 'You scroll past 300 couple photos. You are fine. Totally fine.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 12. February 15th (season: Valentine's (02-07 to 02-15))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'February 15th', 'All the chocolate is 70% off today.', 'opportunity', 0, 0, 0, 0, 'Candy', true, '02-07', '02-15', 'Valentine''s', '💘', 'Valentine''s'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'February 15th')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy a year''s supply', 'You now own nine heart-shaped boxes. They last eleven days.', 25, 0, 1, 5, 0),
    ('Walk past', 'Your dentist would be proud. Your heart is a little sad.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 13. Keyboard Prank (season: April Fools (03-30 to 04-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Keyboard Prank', 'A colleague swapped every keyboard''s Y and Z keys. Today is deadline day.', 'neutral', 0, 0, 0, 0, 'Keyboard', true, '03-30', '04-02', 'April Fools', '🃏', 'April Fools'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Keyboard Prank')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Laugh and fix it', 'You type "zes" in a client email. The client thinks it is charming.', 0, 0, 1, 3, 0),
    ('Plot revenge', 'You wrap their whole desk in foil. HR sends a memo called "Fun Within Reason".', 0, 0, 2, 5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 14. Too Good to Be True (season: April Fools (03-30 to 04-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Too Good to Be True', 'An email says you''ve won a $1,000 gift card. You never entered anything. It is April 1st.', 'emergency', 0, 0, 0, 0, 'Mail', true, '03-30', '04-02', 'April Fools', '🃏', 'April Fools'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Too Good to Be True')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Click the link', 'It was not a gift card. Your bank calls about a $60 charge from a "premium fan club".', 60, 0, 1, -6, 0),
    ('Delete and report it', 'IT thanks you personally. You feel like a cybersecurity expert.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 15. Fake Engagement (season: April Fools (03-30 to 04-02))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Fake Engagement', 'Your best friend posts a fake engagement announcement as a joke. Your mum has already called their mum.', 'neutral', 0, 0, 0, 0, 'Smartphone', true, '03-30', '04-02', 'April Fools', '🃏', 'April Fools'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Fake Engagement')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Play along', 'The comments become legendary. Two aunties have already booked flights.', 0, 0, 1, 4, 0),
    ('Expose the prank', 'Correct, but boring. The aunties are disappointed. They wanted a wedding.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 16. Mid-Year Review (season: Halfway through the year (06-20 to 07-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Mid-Year Review', 'Your manager asks you to "reflect on your growth". You have reflected on nothing.', 'challenge', 0, 0, 0, 0, 'ClipboardCheck', true, '06-20', '07-10', 'Halfway through the year', '☀️', 'Halfway through the year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Mid-Year Review')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Prepare properly', 'Three pages of wins. They give you a small raise: $60 more a month.', 0, 0, 1, 2, 60),
    ('Wing it', 'You describe your growth as "vibes". Your manager writes something down.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 17. Halfway Check (season: Halfway through the year (06-20 to 07-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Halfway Check', 'Six months gone. Your savings goal for the year is at 23%.', 'neutral', 0, 0, 0, 0, 'PiggyBank', true, '06-20', '07-10', 'Halfway through the year', '☀️', 'Halfway through the year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Halfway Check')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Automate it', 'An automatic transfer every payday. Future you sends a thank-you note.', 0, 0, 1, 4, 0),
    ('"Next half will be different"', 'It will not be different. It will be the same, with more optimism.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 18. Long Weekend (season: Halfway through the year (06-20 to 07-10))
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, season_start, season_end, season_label, season_emoji, pack)
    SELECT 'Long Weekend', 'A long weekend is coming. A cheap trip costs $220. Your couch is free.', 'opportunity', 0, 0, 0, 0, 'Sun', true, '06-20', '07-10', 'Halfway through the year', '☀️', 'Halfway through the year'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Long Weekend')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go away', 'Sun, sea or snow: you come back feeling human again.', 220, 0, 1, 9, 0),
    ('Staycation', 'You sleep, read and discover your own city has a museum. Who knew.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 19. The Fourteenth Revision (drop: Side hustle chaos, live from 2026-11-30)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Fourteenth Revision', 'Your freelance client wants "just a few small changes". It is revision number fourteen.', 'challenge', 0, 0, 0, 0, 'Briefcase', true, '2026-11-30T00:00:00+00:00', 'Side hustle chaos'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Fourteenth Revision')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Charge for extra revisions', 'They grumble, then pay $120. You learn the most important word in freelancing: "scope".', 0, 120, 1, -2, 0),
    ('Do it for free', 'Revision fifteen arrives at midnight. It is the first version, but "bolder".', 0, 0, 2, -6, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 20. The Lowballer (drop: Side hustle chaos, live from 2026-11-30)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Lowballer', 'You listed a chair for $80. Someone offers $12 and asks if you can deliver.', 'neutral', 0, 0, 0, 0, 'Tag', true, '2026-11-30T00:00:00+00:00', 'Side hustle chaos'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Lowballer')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Counter at $70', 'They accept and bring their own van. Faith in humanity: slightly restored.', 0, 70, 1, 3, 0),
    ('Block them', 'Peace. The chair stays. You sit in it, angrily.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 21. Your Candles Went Viral (drop: Side hustle chaos, live from 2026-11-30)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Your Candles Went Viral', 'A video of your homemade candles has 800,000 views. You have nine candles.', 'opportunity', 0, 0, 0, 0, 'Flame', true, '2026-11-30T00:00:00+00:00', 'Side hustle chaos'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Your Candles Went Viral')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Take pre-orders', 'Two hundred orders. You pour wax until 3am for two weeks. Your flat smells incredible.', 0, 400, 1, -5, 0),
    ('Post "sold out"', 'Scarcity makes you look fancy. The nine candles sell for double.', 0, 90, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 22. The Building Group Chat (drop: Neighbours, live from 2026-12-07)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Building Group Chat', 'Your building''s group chat is 300 messages deep in an argument about who keeps taking parcels.', 'neutral', 0, 0, 0, 0, 'MessageCircle', true, '2026-12-07T00:00:00+00:00', 'Neighbours'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Building Group Chat')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Stay silent and read', 'You read every single message. Better than television.', 0, 0, 1, 1, 0),
    ('Post the culprit: a cat', 'It is the neighbour''s cat. The whole building unites. You are a hero.', 0, 0, 2, 6, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 23. The Ladder (drop: Neighbours, live from 2026-12-07)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Ladder', 'Your neighbour borrowed your ladder in March. It is now December.', 'challenge', 0, 0, 0, 0, 'Package', true, '2026-12-07T00:00:00+00:00', 'Neighbours'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Ladder')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Knock and ask', 'They return it with a jar of homemade jam and an apology. Excellent trade.', 0, 0, 1, 3, 0),
    ('Buy a new ladder', 'Two days later the old ladder appears outside your door. You now own two ladders.', 60, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 24. The Mystery Smell (drop: Neighbours, live from 2026-12-07)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Mystery Smell', 'Something in your flat smells terrible and you cannot find it.', 'emergency', 0, 0, 0, 0, 'Wind', true, '2026-12-07T00:00:00+00:00', 'Neighbours'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Mystery Smell')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Deep clean everything', 'Behind the fridge: a potato from another era. You light a candle in its memory.', 25, 0, 1, 4, 0),
    ('Open the windows and hope', 'The smell wins. You start spending a lot of evenings at friends'' places.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 25. Office Plant Politics (drop: Office life, live from 2026-12-14)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Office Plant Politics', 'The office plant is dying. Nobody waters it. Everybody has a theory.', 'neutral', 0, 0, 0, 0, 'Leaf', true, '2026-12-14T00:00:00+00:00', 'Office life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Office Plant Politics')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Adopt it', 'New pot, some sunlight, and it thrives. People start calling you "the plant whisperer".', 10, 0, 1, 4, 0),
    ('Let a meeting decide', 'There is now a watering rota. The plant dies during the meeting about the rota.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 26. Coffee Machine Down (drop: Office life, live from 2026-12-14)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Coffee Machine Down', 'The office coffee machine broke. The café downstairs charges $6 a cup.', 'challenge', 0, 0, 0, 0, 'Coffee', true, '2026-12-14T00:00:00+00:00', 'Office life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Coffee Machine Down')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Café every day', 'A month of excellent coffee and a month of $6 receipts.', 60, 0, 1, 3, 0),
    ('Bring a flask', 'Your flask becomes a personality trait. Colleagues ask for refills.', 15, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 27. Project Phoenix (drop: Office life, live from 2026-12-14)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Project Phoenix', 'You were added to a project called "Phoenix" by mistake. Nobody knows what Phoenix is.', 'neutral', 0, 0, 0, 0, 'UserPlus', true, '2026-12-14T00:00:00+00:00', 'Office life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Project Phoenix')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go to the meetings', 'Three weeks in, you discover Phoenix is a rebrand of the stapler policy.', 0, 0, 1, -3, 0),
    ('Quietly leave the chat', 'Nobody notices. Phoenix rises without you.', 0, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 28. The Sneaky Fee (drop: Money moves, live from 2026-12-21)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Sneaky Fee', 'You notice your bank charges $12 a month for an account you thought was free.', 'challenge', 0, 0, 0, 0, 'Landmark', true, '2026-12-21T00:00:00+00:00', 'Money moves'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Sneaky Fee')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Switch banks', 'An hour of forms, and now it really is free. That is $144 a year back.', 0, 0, 1, 3, 12),
    ('Complain online', 'The bank replies with a sad emoji and a link to its fees page.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 29. Round-Up Savings (drop: Money moves, live from 2026-12-21)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Round-Up Savings', 'Your banking app offers to round up every purchase and save the spare change.', 'opportunity', 0, 0, 0, 0, 'Coins', true, '2026-12-21T00:00:00+00:00', 'Money moves'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Round-Up Savings')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Turn it on', 'Coffee for $3.40? Sixty cents to savings. Painless and strangely satisfying.', 0, 0, 1, 4, 0),
    ('Maybe next month', 'You will not do it next month.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 30. A Friend's Hot Tip (drop: Money moves, live from 2026-12-21)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'A Friend''s Hot Tip', 'A friend swears a company is about to "moon". He has a spreadsheet and a lot of emojis.', 'neutral', 0, 0, 0, 0, 'TrendingUp', true, '2026-12-21T00:00:00+00:00', 'Money moves'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'A Friend''s Hot Tip')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Invest $200', 'It drops 30% by Friday. The spreadsheet had a typo.', 200, 0, 1, -3, 0),
    ('Stick with an index fund', 'Boring, sensible, growing. Your friend calls you a coward. Your friend is now very quiet.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 31. Only Calls When Moving (drop: Love and friends, live from 2026-12-28)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Only Calls When Moving', 'A friend calls for the first time in a year. They are moving house on Saturday.', 'challenge', 0, 0, 0, 0, 'Phone', true, '2026-12-28T00:00:00+00:00', 'Love and friends'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Only Calls When Moving')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Help them move', 'Eight hours, four flights of stairs, one pizza. "I owe you," they say. Neither of you believes it.', 0, 0, 1, -4, 0),
    ('Say you''re busy', 'You''re busy doing nothing. It''s glorious.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 32. Meet the Parents (drop: Love and friends, live from 2026-12-28)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Meet the Parents', 'Your partner''s parents invite you to dinner. Their family group chat has already studied your photos.', 'challenge', 0, 0, 0, 0, 'Users', true, '2026-12-28T00:00:00+00:00', 'Love and friends'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Meet the Parents')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Bring a nice gift', 'Flowers for one, good coffee for the other. You are invited to the next family holiday.', 45, 0, 1, 5, 0),
    ('Rely on charm', 'Your charm works on the dog. The parents are reserving judgement.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 33. The Reunion (drop: Love and friends, live from 2026-12-28)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Reunion', 'Your old class is having a reunion. Everyone will ask what you do now.', 'neutral', 0, 0, 0, 0, 'Users', true, '2026-12-28T00:00:00+00:00', 'Love and friends'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Reunion')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go, confidently', 'Half the class is still figuring it out too. You leave feeling surprisingly normal.', 40, 0, 1, 4, 0),
    ('Watch the photos online', 'Everyone looks successful in photos. Nobody looks like that in real life.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 34. The Therapy Waitlist (drop: Look after yourself, live from 2027-01-04)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Therapy Waitlist', 'You finally book therapy. The free waitlist is six weeks; a private session is $90.', 'neutral', 0, 0, 0, 0, 'HeartHandshake', true, '2027-01-04T00:00:00+00:00', 'Look after yourself'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Therapy Waitlist')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Pay for a private session', 'You talk for an hour and leave lighter than you arrived.', 90, 0, 1, 8, 0),
    ('Waitlist and journal', 'Six weeks of journaling. You fill a notebook with things you did not know you felt.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 35. Saturday Run Club (drop: Look after yourself, live from 2027-01-04)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Saturday Run Club', 'A free run club meets every Saturday at 7am. It is cold. It is very early.', 'opportunity', 0, 0, 0, 0, 'Footprints', true, '2027-01-04T00:00:00+00:00', 'Look after yourself'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Saturday Run Club')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go', 'You run 5k, get a free banana and make three friends. Saturdays feel different now.', 0, 0, 1, 6, 0),
    ('Stay in bed', 'You hear them run past your window. Smug, but also jealous.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 36. Screen Time Report (drop: Look after yourself, live from 2027-01-04)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Screen Time Report', 'Your phone says you averaged nine hours of screen time a day last week.', 'neutral', 0, 0, 0, 0, 'Smartphone', true, '2027-01-04T00:00:00+00:00', 'Look after yourself'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Screen Time Report')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Set app limits', 'Day one is awful. By day four you have read a whole book. Who are you?', 0, 0, 1, 4, 0),
    ('Turn off the report', 'Problem solved: you can no longer see the problem.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

commit;
