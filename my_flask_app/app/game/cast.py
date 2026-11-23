"""
The cast: characters who text you.

They react to your weeks (written when a week ends, from the receipt), and a
text can offer two quick replies with small effects on the relationship,
sanity or cash. Relationships (0..100, start at 50) also gate a few weekly
cards (weekly_cards.py: `character`, `min_rel`, `max_rel`).

Writing rules: texts read like real texts (lowercase is fine, short, emoji
sparingly). Every reply option has a `response` so the thread feels alive.
"""
import logging
import random
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase
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


def relationship_label(score):
    return 'Ride or die' if score >= 85 else 'Close' if score >= 65 else 'Good' if score >= 45 else 'Distant' if score >= 25 else 'Cold'


# --- relationships ---------------------------------------------------------------------

def relationships(uid):
    rows = supabase.table('player_relationships').select('character, score').eq('user_id', str(uid)).execute().data or []
    scores = {k: START_SCORE for k in CAST}
    scores.update({r['character']: int(r['score']) for r in rows if r['character'] in CAST})
    return scores


def adjust(uid, character, delta):
    """Nudge a relationship, clamped 0..100. Returns the new score."""
    if character not in CAST or not delta:
        return relationships(uid).get(character, START_SCORE)
    uid = str(uid)
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

def send(uid, character, body, week=None, replies=None, from_player=False):
    row = {
        'user_id': str(uid), 'character': character, 'week': week, 'body': body,
        'from_player': from_player, 'replies': replies, 'replied_with': None,
        'read_at': datetime.now(timezone.utc).isoformat() if from_player else None,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
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


def _week_texts(receipt, rel, present, rng):
    """Candidate texts for a finished week, most relevant first: (character, body, replies)."""
    out = []
    month = receipt.get('month_summary') or {}
    missed = [l for l in month.get('lines', []) if l.get('missed') and not l.get('error')]
    totals = receipt.get('totals') or {}
    cards = receipt.get('cards') or []

    if receipt.get('birthday'):
        out.append(('mom', f"HAPPY {receipt['birthday']}TH BIRTHDAY MY BABY 🎂🎂 I sent you a little something. call me!!", [
            _opt('a', 'Calling now ❤️', "best gift is hearing your voice. (the $50 is also nice)", rel=6, sanity=5, cash=50),
            _opt('b', 'ty mom', "ok. love you. the $50 is for food not 'experiences'", rel=1, cash=50),
        ]))
        out.append(('bestie', "HBD 🎉 another year closer to a 401k. drinks on me this weekend", [
            _opt('a', "I'm holding you to that", "bet. I'll bring my coupon app", rel=4, sanity=3),
            _opt('b', "Can't afford to age", 'none of us can. happy birthday anyway', rel=2, sanity=1),
        ]))

    if missed:
        what = missed[0]['label'].replace('Missed: ', '').replace('Missed rent: ', 'rent')
        out.append(('mom', f"honey the bank called about {what.lower()}?? is everything ok 😟", [
            _opt('a', "It's handled 😅", "ok... you'd tell me if it wasn't right?", rel=-1, sanity=-1),
            _opt('b', "...can you spot me $150?", "just this once. and we're talking about a budget at thanksgiving", rel=-4, cash=150) if rel['mom'] >= 50
            else _opt('b', "...can you spot me $150?", "sweetie I can't right now. maybe call the bank?", rel=-2, sanity=-2),
        ]))
    elif receipt.get('is_payday_week') and rng.random() < 0.6:
        out.append(('mom', "payday!! proud of you. put some in savings ok? ❤️", [
            _opt('a', 'I will mom ❤️', "that's my kid", rel=3),
            _opt('b', 'lol no', "I didn't raise you to say lol no to me", rel=-2, sanity=1),
        ]))

    if (totals.get('sanity') or 0) <= -8:
        out.append(('bestie', "you've been quiet this week. you ok?", [
            _opt('a', 'Not really tbh', "ok I'm coming over with snacks. no arguments", rel=5, sanity=6),
            _opt('b', 'All good!', "...ok. I'm here if that changes", rel=-1, sanity=-2),
        ]))
    elif (totals.get('cash') or 0) <= -150:
        out.append(('bestie', "bro your bank account just called me crying 💀", [
            _opt('a', 'help 😭', "free activities this weekend. I'm thinking park + sad sandwiches", rel=3, sanity=3),
            _opt('b', "I'm fine. Totally fine.", "that's what the titanic said", sanity=-1),
        ]))
    elif any(c.get('category') == 'social' and (c.get('cash') or 0) < 0 for c in cards):
        out.append(('bestie', "last night was LEGENDARY 😂 we're never doing that again (we're doing it again)", [
            _opt('a', 'Same time next week?', "my wallet says no. my heart says yes", rel=4, sanity=2),
            _opt('b', 'My wallet is in the ER', 'tell it to stay strong', rel=2),
        ]))

    if 'roommate' in present and rng.random() < 0.3:
        body, replies = rng.choice([
            ("who ate my leftovers. I'm not mad. I'm just disappointed", [
                _opt('a', 'Guilty. Buying you dinner', "apology accepted. extra guac", rel=5, cash=-15),
                _opt('b', 'Must have been a ghost', "the ghost left a fork in the sink", rel=-4),
            ]),
            ("band practice at ours friday? it'll be quiet I promise", [
                _opt('a', 'Sure, why not', "you're the best. bring earplugs", rel=4, sanity=-3),
                _opt('b', 'I have work Saturday', "fair. we'll do the acoustic version (still loud)", rel=-1),
            ]),
        ])
        out.append(('roommate', body, replies))

    ex_odds = 0.25 if (totals.get('sanity') or 0) < 0 else 0.1
    if rng.random() < ex_odds:
        out.append(('ex', rng.choice(["u up?", "saw something that reminded me of you. anyway how's life", "do you still have my hoodie"]), [
            _opt('a', '...yeah', "lol remember when we... nvm. goodnight", rel=6, sanity=-6),
            _opt('b', 'Blocked.', None, rel=-15, sanity=4),
        ]))
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
        for character, body, replies in _week_texts(receipt, rel, present, rng):
            if sent >= MAX_TEXTS_PER_WEEK:
                break
            if character in used or character not in present:
                continue
            send(uid, character, body, week=week, replies=replies)
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
