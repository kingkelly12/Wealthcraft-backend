"""
Turn-based time: the player's game clock and weekly deck ("This Week").

One turn = one in-game week, played as a deck of CARDS_PER_WEEK swipe cards.
Every WEEKS_PER_MONTH-th week ends with the player's month (salary, loans,
rent, living costs, asset income, missions) via process_month_for_user().

Weeks unlock one per real (UTC) day and up to MAX_BANKED can be saved up, so
missing a day leaves a catch-up deck rather than a lost streak. Set
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

logger = logging.getLogger(__name__)

WEEKS_PER_MONTH = 4
MAX_BANKED = 2
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
                'user_id': uid, 'week': 1, 'banked_weeks': 1, 'bank_updated_on': today.isoformat(),
            }).execute()
        except Exception as e:  # lost a creation race: read the winner's row
            if '23505' not in str(e) and 'duplicate' not in str(e).lower():
                raise
        res = supabase.table('player_game_clock').select('*').eq('user_id', uid).limit(1).execute()
    clock = res.data[0]

    # One new week per day since the bank was last topped up, capped.
    last = date.fromisoformat(str(clock['bank_updated_on'])[:10])
    days = (today - last).days
    if days > 0:
        banked = min(MAX_BANKED, int(clock['banked_weeks']) + days)
        upd = supabase.table('player_game_clock').update({
            'banked_weeks': banked, 'bank_updated_on': today.isoformat(),
        }).eq('user_id', uid).eq('bank_updated_on', clock['bank_updated_on']).execute()
        if upd.data:
            clock = upd.data[0]
        else:  # someone else refreshed it first
            clock = supabase.table('player_game_clock').select('*').eq('user_id', uid).limit(1).execute().data[0]
    return clock


def _can_play(clock) -> bool:
    return _unlimited() or int(clock['banked_weeks']) >= 1


# --- deck ---------------------------------------------------------------------

def _player_context(uid: str) -> dict:
    jobs = supabase.table('jobs').select('id').eq('user_id', uid).eq('is_current', True).limit(1).execute()
    rentals = supabase.table('player_rentals').select('id').eq('player_id', uid).eq('is_active', True).limit(1).execute()
    return {
        'job': bool(jobs.data),
        'rental': bool(rentals.data),
        'balance': BalanceService.get_current_balance(uid),
    }


def _eligible(card, ctx) -> bool:
    req = card.get('requires')
    return {
        None: True,
        'job': ctx['job'],
        'no_job': not ctx['job'],
        'rental': ctx['rental'],
        'no_rental': not ctx['rental'],
    }.get(req, True)


def _everyday_card(card) -> dict:
    def side(sid, c):
        return {
            'id': sid, 'label': c['label'], 'outcome': c['outcome'],
            'cash': float(c.get('cash', 0)), 'sanity': int(c.get('sanity', 0)), 'income': float(c.get('income', 0)),
        }
    return {
        'kind': 'everyday', 'key': card['key'], 'category': card['category'], 'icon': card['icon'],
        'title': card['title'], 'body': card['body'], 'teaser': card['teaser'],
        'choices': [side('left', card['left']), side('right', card['right'])],
    }


def _life_event_card(event, choices, user_life_event_id=None) -> dict:
    """Mirrors life_event_routes.make_life_event_choice's effect rules."""
    def side(sid, ch):
        sanity = ch.get('impact_sanity') or event.get('impact_sanity') or 0
        income = ch.get('impact_income') or event.get('impact_income') or 0
        return {
            'id': sid, 'label': ch['choice_label'], 'outcome': ch.get('outcome_description') or '',
            'cash': float(Decimal(str(ch.get('benefit') or 0)) - Decimal(str(ch.get('cost') or 0))),
            'sanity': int(sanity), 'income': float(income), 'choice_id': ch['id'],
        }
    return {
        'kind': 'life_event', 'life_event_id': event['id'], 'user_life_event_id': user_life_event_id,
        'category': 'life_event', 'event_type': event.get('event_type') or 'neutral', 'icon': None,
        'title': event['title'], 'body': event['description'], 'teaser': f"{event['title']} 👀",
        'choices': [side('left', choices[0]), side('right', choices[1])],
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


def _life_event_cards(uid, rng, ctx, want):
    """Pending life events first (assigned before the player joined game time), then fresh ones."""
    cards = []
    pending = supabase.table('user_life_events').select('id, life_event_id') \
        .eq('user_id', uid).is_('choice_id', 'null').order('created_at').limit(MAX_LIFE_EVENTS).execute().data or []
    recent = supabase.table('user_life_events').select('life_event_id') \
        .eq('user_id', uid).order('created_at', desc=True).limit(30).execute().data or []
    seen = {r['life_event_id'] for r in recent}

    events = supabase.table('life_events').select('*').eq('is_active', True).execute().data or []
    by_id = {e['id']: e for e in events}
    choices = _choices_for(by_id.keys())

    for p in pending:
        event = by_id.get(p['life_event_id'])
        if event and len(choices.get(event['id'], [])) >= 2:
            cards.append(_life_event_card(event, choices[event['id']], user_life_event_id=p['id']))

    fresh = [e for e in events if e['id'] not in seen and len(choices.get(e['id'], [])) >= 2]
    if not fresh:  # played them all: allow repeats rather than an empty slot
        fresh = [e for e in events if len(choices.get(e['id'], [])) >= 2]
    rng.shuffle(fresh)
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
    rows = supabase.table('player_weeks').select('week, cards').eq('user_id', uid) \
        .gte('week', week - RECENT_DECKS_NO_REPEAT).lt('week', week).execute().data or []
    return {c.get('key') for r in rows for c in (r.get('cards') or []) if c.get('kind') == 'everyday'}


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
        pool = [c for c in CARDS if _eligible(c, ctx)]
    picks = rng.sample(pool, k=min(CARDS_PER_WEEK - len(cards), len(pool)))
    cards += [_everyday_card(c) for c in picks]

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


def state(user_id: str) -> dict:
    """Everything the This Week screen and the home card need."""
    uid = str(user_id)
    today = _today()
    clock = get_clock(uid)
    week = int(clock['week'])
    deck = get_week(uid, week)
    cards = deck.get('cards') or []
    remaining = sum(1 for c in cards if not c.get('chosen'))

    last = None
    if week > 1:
        prev = supabase.table('player_weeks').select('receipt').eq('user_id', uid).eq('week', week - 1).limit(1).execute()
        last = prev.data[0].get('receipt') if prev.data else None

    banked = int(clock['banked_weeks'])
    return {
        **week_meta(week),
        'banked_weeks': banked,
        'max_banked': MAX_BANKED,
        'can_play': _can_play(clock),
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


def _is_insufficient(e):
    return 'Insufficient funds' in str(e)


def choose(user_id: str, card_id: str, choice_id: str) -> dict:
    """Resolve one card. Returns {'card': public card, 'result': {...}}."""
    uid = str(user_id)
    clock = get_clock(uid)
    if not _can_play(clock):
        raise WeekError('WEEK_LOCKED', 'Next week unlocks tomorrow.', 403)
    deck = get_week(uid, int(clock['week']))
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
        balance = BalanceService.get_current_balance(uid)
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

    # 2. Money. If it fails, release the claim.
    reason = f"{card['title']} - {choice['label']}"
    try:
        if cash > 0:
            BalanceService.add_balance(uid, cash, reason, category='weekly_card')
        elif cash < 0:
            BalanceService.subtract_balance(uid, -cash, reason, category='weekly_card')
    except Exception as e:
        card['chosen'] = None
        _save_cards(claimed, cards)
        if _is_insufficient(e):
            raise WeekError('INSUFFICIENT_FUNDS', f"You can't afford that (${-cash:,.0f}).", 400)
        raise

    # 3. Income and sanity.
    income = Decimal(str(choice.get('income') or 0))
    if income:
        from app.services.profile_service import ProfileService
        ProfileService.update_monthly_income(uuid.UUID(uid), float(income))

    before = _sanity_of(uid)
    new_sanity = before
    if choice.get('sanity'):
        res = supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': int(choice['sanity'])}).execute()
        new_sanity = int(res.data) if res.data is not None else before

    # 4. Life events keep their history (mentors and analytics read it).
    if card['kind'] == 'life_event':
        try:
            if card.get('user_life_event_id'):
                supabase.table('user_life_events').update({'choice_id': choice['choice_id']}) \
                    .eq('id', card['user_life_event_id']).is_('choice_id', 'null').execute()
            else:
                supabase.table('user_life_events').insert({
                    'user_id': uid, 'life_event_id': card['life_event_id'],
                    'choice_id': choice['choice_id'], 'was_auto_selected': False,
                }).execute()
        except Exception as e:
            logger.error(f"Failed to record life event history for {uid}: {e}")

    result = {
        'outcome': choice['outcome'],
        'cash': float(cash),
        'sanity': new_sanity - before,
        'income': float(income),
        'new_sanity': new_sanity,
        'new_balance': float(BalanceService.get_current_balance(uid)),
        'game_over': new_sanity <= 0 < before,
    }
    card['result'] = result
    if _save_cards(claimed, cards) is None:
        logger.warning(f"Could not store result for {uid} card {card_id} (deck changed)")
    return {'card': public_card(card), 'result': result, 'remaining': sum(1 for c in cards if not c.get('chosen'))}


def complete_week(user_id: str) -> dict:
    """End the week: advance the clock, run the month on payday weeks, deal next week."""
    uid = str(user_id)
    clock = get_clock(uid)
    week = int(clock['week'])
    if not _can_play(clock):
        raise WeekError('WEEK_LOCKED', 'Next week unlocks tomorrow.', 403)
    deck = get_week(uid, week)
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
    month = None
    if meta['is_payday_week']:
        from jobs.monthly_loan_deductions import process_month_for_user
        try:
            month = process_month_for_user(uid, game_years=week / 52)
        except Exception as e:  # the week still ends; the player sees a partial receipt
            logger.error(f"Month processing failed for {uid} at week {week}: {e}")

    lines = []
    for c in cards:
        r = c.get('result') or {}
        choice = next((ch for ch in c['choices'] if ch['id'] == c.get('chosen')), {})
        lines.append({
            'title': c['title'], 'icon': c.get('icon'), 'event_type': c.get('event_type'),
            'choice': choice.get('label'), 'cash': r.get('cash', 0), 'sanity': r.get('sanity', 0), 'income': r.get('income', 0),
        })
    card_cash = sum(Decimal(str(l['cash'])) for l in lines)
    card_sanity = sum(int(l['sanity']) for l in lines)
    month_net = Decimal(str(month['net'])) if month else Decimal('0')
    month_sanity = int(month['sanity_change']) if month else 0

    receipt = {
        **meta,
        'cards': lines,
        'month_summary': month,
        'totals': {
            'cash': float(card_cash + month_net),
            'sanity': card_sanity + month_sanity,
        },
        'balance_after': float(BalanceService.get_current_balance(uid)),
        'sanity_after': _sanity_of(uid),
        'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    supabase.table('player_weeks').update({
        'status': 'completed', 'receipt': receipt, 'completed_at': receipt['completed_at'],
    }).eq('id', deck['id']).execute()

    # Deal next week now so the cliffhanger is about a real card.
    nxt = state(uid)
    return {'receipt': receipt, 'next': nxt}
