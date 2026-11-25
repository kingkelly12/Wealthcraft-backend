"""
80 more life events (migration 20261212000000_more_events.sql is generated from this file).

Each event: (title, description, event_type, icon, pack, [choice, choice]).
Each choice: (label, outcome, cost, benefit, sanity, income)
    cash = benefit - cost; sanity = impact_sanity; income = permanent monthly change.

Packs with a date in DROPS are released that Monday (they get the "✨ New" badge and are dealt
first for two weeks); everything else is live as soon as the migration runs.

Run:  python3 scripts/events/more_events.py > supabase/migrations/20261212000000_more_events.sql
"""
import re
import sys

DROPS = {
    'Getting around': '2027-01-11',
    'Pet life': '2027-01-18',
    'Payday': '2027-01-25',
    'Holiday mode': '2027-02-01',
    'Wellness era': '2027-02-08',
    'Side hustle': '2027-02-15',
    'Home admin': '2027-02-22',
    'Family tech support': '2027-03-01',
}

E = [
    # ---------------------------------------------------------------- live now: everyday chaos
    ('The Tipping Screen', 'The café card machine swivels round: 18%, 22% or 25%. For a bottle of water from the fridge. The barista is watching.', 'neutral', 'CreditCard', None, [
        ('Tap 25% and die inside', 'The barista says "have a great day!" with real warmth. You paid $1.25 for warmth.', 4, 0, -1, 0),
        ('Press "No tip"', 'The screen goes silent. The barista goes silent. The music somehow goes silent.', 0, 0, -3, 0)]),
    ('Self-Checkout Showdown', '"Unexpected item in the bagging area." There is nothing in the bagging area. There has never been anything in the bagging area.', 'neutral', 'ShoppingCart', None, [
        ('Wave for help', 'A teenager types a six-digit code without looking. You feel like a medieval peasant meeting electricity.', 0, 0, -1, 0),
        ('Abandon the shopping', 'You walk out with nothing but your dignity. Dinner is crackers and resentment.', 0, 0, -3, 0)]),
    ('The 7-Minute Voice Note', 'Your friend sent a 7-minute voice note. The first 40 seconds are wind.', 'neutral', 'MessageCircle', None, [
        ('Listen at 2x speed', 'They sound like a chipmunk confessing a crime. The actual news: they cut their fringe.', 0, 0, 2, 0),
        ('Reply "omg 😭"', 'It works for everything. They reply "RIGHT??". You will never know what happened.', 0, 0, 1, 0)]),
    ('Phone at 1%', 'Your phone is on 1%. Your ride is 3 minutes away. Your charger is at home, smugly charging nothing.', 'challenge', 'Battery', None, [
        ('Buy a $25 power bank', 'Overpriced, ugly, and your best friend now. You name it Gerald.', 25, 0, 3, 0),
        ('Screenshot the map and pray', 'The phone dies at the roundabout. You navigate by vibes and arrive 20 minutes late, reborn.', 0, 0, -4, 0)]),
    ('Autocorrect Betrayal', 'You texted your manager "Sorry, running late, see you shirtly." It was not "shortly".', 'neutral', 'Smartphone', None, [
        ('Send a correction', '"*shortly". Your manager replies "👀". The whole office knows by lunch.', 0, 0, -2, 0),
        ('Commit to the bit', 'You arrive in your best shirt. Your manager laughs so hard they forget you were late.', 0, 0, 4, 0)]),
    ('The Sneaker Drop', 'Limited trainers drop at 10am. 400 pairs. 80,000 people. Your thumb is ready.', 'challenge', 'ShoppingBag', None, [
        ('Enter the raffle', 'You lose to a bot named "xX_kicks_Xx". The bot has 400 pairs. Capitalism is undefeated.', 0, 0, -2, 0),
        ('Buy from a reseller', 'You pay $380 for $120 shoes. You will never wear them in rain, which means you will never wear them.', 380, 0, 4, 0)]),
    ('Concert Ticket Queue', 'You are number 48,213 in the ticket queue. The progress bar has not moved since Tuesday.', 'challenge', 'Ticket', None, [
        ('Wait it out', 'You get in at last. Only "obstructed view, behind pillar" is left. You buy it. You see one-third of the singer. Iconic third.', 140, 0, 5, 0),
        ('Close the tab', 'Your friends send 90 videos from the concert. You watch all of them. Free, and painful.', 0, 0, -3, 0)]),
    ('Brunch Queue', 'The brunch place everyone posts about has a 70-minute queue. The menu has a $19 slice of toast.', 'neutral', 'Utensils', None, [
        ('Queue for the toast', 'It is genuinely incredible toast. You post it. 4 likes. One of them is your mum.', 38, 0, 3, 0),
        ('Make eggs at home', 'Your eggs are rubbery but free. You take an aesthetic photo anyway. 6 likes. Mum again.', 6, 0, 2, 0)]),
    ('The Free Gym Session', 'The gym offers a free session with a personal trainer. His name is Blaze. He has never had a carb.', 'opportunity', 'Dumbbell', None, [
        ('Do the session', 'Blaze shouts "ONE MORE" eleven times. You cannot sit down for three days. You feel amazing, eventually.', 0, 0, 3, 0),
        ('Sign up for 12 sessions', 'Blaze becomes your hype man. You can now carry all the shopping in one trip. Worth it.', 360, 0, 7, 0)]),
    ('Smartwatch Judgement', 'Your smartwatch says "You have been sitting for 6 hours. Time to stand!" It is 11pm. You are in bed.', 'neutral', 'Activity', None, [
        ('Stand up, out of guilt', 'You stand in the dark like a lighthouse. The watch gives you a tiny trophy. Pathetically, it works.', 0, 0, 2, 0),
        ('Turn off notifications', 'The watch is now a very expensive clock. Peace returns to the kingdom.', 0, 0, 3, 0)]),
    ('The Sourdough Phase', 'A friend gives you a sourdough starter called "Doug". It needs feeding twice a day. It is basically a pet.', 'neutral', 'Flame', None, [
        ('Raise Doug', 'Your first loaf could stop a door. Your fifth could win awards. You stop buying bread.', 15, 0, 5, 8),
        ('Let Doug go', 'Doug passes quietly at the back of the fridge. Your friend asks after him weekly.', 0, 0, -2, 0)]),
    ('Air Fryer Evangelist', 'Your coworker has mentioned their air fryer 31 times this week. Today they brought a printed brochure.', 'neutral', 'Zap', None, [
        ('Buy one', 'It is, annoyingly, life-changing. You become the person who mentions their air fryer.', 90, 0, 4, 0),
        ('Resist', 'You stay strong. They send you a recipe every morning at 6:14am.', 0, 0, -1, 0)]),
    ('Your Friend Started a Podcast', 'Your friend started a podcast about "mindset". Episode 1 is 3 hours long. They want honest feedback.', 'neutral', 'Music', None, [
        ('Give honest feedback', '"Maybe a bit shorter?" Episode 2 is 4 hours. It is about feedback.', 0, 0, -2, 0),
        ('Leave a 5-star review', 'You are thanked by name in Episode 3. Your mum hears it. She is so proud of you, somehow.', 0, 0, 3, 0)]),
    ('The Business Opportunity', 'An old school friend you haven\'t spoken to in 6 years messages: "Hey hun!! Have you ever thought about being your own boss? 💕"', 'challenge', 'Rocket', None, [
        ('Hear them out', 'It is a $500 starter kit of shakes. You are now "building an empire" from a garage full of shakes.', 500, 0, -6, 0),
        ('"No thanks, hun 💕"', 'They reply "no worries! the offer stands 💕💕". The offer will stand forever.', 0, 0, 2, 0)]),
    ('The AI Wrote It', 'You asked an AI to write your out-of-office. It wrote a 400-word poem about rest.', 'neutral', 'Laptop', None, [
        ('Use the poem', 'Clients love it. One replies with their own poem. You have accidentally started a movement.', 0, 0, 4, 0),
        ('Write "Back Monday"', 'Efficient. Cold. Correct. Your inbox respects you.', 0, 0, 1, 0)]),
    ('Gym Mirror Incident', 'You waved at someone in the gym mirror. They were waving at someone behind you. You both saw it happen.', 'neutral', 'Eye', None, [
        ('Pretend it was a stretch', 'Smooth arm stretch, then the other arm. Nobody is fooled. You do 4 extra sets out of shame.', 0, 0, 1, 0),
        ('Change gyms', 'New gym, $10 more a month, zero witnesses.', 0, 0, 2, -10)]),
    ('The Haunted Printer', 'The office printer has started printing pages nobody sent. Today it printed a lasagne recipe.', 'neutral', 'Printer', None, [
        ('Make the lasagne', 'It is the best lasagne of your life. The printer is now considered a colleague.', 22, 0, 5, 0),
        ('Report it to IT', 'IT says "have you tried turning it off and on again". The printer prints "no".', 0, 0, -2, 0)]),
    ('Reply Guy Manager', 'Your manager now replies to every message with just "?". Even "good morning" got a "?".', 'challenge', 'MessageSquare', None, [
        ('Ask what "?" means', 'Turns out they think it\'s a friendly wave. You teach them emojis. Morale up 40%.', 0, 0, 4, 0),
        ('Reply with "?" too', 'A war of question marks begins. HR is cc\'d. HR replies "?".', 0, 0, -3, 0)]),
    ('Camera On, Unexpectedly', 'The meeting says "cameras on today!" You are in a hoodie with a face mask on. The green kind.', 'neutral', 'Video', None, [
        ('Turn it on anyway', 'You look like a swamp creature in finance. Your boss laughs. Your bond is permanent now.', 0, 0, 3, 0),
        ('"My camera is broken"', 'Third time this month. IT sends you a $70 webcam. You are now trapped.', 0, 0, -2, 0)]),
    ('The Salary Negotiation', 'You got a job offer elsewhere. Your manager says "let\'s talk about what would make you stay".', 'opportunity', 'Briefcase', None, [
        ('Ask for 10% more', 'Long pause. "We can do 7." You say "8 and a better chair." You get both.', 0, 0, 6, 160),
        ('Panic and say "it\'s fine"', 'You walk out with nothing but a "we value you" and a branded water bottle.', 0, 0, -4, 0)]),
    ('Open-Plan Microwave', 'Someone microwaved fish in the open-plan office. The smell has reached the third floor.', 'neutral', 'Wind', None, [
        ('Investigate', 'It was the CEO. You say nothing. You know too much now.', 0, 0, 1, 0),
        ('Work from a café', 'Fish-free and productive, but the café coffees add up.', 18, 0, 3, 0)]),
    ('Jury Duty Letter', 'You have been called for jury duty. The letter says it could take "one to six weeks".', 'neutral', 'Mail', None, [
        ('Serve', 'Week one: a stolen garden gnome. You take it very seriously. Justice is served, gnome is returned.', 0, 0, 3, 0),
        ('Ask to postpone', 'Granted, for six months. Future you will deal with the gnome.', 0, 0, 1, 0)]),
    ('Locked Out', 'The door shuts. Your keys are inside, on the counter, mocking you.', 'emergency', 'Home', None, [
        ('Call a locksmith', '$140 and 9 seconds of work. You ask how. He says "experience". You\'ll never sleep again.', 140, 0, -3, 0),
        ('Wait for your flatmate', 'Three hours on the stairs. You learn the life story of a neighbour\'s cat.', 0, 0, -5, 0)]),
    ('Phone Screen Crack', 'You dropped your phone. Face down. On concrete. You lift it slowly, like an archaeologist.', 'emergency', 'Smartphone', None, [
        ('Get the screen fixed', 'Good as new, $180 lighter. You buy a case that looks like a brick.', 180, 0, 2, 0),
        ('Live with the spiderweb', 'Every text now looks threatening. You cut your thumb on a meme.', 0, 0, -4, 0)]),
    ('Coffee on the Laptop', 'You knocked a full coffee over your laptop. It made a noise like a sad robot.', 'emergency', 'Laptop', None, [
        ('Repair shop', 'They save it, and your files. The technician asks if you take sugar. Not funny. Very funny.', 260, 0, -2, 0),
        ('Rice and prayer', 'Two days in rice. It turns on, but the "E" key is gone. You now write lik this.', 0, 0, -5, 0)]),
    ('The Parking Ticket', 'You parked for "two minutes". You came back to a $65 ticket and a warden still writing.', 'challenge', 'Car', None, [
        ('Pay it', 'Paid on time, so it\'s only $65. Your wallet sighs.', 65, 0, -2, 0),
        ('Appeal with a 3-page letter', 'Your letter includes a diagram. They cancel the ticket, possibly out of respect.', 0, 0, 4, 0)]),
    ('Fridge Dies', 'Your fridge died in the night. Everything inside is now "room-temperature food".', 'emergency', 'Box', None, [
        ('Buy a new fridge', 'It hums, it lights up, it has an egg tray you\'ll never use. Worth it.', 480, 0, 2, 0),
        ('Second-hand from a neighbour', '$60 and slightly loud. You call it "The Generator". It keeps milk cold.', 60, 0, 0, 0)]),
    ('Heatwave', 'It is 38°C. Your fan is just blowing hot air in a circle like a little hairdryer.', 'challenge', 'Sun', None, [
        ('Buy an air conditioner', 'Bliss. Then the power bill comes: about $25 more a month all summer.', 320, 0, 6, -25),
        ('Wet towels and suffering', 'You sleep under a damp towel like a burrito. You survive. Barely.', 0, 0, -5, 0)]),
    ('Mystery Charge', 'Your bank statement has a $49.99 charge from "BRX*SERV 7741". You have no idea what that is.', 'challenge', 'Receipt', None, [
        ('Dispute it', 'It was a fake charge. The bank refunds it and sends you a new card. You feel like a detective.', 0, 50, 4, 0),
        ('Assume you bought something', 'It renews every month. You never find out what it is.', 0, 0, -2, -50)]),
    ('The Phishing Text', '"Your parcel could not be delivered. Pay $1.99 here: rnail-p0st.co." You are expecting a parcel.', 'emergency', 'AlertTriangle', None, [
        ('Report and delete', 'You forward it to your bank\'s fraud team. Your parcel arrives the next day like nothing happened.', 0, 0, 3, 0),
        ('Click the link', 'It wanted your card details. You cancel the card in time, but it costs a weekend of phone calls.', 30, 0, -6, 0)]),
    ('Credit Limit Raised', 'Your bank says "Great news! We\'ve raised your credit limit to $8,000!" It was not great news.', 'neutral', 'CreditCard', None, [
        ('Ask them to lower it', 'The person on the phone has never been asked this. They need a manager. Respect.', 0, 0, 3, 0),
        ('"Just for emergencies"', 'A sale is an emergency. A holiday is an emergency. You now pay $40 a month in interest.', 0, 0, -3, -40)]),
    ('Extended Warranty', 'You bought a $40 kettle. The cashier offers a 3-year warranty for $15. "Kettles fail all the time."', 'neutral', 'Receipt', None, [
        ('Buy the warranty', 'The kettle outlives the warranty, the cashier and possibly you.', 15, 0, -1, 0),
        ('Live dangerously', 'Three years, zero problems. You boil water like a rebel.', 0, 0, 2, 0)]),
    ('The Retirement Email', 'HR emails: "Your employer matches pension contributions up to 5%." You have been ignoring this for a year.', 'opportunity', 'PiggyBank', None, [
        ('Sign up', 'Your take-home drops a bit, but free money appears in your pension. Future you does a little dance.', 0, 0, 4, -60),
        ('"Retirement is ages away"', 'You just turned down free money. Somewhere, an economist faints.', 0, 0, -1, 0)]),
    ('Payday Treat Logic', 'It\'s payday. You "deserve a treat". You also deserved one yesterday, and the day before.', 'challenge', 'Gift', None, [
        ('One small treat', 'A nice coffee and a pastry. Joy, contained.', 9, 0, 3, 0),
        ('Treat yourself, properly', 'New trainers, takeaway, a candle called "Velvet Midnight". You need a treat to recover from the treat.', 220, 0, 2, 0)]),
    ('Insurance Renewal', 'Your renewal quote went up 40%. Nothing changed. You are older, apparently that\'s a crime now.', 'challenge', 'FileText', None, [
        ('Shop around', 'An hour on comparison sites. Same cover, $18 a month cheaper. You\'re basically a hedge fund.', 0, 0, 2, 18),
        ('Auto-renew', 'You pay the "loyalty" price. Loyalty is expensive.', 0, 0, -2, -18)]),
    ('The Group Gift', 'Someone in the office is leaving. A card is going round with a "suggested $20" for a gift. You\'ve never met them.', 'neutral', 'Gift', None, [
        ('Chip in $20', 'You write "Good luck with everything!!" Classic. Timeless. Meaningless.', 20, 0, 1, 0),
        ('Sign without paying', 'Your name sits alone, uncovered by money. Everyone can see. Everyone.', 0, 0, -2, 0)]),
    ('Stag & Hen Season', 'Your friend\'s bachelor weekend is abroad: flights, villa, matching T-shirts. Total: $900.', 'challenge', 'PartyPopper', None, [
        ('Go', 'Three days, zero sleep, one ruined T-shirt. Legendary memories you can\'t fully remember.', 900, 0, 6, 0),
        ('Join for one night only', 'You fly in for the dinner. Cheaper, still fun, and you miss the incident at the go-karts.', 300, 0, 3, 0)]),
    ('Friend\'s Baby Shows Up', 'A friend visits with their baby. The baby looks at you like it knows your bank balance.', 'neutral', 'Baby', None, [
        ('Hold the baby', 'It falls asleep on you. You understand everything now. You also have a wet shoulder.', 0, 0, 5, 0),
        ('Give a respectful wave', 'The baby cries. Message received. You were judged and found wanting.', 0, 0, -1, 0)]),
    ('Sibling Borrowed Your Jacket', 'Your sibling "borrowed" your favourite jacket. You just saw it on their Instagram. At a festival.', 'neutral', 'Shirt', None, [
        ('Demand it back', 'It comes back smelling of festival. You will never know what happened to the pocket.', 0, 0, -1, 0),
        ('Let it go, ask for a favour later', 'You now own a sibling IOU. Valuable currency in any family.', 0, 0, 3, 0)]),
    ('Grandma\'s Envelope', 'Grandma slips you an envelope. "Don\'t tell your mother." It feels thick.', 'opportunity', 'Gift', None, [
        ('Accept it graciously', '$100 in crisp notes and a handwritten "buy something sensible". You buy something sensible. Mostly.', 0, 100, 5, 0),
        ('Refuse politely', 'She puts it in your coat pocket when you aren\'t looking. Grandmas always win.', 0, 100, 4, 0)]),

    # ---------------------------------------------------------------- drop: Getting around
    ('Train Strike', 'Trains are on strike tomorrow. Your meeting is not on strike.', 'challenge', 'Clock', 'Getting around', [
        ('Get a rideshare', 'Surge pricing: $58. The driver plays whale sounds. You arrive calm and broke.', 58, 0, 1, 0),
        ('Ask to work from home', 'Granted. You attend in pyjama bottoms and a very serious shirt.', 0, 0, 4, 0)]),
    ('The E-Scooter', 'An e-scooter is parked outside. $1 to unlock, 30 cents a minute. You\'ve never ridden one.', 'neutral', 'Zap', 'Getting around', [
        ('Ride it', 'You go 4 metres, wobble, and scream. Then you get it. You arrive grinning and windswept.', 6, 0, 4, 0),
        ('Walk like a normal person', 'A scooter overtakes you with someone screaming on it. You feel wise.', 0, 0, 1, 0)]),
    ('Bike Stolen', 'Your bike is gone. Only the lock remains, cut cleanly, like a message.', 'emergency', 'AlertTriangle', 'Getting around', [
        ('Buy a second-hand bike', 'It\'s a bit rusty but loyal. You buy a lock that weighs more than the bike.', 160, 0, 1, 0),
        ('Take the bus', 'The bus is fine. The bus is fine. It\'s $45 a month more, but the bus is fine.', 0, 0, -3, -45)]),
    ('Missed the Last Bus', 'The last bus leaves as you round the corner. The driver sees you. The driver does not stop.', 'challenge', 'Moon', 'Getting around', [
        ('Taxi home', '$42. The driver tells you about his three ex-wives. You learn a lot.', 42, 0, -1, 0),
        ('Walk the hour home', 'You discover a 24-hour bakery on the way. Life-changing croissant at 2am.', 3, 0, 2, 0)]),
    ('Flat Tyre', 'Your tyre is flat. Completely flat. Like your energy on a Monday.', 'emergency', 'Car', 'Getting around', [
        ('Change it yourself', 'One video tutorial, two hours and one injured knuckle. You did it. You are unstoppable.', 0, 0, 3, 0),
        ('Call roadside help', 'They arrive in 90 minutes and fix it in 4. $85. You watch respectfully.', 85, 0, 0, 0)]),

    # ---------------------------------------------------------------- drop: Pet life
    ('Adopt a Cat?', 'The shelter posted a one-eyed cat called Admiral Whiskers. He has been there 200 days.', 'opportunity', 'Heart', 'Pet life', [
        ('Adopt the Admiral', 'He sleeps on your keyboard and judges your choices. Food and litter: about $40 a month. Your heart: full.', 120, 0, 8, -40),
        ('Share the post instead', 'Someone else adopts him. You see photos. He looks happy. You are happy. Mostly.', 0, 0, 1, 0)]),
    ('The Vet Bill', 'Your dog ate a sock. A whole sock. He looks proud.', 'emergency', 'Activity', 'Pet life', [
        ('Rush to the vet', 'The sock is retrieved. The bill is $420. The dog wags like he\'s won.', 420, 0, -2, 0),
        ('Wait and watch', 'The sock reappears two days later, in the garden. You do not talk about it.', 0, 0, -4, 0)]),
    ('Cat vs. Glass', 'Your cat is slowly pushing a full glass of water towards the edge of the table, looking at you.', 'neutral', 'Eye', 'Pet life', [
        ('Save the glass', 'You lunge. The cat waits until you sit down, then does it again. You have lost.', 0, 0, -1, 0),
        ('Let it happen', 'Crash. The cat walks away, satisfied. You both know who runs this house.', 0, 0, 1, 0)]),
    ('Pet-Sitting a Friend\'s Parrot', 'Your friend asks you to watch their parrot for a week. It knows four swear words and your name now.', 'neutral', 'Bird', 'Pet life', [
        ('Say yes', 'The parrot learns your ringtone. Your friend pays you $80 and a bottle of wine.', 0, 80, 2, 0),
        ('Politely decline', 'Your friend finds someone else. The parrot apparently says your name anyway.', 0, 0, 1, 0)]),
    ('Dog Walking Side Gig', 'A neighbour asks if you could walk their two huskies every evening. They pay $15 a walk.', 'opportunity', 'Footprints', 'Pet life', [
        ('Take the job', 'The huskies walk you, mostly. You get fit, and about $120 more a month.', 0, 0, 3, 120),
        ('Keep your evenings', 'The huskies howl when you pass. It feels personal.', 0, 0, 1, 0)]),

    # ---------------------------------------------------------------- drop: Payday
    ('Payday Fake-Out', 'You checked your account at midnight. Payday hasn\'t landed. You checked again at 12:01.', 'neutral', 'Clock', 'Payday', [
        ('Refresh until it lands', 'It lands at 6:43am. You saw every minute of the night. You feel rich and terrible.', 0, 0, -3, 0),
        ('Go to sleep like an adult', 'You wake up and it\'s there. Like magic. Like Christmas. Like a functioning adult.', 0, 0, 3, 0)]),
    ('The Budget Spreadsheet', 'You made a budget spreadsheet with colours and formulas. It looks like a work of art.', 'opportunity', 'FileText', 'Payday', [
        ('Actually follow it', 'Month one: you find $70 of subscriptions you forgot. The spreadsheet pays for itself.', 0, 0, 3, 70),
        ('Admire it and close it', 'You open it once a month to change the colours. It is a beautiful lie.', 0, 0, -1, 0)]),
    ('The Emergency Fund', 'A money video says you should have 3 months of costs saved "for emergencies". You have $36.', 'challenge', 'PiggyBank', 'Payday', [
        ('Move $300 to savings', 'Your current account feels lighter. Your shoulders feel lighter too. Interesting.', 0, 0, 5, 0),
        ('Watch another money video', 'This one says to buy a yacht and rent it out. You don\'t have a yacht. Or a plan.', 0, 0, -2, 0)]),
    ('Payday Group Dinner', 'It\'s payday, so the group chat wants dinner at the new steakhouse. Mains start at $48.', 'neutral', 'Utensils', 'Payday', [
        ('Go big', 'Steak, dessert, a cocktail with smoke coming out of it. You leave a different person, but poorer.', 110, 0, 5, 0),
        ('Suggest the noodle place', 'Everyone pretends to be annoyed, then has the best night. Noodle place forever.', 25, 0, 4, 0)]),
    ('Split the Bill Evenly?', 'You had a salad and tap water. Someone across from you ordered lobster. "Let\'s just split it evenly!"', 'challenge', 'Divide', 'Payday', [
        ('Split it', '$74 for a salad. Your lettuce now has a mortgage.', 74, 0, -3, 0),
        ('Pay for what you had', 'Awkward pause, then two others do the same. You started a revolution.', 18, 0, 2, 0)]),

    # ---------------------------------------------------------------- drop: Holiday mode
    ('The Cleaning Fee', 'The holiday flat is $80 a night. Then a $90 cleaning fee. Then a $40 service fee. Then a "vibes" fee.', 'challenge', 'Home', 'Holiday mode', [
        ('Book it anyway', 'Lovely flat. The checkout list asks you to clean, strip the beds and take the bins out. For the cleaning fee.', 410, 0, 4, 0),
        ('Book a hotel', 'Slightly smaller, but breakfast is included and nobody asks you to vacuum.', 360, 0, 5, 0)]),
    ('Lost Luggage', 'You arrive. Your suitcase does not. The screen says it is "in transit", which means nobody knows.', 'emergency', 'Package', 'Holiday mode', [
        ('Buy emergency clothes', 'Your holiday photos are all in one souvenir T-shirt. Committed to the theme.', 120, 0, -2, 0),
        ('Wait at the airport', 'It arrives on the last day. It went on holiday without you. It looks rested.', 0, 0, -5, 0)]),
    ('Timeshare Pitch', 'A smiling man offers a "free" breakfast and boat trip. You just need to listen to a "quick presentation".', 'neutral', 'Ticket', 'Holiday mode', [
        ('Go for the free breakfast', 'Four hours in a windowless room. You leave with a croissant and no timeshare. Undefeated.', 0, 0, -3, 0),
        ('Keep walking', 'He follows you for two streets, then gives up. You eat breakfast in peace, and you pay for it.', 14, 0, 2, 0)]),
    ('Sunburn', 'You fell asleep on the beach. You are now two colours. Your back looks like a strawberry.', 'neutral', 'Sun', 'Holiday mode', [
        ('Buy aloe gel', 'Sticky but cool. You walk like a robot for two days.', 12, 0, 0, 0),
        ('Tough it out', 'You sleep standing up like a horse. You learn about suncream the hard way.', 0, 0, -4, 0)]),
    ('Airport Snacks', 'At the airport, a bottle of water costs $6 and a sandwich costs $14. The sandwich is mostly bread.', 'neutral', 'Plane', 'Holiday mode', [
        ('Buy the sandwich', 'Three slices of tomato, emotional damage. You eat it slowly to make it last.', 20, 0, -1, 0),
        ('Bring snacks from home next time', 'You arrive with a backpack full of crackers. Other travellers look at you with envy.', 4, 0, 2, 0)]),

    # ---------------------------------------------------------------- drop: Wellness era
    ('The Cold Plunge', 'Everyone online is doing cold plunges. Your friend invites you to try one. It\'s 3°C.', 'neutral', 'Droplets', 'Wellness era', [
        ('Get in', 'You make a sound that only dolphins can hear. You feel incredible. You never do it again.', 20, 0, 5, 0),
        ('Hold their towel', 'You watch them scream. You feel incredible without getting wet.', 0, 0, 3, 0)]),
    ('The Meditation App', 'Your meditation app says "Day 1 of 365". The voice is so calm it\'s slightly sinister.', 'opportunity', 'Moon', 'Wellness era', [
        ('Pay for the year', '$70. You use it 9 times. Those 9 times were very calm.', 70, 0, 4, 0),
        ('Free version only', 'Ten minutes a day, plus adverts for the full version. Still calmer.', 0, 0, 2, 0)]),
    ('Running Club Speed', 'You joined a "social, all-levels" running club. Everyone is running at the speed of a motorbike.', 'challenge', 'Footprints', 'Wellness era', [
        ('Keep up', 'You keep up for 600 metres, then see your ancestors. You\'re fitter by the month\'s end.', 0, 0, 3, 0),
        ('Join the walking group', 'They are hilarious and also bring cake. The best mistake of your life.', 5, 0, 5, 0)]),
    ('The Dentist Floss Question', 'The dentist asks how often you floss. You both know. You both know.', 'neutral', 'Smile', 'Wellness era', [
        ('Tell the truth', '"Twice. This year." The dentist nods sadly. Somehow it\'s therapeutic.', 0, 0, 2, 0),
        ('Lie confidently', '"Every day." Your gums bleed in protest. The dentist writes something down.', 0, 0, -2, 0)]),
    ('Sleep Tracker Data', 'Your sleep tracker says you got "4 hours of poor-quality sleep" and recommends "rest".', 'neutral', 'Activity', 'Wellness era', [
        ('Go to bed at 10', 'You lie awake thinking about going to bed at 10. Eventually it works. You feel human.', 0, 0, 5, 0),
        ('Scroll at 1am again', 'The tracker gives you a red sad face. You screenshot it and post it. 12 likes.', 0, 0, -4, 0)]),

    # ---------------------------------------------------------------- drop: Side hustle
    ('Sell Old Clothes Online', 'Your wardrobe is overflowing. An app says people will pay for your old stuff.', 'opportunity', 'Shirt', 'Side hustle', [
        ('List 20 items', 'You sell 14 things. The 15th buyer sends a 2,000-word message about a stain. Still, $210.', 0, 210, 3, 0),
        ('Keep everything "just in case"', 'The case never comes. The wardrobe door now needs a shoulder.', 0, 0, -2, 0)]),
    ('Weekend Market Stall', 'A friend says you should sell your homemade candles at the weekend market. The stall costs $50.', 'opportunity', 'Flame', 'Side hustle', [
        ('Book the stall', 'Slow morning, then a rush. You sell out. A small business is born: about $90 a month.', 50, 0, 4, 90),
        ('Stick to giving them as gifts', 'Your friends now own 11 of your candles each. They smell of love and slight panic.', 0, 0, 1, 0)]),
    ('Rideshare Rating', 'You drove for a rideshare app this weekend. A passenger gave you 3 stars for "music choice".', 'neutral', 'Car', 'Side hustle', [
        ('Change the playlist', 'You switch to calm piano. Ratings rise to 4.9. You now hate calm piano.', 0, 0, -1, 0),
        ('Stay true to your music', 'Two passengers ask for the playlist. One dances. Art always finds its audience.', 0, 0, 3, 0)]),
    ('The Viral Recipe', 'You posted a 20-second recipe video. It has 400,000 views. Brands are emailing.', 'opportunity', 'Video', 'Side hustle', [
        ('Do a paid post', '$300 to hold a spatula and smile. You smile so hard your face hurts.', 0, 300, 3, 0),
        ('Post another recipe', 'It gets 41 views. The internet is a fickle god.', 0, 0, -2, 0)]),
    ('Freelance Scope Creep', 'A client paid you for "one quick logo". This is now revision 17. They want it to feel "more purple, but not purple".', 'challenge', 'Hammer', 'Side hustle', [
        ('Charge for extra revisions', 'They say "of course!" immediately. You should have done this 16 revisions ago.', 0, 180, 4, 0),
        ('Keep going for free', 'Revision 24: they pick revision 1. You stare at a wall for some time.', 0, 0, -6, 0)]),

    # ---------------------------------------------------------------- drop: Home admin
    ('Landlord Inspection', 'Your landlord is coming tomorrow for an "inspection". Your flat looks like a crime scene with candles.', 'challenge', 'ClipboardCheck', 'Home admin', [
        ('Clean all night', 'The landlord says "lovely" and leaves after 4 minutes. You cleaned behind the oven for 4 minutes.', 15, 0, -3, 0),
        ('Hide everything in the wardrobe', 'He opens the wardrobe. Of course he does. He says nothing. He doesn\'t need to.', 0, 0, -4, 0)]),
    ('Washing Machine Flood', 'The washing machine started walking across the kitchen during the spin cycle. Then it leaked.', 'emergency', 'Droplets', 'Home admin', [
        ('Call a repair person', '$130 to replace a part the size of a coin. The machine stays where it is now.', 130, 0, -1, 0),
        ('Hand-wash for a while', 'You wash jeans in the bath like a Victorian. You develop forearms of steel.', 0, 0, -4, 0)]),
    ('The Deposit Return', 'You moved out. The old landlord kept $300 of your deposit for "general wear". The wear was general.', 'challenge', 'Wallet', 'Home admin', [
        ('Dispute it with photos', 'You sent move-in photos. The deposit scheme sides with you. Full refund. Justice.', 0, 300, 5, 0),
        ('Let it go', 'You let it go. You do not let it go. You think about it in the shower for a year.', 0, 0, -4, 0)]),
    ('Energy Bill Shock', 'Your energy bill arrived. It\'s double last month\'s. Your flatmate has been running a heater in the bathroom 24/7.', 'challenge', 'Zap', 'Home admin', [
        ('Have The Talk', 'Uncomfortable, but the heater goes. Your bill drops back. You both survive the conversation.', 0, 0, 2, 30),
        ('Pay and say nothing', 'Your bathroom is warm. Your bank is not.', 0, 0, -3, -30)]),
    ('The Flat Viewing', 'The listing said "cosy, characterful, two-bed". In person: the second bedroom is a cupboard with a window.', 'neutral', 'Home', 'Home admin', [
        ('Ask about the cupboard', 'The agent says "it\'s a study". You say "it\'s a cupboard". The agent says "it\'s a study". You leave.', 0, 0, 1, 0),
        ('Make an offer anyway', 'You now live in a cosy, characterful cupboard. Rent is lower at least.', 0, 0, -2, 40)]),

    # ---------------------------------------------------------------- drop: Family tech support
    ('Mum\'s Password', 'Mum calls. She forgot her email password. Again. The new one was "Password2".', 'neutral', 'Phone', 'Family tech support', [
        ('Set up a password manager', 'Forty minutes, three cups of tea, and now she\'s safer than you. She tells everyone.', 0, 0, 3, 0),
        ('Write it on a sticky note', 'She sticks it on the screen. Her neighbour now knows her email password.', 0, 0, -1, 0)]),
    ('Dad\'s Forwarded Messages', 'Dad forwarded you "URGENT: share with 10 people or lose your WhatsApp". It\'s his ninth one today.', 'neutral', 'MessageSquare', 'Family tech support', [
        ('Explain it\'s fake', 'He says "better safe than sorry" and forwards it to you again.', 0, 0, -2, 0),
        ('Send him a funny dog video', 'He forwards that to 40 people. You are now responsible for the family\'s mood.', 0, 0, 3, 0)]),
    ('The Family TV', 'Your parents bought a new smart TV. The remote has 74 buttons. They have called you 6 times.', 'challenge', 'Video', 'Family tech support', [
        ('Drive over and set it up', 'Two hours, one tank of petrol, and you get fed like royalty. Fair trade.', 25, 0, 5, 0),
        ('Talk them through it by phone', '"Press the home button." "Which one is home?" "The house." "There\'s no house." Three hours.', 0, 0, -5, 0)]),
    ('Grandpa Discovered Emoji', 'Grandpa learned emoji. He now ends every message with 🍆 because he thinks it\'s a "nice purple vegetable".', 'neutral', 'Smile', 'Family tech support', [
        ('Explain gently', 'There is a long silence on the phone. Then he laughs for 10 minutes. Best call of your year.', 0, 0, 5, 0),
        ('Let him keep going', 'He sends it to the vicar. The family group chat explodes.', 0, 0, 2, 0)]),
    ('Cousin Wants to "Pick Your Brain"', 'Your cousin wants to "pick your brain" about starting a business. It\'s the third time. They never start the business.', 'neutral', 'HelpCircle', 'Family tech support', [
        ('Charge for a coffee', '"Brain-picking costs a flat white." They agree. You have the same chat. At least you got coffee.', 0, 6, 2, 0),
        ('Pick their brain back', 'You ask about their budget. They change the subject. Peace achieved.', 0, 0, 3, 0)]),
]

# --------------------------------------------------------------------------------------------------
TYPES = {'neutral', 'challenge', 'opportunity', 'emergency'}
EDITOR_TRAP = re.compile(r'\b(?:into|table)\s+([\w.]+)', re.I)


def q(s):
    return "'" + str(s).replace("'", "''") + "'"


def check():
    titles = [e[0] for e in E]
    assert len(E) == 80, len(E)
    assert len(set(titles)) == len(titles), 'duplicate title'
    for title, desc, typ, icon, pack, choices in E:
        assert typ in TYPES, title
        assert pack is None or pack in DROPS, (title, pack)
        assert len(choices) == 2, title
        for c in choices:
            assert len(c) == 6, (title, c)
        for text in [title, desc] + [x for c in choices for x in c[:2]]:
            m = EDITOR_TRAP.search(text)
            assert not m, f'{title}: reword "{m.group(0)}" (the Supabase SQL Editor misreads it)'
            assert '$csv$' not in text


def sql():
    out = ['''-- =============================================================================
-- 80 more life events (written in scripts/events/more_events.py; generate this file from it).
-- * 40 are live as soon as this runs.
-- * 40 arrive in 8 weekly drops of 5, every Monday from 11 Jan to 1 Mar 2027. Each one gets the
--   "✨ New" badge and is dealt first for two weeks (released_at, app/game/week_service.py).
-- Safe to re-run: events are skipped by title.
-- =============================================================================

begin;
''']
    for n, (title, desc, typ, icon, pack, choices) in enumerate(E, 1):
        when = DROPS.get(pack)
        cols = 'title, description, event_type, impact_cash, impact_income, impact_expenses, impact_sanity, icon_name, is_active'
        vals = f"{q(title)}, {q(desc)}, {q(typ)}, 0, 0, 0, 0, {q(icon)}, true"
        if when:
            cols += ', released_at, pack'
            vals += f", '{when}T00:00:00+00:00', {q(pack)}"
        rows = ',\n'.join(f"    ({q(l)}, {q(o)}, {c}, {b}, {i}, {s}, {inc})" for i, (l, o, c, b, s, inc) in enumerate(choices, 1))
        out.append(f'''-- {n}. {title}{f' (drop: {pack}, live from {when})' if when else ''}
WITH e AS (
    INSERT INTO life_events ({cols})
    SELECT {vals}
    WHERE NOT EXISTS (SELECT 1 FROM life_events WHERE title = {q(title)})
    RETURNING id
)
INSERT INTO life_event_choices (id, life_event_id, choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income)
SELECT gen_random_uuid(), e.id, v.* FROM e CROSS JOIN (VALUES
{rows}
) AS v(choice_label, outcome_description, cost, benefit, choice_order, impact_sanity, impact_income);
''')
    out.append('commit;\n')
    return '\n'.join(out)


if __name__ == '__main__':
    check()
    sys.stdout.write(sql())
