"""
Turn-based time: the player's game clock and weekly deck ("This Week").

One turn = one in-game week, played as a deck of CARDS_PER_WEEK swipe cards.
Every WEEKS_PER_MONTH-th week ends with the player's month (salary, loans,
rent, living costs, asset income, missions) via process_month_for_user().

WEEKS_PER_DAY weeks unlock per real (UTC) day and up to MAX_BANKED can be saved
up, so a missed weekend can be caught up but a month can't be binged. A life
(18 to 30) takes about ten months of real time. Set
GAME_CLOCK_UNLIMITED=1 to play any number of weeks a day (playtesting).

Tables: player_game_clock (one row per player on game time) and
player_weeks (one row per dealt week, cards as JSON).
"""
import copy
import logging
import os
import random
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from app import supabase
from app.game.weekly_cards import CARDS
from app.services.balance_service import BalanceService
from app.utils.perf import cached, parallel

logger = logging.getLogger(__name__)

WEEKS_PER_MONTH = 4
WEEKS_PER_DAY = 2            # two weeks (8 cards, ~3-4 minutes) a day
FIRST_DAY_WEEKS = 4          # a new player's first day: enough to reach payday (week 4) once
MAX_BANKED = 7               # catch-up for a missed weekend; no binging a month at once
CARDS_PER_WEEK = 4
MAX_LIFE_EVENTS = 2
RECENT_DECKS_NO_REPEAT = 4   # everyday cards don't repeat within this many weeks


class WeekError(Exception):
    """A rule the player hit (shown to them), with an HTTP status."""

    def __init__(self, code, message, status=400, data=None):
        super().__init__(message)
        self.code, self.message, self.status, self.data = code, message, status, data


# --- time -------------------------------------------------------------------

def _today() -> date:
    return datetime.now(timezone.utc).date()


def _unlimited() -> bool:
    return os.environ.get('GAME_CLOCK_UNLIMITED', '').lower() in ('1', 'true', 'yes')


def week_meta(week: int) -> dict:
    month = (week - 1) // WEEKS_PER_MONTH + 1
    week_of_month = (week - 1) % WEEKS_PER_MONTH + 1
    return {
        'week': week,
        'month': month,
        'week_of_month': week_of_month,
        'is_payday_week': week_of_month == WEEKS_PER_MONTH,
        'weeks_lived': week - 1,
    }


def _next_unlock_at(today: date) -> str:
    return datetime.combine(today + timedelta(days=1), time.min, tzinfo=timezone.utc).isoformat()


# --- clock --------------------------------------------------------------------

def get_clock(user_id: str) -> dict:
    """The player's clock, created on first use (this moves them onto game time)."""
    uid = str(user_id)
    today = _today()
    res = supabase.table('player_game_clock').select('*').eq('user_id', uid).limit(1).execute()
    if not res.data:
        try:
            supabase.table('player_game_clock').insert({
                'user_id': uid, 'week': 1, 'banked_weeks': FIRST_DAY_WEEKS, 'bank_updated_on': today.isoformat(),
            }).execute()
        except Exception as e:  # lost a creation race: read the winner's row
            if '23505' not in str(e) and 'duplicate' not in str(e).lower():
                raise
        res = supabase.table('player_game_clock').select('*').eq('user_id', uid).limit(1).execute()
    clock = res.data[0]

    # WEEKS_PER_DAY new weeks per day since the bank was last topped up, capped.
    last = date.fromisoformat(str(clock['bank_updated_on'])[:10])
    days = (today - last).days
    if days > 0:
        banked = topped_up(clock['banked_weeks'], days)
        upd = supabase.table('player_game_clock').update({
            'banked_weeks': banked, 'bank_updated_on': today.isoformat(),
        }).eq('user_id', uid).eq('bank_updated_on', clock['bank_updated_on']).execute()
        if upd.data:
            clock = upd.data[0]
        else:  # someone else refreshed it first
            clock = supabase.table('player_game_clock').select('*').eq('user_id', uid).limit(1).execute().data[0]
    return clock


def topped_up(banked, days) -> int:
    """Weeks ready to play after `days` new days."""
    return min(MAX_BANKED, int(banked) + WEEKS_PER_DAY * max(0, int(days)))


def _can_play(clock) -> bool:
    return _unlimited() or int(clock['banked_weeks']) >= 1


def _life_info(uid, week, life=None, _fetch=True):
    """(start_age, age dict, life_over, life) for the player's current life (default start 18)."""
    from app.game import life as life_mod
    if _fetch and life is None:
        life = life_mod.current_life(uid)
    start_age = int(life['start_age']) if life else life_mod.DEFAULT_START_AGE
    age = life_mod.age_at(week, start_age)
    return start_age, age, bool(life) and age['years'] >= life_mod.MAX_AGE, life


def _has_past_life(uid):
    return bool(supabase.table('player_lives').select('id').eq('user_id', uid).limit(1).execute().data)


def _lives(uid, week):
    """(start_age, age, life_over, life, between_lives), with both reads made at once."""
    from app.game import life as life_mod
    life, past = parallel(lambda: life_mod.current_life(uid), lambda: _has_past_life(uid))
    start_age, age, over, life = _life_info(uid, week, life, _fetch=False)
    return start_age, age, over, life, (life is None and past)


def _between_lives(uid, life):
    """A life ended and the next hasn't begun: the old run can't be played."""
    return False if life else _has_past_life(uid)


def _check_life(uid, week):
    """Raises if this life can't be played. Returns its start age."""
    start_age, _, over, _, between = _lives(uid, week)
    if over:
        raise WeekError('LIFE_OVER', 'This life has reached its end. Time to see how it went.', 409)
    if between:
        raise WeekError('NEEDS_NEW_LIFE', 'Start a new life to keep playing.', 409)
    return start_age


# --- deck ---------------------------------------------------------------------

def _player_context(uid: str) -> dict:
    from app.game import cast, roommates
    jobs, rentals, roommate, owns, balance, rel = parallel(
        lambda: supabase.table('jobs').select('id').eq('user_id', uid).eq('is_current', True).limit(1).execute(),
        lambda: supabase.table('player_rentals').select('id').eq('player_id', uid).eq('is_active', True).limit(1).execute(),
        lambda: roommates.roommate_name(uid),
        lambda: supabase.table('player_homes').select('id').eq('player_id', uid).eq('is_active', True).eq('lives_in', True).limit(1).execute(),
        lambda: BalanceService.get_current_balance(uid),
        lambda: cast.relationships(uid),
    )
    return {
        'job': bool(jobs.data),
        # Living in a home you own: no landlord cards, no "move back home" cards.
        'owner': bool(owns.data),
        # Living in a friend's place counts as renting, for the cards.
        'rental': bool(rentals.data) or bool(roommate),
        'balance': balance,
        'rel': rel,
        'roommate_name': roommate or cast.CAST['roommate']['name'],
    }


def _eligible(card, ctx) -> bool:
    req = card.get('requires')
    ok = {
        None: True,
        'job': ctx['job'],
        'no_job': not ctx['job'],
        'rental': ctx['rental'],
        'no_rental': not ctx['rental'] and not ctx.get('owner'),
    }.get(req, True)
    if card.get('character') == 'roommate' and not ctx['rental']:
        ok = False
    who = card.get('character')
    if who and 'min_rel' in card and ctx['rel'].get(who, 50) < card['min_rel']:
        ok = False
    if who and 'max_rel' in card and ctx['rel'].get(who, 50) > card['max_rel']:
        ok = False
    return ok


def _everyday_card(card, ctx=None) -> dict:
    from app.game.cast import CAST
    name = (ctx or {}).get('roommate_name') or CAST['roommate']['name']

    def fill(text):
        return text.replace('{roommate}', name)

    def side(sid, c):
        return {
            'id': sid, 'label': fill(c['label']), 'outcome': fill(c['outcome']),
            'cash': float(c.get('cash', 0)), 'sanity': int(c.get('sanity', 0)), 'income': float(c.get('income', 0)),
            'rel': int(c.get('rel', 0)),
        }
    who = card.get('character')
    person = None
    if who:
        person = {'key': who, 'name': name if who == 'roommate' else CAST[who]['name'], 'emoji': CAST[who]['emoji']}
    return {
        'kind': 'everyday', 'key': card['key'], 'category': card['category'], 'icon': card['icon'],
        'income_to': card.get('income_to'),
        'character': person,
        'title': fill(card['title']), 'body': fill(card['body']), 'teaser': fill(card['teaser']),
        'choices': [side('left', card['left']), side('right', card['right'])],
    }


# --- new and seasonal events -----------------------------------------------------
# Events can have a release date (released_at: dealt only from then on, so a
# batch written ahead goes live by itself) and a yearly season window
# (season_start / season_end as 'MM-DD', may wrap the new year). New and
# in-season events are dealt first, with a badge on the card.
NEW_FOR_DAYS = 14


def _parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def in_season(event, today: date) -> bool:
    start, end = event.get('season_start'), event.get('season_end')
    if not start or not end:
        return True
    md = today.strftime('%m-%d')
    return start <= md <= end if start <= end else (md >= start or md <= end)


def released(event, now: datetime) -> bool:
    ts = _parse_ts(event.get('released_at'))
    return ts is None or ts <= now


def badge(event, now: datetime):
    """{'emoji', 'label'} for a seasonal or newly released event, else None."""
    if event.get('season_start') and event.get('season_label'):
        return {'emoji': event.get('season_emoji') or '📅', 'label': event['season_label'], 'kind': 'season'}
    ts = _parse_ts(event.get('released_at'))
    if ts and now - ts <= timedelta(days=NEW_FOR_DAYS):
        return {'emoji': '✨', 'label': 'New', 'kind': 'new'}
    return None


def _life_event_card(event, choices, user_life_event_id=None) -> dict:
    """Effects come from app.game.life_events (shared with the event-screen route)."""
    from app.game.life_events import choice_effects

    def side(sid, ch):
        fx = choice_effects(ch)
        return {
            'id': sid, 'label': ch['choice_label'], 'outcome': ch.get('outcome_description') or '',
            'cash': float(fx['cash']), 'sanity': fx['sanity'], 'income': float(fx['income']),
            'choice_id': ch['id'],
        }
    return {
        'kind': 'life_event', 'life_event_id': event['id'], 'user_life_event_id': user_life_event_id,
        'category': 'life_event', 'event_type': event.get('event_type') or 'neutral', 'icon': None,
        'title': event['title'], 'body': event['description'], 'teaser': f"{event['title']} 👀",
        'choices': [side('left', choices[0]), side('right', choices[1])],
        'badge': badge(event, datetime.now(timezone.utc)),
    }


def _choices_for(event_ids):
    if not event_ids:
        return {}
    rows = supabase.table('life_event_choices').select('*').in_('life_event_id', list(event_ids)) \
        .order('choice_order').execute().data or []
    by_event = {}
    for r in sorted(rows, key=lambda r: r.get('choice_order') or 0):
        by_event.setdefault(r['life_event_id'], []).append(r)
    return by_event


def _affordable(card, balance) -> bool:
    """At least one choice the player can pay for right now."""
    return any(c['cash'] >= 0 or Decimal(str(-c['cash'])) <= balance for c in card['choices'])


def _event_catalog():
    """All active life events and their choices ({event_id: [choices]}), cached for a few minutes."""
    def load():
        events = supabase.table('life_events').select('*').eq('is_active', True).execute().data or []
        return events, _choices_for([e['id'] for e in events])
    return cached('life_events', load, client=supabase)


def _life_event_cards(uid, rng, ctx, want):
    """Pending life events first (assigned before the player joined game time), then fresh ones."""
    cards = []
    pending, recent, (all_events, choices) = parallel(
        lambda: supabase.table('user_life_events').select('id, life_event_id')
        .eq('user_id', uid).is_('choice_id', 'null').order('created_at').limit(MAX_LIFE_EVENTS).execute().data or [],
        lambda: supabase.table('user_life_events').select('life_event_id')
        .eq('user_id', uid).order('created_at', desc=True).limit(30).execute().data or [],
        _event_catalog,
    )
    seen = {r['life_event_id'] for r in recent}

    now, today = datetime.now(timezone.utc), _today()
    by_id = {e['id']: e for e in all_events}           # pending ones are always answerable
    events = [e for e in all_events if released(e, now) and in_season(e, today)]

    for p in pending:
        event = by_id.get(p['life_event_id'])
        if event and len(choices.get(event['id'], [])) >= 2:
            cards.append(_life_event_card(event, choices[event['id']], user_life_event_id=p['id']))

    fresh = [e for e in events if e['id'] not in seen and len(choices.get(e['id'], [])) >= 2]
    if not fresh:  # played them all: allow repeats rather than an empty slot
        fresh = [e for e in events if len(choices.get(e['id'], [])) >= 2]
    rng.shuffle(fresh)
    # New drops and in-season events first (stable sort keeps the shuffle within each group).
    fresh.sort(key=lambda e: badge(e, now) is None)
    used = {c['life_event_id'] for c in cards}
    for event in fresh:
        if len(cards) >= want:
            break
        if event['id'] in used:
            continue
        card = _life_event_card(event, choices[event['id']])
        if _affordable(card, ctx['balance']):
            cards.append(card)
            used.add(event['id'])
    return cards[:want]


def _recent_everyday_keys(uid, week):
    """Everyday cards on cooldown: dealt within RECENT_DECKS_NO_REPEAT weeks, or their own cooldown_weeks."""
    longest = max([RECENT_DECKS_NO_REPEAT] + [int(c.get('cooldown_weeks') or 0) for c in CARDS])
    rows = supabase.table('player_weeks').select('week, cards').eq('user_id', uid) \
        .gte('week', week - longest).lt('week', week).execute().data or []
    cooldown = {c['key']: int(c.get('cooldown_weeks') or RECENT_DECKS_NO_REPEAT) for c in CARDS}
    return {c.get('key') for r in rows for c in (r.get('cards') or [])
            if c.get('kind') == 'everyday' and week - int(r['week']) <= cooldown.get(c.get('key'), RECENT_DECKS_NO_REPEAT)}


def build_deck(user_id: str, week: int) -> list:
    """Deal a week: 1-2 life events and everyday cards, shuffled. Deterministic per (player, week)."""
    uid = str(user_id)
    rng = random.Random(f'{uid}:{week}')
    ctx = _player_context(uid)

    want_events = 1 if rng.random() < 0.5 else MAX_LIFE_EVENTS
    cards = _life_event_cards(uid, rng, ctx, want_events)

    recent = _recent_everyday_keys(uid, week)
    pool = [c for c in CARDS if _eligible(c, ctx) and c['key'] not in recent]
    if len(pool) < CARDS_PER_WEEK:
        # Short of cards: relax the 4-week no-repeat, but never a card's own longer cooldown
        pool = [c for c in CARDS if _eligible(c, ctx)
                and not (c.get('cooldown_weeks') and c['key'] in recent)]
    slots = CARDS_PER_WEEK - len(cards)
    gated = [c for c in pool if 'min_rel' in c or 'max_rel' in c]
    picks = rng.sample(gated, k=min(1, len(gated), slots))
    rest = [c for c in pool if c not in picks]
    picks += rng.sample(rest, k=min(slots - len(picks), len(rest)))
    cards += [_everyday_card(c, ctx) for c in picks]

    rng.shuffle(cards)
    for i, card in enumerate(cards):
        card['id'] = f'w{week}c{i + 1}'
        card['chosen'] = None
        card['result'] = None
    return cards


def get_week(user_id: str, week: int) -> dict:
    """The dealt week, dealing it on first request."""
    uid = str(user_id)
    res = supabase.table('player_weeks').select('*').eq('user_id', uid).eq('week', week).limit(1).execute()
    if res.data:
        return res.data[0]
    try:
        supabase.table('player_weeks').insert({
            'user_id': uid, 'week': week, 'cards': build_deck(uid, week), 'version': 0, 'status': 'open',
        }).execute()
    except Exception as e:
        if '23505' not in str(e) and 'duplicate' not in str(e).lower():
            raise
    return supabase.table('player_weeks').select('*').eq('user_id', uid).eq('week', week).limit(1).execute().data[0]


# --- public views -------------------------------------------------------------

_PRIVATE_CARD_FIELDS = ('user_life_event_id',)
_PRIVATE_CHOICE_FIELDS = ('choice_id',)


def public_card(card) -> dict:
    out = {k: v for k, v in card.items() if k not in _PRIVATE_CARD_FIELDS}
    out['choices'] = [{k: v for k, v in ch.items() if k not in _PRIVATE_CHOICE_FIELDS} for ch in card['choices']]
    return out


def _last_receipt(uid, week):
    if week <= 1:
        return None
    prev = supabase.table('player_weeks').select('receipt').eq('user_id', uid).eq('week', week - 1).limit(1).execute()
    return prev.data[0].get('receipt') if prev.data else None


_UNSET = object()


def state(user_id: str, last_receipt=_UNSET, clock=None) -> dict:
    """Everything the This Week screen and the home card need. `last_receipt`: already known (end of week)."""
    uid = str(user_id)
    today = _today()
    clock = clock or get_clock(uid)
    week = int(clock['week'])
    deck, last, (_, age, life_over, life, needs_new_life) = parallel(
        lambda: get_week(uid, week),
        lambda: _last_receipt(uid, week) if last_receipt is _UNSET else last_receipt,
        lambda: _lives(uid, week),
    )
    cards = deck.get('cards') or []
    remaining = sum(1 for c in cards if not c.get('chosen'))

    banked = int(clock['banked_weeks'])
    return {
        **week_meta(week),
        'age': age,
        'has_life': life is not None,
        'life_over': life_over,
        'needs_new_life': needs_new_life,
        'banked_weeks': banked,
        'max_banked': MAX_BANKED,
        'weeks_per_day': WEEKS_PER_DAY,
        'can_play': _can_play(clock) and not life_over and not needs_new_life,
        'unlimited': _unlimited(),
        'next_unlock_at': None if banked >= MAX_BANKED or _unlimited() else _next_unlock_at(today),
        'deck': {
            'id': deck['id'],
            'status': deck['status'],
            'cards': [public_card(c) for c in cards],
            'remaining': remaining,
            'total': len(cards),
        },
        'teaser': next((c.get('teaser') for c in cards if not c.get('chosen')), None),
        'last_receipt': last,
    }


# --- playing ------------------------------------------------------------------

def _sanity_of(uid):
    res = supabase.table('profiles').select('sanity').eq('user_id', uid).limit(1).execute()
    return int(res.data[0].get('sanity') or 0) if res.data else 100


def _save_cards(deck, cards):
    """Optimistic write: fails (returns None) if another request changed the deck first."""
    res = supabase.table('player_weeks').update({'cards': cards, 'version': int(deck['version']) + 1}) \
        .eq('id', deck['id']).eq('version', deck['version']).eq('status', 'open').execute()
    if not res.data:
        return None
    return res.data[0]


def _update_card(uid, week, card_id, mutate, attempts=6):
    """
    Re-read this week's deck, apply `mutate(card)` (return False to skip) and
    save, retrying on version conflicts. A second card played at the same time
    bumps the deck version; a single optimistic write would then silently drop
    this card's result (or fail to release its claim).
    """
    for _ in range(attempts):
        deck = supabase.table('player_weeks').select('*').eq('user_id', uid).eq('week', week).limit(1).execute().data
        if not deck:
            return False
        deck = deck[0]
        cards = copy.deepcopy(deck.get('cards') or [])
        card = next((c for c in cards if c['id'] == card_id), None)
        if card is None or mutate(card) is False:
            return False
        if _save_cards(deck, cards) is not None:
            return True
    logger.error(f"Could not update card {card_id} for {uid} week {week} after {attempts} attempts")
    return False


def _is_insufficient(e):
    return 'Insufficient funds' in str(e)


def choose(user_id: str, card_id: str, choice_id: str) -> dict:
    """Resolve one card. Returns {'card': public card, 'result': {...}}."""
    uid = str(user_id)
    clock = get_clock(uid)
    if not _can_play(clock):
        raise WeekError('WEEK_LOCKED', 'Next week unlocks tomorrow.', 403)
    week = int(clock['week'])

    def baseline():  # the squad race measures growth from before your first card this week
        try:
            from app.game import squads
            squads.ensure_baseline(uid)
        except Exception as e:
            logger.warning(f'Squad baseline failed for {uid}: {e}')

    # The life checks, the deck, the squad baseline and the balance are independent: read them at once.
    _, deck, _, balance = parallel(lambda: _check_life(uid, week), lambda: get_week(uid, week), baseline,
                                   lambda: BalanceService.get_current_balance(uid))
    if deck['status'] != 'open':
        raise WeekError('WEEK_COMPLETED', 'This week is already over.', 409)

    cards = copy.deepcopy(deck.get('cards') or [])
    card = next((c for c in cards if c['id'] == card_id), None)
    if card is None:
        raise WeekError('CARD_NOT_FOUND', "That card isn't in this week's deck.", 404)
    if card.get('chosen'):
        raise WeekError('ALREADY_CHOSEN', 'You already made this call.', 409, data={'card': public_card(card)})
    choice = next((c for c in card['choices'] if c['id'] == choice_id), None)
    if choice is None:
        raise WeekError('CHOICE_NOT_FOUND', 'That choice is not on this card.', 404)

    cash = Decimal(str(choice['cash']))
    if cash < 0:
        if -cash > balance:
            if any(c['cash'] >= 0 for c in card['choices'] if c['id'] != choice_id):
                raise WeekError('INSUFFICIENT_FUNDS', f"You can't afford that (${-cash:,.0f}).", 400)
            # No free way out: pay what you have rather than get stuck on the card.
            cash = -balance

    # 1. Claim the card (so a double swipe can't apply it twice).
    card['chosen'] = choice_id
    claimed = _save_cards(deck, cards)
    if claimed is None:
        raise WeekError('CONFLICT', 'This week changed in another session. Pull to refresh.', 409)

    # 1b. A pending life event can also be answered on the event screen (from
    #     its old push notification). Claim it here BEFORE any money moves; if
    #     it was already answered there, this card is spent with no effect
    #     (it used to pay out a second time).
    if card['kind'] == 'life_event' and card.get('user_life_event_id'):
        taken = supabase.table('user_life_events').update({'choice_id': choice['choice_id']}) \
            .eq('id', card['user_life_event_id']).is_('choice_id', 'null').execute()
        if not taken.data:
            sanity_now = _sanity_of(uid)
            result = {
                'outcome': 'You already dealt with this one.', 'cash': 0.0, 'sanity': 0, 'income': 0.0, 'rel': 0,
                'new_sanity': sanity_now, 'new_balance': float(BalanceService.get_current_balance(uid)),
                'game_over': False,
            }
            card['result'] = result
            _update_card(uid, week, card_id, lambda c: c.update(result=result))
            return {'card': public_card(card), 'result': result,
                    'remaining': sum(1 for c in cards if not c.get('chosen'))}

    # 2. Money. If it fails, release the claim.
    reason = f"{card['title']} - {choice['label']}"
    new_balance = balance
    try:
        if cash > 0:
            new_balance = BalanceService.add_balance(uid, cash, reason, category='weekly_card').get('new_balance', balance + cash)
        elif cash < 0:
            new_balance = BalanceService.subtract_balance(uid, -cash, reason, category='weekly_card').get('new_balance', balance + cash)
    except Exception as e:
        def release(c):
            if c.get('chosen') != choice_id or c.get('result'):
                return False
            c['chosen'] = None
        _update_card(uid, week, card_id, release)
        if card['kind'] == 'life_event' and card.get('user_life_event_id'):
            supabase.table('user_life_events').update({'choice_id': None}) \
                .eq('id', card['user_life_event_id']).eq('choice_id', choice['choice_id']).execute()
        if _is_insufficient(e):
            raise WeekError('INSUFFICIENT_FUNDS', f"You can't afford that (${-cash:,.0f}).", 400)
        raise

    # 3-4. Income, sanity, relationship, history. The money has moved, so a
    #      failure here must not lose the card's result (the receipt reads it).
    income = Decimal('0')
    before = new_sanity = None
    rel_delta = 0
    try:
        income = Decimal(str(choice.get('income') or 0))
        if income and card.get('income_to') == 'job':
            income = _raise_main_job(uid, income)
        elif income:
            from app.services.profile_service import ProfileService
            ProfileService.update_monthly_income(uuid.UUID(uid), float(income))

        before = _sanity_of(uid)
        new_sanity = before
        who = (card.get('character') or {}).get('key') if isinstance(card.get('character'), dict) else None

        def sanity():
            if not choice.get('sanity'):
                return before
            res = supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': int(choice['sanity'])}).execute()
            return int(res.data) if res.data is not None else before

        def relationship():
            if not (who and choice.get('rel')):
                return 0
            from app.game import cast
            before_rel = cast.relationships(uid)[who]
            return cast.adjust(uid, who, choice['rel'], current=before_rel) - before_rel

        new_sanity, rel_delta = parallel(sanity, relationship)

        # 4. Life events keep their history (mentors and analytics read it).
        #    Pending ones were already claimed in step 1b.
        if card['kind'] == 'life_event' and not card.get('user_life_event_id'):
            try:
                supabase.table('user_life_events').insert({
                    'user_id': uid, 'life_event_id': card['life_event_id'], 'choice_id': choice['choice_id'],
                }).execute()
            except Exception as e:
                logger.error(f"Failed to record life event history for {uid}: {e}")

    except Exception as e:
        logger.error(f"Card effects after payment failed for {uid} card {card_id}: {e}")
    if before is None:
        before = new_sanity = _sanity_of(uid)

    result = {
        'outcome': choice['outcome'],
        'cash': float(cash),
        'sanity': new_sanity - before,
        'income': float(income),
        'rel': rel_delta,
        'new_sanity': new_sanity,
        'new_balance': float(new_balance),
        'game_over': new_sanity <= 0 < before,
    }
    card['result'] = result
    # Usually nobody touched the deck since the claim: save on top of it, and only re-read on a conflict.
    if _save_cards(claimed, [dict(c, result=result) if c['id'] == card_id else c for c in claimed.get('cards') or cards]) is None:
        _update_card(uid, week, card_id, lambda c: c.update(result=result) if c.get('chosen') == choice_id else False)
    return {'card': public_card(card), 'result': result, 'remaining': sum(1 for c in cards if not c.get('chosen'))}


def _raise_main_job(uid, monthly):
    """Raise the current main job's (annual) salary. Returns the monthly raise applied (0 if no job now)."""
    jobs = supabase.table('jobs').select('id, salary, kind').eq('user_id', uid).eq('is_current', True).execute().data or []
    main = next((j for j in jobs if (j.get('kind') or 'job') != 'gig'), None)
    if not main:
        return Decimal('0')  # quit between the deal and the swipe: nothing to raise
    new_salary = Decimal(str(main.get('salary') or 0)) + monthly * 12
    supabase.table('jobs').update({'salary': float(new_salary)}).eq('id', main['id']).execute()
    from app.services.profile_service import ProfileService
    ProfileService.recalculate_monthly_income(uuid.UUID(uid))
    return monthly


def _pay_gigs(uid):
    """Gigs pay every week (and the hours cost a little sanity). Returns receipt lines."""
    from app.game import economy
    out = []
    try:
        gigs = economy.current_gigs(uid)
    except Exception as e:
        logger.warning(f"Could not load gigs for {uid}: {e}")
        return out
    from app.game import courses
    for g in gigs:
        pay = economy.money(g.get('weekly_pay'))
        try:  # side-hustle courses raise a gig's pay
            pct, titles = courses.gig_bonus(uid, g['title'])
        except Exception as e:
            logger.warning(f"Gig course bonus for {uid} failed: {e}")
            pct, titles = Decimal('0'), []
        if pct > 0:
            pay = economy.money(pay * (1 + pct))
        if pay > 0:
            BalanceService.add_balance(uid, pay, f"Gig: {g['title']}", category='gig')
        sanity = int(g.get('sanity_per_week') or 0)
        if sanity:
            try:
                supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': sanity}).execute()
            except Exception as e:
                logger.warning(f"Gig sanity for {uid} failed: {e}")
        out.append({'title': g['title'], 'pay': float(pay), 'sanity': sanity, **({'bonus_pct': float(pct * 100), 'bonus_from': titles} if pct > 0 else {})})
    return out


def _course_finished(uid, c):
    """Tell the player (push) and their followers that a course is done."""
    from app.services.push_notification_service import ExpoPushService
    what = []
    if c.get('target_gig') and c.get('gig_bonus_pct'):
        what.append(f"+{c['gig_bonus_pct']:g}% pay as a {c['target_gig']}")
    if c.get('experience_months'):
        what.append(f"counts as {c['experience_months']} months in {c['industry']}")
    if c.get('pay_bonus_pct'):
        what.append(f"+{c['pay_bonus_pct']:g}% pay while you work in {c['industry']}")
    try:
        ExpoPushService.send_notification_to_user(supabase, uid, '📜 Course complete', f"You finished {c['title']}: {', '.join(what) or 'well done'}.",
                                                  notification_type='course_complete', data={'type': 'course_complete', 'screen': '/education'})
        ExpoPushService.notify_followers_of_financial_move(supabase_client=supabase, user_id=uid, move_type='complete_course', item_name=c['title'])
    except Exception as e:
        logger.warning(f'Course alerts failed for {uid}: {e}')


def complete_week(user_id: str) -> dict:
    """End the week: advance the clock, run the month on payday weeks, deal next week."""
    uid = str(user_id)
    clock = get_clock(uid)
    week = int(clock['week'])
    if not _can_play(clock):
        raise WeekError('WEEK_LOCKED', 'Next week unlocks tomorrow.', 403)
    start_age, deck = parallel(lambda: _check_life(uid, week), lambda: get_week(uid, week))
    if deck['status'] != 'open':
        raise WeekError('WEEK_COMPLETED', 'This week is already over.', 409)
    cards = deck.get('cards') or []
    left = [c for c in cards if not c.get('chosen')]
    if left:
        raise WeekError('CARDS_REMAINING', f'{len(left)} card(s) still need a decision.', 400)

    # Claim the turn: only one request can move the clock off this week.
    banked = int(clock['banked_weeks'])
    moved = supabase.table('player_game_clock').update({
        'week': week + 1,
        'banked_weeks': max(0, banked - 1) if not _unlimited() else max(1, banked),
    }).eq('user_id', uid).eq('week', week).execute()
    if not moved.data:
        raise WeekError('WEEK_COMPLETED', 'This week is already over.', 409)

    meta = week_meta(week)
    gigs = _pay_gigs(uid)
    month = None
    month_failed = False
    if meta['is_payday_week']:
        from jobs.monthly_loan_deductions import process_month_for_user
        try:
            month = process_month_for_user(uid, game_years=week / 52)
        except Exception as e:  # the week still ends; the receipt says the month didn't run
            month_failed = True
            logger.error(f"Month processing failed for {uid} at week {week}: {e}", exc_info=True)

    # The market moves one game week (app/game/market.py).
    market_week = None
    try:
        from app.game import market
        market_week = market.advance(uid, week)
        import uuid as _uuid
        from app.services.profile_service import ProfileService
        ProfileService.recalculate_net_worth(_uuid.UUID(uid))
    except Exception as e:  # the market never blocks a week
        logger.error(f"Market step failed for {uid} at week {week}: {e}")

    lines = []
    for c in cards:
        choice = next((ch for ch in c['choices'] if ch['id'] == c.get('chosen')), {})
        # A result that never got stored (see _update_card) falls back to the
        # card's listed effects rather than showing $0 for money that moved.
        r = c.get('result') or {k: choice.get(k, 0) for k in ('cash', 'sanity', 'income')}
        lines.append({
            'title': c['title'], 'icon': c.get('icon'), 'event_type': c.get('event_type'),
            'category': c.get('category'), 'character': c.get('character'),
            'choice': choice.get('label'), 'cash': r.get('cash', 0), 'sanity': r.get('sanity', 0), 'income': r.get('income', 0),
        })
    card_cash = sum(Decimal(str(l['cash'])) for l in lines)
    card_sanity = sum(int(l['sanity']) for l in lines)
    gig_cash = sum((Decimal(str(g['pay'])) for g in gigs), Decimal('0'))
    gig_sanity = sum(int(g['sanity']) for g in gigs)
    month_net = Decimal(str(month['net'])) if month else Decimal('0')
    month_sanity = int(month['sanity_change']) if month else 0

    from app.game import life as life_mod
    balance_after, sanity_after = parallel(lambda: BalanceService.get_current_balance(uid), lambda: _sanity_of(uid))
    receipt = {
        **meta,
        'age': life_mod.age_at(week, start_age),
        'birthday': life_mod.birthday_between(week, week + 1, start_age),
        'cards': lines,
        'gigs': gigs,
        # Your investments this week, and any crash or boom.
        'market': market_week,
        'month_summary': month,
        'month_failed': month_failed,
        'totals': {
            'cash': float(card_cash + gig_cash + month_net),
            'sanity': card_sanity + gig_sanity + month_sanity,
        },
        'balance_after': float(balance_after),
        'sanity_after': sanity_after,
        'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    # The cast, the squad, courses and the wishlist don't depend on each other, and neither does
    # dealing next week: do them all at once. None of them may block the week (the clock has moved on).
    def guarded(label, fn, default):
        def run():
            try:
                return fn()
            except Exception as e:
                logger.warning(f'{label} failed for {uid} at week {week}: {e}')
                return default
        return run

    def courses_done():
        from app.game import courses
        done = courses.after_week(uid)
        for c in done:
            _course_finished(uid, c)
        return done

    from app.game import cast, showroom, squads
    texts, squad, courses_finished, wishlist_unlocked, nxt = parallel(
        guarded('Cast reactions', lambda: cast.react_to_week(uid, receipt), []),
        guarded('Squad update', lambda: squads.record_week(uid, receipt), None),
        guarded('Course update', courses_done, []),
        guarded('Wishlist check', lambda: showroom.after_week(uid), []),
        lambda: state(uid, last_receipt=receipt),   # deals next week so the cliffhanger is a real card
    )
    receipt.update({'texts': texts, 'squad': squad, 'courses_finished': courses_finished, 'wishlist_unlocked': wishlist_unlocked})

    supabase.table('player_weeks').update({
        'status': 'completed', 'receipt': receipt, 'completed_at': receipt['completed_at'],
    }).eq('id', deck['id']).execute()
    return {'receipt': receipt, 'next': nxt}
