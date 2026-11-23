"""
Legacy: what carries over from one life to the next.

* Achievements: earned once, ever, by how a life ENDS (worked out from each
  finished life's summary, so lives played before this existed count too).
* Legacy bonus: every achievement adds LEGACY_CASH_PER to the starting cash
  of every future life.
* Unlockable backgrounds: some achievements unlock a new way to start a life
  (life.UNLOCKABLE_BACKGROUNDS).
* The endings collection: which of the endings you've reached, and how often.

Nothing is stored here: it's all derived from player_lives.summary.
"""
from app import supabase

LEGACY_CASH_PER = 200

# Starting backgrounds everyone has; finishing a life with each earns "Tried Everything".
BASE_BACKGROUNDS = ('scholarship', 'student_loans', 'rich_parents', 'moved_out_17')


def _f(s, key, default=0.0):
    try:
        return float(s.get(key) if s.get(key) is not None else default)
    except (TypeError, ValueError):
        return default


# key, emoji, title, how to earn it, test(summary)
ACHIEVEMENTS = [
    ('first_life', '🏁', 'One Down', 'Finish a life, however it ends.', lambda s: True),
    ('made_it_to_30', '🎂', 'Made It to 30', 'Live a whole life, all the way to 30.', lambda s: s.get('reason') == 'max_age'),
    ('six_figures', '📈', 'Six Figures', 'End a life worth $100,000 or more.', lambda s: _f(s, 'net_worth') >= 100_000),
    ('millionaire', '💎', 'Millionaire', 'End a life worth $1,000,000 or more.', lambda s: _f(s, 'net_worth') >= 1_000_000),
    ('homeowner', '🏡', 'Homeowner', 'End a life owning a home.', lambda s: bool(s.get('owns_home'))),
    ('business_owner', '🏪', 'Business Owner', 'End a life owning a business.', lambda s: bool(s.get('owns_business'))),
    ('corner_office', '👔', 'Corner Office', 'End a life in an executive job.', lambda s: s.get('job_level') == 'executive'),
    ('debt_free', '🕊️', 'Debt-Free', 'End a life owing nothing, with at least $10,000 to your name.',
     lambda s: s.get('debt') is not None and _f(s, 'debt') == 0 and _f(s, 'net_worth') >= 10_000),
    ('zen', '🧘', 'Zen Master', 'Reach 30 with your sanity at 80 or more.', lambda s: s.get('reason') == 'max_age' and _f(s, 'sanity') >= 80),
    ('credit_legend', '💳', 'Credit Legend', 'End a life with a credit score of 750 or more.', lambda s: _f(s, 'credit_score') >= 750),
    ('high_flyer', '🛩️', 'High Flyer', 'End a life owning a helicopter or a plane.', lambda s: bool(s.get('owns_aircraft'))),
    ('against_the_odds', '🔥', 'Against All Odds', 'Start as "Moved Out at 17" and end worth $50,000 or more.',
     lambda s: (s.get('background') or {}).get('key') == 'moved_out_17' and _f(s, 'net_worth') >= 50_000),
    ('tried_everything', '🌍', 'Lived Every Life', 'Finish a life with each of the four starting backgrounds.', None),
]
ACHIEVEMENT_KEYS = [a[0] for a in ACHIEVEMENTS]


def finished_lives(uid) -> list:
    rows = supabase.table('player_lives').select('life_number, background, ending, summary, ended_at') \
        .eq('user_id', str(uid)).eq('is_current', False).order('life_number').execute().data or []
    return [r for r in rows if r.get('summary')]


def earned(summaries) -> dict:
    """{achievement key: life number it was first earned in}."""
    out = {}
    backgrounds = set()
    for s in summaries:
        n = s.get('life_number')
        backgrounds.add((s.get('background') or {}).get('key'))
        for key, _, _, _, test in ACHIEVEMENTS:
            if key not in out and test is not None and test(s):
                out[key] = n
        if 'tried_everything' not in out and set(BASE_BACKGROUNDS) <= backgrounds:
            out['tried_everything'] = n
    return out


def bonus_cash(earned_map) -> int:
    return LEGACY_CASH_PER * len(earned_map)


def unlocked_backgrounds(earned_map) -> set:
    from app.game.life import UNLOCKABLE_BACKGROUNDS
    return {k for k, b in UNLOCKABLE_BACKGROUNDS.items() if b['requires'] in earned_map}


def achievement(key) -> dict:
    a = next(a for a in ACHIEVEMENTS if a[0] == key)
    return {'key': a[0], 'emoji': a[1], 'title': a[2], 'how': a[3]}


def newly_earned(previous_summaries, summary) -> dict:
    """What finishing this life adds: achievements and backgrounds."""
    before = earned(previous_summaries)
    after = earned(list(previous_summaries) + [summary])
    new = [k for k in ACHIEVEMENT_KEYS if k in after and k not in before]
    from app.game.life import UNLOCKABLE_BACKGROUNDS
    unlocks = sorted(unlocked_backgrounds(after) - unlocked_backgrounds(before))
    return {
        'achievements': [achievement(k) for k in new],
        'unlocked_backgrounds': [{'key': k, 'name': UNLOCKABLE_BACKGROUNDS[k]['name'], 'emoji': UNLOCKABLE_BACKGROUNDS[k]['emoji']}
                                 for k in unlocks],
        'bonus_cash': bonus_cash(after),
        'bonus_added': bonus_cash(after) - bonus_cash(before),
    }


def view(uid) -> dict:
    """The Hall of Lives."""
    from app.game.life import ENDINGS, UNLOCKABLE_BACKGROUNDS
    lives = finished_lives(uid)
    summaries = [r['summary'] for r in lives]
    got = earned(summaries)
    unlocked = unlocked_backgrounds(got)
    ending_counts = {}
    for r in lives:
        key = r.get('ending') or ((r.get('summary') or {}).get('ending') or {}).get('key')
        if key:
            ending_counts[key] = ending_counts.get(key, 0) + 1
    return {
        'level': len(got),
        'bonus_cash': bonus_cash(got),
        'cash_per_achievement': LEGACY_CASH_PER,
        'achievements': [{**achievement(k), 'earned': k in got, 'earned_in_life': got.get(k)} for k in ACHIEVEMENT_KEYS],
        'endings': [{'key': k, 'emoji': e, 'title': t.replace(' at {age}', '').replace(' by {age}', ''), 'line': line,
                     'collected': k in ending_counts, 'times': ending_counts.get(k, 0)}
                    for k, (t, e, line) in ENDINGS.items()],
        'backgrounds': [{'key': k, 'name': b['name'], 'emoji': b['emoji'], 'unlocked': k in unlocked,
                         'requires': achievement(b['requires'])} for k, b in UNLOCKABLE_BACKGROUNDS.items()],
        'lives': [{
            'life_number': r['life_number'],
            'ended_at': r.get('ended_at'),
            'background': (r['summary'].get('background') or {}),
            'ending': r['summary'].get('ending') or {},
            'end_age': r['summary'].get('end_age'),
            'net_worth': r['summary'].get('net_worth'),
            'weeks_lived': r['summary'].get('weeks_lived'),
            'achievements': [k for k, n in got.items() if n == r['life_number']],
        } for r in reversed(lives)],
    }
