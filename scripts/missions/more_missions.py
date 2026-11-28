"""
Three more missions (migration 20261216000000_three_missions.sql is generated from this file).

Run:  python3 scripts/missions/more_missions.py > supabase/migrations/20261216000000_three_missions.sql

What the game actually applies (app/game/mission_decisions.py, jobs/monthly_loan_deductions.py):
* a decision option: cash once, and sanity = happiness + motivation/2 - stress;
* goals are checked every game month and at the end, strictly greater/less than the target;
* credit score only moves with loan payments (+2 on time, -25 missed), starting at 650;
* an unanswered decision is made for the player at the end of the month.

Decision option: (label, description, cash, happiness, stress, motivation, risk)
Story event:     (month, title, emoji, narrative, story_type, financial_context, cash, happiness, stress, motivation)
"""
import re
import sys

MISSIONS = [
    {
        'name': 'Credit Comeback', 'icon': '💳', 'category': 'debt_management', 'difficulty': 'beginner', 'months': 8, 'reward': 750,
        'short': 'Borrow small. Repay on time. Watch your score climb.',
        'description': 'Your credit score is a reputation you build one payment at a time. Take small loans, never miss, and get past 665. '
                       'Only payments move the score: Quick Cash plus Emergency Fund gets you there, one of them alone will not.',
        'objectives': ['How a credit score moves', 'Borrow only what you can repay', 'What missed payments cost', 'Why lenders look at your debt-to-income'],
        'flags': {'can_buy_lifestyle_items': False, 'max_loan_amount': 2000},
        'goals': [('credit_score', 'greater_than', 665, 'Credit score above 665', 'About 8 on-time payments from where you start.', '💳'),
                  ('debt_ratio', 'less_than', 0.2, 'Loan payments under 20% of income', 'Lenders like room to breathe.', '⚖️')],
        'decisions': [
            (1, 'The First Loan', 'You want a score, and a score needs history. How do you start?', 'Payments build credit, not borrowing itself.', [
                ('Set up auto-pay first', 'Then borrow. Boring, brilliant.', 0, 2, 0, 4, 'low'),
                ('Borrow now, sort it out later', 'Future you loves surprises.', 0, 1, 4, 0, 'high')]),
            (2, 'The Store Card', 'The cashier offers a store card with 10% off today. The rate is 34%.', 'A discount is not worth a high rate.', [
                ('"No thanks"', 'You pay full price and sleep well.', 0, 1, 0, 3, 'low'),
                ('Sign up for the 10%', 'You save $12 and gain a $30 fee.', -18, 2, 2, 0, 'high')]),
            (3, 'A Tight Month', 'The payment is due and your wallet is thin.', 'Pay on time first; everything else can wait a week.', [
                ('Skip takeaway, pay on time', 'Beans again. Heroic beans.', 40, -2, 0, 4, 'low'),
                ('Pay late, "just this once"', 'A late fee and a stern email.', -35, 0, 5, -2, 'high'),
                ('Sell some old stuff', 'Goodbye, third pair of headphones.', 60, 1, 1, 2, 'low')]),
            (5, 'Check Your Report', 'You can see your credit report for free.', 'Errors happen. Check your report.', [
                ('Read it line by line', 'You find a phone contract you never had, and dispute it.', 0, 2, 1, 4, 'low'),
                ('Ignorance is bliss', 'Bliss, with mystery debts.', 0, 1, 0, -2, 'medium')]),
            (7, 'The Offer Letter', '"Congratulations! You are pre-approved for $20,000!"', 'Pre-approved is not the same as affordable.', [
                ('Shred it', 'Satisfying noise. Strong character.', 0, 3, 0, 3, 'low'),
                ('"Just to see the terms"', 'Three calls a day, forever.', 0, 0, 4, 0, 'high')]),
        ],
        'stories': [
            (1, 'A Blank Page', '📄', 'To a bank you are a mystery: no history, no reputation, no vibes. Time to write the first page.', 'opening',
             'Your score starts at 650. Take a small loan from The Bank.', 0, 0, 0, 6),
            (4, 'The Score Moves', '📈', 'You check your score for the ninth time today. It has gone UP. You tell a stranger on the bus.', 'milestone',
             'Each on-time payment adds 2 points.', 0, 4, 0, 4),
            (6, 'Your Friend Wants a Co-signer', '🙃', '"It is just a signature," says your friend, who once lost a canoe. Co-signing means their debt is yours.', 'crisis',
             'You politely decline. The canoe comes up.', 0, -1, 3, 0),
        ],
    },
    {
        'name': 'Money While You Sleep', 'icon': '😴', 'category': 'passive_income', 'difficulty': 'intermediate', 'months': 6, 'reward': 1500,
        'short': 'Build income that arrives without a shift.',
        'description': 'A salary stops when you stop. Assets keep paying. Build small businesses until they earn more than $150 a month '
                       'and are worth over $2,500. Lifestyle shopping is closed: every spare coin has a job.',
        'objectives': ['Assets pay you, liabilities charge you', 'Reinvest profit', 'Payback time', 'Why one income is a risk'],
        'flags': {'can_buy_lifestyle_items': False},
        'goals': [('passive_income', 'greater_than', 150, 'Over $150 a month while you sleep', 'Count what your businesses earn.', '😴'),
                  ('business_value', 'greater_than', 2500, 'Businesses worth over $2,500', 'Start small: a kiosk or a juice stand.', '🏪')],
        'decisions': [
            (1, 'Pick Your First Hustle', 'You have a little money and big ideas.', 'Check how long it takes to earn back what you pay.', [
                ('Do the maths first', 'Napkin sums: pays back in about two years. Solid.', 0, 1, 0, 5, 'low'),
                ('Go with the vibes', 'The vibes recommend a candle shop for dogs.', -60, 3, 2, 0, 'high')]),
            (2, 'The First Profit', 'Your business paid you. Real money. While you were asleep.', 'Reinvesting profit is how small becomes big.', [
                ('Save it for the next one', 'The empire grows by exactly one brick.', 0, 1, 0, 5, 'low'),
                ('Celebrate properly', 'A dinner costing slightly more than the profit.', -80, 5, 0, 0, 'medium')]),
            (3, 'Broken Equipment', 'Your busiest machine makes a noise like a sad goose.', 'Keep a repair fund: assets need looking after.', [
                ('Repair it properly', 'The goose is silenced.', -120, 0, 0, 3, 'low'),
                ('Tape and hope', 'It holds. Mostly. Customers ask about the goose.', 0, 0, 4, 0, 'high')]),
            (4, 'The Guru', 'A man in a rented sports car sells a course: "$10k a month, no work".', 'If it needs no work and cannot fail, it is selling you.', [
                ('Walk away', 'He calls you "poor-minded". You keep your money.', 0, 2, 0, 3, 'low'),
                ('Buy the course', 'Page one: "sell this course to others".', -300, 0, 4, -2, 'high')]),
            (5, 'Second Stream', 'One business is nice. What about two?', 'Different income streams rarely all fail at once.', [
                ('Add something different', 'Coffee in the morning, laundry at night.', 0, 2, 1, 4, 'medium'),
                ('Another of the same', 'Two identical stands, 40 metres apart. They compete.', 0, 0, 2, 1, 'high')]),
        ],
        'stories': [
            (1, 'Clocking Out Forever?', '⏰', 'Your alarm rings. You dream of money that does not need one.', 'opening',
             'Buy businesses from Investments.', 0, 0, 0, 6),
            (3, 'A Slow Month', '🌧️', 'It rained for nine days. Nobody wants juice in a flood. Businesses swing: that is the deal.', 'crisis',
             'Profit varies month to month.', 0, -2, 3, 0),
            (5, 'A Regular Customer', '🥹', 'Someone orders "the usual". You have a usual. You are basically a landmark.', 'milestone',
             'Steady customers, steady income.', 0, 6, 0, 4),
        ],
    },
    {
        'name': 'Diamond Hands', 'icon': '💎', 'category': 'investment', 'difficulty': 'advanced', 'months': 8, 'reward': 2000,
        'short': 'Invest, then do the hardest thing: wait.',
        'description': 'Markets crash, friends panic and your thumb hovers over "sell". For eight months you cannot sell or borrow. '
                       'Keep over $5,000 invested at the end, however loud it gets. Spread it out: one bet can sink the lot.',
        'objectives': ['Time in the market', 'Diversification', 'Investing a little regularly', 'Hype and panic are expensive'],
        'flags': {'can_sell_assets': False, 'can_take_loans': False},
        'goals': [('asset_value', 'greater_than', 5000, 'Over $5,000 invested at the end', 'Today\'s prices count, so leave some margin.', '💎')],
        'decisions': [
            (1, 'The Plan', 'How will you put your money in?', 'Investing regularly beats guessing the perfect day.', [
                ('A little every month', 'Dull. Effective. Your future self sends a fruit basket.', 0, 1, 0, 5, 'low'),
                ('Wait for the perfect moment', 'You watch charts until 3am. The moment does not text back.', 0, 0, 4, 0, 'high')]),
            (2, 'All Eggs', 'One coin is up 40% this week. Put everything in?', 'Spreading money across things softens the falls.', [
                ('Spread it out', 'Stocks, a property, a business. Sensible shoes for money.', 0, 1, 0, 3, 'low'),
                ('ALL IN', 'You name the coin. Never name the coin.', 0, 4, 5, 0, 'high')]),
            (4, 'Fees', 'Your app offers "premium trading" for $15 a month.', 'Small fees compound too, the wrong way.', [
                ('Keep it simple', 'No fee, no confetti, same market.', 0, 1, 0, 2, 'low'),
                ('Go premium', 'The charts are now in dark mode. Worth it?', -45, 2, 0, 0, 'medium')]),
            (6, 'The Group Chat Is Screaming', 'Everyone is selling. Someone posted a crying cat.', 'A panic sale makes a temporary dip a real loss.', [
                ('Mute the chat', 'Silence. Then a nap. Elite strategy.', 0, 3, 0, 4, 'low'),
                ('Doom-scroll all night', 'You cannot sell anyway. You suffer for free.', 0, -2, 6, 0, 'high')]),
            (8, 'The Finish Line', 'Eight months. You did not sell once.', 'Patience is the part most people skip.', [
                ('Keep holding', 'It turns out not looking is a superpower.', 0, 4, 0, 6, 'low'),
                ('Celebrate with a big spend', 'You earned a treat. A reasonable one. Was it?', -150, 6, 0, 0, 'medium')]),
        ],
        'stories': [
            (1, 'Seat Belt On', '🎢', 'You cannot sell for eight months. This is either discipline or a very long roller coaster.', 'opening',
             'Buy from Investments. Selling is locked.', 0, 0, 0, 6),
            (3, 'The Crash', '📉', 'Red. Everything is red. Your uncle says it is the end of money. He said that last year about oat milk.', 'crisis',
             'Prices move every game week. Falls are normal.', 0, -3, 6, 0),
            (5, 'The Hype', '🚀', 'Your barber is giving crypto advice with scissors in hand. Everyone is a genius this week.', 'opportunity',
             'When everyone is certain, be careful.', 0, 3, 1, 2),
            (7, 'The Quiet Recovery', '🌱', 'No headlines. No crying cats. Your numbers creep back up while you were doing laundry.', 'reflection',
             'Waiting did the work.', 0, 6, -2, 3),
        ],
    },
]

# -------------------------------------------------------------------------------------------------
EDITOR_TRAP = re.compile(r'\b(?:into|table)\s+([\w.]+)', re.I)
STORY_TYPES = {'opening', 'emotional', 'milestone', 'decision_point', 'crisis', 'opportunity', 'reflection'}


def q(v):
    return "'" + str(v).replace("'", "''") + "'"


def check():
    for m in MISSIONS:
        months = [d[0] for d in m['decisions']]
        assert len(months) == len(set(months)) and max(months) <= m['months'], m['name']
        assert all(1 <= s[0] <= m['months'] and s[4] in STORY_TYPES for s in m['stories']), m['name']
        assert len({g[0] for g in m['goals']}) == len(m['goals']), m['name']
        for d in m['decisions']:
            assert any(o[2] >= 0 for o in d[4]), (m['name'], d[1], 'needs a free way out')

        def texts(x):
            if isinstance(x, str):
                yield x
            elif isinstance(x, dict):
                for v in x.values():
                    yield from texts(v)
            elif isinstance(x, (list, tuple)):
                for v in x:
                    yield from texts(v)
        for t in texts(m):
            hit = EDITOR_TRAP.search(t)
            assert not hit, f'reword "{hit.group(0)}" (the Supabase SQL Editor misreads it): {t}'


def sql():
    out = ['''-- =============================================================================
-- Three more missions (written in scripts/missions/more_missions.py; generate this file from it):
-- Credit Comeback (credit score), Money While You Sleep (passive income), Diamond Hands (holding).
-- Safe to run more than once.
-- =============================================================================
begin;
''']
    for m in MISSIONS:
        f = m['flags']
        cols = ['name', 'description', 'short_description', 'icon', 'category', 'difficulty', 'duration_months', 'learning_objectives', 'completion_reward'] + list(f)
        objectives = 'array[' + ', '.join(q(o) for o in m['objectives']) + ']'
        vals = [q(m['name']), q(m['description']), q(m['short']), q(m['icon']), q(m['category']), q(m['difficulty']), str(m['months']), objectives, str(m['reward'])]
        vals += ['true' if v is True else 'false' if v is False else str(v) for v in f.values()]
        mid = f"(select id from public.integrated_missions where name = {q(m['name'])})"
        out.append(f"-- ===== {m['name']} =====")
        out.append(f"insert into public.integrated_missions ({', '.join(cols)})\nvalues ({', '.join(vals)})\non conflict (name) do nothing;\n")
        for metric, comparison, target, label, desc, icon in m['goals']:
            out.append(f"insert into public.mission_success_criteria (mission_id, metric, target, comparison, label, description, icon)\n"
                       f"values ({mid}, {q(metric)}, {target}, {q(comparison)}, {q(label)}, {q(desc)}, {q(icon)})\n"
                       f"on conflict (mission_id, metric) do nothing;\n")
        for month, title, desc, lesson, options in m['decisions']:
            out.append(f"insert into public.mission_decision_points (mission_id, month, title, description, learning_lesson)\n"
                       f"values ({mid}, {month}, {q(title)}, {q(desc)}, {q(lesson)})\non conflict (mission_id, month) do nothing;\n")
            point = f"(select id from public.mission_decision_points where mission_id = {mid} and month = {month})"
            rows = ',\n'.join(f"    ({q(l)}, {q(d)}, {cash}, {h}, {s}, {mo}, {q(risk)}, {i})" for i, (l, d, cash, h, s, mo, risk) in enumerate(options, 1))
            out.append(f"insert into public.mission_decision_options (decision_point_id, label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)\n"
                       f"select {point}, v.* from (values\n{rows}\n) as v(label, description, immediate_cash, happiness_change, stress_change, motivation_change, risk_level, option_order)\n"
                       f"where not exists (select 1 from public.mission_decision_options o where o.decision_point_id = {point});\n")
        for n, (month, title, emoji, narrative, kind, context, cash, h, s, mo) in enumerate(m['stories'], 1):
            out.append(f"insert into public.mission_story_events (mission_id, title, emoji, narrative, story_type, trigger_type, trigger_value, financial_context, immediate_cash, happiness_change, stress_change, motivation_change, display_order)\n"
                       f"values ({mid}, {q(title)}, {q(emoji)}, {q(narrative)}, {q(kind)}, 'month', {month}, {q(context)}, {cash}, {h}, {s}, {mo}, {n})\n"
                       f"on conflict (mission_id, display_order) do nothing;\n")
    out.append("commit;\n\nselect name, duration_months, completion_reward from public.integrated_missions order by name;\n")
    return '\n'.join(out)


if __name__ == '__main__':
    check()
    sys.stdout.write(sql())
