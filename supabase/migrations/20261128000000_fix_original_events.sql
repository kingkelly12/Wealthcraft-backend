-- =============================================================================
-- Fix the original 60 life events
-- =============================================================================
-- The first 60 events stored sanity in the `benefit` column, which the game
-- pays out as CASH (e.g. "Book the Dentist" paid you $5), and both choices of
-- an event shared the event's sanity hit. A few choices had negative costs, so
-- they paid you (e.g. "Stay member" gave +$30).
-- Now every choice has its real cash effect, its own sanity effect and a
-- proper outcome line. Matched by event title; safe to re-run.
-- =============================================================================

begin;

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

commit;
