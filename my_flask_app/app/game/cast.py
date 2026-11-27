"""
The cast: characters who text you.

They react to your weeks (written when a week ends, from the receipt), and a
text can offer two quick replies with small effects on the relationship,
sanity or cash. Relationships (0..100, start at 50) also gate a few weekly
cards (weekly_cards.py: `character`, `min_rel`, `max_rel`).

What they say is in cast_lines.py. A line a player has had in the last REPEAT_DAYS
isn't sent again; if someone has run out, they simply stay quiet.
"""
import logging
import random
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import supabase
from app.game.cast_lines import LINES
from app.services.balance_service import BalanceService

logger = logging.getLogger(__name__)

CAST = {
    'mom': {'name': 'Mom', 'emoji': '👩‍🦱', 'bio': 'Loves you. Worries professionally.'},
    'bestie': {'name': 'Jordan', 'emoji': '🧢', 'bio': 'Best friend since 7th grade. Chaotic good.'},
    'roommate': {'name': 'Sam', 'emoji': '🎧', 'bio': 'Your roommate. Plays bass at 2am.'},
    'ex': {'name': 'Riley', 'emoji': '💔', 'bio': 'Your ex. Texts at the worst possible times.'},
}

START_SCORE = 50
MAX_TEXTS_PER_WEEK = 2
REPEAT_DAYS = 30               # no line twice within this many real days
PUSH_DELAY = timedelta(hours=3)  # a week's texts reach the phone this much later, if unread


def relationship_label(score):
    return 'Ride or die' if score >= 85 else 'Close' if score >= 65 else 'Good' if score >= 45 else 'Distant' if score >= 25 else 'Cold'


# --- relationships ---------------------------------------------------------------------

def relationships(uid):
    rows = supabase.table('player_relationships').select('character, score').eq('user_id', str(uid)).execute().data or []
    scores = {k: START_SCORE for k in CAST}
    scores.update({r['character']: int(r['score']) for r in rows if r['character'] in CAST})
    return scores


def adjust(uid, character, delta, current=None):
    """Nudge a relationship, clamped 0..100. Returns the new score. `current`: already read by the caller."""
    if character not in CAST or not delta:
        return current if current is not None else relationships(uid).get(character, START_SCORE)
    uid = str(uid)
    if current is None:
        current = relationships(uid)[character]
    new = max(0, min(100, current + int(delta)))
    now = datetime.now(timezone.utc).isoformat()
    upd = supabase.table('player_relationships').update({'score': new, 'updated_at': now}) \
        .eq('user_id', uid).eq('character', character).execute()
    if not upd.data:
        supabase.table('player_relationships').insert({'user_id': uid, 'character': character, 'score': new, 'updated_at': now}).execute()
    return new


# --- presence -------------------------------------------------------------------------

def present_cast(uid):
    """Who's in your life right now. Sam only exists if you rent and have no real roommate."""
    from app.game import roommates
    keys = ['mom', 'bestie', 'ex']
    rental = supabase.table('player_rentals').select('id').eq('player_id', str(uid)).eq('is_active', True).limit(1).execute().data
    if rental and not roommates.active_for(uid):
        keys.insert(2, 'roommate')
    return keys


# --- messages -------------------------------------------------------------------------

def send(uid, character, body, week=None, replies=None, from_player=False, push_due_at=None):
    row = {
        'user_id': str(uid), 'character': character, 'week': week, 'body': body,
        'from_player': from_player, 'replies': replies, 'replied_with': None,
        'read_at': datetime.now(timezone.utc).isoformat() if from_player else None,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    if push_due_at:  # jobs/cast_pushes.py sends it then, if it's still unread
        try:
            return supabase.table('cast_messages').insert({**row, 'push_due_at': push_due_at.isoformat()}).execute().data[0]
        except Exception as e:  # the column isn't there yet: the text matters more than its push
            if 'push_due_at' not in str(e):
                raise
            logger.warning('cast_messages.push_due_at is missing: run migration 20261214000000')
    return supabase.table('cast_messages').insert(row).execute().data[0]


def _opt(id_, label, response, rel=0, sanity=0, cash=0):
    return {'id': id_, 'label': label, 'response': response, 'rel': rel, 'sanity': sanity, 'cash': cash}


INTROS = {
    'mom': ("hi sweetie!! did you eat today? call your mother 😘", [
        _opt('a', 'Yes mom ❤️', 'good. eat a vegetable too', rel=3),
        _opt('b', 'define "eat"', "I'm sending you soup recipes. don't argue", rel=1, sanity=1),
    ]),
    'bestie': ("yo. adulting update?? are we thriving or surviving 💀", [
        _opt('a', 'Surviving. Barely.', 'same. we ride at dawn (to the discount aisle)', rel=3, sanity=2),
        _opt('b', 'Thriving obviously', "liar. but I respect the delusion", rel=1),
    ]),
}


def ensure_intros(uid):
    """A first-time player's phone shouldn't be empty."""
    any_msg = supabase.table('cast_messages').select('id').eq('user_id', str(uid)).limit(1).execute().data
    if any_msg:
        return
    for character, (body, replies) in INTROS.items():
        send(uid, character, body, week=None, replies=replies)


def _was_sent(template, recent):
    """Has this line gone out lately? A line with {age} or {what} counts whatever was filled in."""
    pattern = re.escape(template).replace(r'\{age\}', '.+').replace(r'\{what\}', '.+')
    return any(re.fullmatch(pattern, body, re.DOTALL) for body in recent)


def _pick(character, situation, rng, recent, **fill):
    """(body, replies) for a line this player hasn't had in the last REPEAT_DAYS, or None if they've had them all."""
    fresh = [line for line in LINES[(character, situation)] if not _was_sent(line[0], recent)]
    if not fresh:
        return None
    body, options = rng.choice(fresh)
    for key, value in fill.items():
        body = body.replace('{' + key + '}', str(value))
    replies = [_opt('ab'[i], label, response, rel=rel, sanity=sanity, cash=cash)
               for i, (label, response, rel, sanity, cash) in enumerate(options)]
    return body, replies


def recent_bodies(uid, now=None):
    """What the cast has texted this player in the last REPEAT_DAYS."""
    since = ((now or datetime.now(timezone.utc)) - timedelta(days=REPEAT_DAYS)).isoformat()
    rows = supabase.table('cast_messages').select('body').eq('user_id', str(uid)).eq('from_player', False) \
        .gte('created_at', since).limit(1000).execute().data or []
    return [r['body'] for r in rows]


def _week_texts(receipt, rel, present, rng, recent=()):
    """Candidate texts for a finished week, most relevant first: (character, body, replies)."""
    out = []
    month = receipt.get('month_summary') or {}
    missed = [l for l in month.get('lines', []) if l.get('missed') and not l.get('error')]
    totals = receipt.get('totals') or {}
    cards = receipt.get('cards') or []

    def add(character, situation, **fill):
        line = _pick(character, situation, rng, recent, **fill)
        if line:
            out.append((character, *line))

    if receipt.get('birthday'):
        add('mom', 'birthday', age=receipt['birthday'])
        add('bestie', 'birthday', age=receipt['birthday'])

    if missed:
        what = missed[0]['label'].replace('Missed: ', '').replace('Missed rent: ', 'rent')
        add('mom', 'missed', what=what.lower())
        # Mom only lends when you're on good terms.
        if out and out[-1][0] == 'mom' and rel['mom'] < 50:
            for option in out[-1][2]:
                if option['cash'] > 0:
                    option.update(response="sweetie I can't right now. maybe call the bank?", rel=-2, sanity=-2, cash=0)
    elif receipt.get('is_payday_week') and rng.random() < 0.6:
        add('mom', 'payday')

    if (totals.get('sanity') or 0) <= -8:
        add('bestie', 'rough')
    elif (totals.get('cash') or 0) <= -150:
        add('bestie', 'broke')
    elif any(c.get('category') == 'social' and (c.get('cash') or 0) < 0 for c in cards):
        add('bestie', 'social')

    # Out of the blue. Shuffled, so the same person doesn't always get the free slot.
    odds = {'roommate': 0.35, 'ex': 0.2 if (totals.get('sanity') or 0) < 0 else 0.1, 'mom': 0.2, 'bestie': 0.25}
    chatty = [c for c, chance in odds.items() if c in present and rng.random() < chance]
    rng.shuffle(chatty)
    for character in chatty:
        add(character, 'casual')
    return out


def react_to_week(uid, receipt):
    """Write this week's texts (at most MAX_TEXTS_PER_WEEK). Returns how many were sent."""
    uid = str(uid)
    week = receipt.get('week')
    try:
        rel = relationships(uid)
        present = present_cast(uid)
        rng = random.Random(f'{uid}:{week}:texts')
        sent, used = 0, set()
        push_at = datetime.now(timezone.utc) + PUSH_DELAY
        for character, body, replies in _week_texts(receipt, rel, present, rng, recent_bodies(uid)):
            if sent >= MAX_TEXTS_PER_WEEK:
                break
            if character in used or character not in present:
                continue
            send(uid, character, body, week=week, replies=replies, push_due_at=push_at)
            used.add(character)
            sent += 1
        return sent
    except Exception as e:  # texts are flavour: never fail the week over them
        logger.error(f'Cast texts failed for {uid} week {week}: {e}')
        return 0


class CastError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def reply(uid, message_id, reply_id):
    """Answer a text with one of its quick replies, once."""
    uid = str(uid)
    res = supabase.table('cast_messages').select('*').eq('id', message_id).eq('user_id', uid).limit(1).execute()
    if not res.data:
        raise CastError('NOT_FOUND', 'That text no longer exists.', 404)
    msg = res.data[0]
    option = next((o for o in (msg.get('replies') or []) if o['id'] == reply_id), None)
    if option is None:
        raise CastError('INVALID_REPLY', "That's not one of the replies.", 400)
    if msg.get('replied_with'):
        raise CastError('ALREADY_REPLIED', 'You already replied.', 409)

    cash = Decimal(str(option.get('cash') or 0))
    if cash < 0 and BalanceService.get_current_balance(uid) < -cash:
        raise CastError('INSUFFICIENT_FUNDS', f"You can't afford that (${-cash:,.0f}).", 400)

    claimed = supabase.table('cast_messages').update({'replied_with': reply_id}) \
        .eq('id', message_id).is_('replied_with', 'null').execute()
    if not claimed.data:
        raise CastError('ALREADY_REPLIED', 'You already replied.', 409)

    name = CAST.get(msg['character'], {}).get('name', 'them')
    try:
        if cash > 0:
            BalanceService.add_balance(uid, cash, f'From {name}', category='cast')
        elif cash < 0:
            BalanceService.subtract_balance(uid, -cash, f'For {name}', category='cast')
    except Exception:
        # Nothing happened, so the reply stays open.
        supabase.table('cast_messages').update({'replied_with': None}).eq('id', message_id).eq('replied_with', reply_id).execute()
        raise
    new_sanity = None
    if option.get('sanity'):
        new_sanity = supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': int(option['sanity'])}).execute().data
    score = adjust(uid, msg['character'], option.get('rel') or 0)

    send(uid, msg['character'], option['label'], week=msg.get('week'), from_player=True)
    if option.get('response'):
        send(uid, msg['character'], option['response'], week=msg.get('week'))
        mark_read(uid, msg['character'])
    return {
        'relationship': {'score': score, 'label': relationship_label(score)},
        'effects': {'cash': float(cash), 'sanity': int(option.get('sanity') or 0), 'rel': int(option.get('rel') or 0)},
        'new_sanity': new_sanity,
    }


def mark_read(uid, character):
    supabase.table('cast_messages').update({'read_at': datetime.now(timezone.utc).isoformat()}) \
        .eq('user_id', str(uid)).eq('character', character).is_('read_at', 'null').execute()


# --- views ----------------------------------------------------------------------------

def threads(uid):
    uid = str(uid)
    ensure_intros(uid)
    rel = relationships(uid)
    msgs = supabase.table('cast_messages').select('*').eq('user_id', uid).order('created_at', desc=True).limit(200).execute().data or []
    out = []
    for key in present_cast(uid):
        mine = [m for m in msgs if m['character'] == key]
        last = mine[0] if mine else None
        out.append({
            'character': key, **CAST[key],
            'relationship': {'score': rel[key], 'label': relationship_label(rel[key])},
            'last': {'body': last['body'], 'from_player': last['from_player'], 'created_at': last['created_at']} if last else None,
            'unread': sum(1 for m in mine if not m['from_player'] and not m.get('read_at')),
            'awaiting_reply': any(m.get('replies') and not m.get('replied_with') for m in mine),
        })
    out.sort(key=lambda t: (t['last'] or {}).get('created_at') or '', reverse=True)
    return out


def thread(uid, character):
    if character not in CAST:
        raise CastError('NOT_FOUND', 'Unknown contact.', 404)
    uid = str(uid)
    msgs = supabase.table('cast_messages').select('*').eq('user_id', uid).eq('character', character) \
        .order('created_at', desc=True).limit(60).execute().data or []
    mark_read(uid, character)
    rel = relationships(uid)[character]
    return {
        'character': character, **CAST[character],
        'relationship': {'score': rel, 'label': relationship_label(rel)},
        'messages': list(reversed(msgs)),
    }


def unread_count(uid):
    """Unread texts you can actually open: someone who left your life has no thread to clear them."""
    rows = supabase.table('cast_messages').select('id, character').eq('user_id', str(uid)).eq('from_player', False).is_('read_at', 'null').execute().data or []
    present = set(present_cast(uid))
    return sum(1 for r in rows if r['character'] in present)


def reset(uid):
    """New life, new relationships."""
    supabase.table('player_relationships').delete().eq('user_id', str(uid)).execute()
    supabase.table('cast_messages').delete().eq('user_id', str(uid)).execute()
