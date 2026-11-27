"""
Everything the cast can text. cast.py picks from these after a week ends, and never sends a line a
player has received in the last 30 days (so add freely: more lines = more variety).

LINES[(character, situation)] = [(body, [reply, reply]), ...]
    character: mom, bestie (Jordan), roommate (Sam), ex (Riley)
    reply: (label, their answer or None, relationship, sanity, cash)
Bodies may use {age} (birthdays) and {what} (the missed bill).

Writing rules: reads like a real text (lowercase is fine, short, emoji sparingly), funny, kind.
"""

LINES = {
    # ------------------------------------------------------------------------------------------ Mom
    ('mom', 'birthday'): [
        ("HAPPY {age}TH BIRTHDAY MY BABY 🎂🎂 I sent you a little something. call me!!", [
            ('Calling now ❤️', "best gift is hearing your voice. (the $50 is also nice)", 6, 5, 50), ('ty mom', "ok. love you. the $50 is for food not 'experiences'", 1, 0, 50)]),
        ("HAPPY BIRTHDAY!! {age} years ago you ruined my sleep forever 🥳 money is in your account", [
            ('Sorry about that ❤️', "worth it. mostly. eat cake", 6, 5, 50), ('you love it', "I do. don't tell your father", 3, 2, 50)]),
        ("my baby is {age}. I'm not crying, I'm cutting onions. at the office. HAPPY BIRTHDAY 🎉", [
            ('Love you mom', "love you more. wear something warm", 6, 5, 50), ('put the onions down', "never. happy birthday", 2, 3, 50)]),
        ("Happy {age}th!! I found your baby photos and sent them to the family group. you're welcome 📸", [
            ('MOM no', "your aunt says you were a very round baby", 6, 5, 50), ('Iconic, honestly', "THAT'S my child", 6, 4, 50)]),
        ("HAPPY BIRTHDAY SWEETHEART. at {age} I already had a sofa. no pressure. here's $50 toward a sofa", [
            ('Sofa fund activated', "good. get a washable one", 6, 5, 50), ('noted, no pressure', "none at all. (some)", 1, 0, 50)]),
        ("{age}!!! blow a candle for me. if you don't have a candle use the toaster. actually don't", [
            ('No toasters were harmed', "good. proud of you", 6, 5, 50), ('too late', "I'm calling the fire department and also you", 2, 2, 50)]),
    ],
    ('mom', 'missed'): [
        ("honey the bank called about {what}?? is everything ok 😟", [
            ("It's handled 😅", "ok... you'd tell me if it wasn't right?", -1, -1, 0), ('...can you spot me $150?', "just this once. and we're talking about a budget at thanksgiving", -4, 0, 150)]),
        ("a letter about {what} came to MY house. why does it have my address 😳", [
            ('Old habits. Sorting it', "sort it before your father opens it", -1, -1, 0), ('...could you cover $150?', "I will. you will be washing my car until you're 40", -4, 0, 150)]),
        ("I had a feeling. a mother knows. is it {what}?", [
            ('How do you DO that', "I can't tell you. fix it ok?", 1, -1, 0), ("It's under control", "your voice is doing the thing. call me", -1, -2, 0)]),
        ("sweetie about {what}. I'm not angry. I'm sitting down.", [
            ('I have a plan', "a plan! on paper? good", 2, 1, 0), ('Please stay seated', "oh no.", -3, -2, 0)]),
        ("your aunt says people who miss {what} end up on the news. I told her to mind her business. but also pay it", [
            ('Paying it, I promise', "that's my kid. aunt can choke on that", 2, 0, 0), ('Which news channel', "not funny. a bit funny", -1, 1, 0)]),
        ("do you need me to remind you about {what}? I can set alarms. many alarms", [
            ('One alarm is enough', "I have set eleven", 1, -1, 0), ("I'm an adult mom", "an adult with a late bill. love you", -2, -1, 0)]),
        ("money stuff happens. {what} will survive until you call me back. right?", [
            ('Calling you tonight', "good. bring your numbers, I'll bring snacks", 5, 3, 0), ('Right. Probably.', "'probably' is not a payment method", -1, -1, 0)]),
        ("I lit a candle for {what}. it's the least I can do. actually it is the least", [
            ('Appreciate the candle', "it's scented. you're welcome", 2, 1, 0), ('Cash would also work', "bold. no", -2, 0, 0)]),
    ],
    ('mom', 'payday'): [
        ("payday!! proud of you. put some in savings ok? ❤️", [('I will mom ❤️', "that's my kid", 3, 0, 0), ('lol no', "I didn't raise you to say lol no to me", -2, 1, 0)]),
        ("is today the money day?? buy one vegetable with it for me", [('Buying a whole broccoli', "a whole one! look at you", 3, 1, 0), ('Fries are a vegetable', "I'm turning this car around", -1, 2, 0)]),
        ("you got paid. I can feel it. don't buy a drone", [('No drones, promise', "or a second drone", 2, 0, 0), ('What about a small drone', "NO", -1, 2, 0)]),
        ("payday tip from your mother: save first, spend what's left. your father does it backwards. look at him", [('Wise woman', "write that down", 3, 0, 0), ('Poor dad', "he's fine. he has me", 1, 1, 0)]),
        ("money's in? remember the electricity is not optional", [('Bills first, I swear', "my work here is done", 3, 0, 0), ('Candles exist', "I'm not raising a pirate", -2, 1, 0)]),
        ("proud of my working child 🥹 treat yourself to one (1) small thing", [('One small thing', "show me a photo", 3, 2, 0), ('Define small', "smaller than you're thinking", 0, 1, 0)]),
        ("I saw an article about emergency funds. I printed it. it's coming in the mail", [("Can't wait to ignore it", "I highlighted it. you can't", -1, 1, 0), ("I've started one", "I'm framing this text", 5, 1, 0)]),
        ("payday! if anyone asks you to 'invest' today the answer is call your mother", [('Noted. Calling first', "perfect. I'm a very good filter", 3, 0, 0), ('Even if it is a sure thing?', "ESPECIALLY then", 1, 0, 0)]),
        ("happy payday. your cousin spent theirs in one afternoon. be better than your cousin", [('Low bar, clearing it', "high jump champion", 3, 1, 0), ('Cousin had fun though', "cousin has no towels", -1, 1, 0)]),
        ("did you pay yourself first? like the lady on the podcast said", [('You listen to podcasts?', "I'm very current. save something", 2, 1, 0), ('I paid the pizza place first', "I'm going to pretend I didn't see that", -2, 2, 0)]),
    ],
    ('mom', 'casual'): [
        ("how do I send a photo. I've sent your aunt a video of the floor for 3 minutes", [('Press the camera button', "which camera. there are two cameras", 3, 1, 0), ('Keep the floor, it is art', "your aunt did say it was calming", 2, 2, 0)]),
        ("are you drinking water. real water. coffee is not water", [('Drinking some now', "good. I can hear you not doing it", 2, 1, 0), ('Coffee is bean water', "I'm mailing you a bottle", 0, 2, 0)]),
        ("I saw someone who looked like you. I waved. it was not you. he waved back. we're friends now", [('Mom you cannot collect strangers', "his name is Devon. he says hi", 2, 3, 0), ('Say hi to Devon', "he asked if you have a pension", 3, 2, 0)]),
        ("what is a 'situationship'. your cousin says they're in one. is it contagious", [('Very. Wash your hands', "I'm calling your cousin", 1, 2, 0), ("It's complicated mom", "everything with you lot is complicated", 1, 1, 0)]),
        ("thumbs up if you're alive 👍", [('👍', "wonderful. now a full sentence", 3, 0, 0), ('Alive and thriving', "thriving! screenshotting this", 4, 1, 0)]),
        ("your old bedroom is now my craft room. I thought you should hear it from me", [('My posters!', "they're safe. one is a coaster", -1, 1, 0), ('Slay, craft queen', "I've made 40 candles. please take some", 4, 2, 0)]),
        ("I made too much food. I'm not asking you to visit. I'm just saying there is lasagne", [('On my way', "bring the containers back this time", 5, 5, 0), ('Save me some', "I'll guard it from your father", 2, 2, 0)]),
        ("do you have a doctor. an actual one. not the internet", [('I have an appointment', "I'm so proud I might faint. good thing you have a doctor", 4, 0, 0), ('WebMD has been great', "oh my goodness", -2, -1, 0)]),
        ("I joined a pottery class. I made a bowl. it is mostly a plate. it is yours", [('I will treasure the plate-bowl', "it leaks. treasure it anyway", 4, 3, 0), ('Is soup allowed', "not even a little", 2, 3, 0)]),
        ("random question: do you still have your passport. don't ask why", [('...why', "no reason. your uncle. don't worry", 1, 0, 0), ("Somewhere. Probably.", "FIND IT", 0, -1, 0)]),
        ("the neighbour's child just bought a flat. I'm only telling you because I'm petty", [('Petty queen', "thank you. I've been practising", 2, 2, 0), ("I'm getting there", "I know. you're the better child anyway", 4, 2, 0)]),
        ("I've learned a new word: 'delulu'. am I using it right: your father is delulu", [('Perfect usage', "I will be using it constantly", 3, 3, 0), ('Please never say it again', "delulu delulu delulu", 1, 3, 0)]),
        ("it's cold. wear a coat. I don't care if it's not cold where you are", [('Coat on', "good child", 2, 0, 0), ("It's 30 degrees", "a light coat", 1, 2, 0)]),
        ("do you want grandma's old blender. it has one speed: violence", [('Yes. Obviously.', "I'll wrap it in a towel for everyone's safety", 3, 2, 0), ('I fear the blender', "wise. grandma did too", 2, 2, 0)]),
        ("I had a dream you were a dentist. just checking you're not a dentist", [('Not that I know of', "ok good. it was stressful. you kept charging me", 2, 2, 0), ('Open wide', "STOP", 3, 3, 0)]),
        ("sending you a recipe. step one is 'caramelise onions'. I know. I know. try", [('Trying tonight', "take a photo of the smoke", 3, 2, 0), ('Step one defeated me', "start with toast then", 1, 1, 0)]),
        ("your father tried to fix the sink. we now have two sinks' worth of water", [('Call a plumber', "he says he IS a plumber now", 2, 3, 0), ('Send video', "sending. he can't know it's you", 3, 3, 0)]),
        ("just checking in. no reason. no agenda. (when did you last call)", [('Calling now', "oh! I wasn't ready. 20 minutes", 5, 4, 0), ('Soon, I promise', "'soon' is not a date", -1, 0, 0)]),
        ("I downloaded an app that tells me where my family is. I deleted it. too much power", [('Thank you for your restraint', "it was very tempting", 3, 2, 0), ('Mom that is chilling', "you were at a taco place. at 1am. that's all I saw", -1, 1, 0)]),
        ("how's work. and don't say 'fine'. 'fine' is a lie word", [('Honestly? Busy', "that's allowed. eat lunch", 3, 2, 0), ('Fine', "I'm putting the kettle on, call me", -1, 0, 0)]),
        ("I've started walking in the mornings. I know every dog's name and no human's", [('Who is the best dog', "Biscuit. no contest", 3, 3, 0), ('Proud of you', "you made my morning", 5, 2, 0)]),
        ("if you ever feel stuck, remember you once got stuck in a laundry basket for an hour and got out", [('Inspirational', "I took photos first", 3, 4, 0), ('You left me in there?', "it was 20 minutes of quiet. I needed it", 2, 3, 0)]),
        ("I'm making a family group chat for recipes only. your uncle has already posted a car", [('Leave him, it is a nice car', "it is. don't tell him", 2, 2, 0), ('Remove him', "I don't know how. send help", 2, 2, 0)]),
        ("quick: is it 'LOL' when someone's hamster dies? I may have sent it", [('MOM', "I thought it was lots of love!!", 2, 4, 0), ('Send flowers. Now.', "on it. never texting again", 3, 3, 0)]),
        ("I kept your first drawing. it's a horse. or a chair. either way, masterpiece", [("It was clearly a horse-chair", "visionary", 4, 3, 0), ('Sell it, I need rent', "never. it's priceless. zero dollars", 1, 1, 0)]),
    ],

    # --------------------------------------------------------------------------------------- Jordan
    ('bestie', 'birthday'): [
        ("HBD 🎉 another year closer to a 401k. drinks on me this weekend", [("I'm holding you to that", "bet. I'll bring my coupon app", 4, 3, 0), ("Can't afford to age", 'none of us can. happy birthday anyway', 2, 1, 0)]),
        ("happy {age}th you ancient creature 🦖 your knees are officially a topic now", [('My knees are fine (crack)', "heard that from here", 3, 3, 0), ('Rude. Accurate.', "that's friendship", 4, 2, 0)]),
        ("it's your birthday so I'm legally required to be nice. you're ok I guess ❤️", [('Frame this', "do not screenshot", 4, 4, 0), ('Say more', "you're pushing it. fine. love you", 5, 3, 0)]),
        ("{age}!!! I got you a gift. it's a surprise. it's me showing up. surprise", [('Best gift (cheap)', "priceless. literally free", 4, 4, 0), ('Bring cake or leave', "demanding at {age}. respect. cake it is", 3, 3, 0)]),
        ("happy birthday!! remember when we said we'd have it together by now 😂", [('Define together', "owning matching socks. neither of us made it", 4, 3, 0), ('Speak for yourself', "oh you have a spreadsheet now. look at you", 1, 2, 0)]),
        ("HBD. I wrote you a poem. roses are red, you're {age} now, I forgot the rest, wow", [('Beautiful. Weeping.', "I'm available for weddings", 4, 3, 0), ('Refund please', "no refunds on art", 2, 2, 0)]),
    ],
    ('bestie', 'rough'): [
        ("you've been quiet this week. you ok?", [('Not really tbh', "ok I'm coming over with snacks. no arguments", 5, 6, 0), ('All good!', "...ok. I'm here if that changes", -1, -2, 0)]),
        ("your last 'haha' had no h's behind it. what's going on", [('It was a rough one', "scream into this chat. I'm ready", 5, 5, 0), ('Haha', "that's worse. I'm calling", 1, 1, 0)]),
        ("emergency friend check. rate your week out of 10 and no lying", [('A solid 3', "3s get ice cream. non negotiable", 4, 5, 0), ('11!! (lie)', "the lie detector is just me and I detect it", 0, 0, 0)]),
        ("I can smell burnout from here. it smells like cold coffee", [('Guilty', "phone down, shoes on, we're walking", 4, 6, 0), ("I'm fine it's fine", "famous last words of a fine person", 0, -1, 0)]),
        ("do you need advice, snacks or silence. pick one, I deliver all three", [('Snacks', "excellent choice. crisps incoming", 4, 5, 0), ('Silence', "...", 3, 4, 0)]),
        ("hey. whatever it is, it's not your whole life. it's a week. a stupid week", [('Needed that', "anytime. I charge in hugs", 6, 6, 0), ('Very stupid week', "the stupidest. we'll get a better one", 4, 3, 0)]),
        ("I'm sending you 14 videos of cats. do not reply until you've watched them", [('The cats healed me', "science", 4, 7, 0), ('I have no time for cats', "everyone has time for cats", -1, 2, 0)]),
        ("when did you last sleep like a person", [('Define person', "horizontal, dark room, no phone. try it", 2, 3, 0), ('Tonight, I promise', "I'll be checking. creepily", 3, 4, 0)]),
        ("you ghosted the meme I sent. now I'm worried. it was a GOOD meme", [("Sorry, rough week", "forgiven. the meme will wait. will you tell me about it", 5, 4, 0), ('It was mid', "ok you're clearly unwell", -2, 1, 0)]),
        ("reminder: you're allowed to be bad at adulting some weeks. I'm bad at it most", [('You really are', "wow. but yes. we're a team of disasters", 4, 5, 0), ('Thank you', "that's what the group chat of two is for", 5, 4, 0)]),
    ],
    ('bestie', 'broke'): [
        ("bro your bank account just called me crying 💀", [('help 😭', "free activities this weekend. I'm thinking park + sad sandwiches", 3, 3, 0), ("I'm fine. Totally fine.", "that's what the titanic said", 0, -1, 0)]),
        ("saw your spending. spiritually. are we ok", [('We are not ok', "ok: pasta night at yours, everyone brings one tomato", 3, 3, 0), ('It was an investment', "in what. in WHAT", 1, 1, 0)]),
        ("your wallet filed a missing persons report", [('For itself, yes', "I'll put up posters", 3, 3, 0), ("It'll turn up", "on payday, briefly", 1, 1, 0)]),
        ("congrats on funding the local economy single handedly", [('Someone had to', "the mayor would like a word", 3, 3, 0), ('No regrets', "some regrets. a few. I can see them", 1, 1, 0)]),
        ("I have a financial plan for you: step one, stop. step two, see step one", [('Revolutionary', "I'll be doing a talk", 2, 2, 0), ('What about treats', "treats are in step three. there is no step three", 2, 2, 0)]),
        ("are we in our broke era? because I have matching outfits for it", [('Broke and iconic', "matching. frugal. unstoppable", 4, 4, 0), ('Speak for yourself', "your last purchase says otherwise", -1, 0, 0)]),
        ("if you need dinner I have rice and a dangerous amount of confidence", [('On my way', "bring a fork. I only have one", 4, 4, 0), ('I have noodles at home', "look at us. chefs", 2, 2, 0)]),
        ("remember that thing you bought? how is it. was it worth the soup diet", [('Worth every sip', "I respect the commitment", 2, 3, 0), ('We do not speak of it', "understood. moment of silence", 3, 1, 0)]),
        ("I'm hosting a 'free things only' weekend. attendance mandatory", [("What's on", "library, sunset, and judging dogs", 4, 5, 0), ('Can I pay to skip', "the whole point has escaped you", -1, 1, 0)]),
        ("your account balance is giving 'minimalist'", [('Aesthetic choice', "very clean. very empty", 3, 3, 0), ('Ouch', "love you. the numbers don't", 1, 0, 0)]),
    ],
    ('bestie', 'social'): [
        ("last night was LEGENDARY 😂 we're never doing that again (we're doing it again)", [('Same time next week?', "my wallet says no. my heart says yes", 4, 2, 0), ('My wallet is in the ER', 'tell it to stay strong', 2, 0, 0)]),
        ("I have your left shoe. I have questions", [('Keep it, I need closure', "I'm putting it on a shelf", 3, 3, 0), ("That's not my shoe", "oh no. then whose shoe is this", 2, 3, 0)]),
        ("we told a stranger our whole life stories. his name is Gary. he follows me now", [('Gary seemed nice', "Gary has opinions about your ex", 3, 3, 0), ('Block Gary', "I can't. he gave us fries", 2, 2, 0)]),
        ("do you remember promising to start a podcast with me", [('I remember nothing', "good because I bought a microphone", 2, 3, 0), ('Episode one drops never', "bold of you to think I'll let this go", 3, 3, 0)]),
        ("my head. my money. my dignity. all gone. 10/10 night", [('Worth it', "say it again but quieter", 3, 2, 0), ('Never again', "see you friday", 2, 2, 0)]),
        ("you sang. loudly. there is footage. it will be used at your wedding", [('Delete it', "it's already in three clouds", 1, 1, 0), ('I was incredible', "you were certainly something", 3, 4, 0)]),
        ("splitwise says you owe me for 'emergency kebab'. it was an emergency", [('Fair, paid', "friendship restored", 3, 0, -12), ("I don't recall the kebab", "the kebab recalls you", -2, 1, 0)]),
        ("I woke up with a traffic cone. we should talk about it", [('Return it quietly', "mission accepted. wearing black", 3, 3, 0), ('Name it', "its name is Colin", 4, 4, 0)]),
    ],
    ('bestie', 'casual'): [
        ("yo if I sell one kidney can we get a boat. hypothetically", [('Both of us sell one. Matching', "that's the friendship I signed up for", 4, 4, 0), ('Absolutely not', "boring. correct. boring", 1, 1, 0)]),
        ("I've been staring at a spreadsheet so long the cells have started to blink", [('Go outside', "what's outside. is it formatted", 2, 2, 0), ('Same, solidarity', "two zombies. one excel", 3, 1, 0)]),
        ("quick vote: is cereal for dinner a cry for help", [("It's a lifestyle", "THANK you", 3, 3, 0), ('Yes. Come eat real food', "you had me at free", 4, 2, 0)]),
        ("I downloaded a language app. I can now say 'the duck is sad' in three languages", [('Is the duck ok', "no. none of them are", 3, 4, 0), ('Useful for travel', "extremely, if you meet a sad duck", 3, 3, 0)]),
        ("rate my new haircut: ●", [('10/10 very round', "it's what the barber chose for me", 3, 3, 0), ('I need a photo', "you couldn't handle it", 2, 2, 0)]),
        ("do you ever think pigeons are just city chickens with trust issues", [('Constantly', "my person", 4, 3, 0), ('Please sleep', "can't. pigeons", 1, 2, 0)]),
        ("I said 'you too' when the waiter said enjoy your meal. I'm moving countries", [('He has a meal sometimes', "that's... actually comforting", 4, 3, 0), ("I'll help you pack", "you're so supportive it's suspicious", 2, 3, 0)]),
        ("we're old now. I got excited about a sponge today", [('Which sponge', "the good kind. with the scratchy side", 3, 3, 0), ('Embarrassing', "you own a favourite mug. don't start", 3, 3, 0)]),
        ("if I text you 'banana' at a party it means rescue me", [('Understood. Banana protocol', "you're the only one I trust with this", 5, 3, 0), ("What if you want a banana", "then I'll say 'the yellow one'", 3, 3, 0)]),
        ("my plant has a new leaf. I'm basically a farmer", [('Congrats farmer', "taking my first harvest in 2041", 3, 3, 0), ('Overwatering it, probably', "how dare you. yes", 1, 1, 0)]),
        ("what's your villain origin story. mine is the self checkout", [('Group projects', "valid. terrifying", 3, 3, 0), ('A printer', "say no more", 4, 3, 0)]),
        ("I joined a gym. I've been once. I'm paying to feel guilty", [("I'll go with you", "oh no. accountability", 4, 3, 0), ('Cancel it', "they require a written essay and my firstborn", 2, 2, 0)]),
        ("send me a song. no skips. I trust you with my commute", [('Sending an absolute banger', "if it's whale sounds I'm blocking you", 4, 4, 0), ("I only have one song", "play it until we both hate it", 2, 2, 0)]),
        ("reminder that we've been friends so long you've seen my frosted tips era", [('I have the photos', "I'll pay for silence", 3, 4, 0), ('We never speak of it', "bless you", 4, 2, 0)]),
        ("I cooked. nothing caught fire. I want a medal", [('🥇', "I'm adding it to my CV", 3, 3, 0), ('What did you make', "toast. ambitious toast", 3, 3, 0)]),
        ("hypothetical: how much to sleep in a furniture store overnight", [('Free if you commit', "meet me by the beds at closing. kidding. mostly", 3, 4, 0), ('Your bail is not in my budget', "that's fair and also hurtful", 1, 2, 0)]),
        ("you free this week or are you doing 'self care' (a nap)", [('Free! Let us do nothing together', "nothing. my favourite", 5, 4, 0), ('Nap. Do not disturb', "respect the nap", 0, 5, 0)]),
        ("my autocorrect changed 'meeting' to 'meatball' in an email to my boss", [('How was the meatball', "he scheduled a follow up meatball", 3, 4, 0), ('Resign immediately', "already packed my desk plant", 2, 3, 0)]),
        ("I've made a bucket list. item one: find a bucket", [('Aim high', "item two is a bigger bucket", 3, 3, 0), ('I have a spare', "see? this is why we're friends", 4, 3, 0)]),
        ("thinking of becoming a morning person. talk me out of it", [('Mornings are a scam', "knew I could count on you", 3, 2, 0), ("Do it. I believe in you", "ugh, support. gross. thank you", 4, 3, 0)]),
    ],

    # ------------------------------------------------------------------------------------------ Sam
    ('roommate', 'casual'): [
        ("who ate my leftovers. I'm not mad. I'm just disappointed", [('Guilty. Buying you dinner', "apology accepted. extra guac", 5, 0, -15), ('Must have been a ghost', "the ghost left a fork in the sink", -4, 0, 0)]),
        ("band practice at ours friday? it'll be quiet I promise", [('Sure, why not', "you're the best. bring earplugs", 4, -3, 0), ('I have work Saturday', "fair. we'll do the acoustic version (still loud)", -1, 0, 0)]),
        ("the dishes have started a civilisation. they have a flag", [('I will negotiate', "bring sponge. and diplomacy", 3, -1, 0), ('Those are your dishes', "some of them are citizens of your plates", -2, 0, 0)]),
        ("I wrote a bass line at 3am and I need you to hear it. now. you're awake right", [('I am NOW', "ok it goes: bwom. bwom bwom. thoughts?", 3, -3, 0), ('Sam it is 3am', "art doesn't have office hours", -3, -1, 0)]),
        ("we're out of toilet paper. this is not a drill", [("Buying the big pack", "a hero. a soft, 3-ply hero", 5, 0, -12), ('Your turn', "I bought the last one. in March. it was a good one", -3, -1, 0)]),
        ("did you move my charger or has it begun walking", [('It is on your head', "...how long have you let me look", 3, 2, 0), ('Not me', "then the flat is haunted by someone with 12% battery", 0, 0, 0)]),
        ("I adopted a cactus. he lives in the bathroom now. his name is Steve", [('Welcome Steve', "he says thanks. through spikes", 4, 2, 0), ('Why the bathroom', "humidity. also drama", 2, 2, 0)]),
        ("the wifi password is now 'doTheDishes2'. you're welcome", [('Subtle', "it's a lifestyle password", 2, 1, 0), ('I am changing it back', "I'll change it to something worse", -2, 1, 0)]),
        ("I cooked. there's smoke. don't panic. panic a little", [('Opening all windows', "you're a good one", 4, -1, 0), ('What did you do', "I asked an egg to be something it wasn't", 2, 2, 0)]),
        ("can my cousin crash on the sofa for 'a night'", [('One night', "define night", 3, -2, 0), ('Absolutely not', "he's already on the sofa. so", -3, -2, 0)]),
        ("I put your name on the rota. you're 'bins' forever", [('I accept bins', "a true leader", 4, 0, 0), ('I demand a vote', "the vote was held. you weren't there", -2, 1, 0)]),
        ("movie night? I have popcorn and a very strong opinion", [("I'm in", "great. no talking during my favourite bit (all of it)", 5, 5, 0), ('Early night', "traitor. I'll narrate it through the wall", -1, 1, 0)]),
        ("the heating is on 28 degrees. was that you. are you a lizard", [('I am a lizard', "respect. split the bill, lizard", 1, 1, -10), ('Turning it down', "my wallet loves you", 3, 0, 0)]),
        ("someone's used my expensive shampoo and now they smell incredible", [('Replacing it, sorry', "forgiven. you do smell amazing", 4, 0, -10), ('I smell like this naturally', "you smell like $14 of coconut", -2, 2, 0)]),
        ("learning the drums. just so you know. in advance", [('Sam. No.', "too late. they arrive tuesday", -2, -2, 0), ('Electric ones? With headphones?', "...ok fine. compromise legend", 4, 1, 0)]),
        ("I left a banana in my bag for 9 days. we need to talk to the bag", [('Burn the bag', "it's been a good bag. it deserved better", 3, 2, 0), ('I will not be involved', "coward. fair", 0, 1, 0)]),
        ("the neighbour knocked. I hid. we're both hiding now. get down", [('Hiding', "excellent. stay low until they give up", 4, 2, 0), ('I will answer it', "if it's about the drums I don't live here", 1, -1, 0)]),
        ("your plant is dying and it keeps looking at me", [('Water it for me?', "done. it forgave me. it hasn't forgiven you", 4, 1, 0), ('It is resting', "it is resting in peace", -1, 1, 0)]),
        ("I made too much curry. help me or it wins", [('Reporting for curry duty', "two spoons, one pot, no mercy", 5, 5, 0), ('Save me a bowl', "I'll write your name on it. in curry", 3, 3, 0)]),
        ("hypothetically if a mug broke and it was your favourite mug", [('SAM', "it died doing what it loved. holding tea", -3, -1, 0), ('Hypothetically you replace it', "hypothetically I already ordered one", 3, 1, 0)]),
        ("do you hear that. no? exactly. I broke the amp", [('Moment of silence', "enjoy it. new one comes friday", 3, 3, 0), ('This is the best day', "wow. noted. writing a song about you", -2, 3, 0)]),
        ("flat meeting. agenda: 1. bins 2. snacks 3. whether soup is a drink", [('Soup is a drink', "sensible. you may stay", 4, 3, 0), ('Soup is a meal', "we have a lot to discuss", 2, 2, 0)]),
        ("I've been in the shower so long I solved a few things", [('Did you solve the water bill', "that was not among them", 1, 1, 0), ('Share the wisdom', "ducks are just boats that eat bread", 3, 3, 0)]),
        ("I labelled my food. I labelled your food too. yours says 'also Sam's'", [('Absolutely not', "worth a try", 1, 2, 0), ('Fine, sharing is caring', "you've made a powerful enemy of your own snacks", 4, 1, 0)]),
        ("the washing machine ate one of my socks and I need to sit with that", [('A moment for the sock', "he was the left one. he knew", 3, 2, 0), ('Check behind the drum', "I'm not going back in there", 1, 1, 0)]),
        ("I told my mum you're 'the responsible one'. don't ruin it. she's visiting", [('Cleaning now', "you're the best fake adult I know", 5, -2, 0), ('You lied to your mother', "a lie of love. hide the cone", 1, 1, 0)]),
        ("quick question: how do you put out a candle that's on a pizza box", [('WATER. NOW', "handled. the box had a good life", 2, -2, 0), ('Why is it on the box', "ambience", 1, 1, 0)]),
        ("our delivery driver knows my name, my order and my emotional state", [('Tip him extra', "he deserves a pension", 3, 1, -5), ('Cook once this week', "bold words from a cereal-for-dinner person", 0, 1, 0)]),
        ("I'm doing a no-spend week. can I borrow everything you own", [('Take the pasta', "a feast. I'll remember this", 4, 0, 0), ('Defeats the point', "the point is MY wallet", -1, 1, 0)]),
        ("there's a spider in the hall the size of a decision. I've moved out", [('Cup and paper, I got this', "I'll write songs about you", 5, -1, 0), ('He pays rent now', "if he does dishes he can stay", 2, 3, 0)]),
        ("I reorganised the fridge by vibes. milk is with the happy things", [('Where are the sad things', "your lettuce. bottom drawer", 3, 3, 0), ('Put it back', "the milk is thriving, leave it", 0, 1, 0)]),
        ("you left the door unlocked. I locked it. then I locked myself out. help", [('Coming', "I'm sitting on the step reflecting", 4, -1, 0), ('Reflect a bit longer', "the neighbour's cat has joined me. we're fine", -2, 2, 0)]),
        ("I'm trying to keep a sourdough starter alive and I've named it after you", [('Honoured', "it's very needy. good name", 3, 3, 0), ('Rename it', "too late. it answers to it", 1, 2, 0)]),
    ],

    # ---------------------------------------------------------------------------------------- Riley
    ('ex', 'casual'): [
        ("u up?", [('...yeah', "lol remember when we... nvm. goodnight", 6, -6, 0), ('Blocked.', None, -15, 4, 0)]),
        ("saw something that reminded me of you. anyway how's life", [('Good actually. You?', "good. good good. very good. ok bye", 4, -3, 0), ('Busy thriving', "wow. ok. thriving. cool", -6, 3, 0)]),
        ("do you still have my hoodie", [('I do. Come get it', "keep it. it looks better on you. ignore that", 6, -4, 0), ('It is a cleaning rag now', "savage. deserved", -8, 4, 0)]),
        ("random but what was the name of that pizza place", [('Tony\'s. Why', "no reason. taking someone. a friend. a hungry friend", 2, -4, 0), ('Google exists', "ok google. rude google", -5, 2, 0)]),
        ("your netflix profile is still on my account. it has been judging my choices", [('Delete it', "I can't. it knows too much", 1, -2, 0), ('It was right to judge', "wow. true though", 3, 1, 0)]),
        ("not to be weird but your dog sends his regards. well. my dog. our dog. the dog", [('Give him a treat', "he misses you. he's the only one. mostly", 5, -3, 0), ('He was never ours', "tell that to his face. you can't. because he's cute", -4, 0, 0)]),
        ("I'm doing really well. just thought you should know. unprompted", [('Happy for you', "oh. that was... nice. suspicious", 5, -1, 0), ('Cool story', "it's a GREAT story", -4, 2, 0)]),
        ("found a photo of us. you have terrible hair in it", [('So did you', "ok yes. we were a matching disaster", 4, -2, 0), ('Burn it', "already framed it. kidding. maybe", -2, 1, 0)]),
        ("my new partner can't parallel park. just saying. no reason", [('Not my problem', "correct. completely correct. bye", -3, 3, 0), ('Neither can you', "WOW. blocked in my heart", -5, 4, 0)]),
        ("happy random tuesday", [('It is friday', "I knew that", 2, 0, 0), ('Happy tuesday', "see this is why it didn't work. you agree too fast", 3, -2, 0)]),
        ("I took up running. mostly away from my problems. you were one", [('Keep running', "personal best today", -3, 3, 0), ('Proud of you honestly', "...don't be nice, it confuses me", 6, -2, 0)]),
        ("can I have the air fryer", [('Absolutely not', "worth a try. you always did love that thing more", -2, 2, 0), ('Fine, take it', "wait really? are you ok??", 6, -2, 0)]),
        ("your song came on. skipped it. then went back. anyway", [("We had a song?", "WOW", -6, -1, 0), ('Still a good song', "it is. unfortunately", 6, -5, 0)]),
        ("my mum asked about you. I told her you moved to antarctica", [('The penguins say hi', "she believed it. she's knitting you a scarf", 3, 2, 0), ('Tell her the truth', "the truth is boring. antarctica has penguins", 1, 0, 0)]),
        ("I'm only texting because I'm at the dentist and bored", [('Floss, Riley', "you still care. disgusting", 3, 1, 0), ('Do not text under drills', "he's not drilling. yet. oh no", 1, 1, 0)]),
        ("did you take the good scissors", [('Yes. No regrets', "monster. those cut EVERYTHING", -3, 3, 0), ('Check your drawer', "...they were there. we will not discuss this", 2, 2, 0)]),
        ("just so we're clear I won the breakup. I have a plant now", [('I have two plants', "this isn't over", -2, 4, 0), ('Congrats on the plant', "thank you. it's fake. don't tell anyone", 4, 2, 0)]),
        ("I dreamt you apologised. it was beautiful. very unrealistic", [('Sorry for something', "oh my god. is this real", 7, -3, 0), ('Keep dreaming', "I will. nightly. for free", -4, 3, 0)]),
        ("what's your wifi password. asking for no reason from outside", [('RILEY', "joking!! I'm on the bus", 1, -3, 0), ('GetOverIt123', "that one's actually good. rude but good", -4, 4, 0)]),
        ("I saw you liked a photo from 2019. brave", [('Accident', "sure. at 2am. thumbs are wild like that", 3, -4, 0), ('I stand by it', "...it was a good haircut", 6, -3, 0)]),
        ("you left a sock here. one sock. I think it's a message", [('The message is keep it', "I'll treasure the sock", 4, -2, 0), ('Post it', "I'm not paying postage for one sock", -1, 1, 0)]),
        ("we should be friends. like normal people who definitely never cried in a car park", [('Friends. Sure', "great. so normal. loving this", 5, -2, 0), ('Let us not', "yeah no that's smart. ugh. smart", -5, 4, 0)]),
        ("thought you'd like to know the neighbours still hate us. me. hate me", [('They hated me more', "true. you sang in the stairwell", 3, 2, 0), ('Not my neighbours now', "cold. fair. cold", -3, 2, 0)]),
        ("I need a plus one for a wedding. don't. forget I asked", [('Forgotten', "good. great. it's on the 14th if you remember", 2, -3, 0), ('Is there cake', "three tiers. think about it", 5, -4, 0)]),
        ("just finished a self help book. chapter 4 was about you", [('Was I the hero', "you were the 'before'", -3, 2, 0), ('Hope it helped', "...it did actually. thanks", 6, -1, 0)]),
        ("I made your pasta recipe. it's worse when I do it", [('You skip the salt', "SO that's it", 5, -2, 0), ('Some magic cannot be copied', "insufferable. correct", 2, 2, 0)]),
        ("do you ever think about that road trip", [('The flat tyre? Yes', "best worst day", 6, -5, 0), ('Nope', "liar. you still have the keyring", -4, 1, 0)]),
        ("my horoscope said 'reach out'. so. reaching. that's it", [('Your horoscope is messy', "she really is", 3, 0, 0), ('Mine said ignore you', "you made that up. didn't you. DIDN'T YOU", -4, 4, 0)]),
        ("ok last text ever. (not a promise)", [('See you next week', "you know me too well. disgusting", 4, -3, 0), ('Accepted', "oh. you didn't have to accept it THAT fast", -4, 3, 0)]),
        ("I cut my own fringe. I just needed someone to know", [('Send a photo', "never. I'm wearing a hat until spring", 4, 2, 0), ('We have all been there', "...that was weirdly kind", 5, 0, 0)]),
    ],
}
