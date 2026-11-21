"""
Everyday cards for the weekly deck ("This Week").

Life events from the database bring the big swings; these are the small,
social, funny decisions that give every week texture. Each card is two
choices, swiped left or right.

Writing rules (keep the voice consistent when adding cards):
  * Second person, present tense, one or two short sentences.
  * Stakes are small: roughly -$150..+$150 and -8..+8 sanity. Big swings
    belong in life events.
  * At least one choice must be free (cash >= 0), so a broke player is never
    stuck on a card.
  * The outcome line is the punchline. Make it land.
  * `teaser` is shown as next week's cliffhanger, so it hints, never spoils.

Fields per choice: label, outcome, cash (signed $), sanity (signed), income
(signed $/month, permanent; use sparingly).
`requires`: optional 'job' | 'no_job' | 'rental' | 'no_rental'.
"""

CARDS = [
    # --- Social ---------------------------------------------------------------
    {
        'key': 'birthday_dinner', 'icon': '🍕', 'category': 'social',
        'title': 'Birthday dinner',
        'body': "Jordan's birthday dinner is at the place with $18 fries. The group chat expects you.",
        'teaser': 'Someone in the group chat is planning something 👀',
        'left': {'label': "Can't, I'm broke", 'outcome': 'You send a gif instead. The gif was not enough.', 'cash': 0, 'sanity': -4},
        'right': {'label': "I'm in!", 'outcome': 'You split the bill evenly even though you had water. Worth it, mostly.', 'cash': -45, 'sanity': 6},
    },
    {
        'key': 'concert_tickets', 'icon': '🎤', 'category': 'social',
        'title': 'Concert drop',
        'body': 'Your favourite artist just dropped tour dates. Tickets are $120 and selling out in 4 minutes.',
        'teaser': 'Your favourite artist is up to something 🎶',
        'left': {'label': 'Watch the TikToks', 'outcome': "You watch it all from 40 strangers' phones. Basically there.", 'cash': 0, 'sanity': -3},
        'right': {'label': 'Buy it. Now.', 'outcome': 'You scream every lyric. Your bank account screams too.', 'cash': -120, 'sanity': 8},
    },
    {
        'key': 'roommate_party', 'icon': '🎉', 'category': 'social',
        'title': 'House party',
        'body': 'Your roommate wants to throw a party "for like 10 people". You know what that means.',
        'teaser': 'Your roommate has an idea. It is not a good idea.',
        'requires': 'rental',
        'left': {'label': 'Absolutely not', 'outcome': 'You become the Responsible One. Nobody thanks you.', 'cash': 0, 'sanity': -2},
        'right': {'label': 'Send it', 'outcome': '60 people came. Someone broke the blinds. Legendary night though.', 'cash': -60, 'sanity': 7},
    },
    {
        'key': 'friend_loan', 'icon': '🤝', 'category': 'social',
        'title': 'Can I borrow $50?',
        'body': 'Your friend needs $50 "until Friday". They said the same thing in March.',
        'teaser': 'A friend is about to ask you for something 💸',
        'left': {'label': 'Sorry, tight month', 'outcome': 'Slightly awkward. Your $50 is safe.', 'cash': 0, 'sanity': -2},
        'right': {'label': 'Send it', 'outcome': "You'll never see that $50 again, but they owe you forever.", 'cash': -50, 'sanity': 4},
    },
    {
        'key': 'situationship', 'icon': '💬', 'category': 'social',
        'title': '"wyd"',
        'body': 'Your situationship texts "wyd" at 11:48pm. You have an 8am.',
        'teaser': 'Your phone is going to light up at midnight 📱',
        'left': {'label': 'Leave on read', 'outcome': 'You sleep 8 hours. Growth looks boring and feels amazing.', 'cash': 0, 'sanity': 5},
        'right': {'label': '"nm u?"', 'outcome': "Uber, 2am fries, 8am regret. The plot doesn't thicken.", 'cash': -35, 'sanity': -4},
    },
    {
        'key': 'wedding_invite', 'icon': '💍', 'category': 'social',
        'title': 'Save the date',
        'body': 'Your cousin is getting married. Gift registry starts at $85 for a single spoon.',
        'teaser': 'Something with a dress code is coming 💌',
        'left': {'label': 'Handwritten card', 'outcome': 'Heartfelt, free, and your aunt will mention it for years.', 'cash': 0, 'sanity': -1},
        'right': {'label': 'Buy the spoon', 'outcome': 'It is a very nice spoon. You are now a Gift Person.', 'cash': -85, 'sanity': 3},
    },
    {
        'key': 'group_trip', 'icon': '🏖️', 'category': 'social',
        'title': 'Group trip',
        'body': 'The group chat is planning a beach weekend. Deposit is $150 by tonight.',
        'teaser': 'The group chat is about to propose a trip 🧳',
        'left': {'label': 'FOMO it out', 'outcome': 'You watch their stories from your bed. The sand looks soft.', 'cash': 0, 'sanity': -6},
        'right': {'label': 'Pay the deposit', 'outcome': 'Best weekend in months. You come back tanned and broke.', 'cash': -150, 'sanity': 8},
    },

    # --- Money / temptation ----------------------------------------------------
    {
        'key': 'flash_sale', 'icon': '🛍️', 'category': 'temptation',
        'title': 'FLASH SALE 70% OFF',
        'body': 'Those shoes you liked are on sale. "Only 2 left in your size."',
        'teaser': 'Your inbox has a sale in it 🛒',
        'left': {'label': 'Close the tab', 'outcome': 'They were going to sell out anyway. Probably.', 'cash': 0, 'sanity': -1},
        'right': {'label': 'Add to cart', 'outcome': 'They look great. You will wear them twice.', 'cash': -90, 'sanity': 4},
    },
    {
        'key': 'subscription_trial', 'icon': '📺', 'category': 'money',
        'title': 'Free trial ending',
        'body': 'Your "free trial" of three streaming services ends tomorrow. Combined: $42/month.',
        'teaser': 'A free trial is about to stop being free ⏰',
        'left': {'label': 'Cancel all three', 'outcome': 'You spend 40 minutes finding the cancel button. Victory.', 'cash': 0, 'sanity': -2},
        'right': {'label': "I'll cancel later", 'outcome': 'You will not cancel later. Nobody cancels later.', 'cash': -42, 'sanity': 2},
    },
    {
        'key': 'crypto_tip', 'icon': '🚀', 'category': 'money',
        'title': 'A hot tip',
        'body': 'A guy from your class says $FROG coin is "about to go crazy". He has a podcast.',
        'teaser': 'Someone has a "can\'t lose" investment for you 🐸',
        'left': {'label': 'Nah', 'outcome': '$FROG went to zero by Thursday. You remain unfrogged.', 'cash': 0, 'sanity': 1},
        'right': {'label': 'Throw in $100', 'outcome': '$FROG did go crazy. Straight down. The podcast is on hiatus.', 'cash': -100, 'sanity': -5},
    },
    {
        'key': 'meal_prep', 'icon': '🥡', 'category': 'money',
        'title': 'Sunday meal prep',
        'body': "It's Sunday. You could cook for the week, or rely on delivery and vibes.",
        'teaser': "Next week's lunch situation is undecided 🍱",
        'left': {'label': 'Meal prep', 'outcome': 'Five boxes of the same chicken. Your wallet thanks you. Your tastebuds file a complaint.', 'cash': 30, 'sanity': -2},
        'right': {'label': 'Delivery all week', 'outcome': 'Delivery fees, service fees, "small order" fees. Delicious though.', 'cash': -70, 'sanity': 3},
    },
    {
        'key': 'phone_crack', 'icon': '📱', 'category': 'money',
        'title': 'Cracked screen',
        'body': 'You dropped your phone. The crack goes right through the clock.',
        'teaser': 'Gravity has plans for your phone 📉',
        'left': {'label': 'Live with it', 'outcome': 'You now read every text through a spiderweb. Character building.', 'cash': 0, 'sanity': -4},
        'right': {'label': 'Repair shop', 'outcome': 'Good as new. For now.', 'cash': -110, 'sanity': 3},
    },
    {
        'key': 'textbook', 'icon': '📚', 'category': 'school',
        'title': 'The $140 textbook',
        'body': 'Your professor says the textbook is "required". It is in its 14th edition.',
        'teaser': 'A professor is about to make a demand 📖',
        'left': {'label': 'Find a PDF', 'outcome': 'Page 212 is missing, but so is your debt. Fair trade.', 'cash': 0, 'sanity': -2},
        'right': {'label': 'Buy it new', 'outcome': 'You open it once. The plastic wrap was the best part.', 'cash': -140, 'sanity': 2},
    },
    {
        'key': 'coffee_habit', 'icon': '☕', 'category': 'money',
        'title': 'The coffee math',
        'body': "You've spent $38 on oat lattes this week. The barista knows your name and your trauma.",
        'teaser': 'Your coffee habit is being audited ☕',
        'left': {'label': 'Home coffee era', 'outcome': 'It tastes like sadness, but affordable sadness.', 'cash': 25, 'sanity': -3},
        'right': {'label': 'Latte is self-care', 'outcome': 'Oat milk, extra shot, zero regrets. Some regrets.', 'cash': -20, 'sanity': 3},
    },

    # --- Hustle ----------------------------------------------------------------
    {
        'key': 'weekend_shift', 'icon': '🧾', 'category': 'hustle',
        'title': 'Extra shift',
        'body': 'Your manager asks if you can cover Saturday. Time-and-a-half.',
        'teaser': 'Your manager is about to text you 📲',
        'requires': 'job',
        'left': {'label': 'Protect the weekend', 'outcome': 'You sleep until noon. Restorative and unpaid.', 'cash': 0, 'sanity': 4},
        'right': {'label': 'Take the shift', 'outcome': 'Eight hours, three rude customers, one fat paycheck.', 'cash': 120, 'sanity': -5},
    },
    {
        'key': 'tutoring_gig', 'icon': '✏️', 'category': 'hustle',
        'title': 'Tutoring gig',
        'body': "A parent wants someone to tutor their kid in maths. Their kid is 'very spirited'.",
        'teaser': 'Someone wants to pay you for what you know 🧠',
        'left': {'label': 'Pass', 'outcome': 'You dodge the spirited child. Peace is priceless.', 'cash': 0, 'sanity': 1},
        'right': {'label': "I'll do it", 'outcome': 'The kid learned fractions. You learned patience. $80 richer.', 'cash': 80, 'sanity': -3},
    },
    {
        'key': 'sell_stuff', 'icon': '📦', 'category': 'hustle',
        'title': 'Closet cleanout',
        'body': "Your room is 40% clothes you don't wear. Resale apps exist.",
        'teaser': 'Your closet is hiding money 👕',
        'left': {'label': 'Too much effort', 'outcome': 'The clothes stay. They judge you silently.', 'cash': 0, 'sanity': 0},
        'right': {'label': 'List everything', 'outcome': 'Someone paid $60 for a hoodie you got free at orientation.', 'cash': 60, 'sanity': 2},
    },
    {
        'key': 'delivery_gig', 'icon': '🛵', 'category': 'hustle',
        'title': 'Delivery app',
        'body': 'Delivery app says there is "surge pricing" in your area tonight.',
        'teaser': 'Surge pricing is coming to your neighbourhood 🛵',
        'left': {'label': 'Stay in', 'outcome': 'You watch other people deliver food to you. Ironic.', 'cash': 0, 'sanity': 2},
        'right': {'label': 'Grind tonight', 'outcome': "Five hours, $95, one dog who absolutely wasn't friendly.", 'cash': 95, 'sanity': -4},
    },
    {
        'key': 'ask_raise', 'icon': '📈', 'category': 'hustle',
        'title': 'The raise conversation',
        'body': "You've been killing it at work. You could ask for a raise. Your palms are already sweating.",
        'teaser': 'Something brave is on your calendar 😬',
        'requires': 'job',
        'left': {'label': 'Maybe next year', 'outcome': 'Nothing changes. Comfortable, safe, slightly underpaid.', 'cash': 0, 'sanity': 0},
        'right': {'label': 'Ask for it', 'outcome': 'Your voice cracked twice but you got it. +$100 a month.', 'cash': 0, 'sanity': -3, 'income': 100},
    },
    {
        'key': 'job_fair', 'icon': '🪪', 'category': 'hustle',
        'title': 'Career fair',
        'body': 'There is a career fair on campus. Free pens, free pizza, free existential pressure.',
        'teaser': 'Free pizza and networking are coming 🍕',
        'requires': 'no_job',
        'left': {'label': 'Skip it', 'outcome': 'You stay home. The pizza goes to someone more employable.', 'cash': 0, 'sanity': 1},
        'right': {'label': 'Go network', 'outcome': 'You collect 9 business cards and 2 tote bags. Somebody said "circle back".', 'cash': 0, 'sanity': -2},
    },

    # --- Health / self --------------------------------------------------------
    {
        'key': 'gym_membership', 'icon': '🏋️', 'category': 'health',
        'title': 'New year, new you?',
        'body': 'The gym has a student deal: $30 this month. You have walked past it 200 times.',
        'teaser': 'Your body is about to make a request 💪',
        'left': {'label': 'Walk instead', 'outcome': 'Free, fresh air, and you found a cat. Great workout.', 'cash': 0, 'sanity': 3},
        'right': {'label': 'Sign up', 'outcome': 'You went 4 times. Your legs still remember.', 'cash': -30, 'sanity': 5},
    },
    {
        'key': 'all_nighter', 'icon': '🌙', 'category': 'school',
        'title': 'Deadline tomorrow',
        'body': "Your essay is due at 9am. You've written the title. It's 10pm.",
        'teaser': 'A deadline is creeping up on you 📝',
        'left': {'label': 'All-nighter', 'outcome': 'You submitted at 8:59. Your soul left your body at 4am.', 'cash': 0, 'sanity': -7},
        'right': {'label': 'Ask for an extension', 'outcome': 'The professor said yes. Asking was the hardest part.', 'cash': 0, 'sanity': 3},
    },
    {
        'key': 'touch_grass', 'icon': '🌱', 'category': 'health',
        'title': 'Screen time report',
        'body': 'Your phone says you averaged 9 hours of screen time a day. It sounds disappointed.',
        'teaser': 'Your phone has some feedback for you 📊',
        'left': {'label': 'Touch grass', 'outcome': 'You went outside. The sky is still there. Highly recommend.', 'cash': 0, 'sanity': 6},
        'right': {'label': 'Scroll harder', 'outcome': 'You learned how to make bread from a raccoon. Unclear if useful.', 'cash': 0, 'sanity': -4},
    },
    {
        'key': 'therapy_app', 'icon': '🛋️', 'category': 'health',
        'title': 'Rough week',
        'body': 'Everything feels heavy this week. A campus counselling slot just opened up.',
        'teaser': 'Next week might feel heavy. Be gentle with yourself 💜',
        'left': {'label': 'Book the slot', 'outcome': 'You talked. It helped more than you expected.', 'cash': 0, 'sanity': 8},
        'right': {'label': 'Push through', 'outcome': "You got through it. It's okay to ask for help next time.", 'cash': 0, 'sanity': -5},
    },
    {
        'key': 'sick_day', 'icon': '🤒', 'category': 'health',
        'title': 'Scratchy throat',
        'body': "You wake up feeling rough. There's a shift today.",
        'teaser': "Your immune system isn't feeling great 🤧",
        'requires': 'job',
        'left': {'label': 'Call in sick', 'outcome': 'Soup, blankets, and unpaid rest. Your body says thanks.', 'cash': -40, 'sanity': 4},
        'right': {'label': 'Power through', 'outcome': 'You got paid and also gave it to three coworkers.', 'cash': 0, 'sanity': -6},
    },
    {
        'key': 'haircut', 'icon': '💇', 'category': 'self',
        'title': 'Hair situation',
        'body': 'Your hair has entered its "creative" phase. A proper cut is $45.',
        'teaser': 'A mirror is about to be honest with you 🪞',
        'left': {'label': 'Kitchen scissors', 'outcome': "It's... a look. Hats exist.", 'cash': 0, 'sanity': -3},
        'right': {'label': 'Book the barber', 'outcome': 'Fresh cut. You look employable and emotionally stable.', 'cash': -45, 'sanity': 5},
    },

    # --- Home ------------------------------------------------------------------
    {
        'key': 'landlord_text', 'icon': '🏚️', 'category': 'home',
        'title': 'The landlord texts',
        'body': 'The sink is leaking. Your landlord replies "will look into it" with the energy of a man who will not.',
        'teaser': 'Your landlord has news 👀',
        'requires': 'rental',
        'left': {'label': 'Bucket solution', 'outcome': 'The bucket fills every 6 hours. You are now a plumber, emotionally.', 'cash': 0, 'sanity': -4},
        'right': {'label': 'Call a plumber', 'outcome': 'Fixed in 20 minutes. You pay, then send the landlord the receipt. Bold.', 'cash': -75, 'sanity': 3},
    },
    {
        'key': 'roommate_dishes', 'icon': '🍽️', 'category': 'home',
        'title': 'The dishes',
        'body': 'The dishes have been in the sink for 6 days. They are developing a culture.',
        'teaser': 'Something in the kitchen is evolving 🦠',
        'left': {'label': 'Just do them', 'outcome': 'Clean kitchen, quiet resentment. Very adult of you.', 'cash': 0, 'sanity': -2},
        'right': {'label': 'Passive-aggressive note', 'outcome': 'The note started a war. The dishes remain.', 'cash': 0, 'sanity': -4},
    },
    {
        'key': 'thrift_furniture', 'icon': '🛋️', 'category': 'home',
        'title': 'Free couch!',
        'body': 'Someone left a "FREE" couch on the sidewalk. It looks fine. Mostly.',
        'teaser': 'The sidewalk has an offer for you 🛋️',
        'left': {'label': 'Leave it', 'outcome': 'You live another week without bed bugs. Smart.', 'cash': 0, 'sanity': 0},
        'right': {'label': 'Carry it home', 'outcome': 'It smells like 2009, but it is YOUR couch now.', 'cash': 0, 'sanity': 4},
    },
    {
        'key': 'moving_home', 'icon': '🏠', 'category': 'home',
        'title': 'Mom calls',
        'body': '"You know your old room is still here." She means it kindly. You feel it anyway.',
        'teaser': 'Your mom is about to call 📞',
        'requires': 'no_rental',
        'left': {'label': 'Stay home a bit', 'outcome': 'Free food, free laundry, zero privacy. You call it "saving".', 'cash': 40, 'sanity': -2},
        'right': {'label': 'Start apartment hunting', 'outcome': 'You save 14 listings. One has a "cozy" (tiny) bedroom.', 'cash': 0, 'sanity': 2},
    },

    # --- Weird / rare ------------------------------------------------------------
    {
        'key': 'found_twenty', 'icon': '💵', 'category': 'luck',
        'title': 'Old jacket',
        'body': "You find $20 in a jacket pocket from last winter. Past you was looking out for you.",
        'teaser': 'Past you left something for future you 🧥',
        'left': {'label': 'Save it', 'outcome': 'Into the savings it goes. Future you will never know.', 'cash': 20, 'sanity': 1},
        'right': {'label': 'Treat yourself', 'outcome': 'Bubble tea and a pastry. Past you would be proud.', 'cash': 0, 'sanity': 4},
    },
    {
        'key': 'viral_post', 'icon': '🔥', 'category': 'luck',
        'title': 'You went viral',
        'body': 'Your rant about the cost of eggs got 400k views. A brand slides into your DMs.',
        'teaser': 'The internet is about to notice you 📈',
        'left': {'label': 'Stay mysterious', 'outcome': 'You fade back into obscurity. Your aura remains intact.', 'cash': 0, 'sanity': 2},
        'right': {'label': 'Sponsored post', 'outcome': "You hold up a protein bar and say 'game changer'. $150. Sold out.", 'cash': 150, 'sanity': -2},
    },
    {
        'key': 'scratch_card', 'icon': '🎟️', 'category': 'luck',
        'title': 'Scratch card',
        'body': 'The corner store has $5 scratch cards. The cashier says "feeling lucky?"',
        'teaser': 'The corner store wants to test your luck 🍀',
        'left': {'label': 'Not today', 'outcome': 'You keep the $5. Math wins again.', 'cash': 0, 'sanity': 0},
        'right': {'label': 'Scratch it', 'outcome': 'You won $5. You broke even and somehow feel like a genius.', 'cash': 0, 'sanity': 3},
    },
    {
        'key': 'void_scream', 'icon': '🕳️', 'category': 'void',
        'title': 'The Void calls',
        'body': "Today's Void prompt: 'What's the dumbest thing you bought this month?' Everyone's confessing.",
        'teaser': 'The Void has a question for you 🕳️',
        'left': {'label': 'Lurk', 'outcome': "Someone bought a $200 lamp shaped like a duck. You feel better.", 'cash': 0, 'sanity': 2},
        'right': {'label': 'Confess', 'outcome': '43 people replied "same". You are not alone in the Void.', 'cash': 0, 'sanity': 5},
    },
]

CARDS_BY_KEY = {c['key']: c for c in CARDS}
