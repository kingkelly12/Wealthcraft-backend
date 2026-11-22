"""
Lives: the character you play, their age, where they started and how it ended.

* One life at a time (player_lives.is_current). Age comes from the game clock:
  52 game weeks = 1 year, so annual salaries still mean 12 paydays.
* A background sets the starting conditions (cash, debt, allowance, sanity,
  start age). Starting a new life resets the run and keeps the person.
* A life ends by burnout (sanity 0), at MAX_AGE, or when the player chooses to
  start over. The ending is picked from what the life looked like at the end.
"""
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase
from app.services.balance_service import BalanceService

logger = logging.getLogger(__name__)

WEEKS_PER_YEAR = 52
DEFAULT_START_AGE = 18
MAX_AGE = 30
MIN_WEEKS_BEFORE_RETIRING = 4   # can't reroll a life on day one

# --- backgrounds -------------------------------------------------------------------

BACKGROUNDS = {
    'scholarship': {
        'name': 'Scholarship Kid', 'emoji': '🎓',
        'tagline': 'Smart. Broke. Determined.',
        'description': 'Your tuition is covered, your fridge is not. No debt, very little cash, and a lot to prove.',
        'cash': 800, 'debt': 0, 'allowance': 0, 'sanity': 80, 'start_age': 18,
        'difficulty': 'Medium',
    },
    'student_loans': {
        'name': 'Student Loan Era', 'emoji': '📚',
        'tagline': 'Degree: loading. Debt: loaded.',
        'description': 'You start with some cash and a $24,000 student loan that wants $250 every month.',
        'cash': 3000, 'debt': 24000, 'debt_payment': 250, 'allowance': 0, 'sanity': 70, 'start_age': 18,
        'difficulty': 'Hard',
    },
    'rich_parents': {
        'name': 'Rich Parents', 'emoji': '💎',
        'tagline': "Daddy's card. Daddy's rules.",
        'description': 'A fat starting balance and a $400/month allowance. The challenge: becoming a person anyway.',
        'cash': 15000, 'debt': 0, 'allowance': 400, 'sanity': 85, 'start_age': 18,
        'difficulty': 'Easy',
    },
    'moved_out_17': {
        'name': 'Moved Out at 17', 'emoji': '🎒',
        'tagline': 'Street smart. Sleep deprived.',
        'description': 'You left home a year early with $300 and a backpack. Everything is harder. Everything counts.',
        'cash': 300, 'debt': 0, 'allowance': 0, 'sanity': 60, 'start_age': 17,
        'difficulty': 'Brutal',
    },
}

# Existing players keep the life they already have; never offered for new lives.
ORIGINAL = {
    'name': 'The Original', 'emoji': '🌱',
    'tagline': 'The life you were already living.',
    'description': 'Keep your money, job and home exactly as they are.',
    'start_age': DEFAULT_START_AGE, 'difficulty': 'Your call',
}


def background_info(key):
    return ORIGINAL if key == 'original' else BACKGROUNDS.get(key)


# --- avatar -------------------------------------------------------------------------

# Index ranges for the app's SVG avatar (components/avatar/Avatar.tsx).
AVATAR_PARTS = {'skin': 6, 'hair': 7, 'hairColor': 7, 'eyes': 4, 'accessory': 5, 'bg': 6}


def clean_avatar(raw):
    """Keep only known parts with in-range integer values."""
    out = {}
    for part, count in AVATAR_PARTS.items():
        try:
            v = int((raw or {}).get(part, 0))
        except (TypeError, ValueError):
            v = 0
        out[part] = v if 0 <= v < count else 0
    return out


# --- age ----------------------------------------------------------------------------

CHAPTERS = [
    (17, 'Too young to rent a car'),
    (18, 'Fresh out of school'),
    (20, 'Main character era'),
    (22, 'Entry-level everything'),
    (24, 'Quarter-life crisis'),
    (26, 'Pretending to have it together'),
    (28, 'Suddenly into houseplants'),
    (30, 'The big 3-0'),
]


def chapter_for(age):
    title = CHAPTERS[0][1]
    for min_age, name in CHAPTERS:
        if age >= min_age:
            title = name
    return title


def age_at(week, start_age):
    """Age on a given game week (week 1 = start_age, 0 months)."""
    lived = max(0, int(week) - 1)
    years, rem = divmod(lived, WEEKS_PER_YEAR)
    return {
        'years': int(start_age) + years,
        'months': rem * 12 // WEEKS_PER_YEAR,
        'chapter': chapter_for(int(start_age) + years),
        'weeks_to_birthday': WEEKS_PER_YEAR - rem,
    }


def birthday_between(week_before, week_after, start_age):
    """The age reached if a birthday falls between two weeks, else None."""
    a = age_at(week_before, start_age)['years']
    b = age_at(week_after, start_age)['years']
    return b if b > a else None


# --- reading ------------------------------------------------------------------------

def current_life(user_id):
    res = supabase.table('player_lives').select('*').eq('user_id', str(user_id)).eq('is_current', True).limit(1).execute()
    return res.data[0] if res.data else None


def _clock_week(uid):
    res = supabase.table('player_game_clock').select('week').eq('user_id', uid).limit(1).execute()
    return int(res.data[0]['week']) if res.data else 1


def _has_progress(uid):
    """Anything worth keeping: weeks played, a job, a home or investments."""
    if _clock_week(uid) > 1:
        return True
    for table, col, extra in (('jobs', 'user_id', ('is_current', True)), ('player_rentals', 'player_id', ('is_active', True)), ('user_assets', 'user_id', None),
                              ('player_homes', 'player_id', ('is_active', True))):
        q = supabase.table(table).select('id').eq(col, uid)
        if extra:
            q = q.eq(*extra)
        if q.limit(1).execute().data:
            return True
    return False


def avatars_for(user_ids):
    """
    Public look of other players: {user_id: {'avatar', 'age', 'background_emoji'}}.
    Players without a current life are left out (the app falls back to their photo).
    """
    ids = list({str(i) for i in user_ids if i})[:200]
    if not ids:
        return {}
    lives = supabase.table('player_lives').select('user_id, avatar, start_age, background') \
        .in_('user_id', ids).eq('is_current', True).execute().data or []
    if not lives:
        return {}
    clocks = supabase.table('player_game_clock').select('user_id, week').in_('user_id', ids).execute().data or []
    weeks = {str(c['user_id']): int(c['week']) for c in clocks}
    out = {}
    for l in lives:
        uid = str(l['user_id'])
        info = background_info(l['background']) or ORIGINAL
        out[uid] = {
            'avatar': l.get('avatar') or {},
            'age': age_at(weeks.get(uid, 1), l['start_age'])['years'],
            'background_emoji': info['emoji'],
        }
    return out


def attach_avatars(rows, key='user_id'):
    """Add 'avatar' and 'age' to each row (in place) for rows that have a current life."""
    found = avatars_for([r.get(key) for r in rows])
    for r in rows:
        a = found.get(str(r.get(key)))
        r['avatar'] = a['avatar'] if a else None
        r['age'] = a['age'] if a else None
    return rows


def public_life(life, week=None):
    if not life:
        return None
    info = background_info(life['background']) or ORIGINAL
    week = week if week is not None else _clock_week(str(life['user_id']))
    age = age_at(week, life['start_age'])
    return {
        'id': life['id'],
        'life_number': life['life_number'],
        'background': {'key': life['background'], 'name': info['name'], 'emoji': info['emoji']},
        'start_age': life['start_age'],
        'avatar': life.get('avatar') or {},
        'age': age,
        'is_over': age['years'] >= MAX_AGE,
        'started_at': life.get('started_at'),
    }


def state(user_id):
    uid = str(user_id)
    life = current_life(uid)
    past = supabase.table('player_lives').select('life_number, background, ending, summary, ended_at') \
        .eq('user_id', uid).eq('is_current', False).order('life_number', desc=True).limit(20).execute().data or []
    return {
        'current': public_life(life),
        'needs_setup': life is None,
        'can_keep_current': life is None and not past and _has_progress(uid),
        'backgrounds': [{'key': k, **{f: v for f, v in b.items()}} for k, b in BACKGROUNDS.items()],
        'past_lives': past,
        'max_age': MAX_AGE,
        'min_weeks_before_retiring': MIN_WEEKS_BEFORE_RETIRING,
    }


# --- endings ------------------------------------------------------------------------

def _snapshot(uid):
    prof = supabase.table('profiles').select('username, net_worth, monthly_income, sanity, credit_score') \
        .eq('user_id', uid).limit(1).execute().data
    profile = prof[0] if prof else {}
    debts = supabase.table('liabilities').select('remaining_balance').eq('user_id', uid).gt('remaining_balance', 0).execute().data or []
    assets = supabase.table('user_assets').select('asset_type, value').eq('user_id', uid).execute().data or []
    job = supabase.table('jobs').select('title').eq('user_id', uid).eq('is_current', True).limit(1).execute().data
    rental = supabase.table('player_rentals').select('id').eq('player_id', uid).eq('is_active', True).limit(1).execute().data
    return {
        'net_worth': float(profile.get('net_worth') or 0),
        'income': float(profile.get('monthly_income') or 0),
        'sanity': int(profile.get('sanity') if profile.get('sanity') is not None else 100),
        'credit_score': int(profile.get('credit_score') or 650),
        'cash': float(BalanceService.get_current_balance(uid)),
        'debt': float(sum(Decimal(str(d.get('remaining_balance') or 0)) for d in debts)),
        'assets_value': float(sum(Decimal(str(a.get('value') or 0)) for a in assets)),
        'owns_business': any((a.get('asset_type') or '').lower() == 'business' for a in assets),
        'job': job[0]['title'] if job else None,
        'has_home': bool(rental),
    }


ENDINGS = {
    'burnout': ('Burnout at {age}', '🫠', 'You gave it everything. It took everything back.'),
    'millionaire': ('Millionaire by {age}', '💎', 'Seven figures. Your financial advisor calls you "sir" now.'),
    'business': ('Built a business by {age}', '🏗️', "You're the boss. Nobody approves your time off, including you."),
    'debt_free': ('Debt-free by {age}', '🕊️', 'You owe nobody anything. Genuinely rare. Frame this.'),
    'six_figures': ('Six figures by {age}', '📈', 'Your net worth has a comma in the right place.'),
    'drowning': ('Drowning in debt at {age}', '🌊', 'You owe more than you own. The minimum payment owns you.'),
    'moved_back_home': ('Moved back home at {age}', '🏠', 'Your childhood bedroom welcomes you back. The posters never left.'),
    'unemployed': ('Professional vibe curator', '🛋️', 'No job, no boss, no money. Strong vibes though.'),
    'getting_by': ('Just getting by at {age}', '📆', 'Rent paid. Mostly. That counts.'),
}


def pick_ending(snap, age, reason):
    if reason == 'burnout':
        key = 'burnout'
    elif snap['net_worth'] >= 1_000_000:
        key = 'millionaire'
    elif snap['owns_business']:
        key = 'business'
    elif snap['debt'] == 0 and snap['net_worth'] >= 10_000:
        key = 'debt_free'
    elif snap['net_worth'] >= 100_000:
        key = 'six_figures'
    elif snap['net_worth'] < 0:
        key = 'drowning'
    elif not snap['has_home'] and age >= 22:
        key = 'moved_back_home'
    elif not snap['job']:
        key = 'unemployed'
    else:
        key = 'getting_by'
    title, emoji, line = ENDINGS[key]
    return {'key': key, 'title': title.format(age=age), 'emoji': emoji, 'line': line}


def _week_stats(uid):
    rows = supabase.table('player_weeks').select('week, receipt').eq('user_id', uid).eq('status', 'completed').execute().data or []
    receipts = [r['receipt'] for r in rows if r.get('receipt')]
    cash = [(r.get('totals') or {}).get('cash', 0) for r in receipts]
    return {
        'weeks_played': len(receipts),
        'cards_played': sum(len(r.get('cards') or []) for r in receipts),
        'paydays': sum(1 for r in receipts if r.get('month_summary')),
        'best_week': max(cash) if cash else 0,
        'worst_week': min(cash) if cash else 0,
    }


class LifeError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def end_life(user_id):
    """End the current life: pick the ending, store the summary. Returns the summary."""
    uid = str(user_id)
    life = current_life(uid)
    if not life:
        raise LifeError('NO_LIFE', "You don't have a life in progress.", 404)

    week = _clock_week(uid)
    age = age_at(week, life['start_age'])['years']
    snap = _snapshot(uid)
    weeks_lived = week - 1
    if snap['sanity'] <= 0:
        reason = 'burnout'
    elif age >= MAX_AGE:
        reason = 'max_age'
    else:
        reason = 'started_over'
        if weeks_lived < MIN_WEEKS_BEFORE_RETIRING:
            raise LifeError('TOO_SOON', f'Live at least {MIN_WEEKS_BEFORE_RETIRING} weeks before starting over.', 400)

    ending = pick_ending(snap, age, reason)
    info = background_info(life['background']) or ORIGINAL
    summary = {
        'life_number': life['life_number'],
        'background': {'key': life['background'], 'name': info['name'], 'emoji': info['emoji']},
        'avatar': life.get('avatar') or {},
        'start_age': life['start_age'],
        'end_age': age,
        'weeks_lived': weeks_lived,
        'reason': reason,
        'ending': ending,
        **snap,
        **_week_stats(uid),
    }
    closed = supabase.table('player_lives').update({
        'is_current': False,
        'ended_at': datetime.now(timezone.utc).isoformat(),
        'ending': ending['key'],
        'summary': summary,
    }).eq('id', life['id']).eq('is_current', True).execute()
    if not closed.data:
        raise LifeError('CONFLICT', 'This life already ended.', 409)
    try:
        from app.game import squads
        squads.on_life_ended(uid, summary)
    except Exception as e:
        logger.warning(f'Squad post for ended life failed for {uid}: {e}')
    return summary


# --- beginning ----------------------------------------------------------------------

def _reset_run(uid, bg):
    """Wipe the run (money, job, home, assets, loans, missions, clock). Keep the person."""
    now = datetime.now(timezone.utc).isoformat()

    # P2P loans involve another player's money: they must be settled first.
    for col in ('borrower_id', 'lender_id'):
        open_loans = supabase.table('p2p_loans').select('id').eq(col, uid).in_('status', ['pending', 'active']).limit(1).execute()
        if open_loans.data:
            raise LifeError('P2P_OPEN', 'Settle or cancel your P2P loans before starting a new life.', 409)

    supabase.table('jobs').update({'is_current': False}).eq('user_id', uid).eq('is_current', True).execute()
    supabase.table('player_rentals').update({'is_active': False}).eq('player_id', uid).eq('is_active', True).execute()
    supabase.table('player_liabilities').update({'is_active': False}).eq('player_id', uid).eq('is_active', True).execute()
    supabase.table('user_assets').delete().eq('user_id', uid).execute()
    from app.game import homes
    homes.clear_for_new_life(uid)
    supabase.table('liabilities').delete().eq('user_id', uid).execute()
    supabase.table('bank_loans').update({'status': 'completed'}).eq('borrower_id', uid).eq('status', 'active').execute()
    supabase.table('user_courses').delete().eq('user_id', uid).is_('completed_at', 'null').execute()
    supabase.table('player_mission_progress').update({'is_active': False, 'abandoned_at': now}) \
        .eq('player_id', uid).eq('is_active', True).execute()

    # New person, new relationships; any shared flat is left behind.
    from app.game import cast, roommates
    roommates.end_all_for(uid)
    cast.reset(uid)

    # A fresh clock: week 1, one week ready to play.
    supabase.table('player_weeks').delete().eq('user_id', uid).execute()
    today = datetime.now(timezone.utc).date().isoformat()
    clock = supabase.table('player_game_clock').update({'week': 1, 'banked_weeks': 1, 'bank_updated_on': today}).eq('user_id', uid).execute()
    if not clock.data:
        supabase.table('player_game_clock').insert({'user_id': uid, 'week': 1, 'banked_weeks': 1, 'bank_updated_on': today}).execute()

    # Money: set the balance to the background's starting cash.
    current = BalanceService.get_current_balance(uid)
    target = Decimal(str(bg['cash']))
    if target > current:
        BalanceService.add_balance(uid, target - current, f"New life: {bg['name']}", category='new_life')
    elif current > target:
        BalanceService.subtract_balance(uid, current - target, f"New life: {bg['name']}", category='new_life')

    if bg.get('debt'):
        supabase.table('liabilities').insert({
            'user_id': uid, 'name': 'Student loan', 'liability_type': 'bank_loan',
            'amount': bg['debt'], 'interest_rate': 5, 'monthly_payment': bg.get('debt_payment', 0),
            'remaining_balance': bg['debt'], 'remaining_term': int(bg['debt'] / max(1, bg.get('debt_payment', 1))),
        }).execute()

    supabase.table('profiles').update({
        'base_monthly_income': bg.get('allowance', 0),
        'monthly_income': bg.get('allowance', 0),
        'sanity': bg['sanity'],
        'credit_score': 650,
        'last_free_recovery_at': None,
    }).eq('user_id', uid).execute()

    try:
        from app.services.profile_service import ProfileService
        ProfileService.recalculate_net_worth(uuid.UUID(uid))
    except Exception as e:
        logger.warning(f'Net worth refresh after new life failed for {uid}: {e}')


def begin_life(user_id, background, avatar):
    """
    Start a life. 'original' keeps everything as it is (only for a player's
    first life when they already have progress); any other background resets
    the run to its starting conditions.
    """
    uid = str(user_id)
    if current_life(uid):
        raise LifeError('LIFE_IN_PROGRESS', 'Finish your current life before starting a new one.', 409)

    lives = supabase.table('player_lives').select('life_number').eq('user_id', uid) \
        .order('life_number', desc=True).limit(1).execute().data or []
    life_number = (lives[0]['life_number'] + 1) if lives else 1

    if background == 'original':
        if life_number != 1:
            raise LifeError('INVALID_BACKGROUND', 'Pick a background for your new life.', 400)
        start_age = DEFAULT_START_AGE
    else:
        bg = BACKGROUNDS.get(background)
        if not bg:
            raise LifeError('INVALID_BACKGROUND', 'Unknown background.', 400)
        _reset_run(uid, bg)
        start_age = bg['start_age']

    try:
        supabase.table('player_lives').insert({
            'user_id': uid, 'life_number': life_number, 'background': background,
            'start_age': start_age, 'avatar': clean_avatar(avatar), 'is_current': True,
        }).execute()
    except Exception as e:
        if '23505' in str(e) or 'duplicate' in str(e).lower():
            raise LifeError('LIFE_IN_PROGRESS', 'A life was just started in another session.', 409)
        raise
    try:
        from app.game import squads
        info = background_info(background) or ORIGINAL
        squads.on_life_started(uid, life_number, info['name'], info['emoji'], reset=background != 'original')
    except Exception as e:
        logger.warning(f'Squad post for new life failed for {uid}: {e}')
    return public_life(current_life(uid))


def update_avatar(user_id, avatar):
    uid = str(user_id)
    life = current_life(uid)
    if not life:
        raise LifeError('NO_LIFE', "You don't have a life in progress.", 404)
    supabase.table('player_lives').update({'avatar': clean_avatar(avatar)}).eq('id', life['id']).execute()
    return public_life(current_life(uid))
