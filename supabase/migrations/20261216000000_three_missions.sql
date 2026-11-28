-- =============================================================================
-- Three more missions (written in scripts/missions/more_missions.py; generate this file from it):
-- Credit Comeback (credit score), Money While You Sleep (passive income), Diamond Hands (holding).
-- Safe to run more than once.
-- =============================================================================
begin;

-- ===== Credit Comeback =====
insert into public.integrated_missions (name, description, short_description, icon, category, difficulty, duration_months, learning_objectives, completion_reward, can_buy_lifestyle_items, max_loan_amount)
values ('Credit Comeback', 'Your credit score is a reputation you build one payment at a time. Take small loans, never miss, and get past 665. Only payments move the score: Quick Cash plus Emergency Fund gets you there, one of them alone will not.', 'Borrow small. Repay on time. Watch your score climb.', '💳', 'debt_management', 'beginner', 8, array['How a credit score moves', 'Borrow only what you can repay', 'What missed payments cost', 'Why lenders look at your debt-to-income'], 750, false, 2000)
on conflict (name) do nothing;

insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 'credit_score', 665, 'greater_than', 'Credit score above 665', 'About 8 on-time payments from where you start.', '💳')
on conflict (mission_id, metric) do nothing;

insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 'debt_ratio', 0.2, 'less_than', 'Loan payments under 20% of income', 'Lenders like room to breathe.', '⚖️')
on conflict (mission_id, metric) do nothing;

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 1, 'The First Loan', 'You want a score, and a score needs history. How do you start?', 'Payments build credit, not borrowing itself.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 1), v.* from (values
    ('Set up auto-pay first', 'Then borrow. Boring, brilliant.', 0, 2, 0, 4, 'low', 1),
    ('Borrow now, sort it out later', 'Future you loves surprises.', 0, 1, 4, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 1));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 2, 'The Store Card', 'The cashier offers a store card with 10% off today. The rate is 34%.', 'A discount is not worth a high rate.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 2), v.* from (values
    ('"No thanks"', 'You pay full price and sleep well.', 0, 1, 0, 3, 'low', 1),
    ('Sign up for the 10%', 'You save $12 and gain a $30 fee.', -18, 2, 2, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 2));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 3, 'A Tight Month', 'The payment is due and your wallet is thin.', 'Pay on time first; everything else can wait a week.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 3), v.* from (values
    ('Skip takeaway, pay on time', 'Beans again. Heroic beans.', 40, -2, 0, 4, 'low', 1),
    ('Pay late, "just this once"', 'A late fee and a stern email.', -35, 0, 5, -2, 'high', 2),
    ('Sell some old stuff', 'Goodbye, third pair of headphones.', 60, 1, 1, 2, 'low', 3)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 3));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 5, 'Check Your Report', 'You can see your credit report for free.', 'Errors happen. Check your report.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 5), v.* from (values
    ('Read it line by line', 'You find a phone contract you never had, and dispute it.', 0, 2, 1, 4, 'low', 1),
    ('Ignorance is bliss', 'Bliss, with mystery debts.', 0, 1, 0, -2, 'medium', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 5));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 7, 'The Offer Letter', '"Congratulations! You are pre-approved for $20,000!"', 'Pre-approved is not the same as affordable.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 7), v.* from (values
    ('Shred it', 'Satisfying noise. Strong character.', 0, 3, 0, 3, 'low', 1),
    ('"Just to see the terms"', 'Three calls a day, forever.', 0, 0, 4, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Credit Comeback') and month = 7));

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 'A Blank Page', '📄', 'To a bank you are a mystery: no history, no reputation, no vibes. Time to write the first page.', 'opening', 'month', 1, 'Your score starts at 650. Take a small loan from The Bank.', 0, 0, 0, 6, 1)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 'The Score Moves', '📈', 'You check your score for the ninth time today. It has gone UP. You tell a stranger on the bus.', 'milestone', 'month', 4, 'Each on-time payment adds 2 points.', 0, 4, 0, 4, 2)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Credit Comeback'), 'Your Friend Wants a Co-signer', '🙃', '"It is just a signature," says your friend, who once lost a canoe. Co-signing means their debt is yours.', 'crisis', 'month', 6, 'You politely decline. The canoe comes up.', 0, -1, 3, 0, 3)
on conflict (mission_id, display_order) do nothing;

-- ===== Money While You Sleep =====
insert into public.integrated_missions (name, description, short_description, icon, category, difficulty, duration_months, learning_objectives, completion_reward, can_buy_lifestyle_items)
values ('Money While You Sleep', 'A salary stops when you stop. Assets keep paying. Build small businesses until they earn more than $150 a month and are worth over $2,500. Lifestyle shopping is closed: every spare coin has a job.', 'Build income that arrives without a shift.', '😴', 'passive_income', 'intermediate', 6, array['Assets pay you, liabilities charge you', 'Reinvest profit', 'Payback time', 'Why one income is a risk'], 1500, false)
on conflict (name) do nothing;

insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 'passive_income', 150, 'greater_than', 'Over $150 a month while you sleep', 'Count what your businesses earn.', '😴')
on conflict (mission_id, metric) do nothing;

insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 'business_value', 2500, 'greater_than', 'Businesses worth over $2,500', 'Start small: a kiosk or a juice stand.', '🏪')
on conflict (mission_id, metric) do nothing;

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 1, 'Pick Your First Hustle', 'You have a little money and big ideas.', 'Check how long it takes to earn back what you pay.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 1), v.* from (values
    ('Do the maths first', 'Napkin sums: pays back in about two years. Solid.', 0, 1, 0, 5, 'low', 1),
    ('Go with the vibes', 'The vibes recommend a candle shop for dogs.', -60, 3, 2, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 1));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 2, 'The First Profit', 'Your business paid you. Real money. While you were asleep.', 'Reinvesting profit is how small becomes big.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 2), v.* from (values
    ('Save it for the next one', 'The empire grows by exactly one brick.', 0, 1, 0, 5, 'low', 1),
    ('Celebrate properly', 'A dinner costing slightly more than the profit.', -80, 5, 0, 0, 'medium', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 2));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 3, 'Broken Equipment', 'Your busiest machine makes a noise like a sad goose.', 'Keep a repair fund: assets need looking after.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 3), v.* from (values
    ('Repair it properly', 'The goose is silenced.', -120, 0, 0, 3, 'low', 1),
    ('Tape and hope', 'It holds. Mostly. Customers ask about the goose.', 0, 0, 4, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 3));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 4, 'The Guru', 'A man in a rented sports car sells a course: "$10k a month, no work".', 'If it needs no work and cannot fail, it is selling you.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 4), v.* from (values
    ('Walk away', 'He calls you "poor-minded". You keep your money.', 0, 2, 0, 3, 'low', 1),
    ('Buy the course', 'Page one: "sell this course to others".', -300, 0, 4, -2, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 4));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 5, 'Second Stream', 'One business is nice. What about two?', 'Different income streams rarely all fail at once.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 5), v.* from (values
    ('Add something different', 'Coffee in the morning, laundry at night.', 0, 2, 1, 4, 'medium', 1),
    ('Another of the same', 'Two identical stands, 40 metres apart. They compete.', 0, 0, 2, 1, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Money While You Sleep') and month = 5));

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 'Clocking Out Forever?', '⏰', 'Your alarm rings. You dream of money that does not need one.', 'opening', 'month', 1, 'Buy businesses from Investments.', 0, 0, 0, 6, 1)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 'A Slow Month', '🌧️', 'It rained for nine days. Nobody wants juice in a flood. Businesses swing: that is the deal.', 'crisis', 'month', 3, 'Profit varies month to month.', 0, -2, 3, 0, 2)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Money While You Sleep'), 'A Regular Customer', '🥹', 'Someone orders "the usual". You have a usual. You are basically a landmark.', 'milestone', 'month', 5, 'Steady customers, steady income.', 0, 6, 0, 4, 3)
on conflict (mission_id, display_order) do nothing;

-- ===== Diamond Hands =====
insert into public.integrated_missions (name, description, short_description, icon, category, difficulty, duration_months, learning_objectives, completion_reward, can_sell_assets, can_take_loans)
values ('Diamond Hands', 'Markets crash, friends panic and your thumb hovers over "sell". For eight months you cannot sell or borrow. Keep over $5,000 invested at the end, however loud it gets. Spread it out: one bet can sink the lot.', 'Invest, then do the hardest thing: wait.', '💎', 'investment', 'advanced', 8, array['Time in the market', 'Diversification', 'Investing a little regularly', 'Hype and panic are expensive'], 2000, false, false)
on conflict (name) do nothing;

insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 'asset_value', 5000, 'greater_than', 'Over $5,000 invested at the end', 'Today''s prices count, so leave some margin.', '💎')
on conflict (mission_id, metric) do nothing;

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 1, 'The Plan', 'How will you put your money in?', 'Investing regularly beats guessing the perfect day.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 1), v.* from (values
    ('A little every month', 'Dull. Effective. Your future self sends a fruit basket.', 0, 1, 0, 5, 'low', 1),
    ('Wait for the perfect moment', 'You watch charts until 3am. The moment does not text back.', 0, 0, 4, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 1));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 2, 'All Eggs', 'One coin is up 40% this week. Put everything in?', 'Spreading money across things softens the falls.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 2), v.* from (values
    ('Spread it out', 'Stocks, a property, a business. Sensible shoes for money.', 0, 1, 0, 3, 'low', 1),
    ('ALL IN', 'You name the coin. Never name the coin.', 0, 4, 5, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 2));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 4, 'Fees', 'Your app offers "premium trading" for $15 a month.', 'Small fees compound too, the wrong way.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 4), v.* from (values
    ('Keep it simple', 'No fee, no confetti, same market.', 0, 1, 0, 2, 'low', 1),
    ('Go premium', 'The charts are now in dark mode. Worth it?', -45, 2, 0, 0, 'medium', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 4));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 6, 'The Group Chat Is Screaming', 'Everyone is selling. Someone posted a crying cat.', 'A panic sale makes a temporary dip a real loss.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 6), v.* from (values
    ('Mute the chat', 'Silence. Then a nap. Elite strategy.', 0, 3, 0, 4, 'low', 1),
    ('Doom-scroll all night', 'You cannot sell anyway. You suffer for free.', 0, -2, 6, 0, 'high', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 6));

insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 8, 'The Finish Line', 'Eight months. You did not sell once.', 'Patience is the part most people skip.')
on conflict (mission_id, month) do nothing;

insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
select (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 8), v.* from (values
    ('Keep holding', 'It turns out not looking is a superpower.', 0, 4, 0, 6, 'low', 1),
    ('Celebrate with a big spend', 'You earned a treat. A reasonable one. Was it?', -150, 6, 0, 0, 'medium', 2)
) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)
where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = (select id from public.mission_decision_points where mission_id = (select id from public.integrated_missions where name = 'Diamond Hands') and month = 8));

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 'Seat Belt On', '🎢', 'You cannot sell for eight months. This is either discipline or a very long roller coaster.', 'opening', 'month', 1, 'Buy from Investments. Selling is locked.', 0, 0, 0, 6, 1)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 'The Crash', '📉', 'Red. Everything is red. Your uncle says it is the end of money. He said that last year about oat milk.', 'crisis', 'month', 3, 'Prices move every game week. Falls are normal.', 0, -3, 6, 0, 2)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 'The Hype', '🚀', 'Your barber is giving crypto advice with scissors in hand. Everyone is a genius this week.', 'opportunity', 'month', 5, 'When everyone is certain, be careful.', 0, 3, 1, 2, 3)
on conflict (mission_id, display_order) do nothing;

insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)
values ((select id from public.integrated_missions where name = 'Diamond Hands'), 'The Quiet Recovery', '🌱', 'No headlines. No crying cats. Your numbers creep back up while you were doing laundry.', 'reflection', 'month', 7, 'Waiting did the work.', 0, 6, -2, 3, 4)
on conflict (mission_id, display_order) do nothing;

commit;

select name, duration_months, completion_reward from public.integrated_missions order by name;
