-- =============================================================================
-- 80 more life events (written in scripts/events/more_events.py; generate this file from it).
-- * 40 are live as soon as this runs.
-- * 40 arrive in 8 weekly drops of 5, every Monday from 11 Jan to 1 Mar 2027. Each one gets the
--   "✨ New" badge and is dealt first for two weeks (released_at, app/game/week_service.py).
-- Safe to re-run: events are skipped by title.
-- =============================================================================

begin;

-- 1. The Tipping Screen
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Tipping Screen', 'The café card machine swivels round: 18%, 22% or 25%. For a bottle of water from the fridge. The barista is watching.', 'neutral', 0, 0, 0, 0, 'CreditCard', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Tipping Screen')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Tap 25% and die inside', 'The barista says "have a great day!" with real warmth. You paid $1.25 for warmth.', 4, 0, 1, -1, 0),
    ('Press "No tip"', 'The screen goes silent. The barista goes silent. The music somehow goes silent.', 0, 0, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 2. Self-Checkout Showdown
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Self-Checkout Showdown', '"Unexpected item in the bagging area." There is nothing in the bagging area. There has never been anything in the bagging area.', 'neutral', 0, 0, 0, 0, 'ShoppingCart', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Self-Checkout Showdown')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Wave for help', 'A teenager types a six-digit code without looking. You feel like a medieval peasant meeting electricity.', 0, 0, 1, -1, 0),
    ('Abandon the shopping', 'You walk out with nothing but your dignity. Dinner is crackers and resentment.', 0, 0, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 3. The 7-Minute Voice Note
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The 7-Minute Voice Note', 'Your friend sent a 7-minute voice note. The first 40 seconds are wind.', 'neutral', 0, 0, 0, 0, 'MessageCircle', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The 7-Minute Voice Note')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Listen at 2x speed', 'They sound like a chipmunk confessing a crime. The actual news: they cut their fringe.', 0, 0, 1, 2, 0),
    ('Reply "omg 😭"', 'It works for everything. They reply "RIGHT??". You will never know what happened.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 4. Phone at 1%
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Phone at 1%', 'Your phone is on 1%. Your ride is 3 minutes away. Your charger is at home, smugly charging nothing.', 'challenge', 0, 0, 0, 0, 'Battery', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Phone at 1%')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy a $25 power bank', 'Overpriced, ugly, and your best friend now. You name it Gerald.', 25, 0, 1, 3, 0),
    ('Screenshot the map and pray', 'The phone dies at the roundabout. You navigate by vibes and arrive 20 minutes late, reborn.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 5. Autocorrect Betrayal
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Autocorrect Betrayal', 'You texted your manager "Sorry, running late, see you shirtly." It was not "shortly".', 'neutral', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Autocorrect Betrayal')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Send a correction', '"*shortly". Your manager replies "👀". The whole office knows by lunch.', 0, 0, 1, -2, 0),
    ('Commit to the bit', 'You arrive in your best shirt. Your manager laughs so hard they forget you were late.', 0, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 6. The Sneaker Drop
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Sneaker Drop', 'Limited trainers drop at 10am. 400 pairs. 80,000 people. Your thumb is ready.', 'challenge', 0, 0, 0, 0, 'ShoppingBag', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Sneaker Drop')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Enter the raffle', 'You lose to a bot named "xX_kicks_Xx". The bot has 400 pairs. Capitalism is undefeated.', 0, 0, 1, -2, 0),
    ('Buy from a reseller', 'You pay $380 for $120 shoes. You will never wear them in rain, which means you will never wear them.', 380, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 7. Concert Ticket Queue
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Concert Ticket Queue', 'You are number 48,213 in the ticket queue. The progress bar has not moved since Tuesday.', 'challenge', 0, 0, 0, 0, 'Ticket', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Concert Ticket Queue')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Wait it out', 'You get in at last. Only "obstructed view, behind pillar" is left. You buy it. You see one-third of the singer. Iconic third.', 140, 0, 1, 5, 0),
    ('Close the tab', 'Your friends send 90 videos from the concert. You watch all of them. Free, and painful.', 0, 0, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 8. Brunch Queue
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Brunch Queue', 'The brunch place everyone posts about has a 70-minute queue. The menu has a $19 slice of toast.', 'neutral', 0, 0, 0, 0, 'Utensils', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Brunch Queue')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Queue for the toast', 'It is genuinely incredible toast. You post it. 4 likes. One of them is your mum.', 38, 0, 1, 3, 0),
    ('Make eggs at home', 'Your eggs are rubbery but free. You take an aesthetic photo anyway. 6 likes. Mum again.', 6, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 9. The Free Gym Session
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Free Gym Session', 'The gym offers a free session with a personal trainer. His name is Blaze. He has never had a carb.', 'opportunity', 0, 0, 0, 0, 'Dumbbell', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Free Gym Session')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Do the session', 'Blaze shouts "ONE MORE" eleven times. You cannot sit down for three days. You feel amazing, eventually.', 0, 0, 1, 3, 0),
    ('Sign up for 12 sessions', 'Blaze becomes your hype man. You can now carry all the shopping in one trip. Worth it.', 360, 0, 2, 7, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 10. Smartwatch Judgement
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Smartwatch Judgement', 'Your smartwatch says "You have been sitting for 6 hours. Time to stand!" It is 11pm. You are in bed.', 'neutral', 0, 0, 0, 0, 'Activity', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Smartwatch Judgement')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Stand up, out of guilt', 'You stand in the dark like a lighthouse. The watch gives you a tiny trophy. Pathetically, it works.', 0, 0, 1, 2, 0),
    ('Turn off notifications', 'The watch is now a very expensive clock. Peace returns to the kingdom.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 11. The Sourdough Phase
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Sourdough Phase', 'A friend gives you a sourdough starter called "Doug". It needs feeding twice a day. It is basically a pet.', 'neutral', 0, 0, 0, 0, 'Flame', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Sourdough Phase')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Raise Doug', 'Your first loaf could stop a door. Your fifth could win awards. You stop buying bread.', 15, 0, 1, 5, 8),
    ('Let Doug go', 'Doug passes quietly at the back of the fridge. Your friend asks after him weekly.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 12. Air Fryer Evangelist
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Air Fryer Evangelist', 'Your coworker has mentioned their air fryer 31 times this week. Today they brought a printed brochure.', 'neutral', 0, 0, 0, 0, 'Zap', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Air Fryer Evangelist')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy one', 'It is, annoyingly, life-changing. You become the person who mentions their air fryer.', 90, 0, 1, 4, 0),
    ('Resist', 'You stay strong. They send you a recipe every morning at 6:14am.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 13. Your Friend Started a Podcast
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Your Friend Started a Podcast', 'Your friend started a podcast about "mindset". Episode 1 is 3 hours long. They want honest feedback.', 'neutral', 0, 0, 0, 0, 'Music', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Your Friend Started a Podcast')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Give honest feedback', '"Maybe a bit shorter?" Episode 2 is 4 hours. It is about feedback.', 0, 0, 1, -2, 0),
    ('Leave a 5-star review', 'You are thanked by name in Episode 3. Your mum hears it. She is so proud of you, somehow.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 14. The Business Opportunity
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Business Opportunity', 'An old school friend you haven''t spoken to in 6 years messages: "Hey hun!! Have you ever thought about being your own boss? 💕"', 'challenge', 0, 0, 0, 0, 'Rocket', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Business Opportunity')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Hear them out', 'It is a $500 starter kit of shakes. You are now "building an empire" from a garage full of shakes.', 500, 0, 1, -6, 0),
    ('"No thanks, hun 💕"', 'They reply "no worries! the offer stands 💕💕". The offer will stand forever.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 15. The AI Wrote It
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The AI Wrote It', 'You asked an AI to write your out-of-office. It wrote a 400-word poem about rest.', 'neutral', 0, 0, 0, 0, 'Laptop', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The AI Wrote It')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Use the poem', 'Clients love it. One replies with their own poem. You have accidentally started a movement.', 0, 0, 1, 4, 0),
    ('Write "Back Monday"', 'Efficient. Cold. Correct. Your inbox respects you.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 16. Gym Mirror Incident
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Gym Mirror Incident', 'You waved at someone in the gym mirror. They were waving at someone behind you. You both saw it happen.', 'neutral', 0, 0, 0, 0, 'Eye', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Gym Mirror Incident')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Pretend it was a stretch', 'Smooth arm stretch, then the other arm. Nobody is fooled. You do 4 extra sets out of shame.', 0, 0, 1, 1, 0),
    ('Change gyms', 'New gym, $10 more a month, zero witnesses.', 0, 0, 2, 2, -10)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 17. The Haunted Printer
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Haunted Printer', 'The office printer has started printing pages nobody sent. Today it printed a lasagne recipe.', 'neutral', 0, 0, 0, 0, 'Printer', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Haunted Printer')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Make the lasagne', 'It is the best lasagne of your life. The printer is now considered a colleague.', 22, 0, 1, 5, 0),
    ('Report it to IT', 'IT says "have you tried turning it off and on again". The printer prints "no".', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 18. Reply Guy Manager
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Reply Guy Manager', 'Your manager now replies to every message with just "?". Even "good morning" got a "?".', 'challenge', 0, 0, 0, 0, 'MessageSquare', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Reply Guy Manager')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Ask what "?" means', 'Turns out they think it''s a friendly wave. You teach them emojis. Morale up 40%.', 0, 0, 1, 4, 0),
    ('Reply with "?" too', 'A war of question marks begins. HR is cc''d. HR replies "?".', 0, 0, 2, -3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 19. Camera On, Unexpectedly
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Camera On, Unexpectedly', 'The meeting says "cameras on today!" You are in a hoodie with a face mask on. The green kind.', 'neutral', 0, 0, 0, 0, 'Video', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Camera On, Unexpectedly')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Turn it on anyway', 'You look like a swamp creature in finance. Your boss laughs. Your bond is permanent now.', 0, 0, 1, 3, 0),
    ('"My camera is broken"', 'Third time this month. IT sends you a $70 webcam. You are now trapped.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 20. The Salary Negotiation
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Salary Negotiation', 'You got a job offer elsewhere. Your manager says "let''s talk about what would make you stay".', 'opportunity', 0, 0, 0, 0, 'Briefcase', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Salary Negotiation')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Ask for 10% more', 'Long pause. "We can do 7." You say "8 and a better chair." You get both.', 0, 0, 1, 6, 160),
    ('Panic and say "it''s fine"', 'You walk out with nothing but a "we value you" and a branded water bottle.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 21. Open-Plan Microwave
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Open-Plan Microwave', 'Someone microwaved fish in the open-plan office. The smell has reached the third floor.', 'neutral', 0, 0, 0, 0, 'Wind', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Open-Plan Microwave')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Investigate', 'It was the CEO. You say nothing. You know too much now.', 0, 0, 1, 1, 0),
    ('Work from a café', 'Fish-free and productive, but the café coffees add up.', 18, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 22. Jury Duty Letter
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Jury Duty Letter', 'You have been called for jury duty. The letter says it could take "one to six weeks".', 'neutral', 0, 0, 0, 0, 'Mail', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Jury Duty Letter')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Serve', 'Week one: a stolen garden gnome. You take it very seriously. Justice is served, gnome is returned.', 0, 0, 1, 3, 0),
    ('Ask to postpone', 'Granted, for six months. Future you will deal with the gnome.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 23. Locked Out
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Locked Out', 'The door shuts. Your keys are inside, on the counter, mocking you.', 'emergency', 0, 0, 0, 0, 'Home', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Locked Out')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Call a locksmith', '$140 and 9 seconds of work. You ask how. He says "experience". You''ll never sleep again.', 140, 0, 1, -3, 0),
    ('Wait for your flatmate', 'Three hours on the stairs. You learn the life story of a neighbour''s cat.', 0, 0, 2, -5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 24. Phone Screen Crack
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Phone Screen Crack', 'You dropped your phone. Face down. On concrete. You lift it slowly, like an archaeologist.', 'emergency', 0, 0, 0, 0, 'Smartphone', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Phone Screen Crack')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Get the screen fixed', 'Good as new, $180 lighter. You buy a case that looks like a brick.', 180, 0, 1, 2, 0),
    ('Live with the spiderweb', 'Every text now looks threatening. You cut your thumb on a meme.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 25. Coffee on the Laptop
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Coffee on the Laptop', 'You knocked a full coffee over your laptop. It made a noise like a sad robot.', 'emergency', 0, 0, 0, 0, 'Laptop', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Coffee on the Laptop')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Repair shop', 'They save it, and your files. The technician asks if you take sugar. Not funny. Very funny.', 260, 0, 1, -2, 0),
    ('Rice and prayer', 'Two days in rice. It turns on, but the "E" key is gone. You now write lik this.', 0, 0, 2, -5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 26. The Parking Ticket
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Parking Ticket', 'You parked for "two minutes". You came back to a $65 ticket and a warden still writing.', 'challenge', 0, 0, 0, 0, 'Car', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Parking Ticket')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Pay it', 'Paid on time, so it''s only $65. Your wallet sighs.', 65, 0, 1, -2, 0),
    ('Appeal with a 3-page letter', 'Your letter includes a diagram. They cancel the ticket, possibly out of respect.', 0, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 27. Fridge Dies
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Fridge Dies', 'Your fridge died in the night. Everything inside is now "room-temperature food".', 'emergency', 0, 0, 0, 0, 'Box', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Fridge Dies')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy a new fridge', 'It hums, it lights up, it has an egg tray you''ll never use. Worth it.', 480, 0, 1, 2, 0),
    ('Second-hand from a neighbour', '$60 and slightly loud. You call it "The Generator". It keeps milk cold.', 60, 0, 2, 0, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 28. Heatwave
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Heatwave', 'It is 38°C. Your fan is just blowing hot air in a circle like a little hairdryer.', 'challenge', 0, 0, 0, 0, 'Sun', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Heatwave')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy an air conditioner', 'Bliss. Then the power bill comes: about $25 more a month all summer.', 320, 0, 1, 6, -25),
    ('Wet towels and suffering', 'You sleep under a damp towel like a burrito. You survive. Barely.', 0, 0, 2, -5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 29. Mystery Charge
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Mystery Charge', 'Your bank statement has a $49.99 charge from "BRX*SERV 7741". You have no idea what that is.', 'challenge', 0, 0, 0, 0, 'Receipt', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Mystery Charge')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Dispute it', 'It was a fake charge. The bank refunds it and sends you a new card. You feel like a detective.', 0, 50, 1, 4, 0),
    ('Assume you bought something', 'It renews every month. You never find out what it is.', 0, 0, 2, -2, -50)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 30. The Phishing Text
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Phishing Text', '"Your parcel could not be delivered. Pay $1.99 here: rnail-p0st.co." You are expecting a parcel.', 'emergency', 0, 0, 0, 0, 'AlertTriangle', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Phishing Text')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Report and delete', 'You forward it to your bank''s fraud team. Your parcel arrives the next day like nothing happened.', 0, 0, 1, 3, 0),
    ('Click the link', 'It wanted your card details. You cancel the card in time, but it costs a weekend of phone calls.', 30, 0, 2, -6, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 31. Credit Limit Raised
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Credit Limit Raised', 'Your bank says "Great news! We''ve raised your credit limit to $8,000!" It was not great news.', 'neutral', 0, 0, 0, 0, 'CreditCard', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Credit Limit Raised')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Ask them to lower it', 'The person on the phone has never been asked this. They need a manager. Respect.', 0, 0, 1, 3, 0),
    ('"Just for emergencies"', 'A sale is an emergency. A holiday is an emergency. You now pay $40 a month in interest.', 0, 0, 2, -3, -40)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 32. Extended Warranty
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Extended Warranty', 'You bought a $40 kettle. The cashier offers a 3-year warranty for $15. "Kettles fail all the time."', 'neutral', 0, 0, 0, 0, 'Receipt', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Extended Warranty')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy the warranty', 'The kettle outlives the warranty, the cashier and possibly you.', 15, 0, 1, -1, 0),
    ('Live dangerously', 'Three years, zero problems. You boil water like a rebel.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 33. The Retirement Email
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Retirement Email', 'HR emails: "Your employer matches pension contributions up to 5%." You have been ignoring this for a year.', 'opportunity', 0, 0, 0, 0, 'PiggyBank', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Retirement Email')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Sign up', 'Your take-home drops a bit, but free money appears in your pension. Future you does a little dance.', 0, 0, 1, 4, -60),
    ('"Retirement is ages away"', 'You just turned down free money. Somewhere, an economist faints.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 34. Payday Treat Logic
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Payday Treat Logic', 'It''s payday. You "deserve a treat". You also deserved one yesterday, and the day before.', 'challenge', 0, 0, 0, 0, 'Gift', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Payday Treat Logic')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('One small treat', 'A nice coffee and a pastry. Joy, contained.', 9, 0, 1, 3, 0),
    ('Treat yourself, properly', 'New trainers, takeaway, a candle called "Velvet Midnight". You need a treat to recover from the treat.', 220, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 35. Insurance Renewal
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Insurance Renewal', 'Your renewal quote went up 40%. Nothing changed. You are older, apparently that''s a crime now.', 'challenge', 0, 0, 0, 0, 'FileText', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Insurance Renewal')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Shop around', 'An hour on comparison sites. Same cover, $18 a month cheaper. You''re basically a hedge fund.', 0, 0, 1, 2, 18),
    ('Auto-renew', 'You pay the "loyalty" price. Loyalty is expensive.', 0, 0, 2, -2, -18)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 36. The Group Gift
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'The Group Gift', 'Someone in the office is leaving. A card is going round with a "suggested $20" for a gift. You''ve never met them.', 'neutral', 0, 0, 0, 0, 'Gift', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Group Gift')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Chip in $20', 'You write "Good luck with everything!!" Classic. Timeless. Meaningless.', 20, 0, 1, 1, 0),
    ('Sign without paying', 'Your name sits alone, uncovered by money. Everyone can see. Everyone.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 37. Stag & Hen Season
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Stag & Hen Season', 'Your friend''s bachelor weekend is abroad: flights, villa, matching T-shirts. Total: $900.', 'challenge', 0, 0, 0, 0, 'PartyPopper', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Stag & Hen Season')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go', 'Three days, zero sleep, one ruined T-shirt. Legendary memories you can''t fully remember.', 900, 0, 1, 6, 0),
    ('Join for one night only', 'You fly in for the dinner. Cheaper, still fun, and you miss the incident at the go-karts.', 300, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 38. Friend's Baby Shows Up
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Friend''s Baby Shows Up', 'A friend visits with their baby. The baby looks at you like it knows your bank balance.', 'neutral', 0, 0, 0, 0, 'Baby', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Friend''s Baby Shows Up')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Hold the baby', 'It falls asleep on you. You understand everything now. You also have a wet shoulder.', 0, 0, 1, 5, 0),
    ('Give a respectful wave', 'The baby cries. Message received. You were judged and found wanting.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 39. Sibling Borrowed Your Jacket
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Sibling Borrowed Your Jacket', 'Your sibling "borrowed" your favourite jacket. You just saw it on their Instagram. At a festival.', 'neutral', 0, 0, 0, 0, 'Shirt', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Sibling Borrowed Your Jacket')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Demand it back', 'It comes back smelling of festival. You will never know what happened to the pocket.', 0, 0, 1, -1, 0),
    ('Let it go, ask for a favour later', 'You now own a sibling IOU. Valuable currency in any family.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 40. Grandma's Envelope
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active)
    SELECT 'Grandma''s Envelope', 'Grandma slips you an envelope. "Don''t tell your mother." It feels thick.', 'opportunity', 0, 0, 0, 0, 'Gift', true
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Grandma''s Envelope')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Accept it graciously', '$100 in crisp notes and a handwritten "buy something sensible". You buy something sensible. Mostly.', 0, 100, 1, 5, 0),
    ('Refuse politely', 'She puts it in your coat pocket when you aren''t looking. Grandmas always win.', 0, 100, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 41. Train Strike (drop: Getting around, live from 2027-01-11)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Train Strike', 'Trains are on strike tomorrow. Your meeting is not on strike.', 'challenge', 0, 0, 0, 0, 'Clock', true, '2027-01-11T00:00:00+00:00', 'Getting around'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Train Strike')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Get a rideshare', 'Surge pricing: $58. The driver plays whale sounds. You arrive calm and broke.', 58, 0, 1, 1, 0),
    ('Ask to work from home', 'Granted. You attend in pyjama bottoms and a very serious shirt.', 0, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 42. The E-Scooter (drop: Getting around, live from 2027-01-11)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The E-Scooter', 'An e-scooter is parked outside. $1 to unlock, 30 cents a minute. You''ve never ridden one.', 'neutral', 0, 0, 0, 0, 'Zap', true, '2027-01-11T00:00:00+00:00', 'Getting around'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The E-Scooter')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Ride it', 'You go 4 metres, wobble, and scream. Then you get it. You arrive grinning and windswept.', 6, 0, 1, 4, 0),
    ('Walk like a normal person', 'A scooter overtakes you with someone screaming on it. You feel wise.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 43. Bike Stolen (drop: Getting around, live from 2027-01-11)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Bike Stolen', 'Your bike is gone. Only the lock remains, cut cleanly, like a message.', 'emergency', 0, 0, 0, 0, 'AlertTriangle', true, '2027-01-11T00:00:00+00:00', 'Getting around'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Bike Stolen')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy a second-hand bike', 'It''s a bit rusty but loyal. You buy a lock that weighs more than the bike.', 160, 0, 1, 1, 0),
    ('Take the bus', 'The bus is fine. The bus is fine. It''s $45 a month more, but the bus is fine.', 0, 0, 2, -3, -45)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 44. Missed the Last Bus (drop: Getting around, live from 2027-01-11)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Missed the Last Bus', 'The last bus leaves as you round the corner. The driver sees you. The driver does not stop.', 'challenge', 0, 0, 0, 0, 'Moon', true, '2027-01-11T00:00:00+00:00', 'Getting around'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Missed the Last Bus')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Taxi home', '$42. The driver tells you about his three ex-wives. You learn a lot.', 42, 0, 1, -1, 0),
    ('Walk the hour home', 'You discover a 24-hour bakery on the way. Life-changing croissant at 2am.', 3, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 45. Flat Tyre (drop: Getting around, live from 2027-01-11)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Flat Tyre', 'Your tyre is flat. Completely flat. Like your energy on a Monday.', 'emergency', 0, 0, 0, 0, 'Car', true, '2027-01-11T00:00:00+00:00', 'Getting around'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Flat Tyre')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Change it yourself', 'One video tutorial, two hours and one injured knuckle. You did it. You are unstoppable.', 0, 0, 1, 3, 0),
    ('Call roadside help', 'They arrive in 90 minutes and fix it in 4. $85. You watch respectfully.', 85, 0, 2, 0, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 46. Adopt a Cat? (drop: Pet life, live from 2027-01-18)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Adopt a Cat?', 'The shelter posted a one-eyed cat called Admiral Whiskers. He has been there 200 days.', 'opportunity', 0, 0, 0, 0, 'Heart', true, '2027-01-18T00:00:00+00:00', 'Pet life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Adopt a Cat?')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Adopt the Admiral', 'He sleeps on your keyboard and judges your choices. Food and litter: about $40 a month. Your heart: full.', 120, 0, 1, 8, -40),
    ('Share the post instead', 'Someone else adopts him. You see photos. He looks happy. You are happy. Mostly.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 47. The Vet Bill (drop: Pet life, live from 2027-01-18)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Vet Bill', 'Your dog ate a sock. A whole sock. He looks proud.', 'emergency', 0, 0, 0, 0, 'Activity', true, '2027-01-18T00:00:00+00:00', 'Pet life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Vet Bill')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Rush to the vet', 'The sock is retrieved. The bill is $420. The dog wags like he''s won.', 420, 0, 1, -2, 0),
    ('Wait and watch', 'The sock reappears two days later, in the garden. You do not talk about it.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 48. Cat vs. Glass (drop: Pet life, live from 2027-01-18)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Cat vs. Glass', 'Your cat is slowly pushing a full glass of water towards the edge of the table, looking at you.', 'neutral', 0, 0, 0, 0, 'Eye', true, '2027-01-18T00:00:00+00:00', 'Pet life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Cat vs. Glass')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Save the glass', 'You lunge. The cat waits until you sit down, then does it again. You have lost.', 0, 0, 1, -1, 0),
    ('Let it happen', 'Crash. The cat walks away, satisfied. You both know who runs this house.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 49. Pet-Sitting a Friend's Parrot (drop: Pet life, live from 2027-01-18)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Pet-Sitting a Friend''s Parrot', 'Your friend asks you to watch their parrot for a week. It knows four swear words and your name now.', 'neutral', 0, 0, 0, 0, 'Bird', true, '2027-01-18T00:00:00+00:00', 'Pet life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Pet-Sitting a Friend''s Parrot')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Say yes', 'The parrot learns your ringtone. Your friend pays you $80 and a bottle of wine.', 0, 80, 1, 2, 0),
    ('Politely decline', 'Your friend finds someone else. The parrot apparently says your name anyway.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 50. Dog Walking Side Gig (drop: Pet life, live from 2027-01-18)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Dog Walking Side Gig', 'A neighbour asks if you could walk their two huskies every evening. They pay $15 a walk.', 'opportunity', 0, 0, 0, 0, 'Footprints', true, '2027-01-18T00:00:00+00:00', 'Pet life'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Dog Walking Side Gig')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Take the job', 'The huskies walk you, mostly. You get fit, and about $120 more a month.', 0, 0, 1, 3, 120),
    ('Keep your evenings', 'The huskies howl when you pass. It feels personal.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 51. Payday Fake-Out (drop: Payday, live from 2027-01-25)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Payday Fake-Out', 'You checked your account at midnight. Payday hasn''t landed. You checked again at 12:01.', 'neutral', 0, 0, 0, 0, 'Clock', true, '2027-01-25T00:00:00+00:00', 'Payday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Payday Fake-Out')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Refresh until it lands', 'It lands at 6:43am. You saw every minute of the night. You feel rich and terrible.', 0, 0, 1, -3, 0),
    ('Go to sleep like an adult', 'You wake up and it''s there. Like magic. Like Christmas. Like a functioning adult.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 52. The Budget Spreadsheet (drop: Payday, live from 2027-01-25)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Budget Spreadsheet', 'You made a budget spreadsheet with colours and formulas. It looks like a work of art.', 'opportunity', 0, 0, 0, 0, 'FileText', true, '2027-01-25T00:00:00+00:00', 'Payday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Budget Spreadsheet')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Actually follow it', 'Month one: you find $70 of subscriptions you forgot. The spreadsheet pays for itself.', 0, 0, 1, 3, 70),
    ('Admire it and close it', 'You open it once a month to change the colours. It is a beautiful lie.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 53. The Emergency Fund (drop: Payday, live from 2027-01-25)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Emergency Fund', 'A money video says you should have 3 months of costs saved "for emergencies". You have $36.', 'challenge', 0, 0, 0, 0, 'PiggyBank', true, '2027-01-25T00:00:00+00:00', 'Payday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Emergency Fund')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Move $300 to savings', 'Your current account feels lighter. Your shoulders feel lighter too. Interesting.', 0, 0, 1, 5, 0),
    ('Watch another money video', 'This one says to buy a yacht and rent it out. You don''t have a yacht. Or a plan.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 54. Payday Group Dinner (drop: Payday, live from 2027-01-25)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Payday Group Dinner', 'It''s payday, so the group chat wants dinner at the new steakhouse. Mains start at $48.', 'neutral', 0, 0, 0, 0, 'Utensils', true, '2027-01-25T00:00:00+00:00', 'Payday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Payday Group Dinner')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go big', 'Steak, dessert, a cocktail with smoke coming out of it. You leave a different person, but poorer.', 110, 0, 1, 5, 0),
    ('Suggest the noodle place', 'Everyone pretends to be annoyed, then has the best night. Noodle place forever.', 25, 0, 2, 4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 55. Split the Bill Evenly? (drop: Payday, live from 2027-01-25)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Split the Bill Evenly?', 'You had a salad and tap water. Someone across from you ordered lobster. "Let''s just split it evenly!"', 'challenge', 0, 0, 0, 0, 'Divide', true, '2027-01-25T00:00:00+00:00', 'Payday'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Split the Bill Evenly?')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Split it', '$74 for a salad. Your lettuce now has a mortgage.', 74, 0, 1, -3, 0),
    ('Pay for what you had', 'Awkward pause, then two others do the same. You started a revolution.', 18, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 56. The Cleaning Fee (drop: Holiday mode, live from 2027-02-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Cleaning Fee', 'The holiday flat is $80 a night. Then a $90 cleaning fee. Then a $40 service fee. Then a "vibes" fee.', 'challenge', 0, 0, 0, 0, 'Home', true, '2027-02-01T00:00:00+00:00', 'Holiday mode'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Cleaning Fee')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Book it anyway', 'Lovely flat. The checkout list asks you to clean, strip the beds and take the bins out. For the cleaning fee.', 410, 0, 1, 4, 0),
    ('Book a hotel', 'Slightly smaller, but breakfast is included and nobody asks you to vacuum.', 360, 0, 2, 5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 57. Lost Luggage (drop: Holiday mode, live from 2027-02-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Lost Luggage', 'You arrive. Your suitcase does not. The screen says it is "in transit", which means nobody knows.', 'emergency', 0, 0, 0, 0, 'Package', true, '2027-02-01T00:00:00+00:00', 'Holiday mode'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Lost Luggage')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy emergency clothes', 'Your holiday photos are all in one souvenir T-shirt. Committed to the theme.', 120, 0, 1, -2, 0),
    ('Wait at the airport', 'It arrives on the last day. It went on holiday without you. It looks rested.', 0, 0, 2, -5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 58. Timeshare Pitch (drop: Holiday mode, live from 2027-02-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Timeshare Pitch', 'A smiling man offers a "free" breakfast and boat trip. You just need to listen to a "quick presentation".', 'neutral', 0, 0, 0, 0, 'Ticket', true, '2027-02-01T00:00:00+00:00', 'Holiday mode'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Timeshare Pitch')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go for the free breakfast', 'Four hours in a windowless room. You leave with a croissant and no timeshare. Undefeated.', 0, 0, 1, -3, 0),
    ('Keep walking', 'He follows you for two streets, then gives up. You eat breakfast in peace, and you pay for it.', 14, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 59. Sunburn (drop: Holiday mode, live from 2027-02-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Sunburn', 'You fell asleep on the beach. You are now two colours. Your back looks like a strawberry.', 'neutral', 0, 0, 0, 0, 'Sun', true, '2027-02-01T00:00:00+00:00', 'Holiday mode'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Sunburn')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy aloe gel', 'Sticky but cool. You walk like a robot for two days.', 12, 0, 1, 0, 0),
    ('Tough it out', 'You sleep standing up like a horse. You learn about suncream the hard way.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 60. Airport Snacks (drop: Holiday mode, live from 2027-02-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Airport Snacks', 'At the airport, a bottle of water costs $6 and a sandwich costs $14. The sandwich is mostly bread.', 'neutral', 0, 0, 0, 0, 'Plane', true, '2027-02-01T00:00:00+00:00', 'Holiday mode'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Airport Snacks')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Buy the sandwich', 'Three slices of tomato, emotional damage. You eat it slowly to make it last.', 20, 0, 1, -1, 0),
    ('Bring snacks from home next time', 'You arrive with a backpack full of crackers. Other travellers look at you with envy.', 4, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 61. The Cold Plunge (drop: Wellness era, live from 2027-02-08)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Cold Plunge', 'Everyone online is doing cold plunges. Your friend invites you to try one. It''s 3°C.', 'neutral', 0, 0, 0, 0, 'Droplets', true, '2027-02-08T00:00:00+00:00', 'Wellness era'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Cold Plunge')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Get in', 'You make a sound that only dolphins can hear. You feel incredible. You never do it again.', 20, 0, 1, 5, 0),
    ('Hold their towel', 'You watch them scream. You feel incredible without getting wet.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 62. The Meditation App (drop: Wellness era, live from 2027-02-08)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Meditation App', 'Your meditation app says "Day 1 of 365". The voice is so calm it''s slightly sinister.', 'opportunity', 0, 0, 0, 0, 'Moon', true, '2027-02-08T00:00:00+00:00', 'Wellness era'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Meditation App')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Pay for the year', '$70. You use it 9 times. Those 9 times were very calm.', 70, 0, 1, 4, 0),
    ('Free version only', 'Ten minutes a day, plus adverts for the full version. Still calmer.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 63. Running Club Speed (drop: Wellness era, live from 2027-02-08)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Running Club Speed', 'You joined a "social, all-levels" running club. Everyone is running at the speed of a motorbike.', 'challenge', 0, 0, 0, 0, 'Footprints', true, '2027-02-08T00:00:00+00:00', 'Wellness era'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Running Club Speed')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Keep up', 'You keep up for 600 metres, then see your ancestors. You''re fitter by the month''s end.', 0, 0, 1, 3, 0),
    ('Join the walking group', 'They are hilarious and also bring cake. The best mistake of your life.', 5, 0, 2, 5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 64. The Dentist Floss Question (drop: Wellness era, live from 2027-02-08)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Dentist Floss Question', 'The dentist asks how often you floss. You both know. You both know.', 'neutral', 0, 0, 0, 0, 'Smile', true, '2027-02-08T00:00:00+00:00', 'Wellness era'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Dentist Floss Question')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Tell the truth', '"Twice. This year." The dentist nods sadly. Somehow it''s therapeutic.', 0, 0, 1, 2, 0),
    ('Lie confidently', '"Every day." Your gums bleed in protest. The dentist writes something down.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 65. Sleep Tracker Data (drop: Wellness era, live from 2027-02-08)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Sleep Tracker Data', 'Your sleep tracker says you got "4 hours of poor-quality sleep" and recommends "rest".', 'neutral', 0, 0, 0, 0, 'Activity', true, '2027-02-08T00:00:00+00:00', 'Wellness era'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Sleep Tracker Data')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Go to bed at 10', 'You lie awake thinking about going to bed at 10. Eventually it works. You feel human.', 0, 0, 1, 5, 0),
    ('Scroll at 1am again', 'The tracker gives you a red sad face. You screenshot it and post it. 12 likes.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 66. Sell Old Clothes Online (drop: Side hustle, live from 2027-02-15)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Sell Old Clothes Online', 'Your wardrobe is overflowing. An app says people will pay for your old stuff.', 'opportunity', 0, 0, 0, 0, 'Shirt', true, '2027-02-15T00:00:00+00:00', 'Side hustle'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Sell Old Clothes Online')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('List 20 items', 'You sell 14 things. The 15th buyer sends a 2,000-word message about a stain. Still, $210.', 0, 210, 1, 3, 0),
    ('Keep everything "just in case"', 'The case never comes. The wardrobe door now needs a shoulder.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 67. Weekend Market Stall (drop: Side hustle, live from 2027-02-15)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Weekend Market Stall', 'A friend says you should sell your homemade candles at the weekend market. The stall costs $50.', 'opportunity', 0, 0, 0, 0, 'Flame', true, '2027-02-15T00:00:00+00:00', 'Side hustle'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Weekend Market Stall')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Book the stall', 'Slow morning, then a rush. You sell out. A small business is born: about $90 a month.', 50, 0, 1, 4, 90),
    ('Stick to giving them as gifts', 'Your friends now own 11 of your candles each. They smell of love and slight panic.', 0, 0, 2, 1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 68. Rideshare Rating (drop: Side hustle, live from 2027-02-15)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Rideshare Rating', 'You drove for a rideshare app this weekend. A passenger gave you 3 stars for "music choice".', 'neutral', 0, 0, 0, 0, 'Car', true, '2027-02-15T00:00:00+00:00', 'Side hustle'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Rideshare Rating')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Change the playlist', 'You switch to calm piano. Ratings rise to 4.9. You now hate calm piano.', 0, 0, 1, -1, 0),
    ('Stay true to your music', 'Two passengers ask for the playlist. One dances. Art always finds its audience.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 69. The Viral Recipe (drop: Side hustle, live from 2027-02-15)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Viral Recipe', 'You posted a 20-second recipe video. It has 400,000 views. Brands are emailing.', 'opportunity', 0, 0, 0, 0, 'Video', true, '2027-02-15T00:00:00+00:00', 'Side hustle'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Viral Recipe')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Do a paid post', '$300 to hold a spatula and smile. You smile so hard your face hurts.', 0, 300, 1, 3, 0),
    ('Post another recipe', 'It gets 41 views. The internet is a fickle god.', 0, 0, 2, -2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 70. Freelance Scope Creep (drop: Side hustle, live from 2027-02-15)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Freelance Scope Creep', 'A client paid you for "one quick logo". This is now revision 17. They want it to feel "more purple, but not purple".', 'challenge', 0, 0, 0, 0, 'Hammer', true, '2027-02-15T00:00:00+00:00', 'Side hustle'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Freelance Scope Creep')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Charge for extra revisions', 'They say "of course!" immediately. You should have done this 16 revisions ago.', 0, 180, 1, 4, 0),
    ('Keep going for free', 'Revision 24: they pick revision 1. You stare at a wall for some time.', 0, 0, 2, -6, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 71. Landlord Inspection (drop: Home admin, live from 2027-02-22)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Landlord Inspection', 'Your landlord is coming tomorrow for an "inspection". Your flat looks like a crime scene with candles.', 'challenge', 0, 0, 0, 0, 'ClipboardCheck', true, '2027-02-22T00:00:00+00:00', 'Home admin'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Landlord Inspection')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Clean all night', 'The landlord says "lovely" and leaves after 4 minutes. You cleaned behind the oven for 4 minutes.', 15, 0, 1, -3, 0),
    ('Hide everything in the wardrobe', 'He opens the wardrobe. Of course he does. He says nothing. He doesn''t need to.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 72. Washing Machine Flood (drop: Home admin, live from 2027-02-22)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Washing Machine Flood', 'The washing machine started walking across the kitchen during the spin cycle. Then it leaked.', 'emergency', 0, 0, 0, 0, 'Droplets', true, '2027-02-22T00:00:00+00:00', 'Home admin'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Washing Machine Flood')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Call a repair person', '$130 to replace a part the size of a coin. The machine stays where it is now.', 130, 0, 1, -1, 0),
    ('Hand-wash for a while', 'You wash jeans in the bath like a Victorian. You develop forearms of steel.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 73. The Deposit Return (drop: Home admin, live from 2027-02-22)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Deposit Return', 'You moved out. The old landlord kept $300 of your deposit for "general wear". The wear was general.', 'challenge', 0, 0, 0, 0, 'Wallet', true, '2027-02-22T00:00:00+00:00', 'Home admin'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Deposit Return')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Dispute it with photos', 'You sent move-in photos. The deposit scheme sides with you. Full refund. Justice.', 0, 300, 1, 5, 0),
    ('Let it go', 'You let it go. You do not let it go. You think about it in the shower for a year.', 0, 0, 2, -4, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 74. Energy Bill Shock (drop: Home admin, live from 2027-02-22)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Energy Bill Shock', 'Your energy bill arrived. It''s double last month''s. Your flatmate has been running a heater in the bathroom 24/7.', 'challenge', 0, 0, 0, 0, 'Zap', true, '2027-02-22T00:00:00+00:00', 'Home admin'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Energy Bill Shock')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Have The Talk', 'Uncomfortable, but the heater goes. Your bill drops back. You both survive the conversation.', 0, 0, 1, 2, 30),
    ('Pay and say nothing', 'Your bathroom is warm. Your bank is not.', 0, 0, 2, -3, -30)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 75. The Flat Viewing (drop: Home admin, live from 2027-02-22)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Flat Viewing', 'The listing said "cosy, characterful, two-bed". In person: the second bedroom is a cupboard with a window.', 'neutral', 0, 0, 0, 0, 'Home', true, '2027-02-22T00:00:00+00:00', 'Home admin'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Flat Viewing')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Ask about the cupboard', 'The agent says "it''s a study". You say "it''s a cupboard". The agent says "it''s a study". You leave.', 0, 0, 1, 1, 0),
    ('Make an offer anyway', 'You now live in a cosy, characterful cupboard. Rent is lower at least.', 0, 0, 2, -2, 40)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 76. Mum's Password (drop: Family tech support, live from 2027-03-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Mum''s Password', 'Mum calls. She forgot her email password. Again. The new one was "Password2".', 'neutral', 0, 0, 0, 0, 'Phone', true, '2027-03-01T00:00:00+00:00', 'Family tech support'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Mum''s Password')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Set up a password manager', 'Forty minutes, three cups of tea, and now she''s safer than you. She tells everyone.', 0, 0, 1, 3, 0),
    ('Write it on a sticky note', 'She sticks it on the screen. Her neighbour now knows her email password.', 0, 0, 2, -1, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 77. Dad's Forwarded Messages (drop: Family tech support, live from 2027-03-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Dad''s Forwarded Messages', 'Dad forwarded you "URGENT: share with 10 people or lose your WhatsApp". It''s his ninth one today.', 'neutral', 0, 0, 0, 0, 'MessageSquare', true, '2027-03-01T00:00:00+00:00', 'Family tech support'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Dad''s Forwarded Messages')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Explain it''s fake', 'He says "better safe than sorry" and forwards it to you again.', 0, 0, 1, -2, 0),
    ('Send him a funny dog video', 'He forwards that to 40 people. You are now responsible for the family''s mood.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 78. The Family TV (drop: Family tech support, live from 2027-03-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'The Family TV', 'Your parents bought a new smart TV. The remote has 74 buttons. They have called you 6 times.', 'challenge', 0, 0, 0, 0, 'Video', true, '2027-03-01T00:00:00+00:00', 'Family tech support'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'The Family TV')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Drive over and set it up', 'Two hours, one tank of petrol, and you get fed like royalty. Fair trade.', 25, 0, 1, 5, 0),
    ('Talk them through it by phone', '"Press the home button." "Which one is home?" "The house." "There''s no house." Three hours.', 0, 0, 2, -5, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 79. Grandpa Discovered Emoji (drop: Family tech support, live from 2027-03-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Grandpa Discovered Emoji', 'Grandpa learned emoji. He now ends every message with 🍆 because he thinks it''s a "nice purple vegetable".', 'neutral', 0, 0, 0, 0, 'Smile', true, '2027-03-01T00:00:00+00:00', 'Family tech support'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Grandpa Discovered Emoji')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Explain gently', 'There is a long silence on the phone. Then he laughs for 10 minutes. Best call of your year.', 0, 0, 1, 5, 0),
    ('Let him keep going', 'He sends it to the vicar. The family group chat explodes.', 0, 0, 2, 2, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

-- 80. Cousin Wants to "Pick Your Brain" (drop: Family tech support, live from 2027-03-01)
WITH e AS (
    INSERT INTO life_events (title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active, released_at, pack)
    SELECT 'Cousin Wants to "Pick Your Brain"', 'Your cousin wants to "pick your brain" about starting a business. It''s the third time. They never start the business.', 'neutral', 0, 0, 0, 0, 'HelpCircle', true, '2027-03-01T00:00:00+00:00', 'Family tech support'
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = 'Cousin Wants to "Pick Your Brain"')
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
    ('Charge for a coffee', '"Brain-picking costs a flat white." They agree. You have the same chat. At least you got coffee.', 0, 6, 1, 2, 0),
    ('Pick their brain back', 'You ask about their budget. They change the subject. Peace achieved.', 0, 0, 2, 3, 0)
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);

commit;
