"""
Squads: a named crew of up to MAX_MEMBERS players who play together.

* One squad per player. Anyone can start one; others join with its code (or a
  push invite from a friend they're followed by, which carries the code).
* Squads run on the real calendar week (Monday 00:00 UTC), because every
  player's game clock is different:
  - The race: members are ranked by net worth growth this week (net worth now
    minus at the start of the week), so a low earner can beat a high earner.
  - The squad goal (co-op): play GOAL_PER_MEMBER game weeks per member between
    you, AND every member plays at least MIN_WEEKS_PER_MEMBER of them (one player
    can't carry the squad). Hitting it gives every member +GOAL_SANITY sanity
    (once a week per player, even if they hop squads) and extends the squad streak.
  - Last week's MVP: the member who played and grew the most.
* Settlement (MVP, streak) happens lazily the first time anyone touches the
  squad in a new week, claimed with an optimistic update on settled_week.
* The feed: paydays, birthdays, big swings, endings, joins and goals, with
  emoji reactions.

Tables: squads, squad_members, squad_member_weeks, squad_feed, squad_reactions, squad_rewards.
"""
import logging
import random
import re
import uuid as _uuidlib
from datetime import date, datetime, timedelta, timezone

from app import supabase

logger = logging.getLogger(__name__)

MAX_MEMBERS = 8
GOAL_PER_MEMBER = 3
MIN_WEEKS_PER_MEMBER = 1      # nobody rides for free: every member plays at least this many weeks
GOAL_SANITY = 5
BIG_SWING = 500             # a card worth at least this much makes the feed
POSTS_PER_WEEK = 2          # feed posts one finished game week can make
FEED_LIMIT = 30
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'   # no 0/O, 1/I/L
CODE_LENGTH = 6
EMOJIS = ['🔥', '🦁', '🐺', '🦈', '💸', '🍕', '🚀', '👑', '🌱', '🎯', '🐐', '🛋️']
REACTIONS = ['🔥', '😂', '💀', '🫡', '❤️']
FEED_RETENTION_DAYS = 60    # older posts are pruned when the week settles
WEEKS_KEPT = 8              # per-member week rows older than this are pruned (only last week is ever read)


class SquadError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


# --- time ---------------------------------------------------------------------------

def _today() -> date:
    return datetime.now(timezone.utc).date()


def week_start(d: date = None) -> date:
    d = d or _today()
    return d - timedelta(days=d.weekday())


def _now():
    return datetime.now(timezone.utc).isoformat()


def _uuid(value, status=400, code='INVALID_ID', message='That id is not valid.'):
    """A well-formed uuid string, else a client error (Postgres answers a malformed one with a 500)."""
    try:
        return str(_uuidlib.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        raise SquadError(code, message, status)


def _is_duplicate(e) -> bool:
    return '23505' in str(e) or 'duplicate' in str(e).lower()


def _money(n) -> str:
    n = float(n or 0)
    return f"{'+' if n >= 0 else '−'}${abs(n):,.0f}"


# --- reads --------------------------------------------------------------------------

def membership(uid):
    res = supabase.table('squad_members').select('*').eq('user_id', str(uid)).limit(1).execute()
    return res.data[0] if res.data else None


def _squad(sid):
    res = supabase.table('squads').select('*').eq('id', sid).limit(1).execute()
    return res.data[0] if res.data else None


def _members(sid):
    return supabase.table('squad_members').select('*').eq('squad_id', sid).order('joined_at').execute().data or []


def _profiles(ids):
    ids = [str(i) for i in ids if i]
    if not ids:
        return {}
    rows = supabase.table('profiles').select('user_id, username, profile_picture_url, net_worth, sanity') \
        .in_('user_id', ids).execute().data or []
    return {str(r['user_id']): r for r in rows}


def _nw(profile) -> float:
    return float((profile or {}).get('net_worth') or 0)


def _week_rows(sid, ws):
    rows = supabase.table('squad_member_weeks').select('*').eq('squad_id', sid).eq('week_start', ws.isoformat()).execute().data or []
    return {str(r['user_id']): r for r in rows}


def _ensure_rows(sid, uids, profiles, ws):
    """This week's row for each member (start net worth = now, the first time we see them)."""
    rows = _week_rows(sid, ws)
    for uid in uids:
        if uid in rows:
            continue
        try:
            row = supabase.table('squad_member_weeks').insert({
                'squad_id': sid, 'user_id': uid, 'week_start': ws.isoformat(),
                'start_net_worth': _nw(profiles.get(uid)), 'weeks_played': 0,
            }).execute().data[0]
            rows[uid] = row
        except Exception as e:  # another request created it first
            if not _is_duplicate(e):
                raise
            rows = {**rows, **_week_rows(sid, ws)}
    return rows


def _post(sid, uid, kind, emoji, body):
    try:
        supabase.table('squad_feed').insert({
            'squad_id': sid, 'user_id': str(uid) if uid else None, 'kind': kind,
            'emoji': emoji, 'body': body, 'created_at': _now(),
        }).execute()
    except Exception as e:
        logger.warning(f'Squad feed post failed ({kind}): {e}')


def _push(uids, title, body, data=None):
    """One batched push to several players (one Expo request, not one per member)."""
    uids = [str(u) for u in uids if u]
    if not uids:
        return
    try:
        from app.services.push_notification_service import ExpoPushService
        ExpoPushService.send_notifications_to_users(
            supabase_client=supabase,
            user_notifications=[{'user_id': u, 'title': title, 'body': body,
                                 'data': data or {'screen': '/(tabs)/squad'}} for u in uids],
            notification_type='social')
    except Exception as e:
        logger.warning(f'Squad push failed: {e}')


# --- weekly settlement ----------------------------------------------------------------

def _settle(squad):
    """Close last week (MVP, streak) once, the first time the squad is touched this week."""
    ws = week_start()
    if str(squad['settled_week']) >= ws.isoformat():
        return squad
    prev = ws - timedelta(days=7)
    member_ids = [str(m['user_id']) for m in _members(squad['id'])]
    profiles = _profiles(member_ids)
    rows = _week_rows(squad['id'], prev)

    best = None
    for uid, r in rows.items():
        if uid not in profiles or int(r.get('weeks_played') or 0) <= 0:
            continue
        # Net worth when they last finished a game week IN that week (record_week).
        # Reading it now instead would count this week's growth too: settlement is
        # lazy, so "now" can be days into the new week.
        end = r.get('end_net_worth')
        end = float(end) if end is not None else _nw(profiles[uid])   # rows from before end_net_worth was recorded
        growth = end - float(r.get('start_net_worth') or 0)
        if growth > 0 and (best is None or growth > best[1]):   # nobody is MVP of a week they lost money in
            best = (uid, growth)
    mvp = None
    if best:
        mvp = {'user_id': best[0], 'username': profiles[best[0]].get('username', 'Someone'),
               'growth': round(best[1], 2), 'week_start': prev.isoformat()}
    streak = int(squad.get('streak') or 0) if str(squad.get('goal_hit_week')) == prev.isoformat() else 0

    claimed = supabase.table('squads').update({'settled_week': ws.isoformat(), 'last_mvp': mvp, 'streak': streak}) \
        .eq('id', squad['id']).eq('settled_week', squad['settled_week']).execute()
    if not claimed.data:
        return _squad(squad['id']) or squad
    try:  # housekeeping: the feed and old week rows only ever grow
        supabase.table('squad_feed').delete().eq('squad_id', squad['id']) \
            .lt('created_at', (datetime.now(timezone.utc) - timedelta(days=FEED_RETENTION_DAYS)).isoformat()).execute()
        supabase.table('squad_member_weeks').delete().eq('squad_id', squad['id']) \
            .lt('week_start', (ws - timedelta(weeks=WEEKS_KEPT)).isoformat()).execute()
    except Exception as e:
        logger.warning(f'Squad pruning failed: {e}')
    if mvp:
        _post(squad['id'], mvp['user_id'], 'mvp', '👑', f"was last week's MVP ({_money(mvp['growth'])})")
    return claimed.data[0]


def _played(rows, member_ids):
    """(total weeks played, ids of the members who haven't played the minimum yet)."""
    total = sum(int((rows.get(i) or {}).get('weeks_played') or 0) for i in member_ids)
    idle = [i for i in member_ids if int((rows.get(i) or {}).get('weeks_played') or 0) < MIN_WEEKS_PER_MEMBER]
    return total, idle


def _effective_streak(squad, ws):
    hit = str(squad.get('goal_hit_week'))
    if hit in (ws.isoformat(), (ws - timedelta(days=7)).isoformat()):
        return int(squad.get('streak') or 0)
    return 0


# --- the game hooks -------------------------------------------------------------------

def ensure_baseline(uid):
    """Before a player's first card of the calendar week: record where their net worth started."""
    uid = str(uid)
    m = membership(uid)
    if not m:
        return
    squad = _squad(m['squad_id'])
    if not squad:
        return
    _settle(squad)
    ws = week_start()
    have = supabase.table('squad_member_weeks').select('user_id').eq('squad_id', squad['id']) \
        .eq('user_id', uid).eq('week_start', ws.isoformat()).limit(1).execute()
    if not have.data:   # runs before every card; only the first of the week needs the work
        _ensure_rows(squad['id'], [uid], _profiles([uid]), ws)


def _receipt_posts(receipt):
    posts = []
    if receipt.get('birthday'):
        posts.append(('birthday', '🎂', f"turned {receipt['birthday']}"))
    month = receipt.get('month_summary')
    if month:
        net = float(month.get('net') or 0)
        posts.append(('payday', '💸' if net >= 0 else '😬', f'closed the month at {_money(net)}'))
    cards = [c for c in receipt.get('cards') or [] if abs(float(c.get('cash') or 0)) >= BIG_SWING]
    if cards:
        c = max(cards, key=lambda c: abs(float(c.get('cash') or 0)))
        what = f"{c.get('title')}: {c.get('choice')}" if c.get('choice') else c.get('title')
        posts.append(('swing', c.get('icon') or '🎰', f"{what} ({_money(c.get('cash'))})"))
    return posts[:POSTS_PER_WEEK]


def record_week(uid, receipt):
    """A member finished a game week: count it for the squad goal and post the highlights."""
    uid = str(uid)
    m = membership(uid)
    if not m:
        return None
    squad = _squad(m['squad_id'])
    if not squad:
        return None
    squad = _settle(squad)
    sid, ws = squad['id'], week_start()
    prev = ws - timedelta(days=7)

    members = _members(sid)
    member_ids = [str(x['user_id']) for x in members]
    profiles = _profiles(member_ids)
    rows = _ensure_rows(sid, member_ids, profiles, ws)
    mine = rows[uid]
    # weeks_played counts this week; end_net_worth is where they stand now, so the
    # MVP is decided on the week's own growth (see _settle).
    supabase.table('squad_member_weeks').update({
        'weeks_played': int(mine.get('weeks_played') or 0) + 1, 'end_net_worth': _nw(profiles.get(uid)),
    }).eq('squad_id', sid).eq('user_id', uid).eq('week_start', ws.isoformat()).execute()
    # Re-read AFTER our own write: two members finishing their last week at the same
    # moment each used to add their own week to a stale copy of the other's, and
    # neither saw the goal reached. After this read, whoever wrote last sees both.
    rows = _week_rows(sid, ws)

    for kind, emoji, body in _receipt_posts(receipt):
        _post(sid, uid, kind, emoji, body)

    played, idle = _played(rows, member_ids)
    target = GOAL_PER_MEMBER * len(member_ids)
    already = str(squad.get('goal_hit_week')) == ws.isoformat()
    just_hit = False
    streak = _effective_streak(squad, ws)
    if not already and played >= target and not idle:
        streak = (int(squad.get('streak') or 0) if str(squad.get('goal_hit_week')) == prev.isoformat() else 0) + 1
        claimed = supabase.table('squads').update({'goal_hit_week': ws.isoformat(), 'streak': streak}) \
            .eq('id', sid).eq('goal_hit_week', squad['goal_hit_week']).execute()
        if claimed.data:
            just_hit = True
            _reward(sid, member_ids, ws)
            fire = f' · 🔥 {streak}-week streak' if streak > 1 else ''
            _post(sid, None, 'goal', '🎯', f'Squad goal hit! Everyone gets +{GOAL_SANITY} sanity{fire}')
            _push([i for i in member_ids if i != uid], f"🎯 {squad['emoji']} {squad['name']} hit the squad goal",
                  f'+{GOAL_SANITY} sanity for everyone.{fire}')
        else:
            streak = _effective_streak(_squad(sid) or squad, ws)

    return {
        'name': squad['name'], 'emoji': squad['emoji'],
        'played': played, 'target': target,
        'waiting_on': [] if already or just_hit else [profiles.get(i, {}).get('username', 'Someone') for i in idle],
        'goal_hit': already or just_hit, 'just_hit': just_hit,
        'reward_sanity': GOAL_SANITY, 'streak': streak,
    }


def _reward(sid, member_ids, ws):
    """
    +GOAL_SANITY to each member, at most once per player per calendar week, whatever
    squad. Tracked in squad_rewards (primary key user + week), which outlives the
    squad: the flag used to live on squad_member_weeks, which Postgres deletes with
    an emptied squad, so leaving, re-creating and replaying paid out again.
    """
    for uid in member_ids:
        got = supabase.table('squad_rewards').select('user_id').eq('user_id', uid) \
            .eq('week_start', ws.isoformat()).limit(1).execute()
        if got.data:
            continue
        try:
            supabase.table('squad_rewards').insert({'user_id': uid, 'week_start': ws.isoformat(), 'squad_id': sid}).execute()
        except Exception as e:
            if not _is_duplicate(e):   # the primary key makes the claim atomic
                logger.warning(f'Squad reward claim for {uid} failed: {e}')
            continue
        try:
            supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': GOAL_SANITY}).execute()
        except Exception as e:
            logger.warning(f'Squad goal sanity for {uid} failed: {e}')


def on_life_ended(uid, summary):
    m = membership(uid)
    if not m:
        return
    ending = summary.get('ending') or {}
    _post(m['squad_id'], uid, 'ending', ending.get('emoji') or '🏁',
          f"finished life #{summary.get('life_number')} at {summary.get('end_age')}: {ending.get('title', 'The end')}")


def on_life_started(uid, life_number, background_name, background_emoji, reset):
    """A new life: post it, and (if the run was reset) restart this week's growth from here."""
    uid = str(uid)
    m = membership(uid)
    if not m:
        return
    if reset:
        nw = _nw(_profiles([uid]).get(uid))
        supabase.table('squad_member_weeks').update({'start_net_worth': nw}) \
            .eq('squad_id', m['squad_id']).eq('user_id', uid).eq('week_start', week_start().isoformat()).execute()
    _post(m['squad_id'], uid, 'new_life', background_emoji or '🐣', f'started life #{life_number} as {background_name}')


# --- the squad screen -----------------------------------------------------------------

def _empty():
    return {'squad': None, 'max_members': MAX_MEMBERS, 'emojis': EMOJIS, 'reactions': REACTIONS}


def _reaction_summary(feed_ids, uid):
    if not feed_ids:
        return {}
    rows = supabase.table('squad_reactions').select('feed_id, user_id, emoji').in_('feed_id', feed_ids).execute().data or []
    out = {}
    for r in rows:
        f = out.setdefault(str(r['feed_id']), {'counts': {}, 'mine': None})
        f['counts'][r['emoji']] = f['counts'].get(r['emoji'], 0) + 1
        if str(r['user_id']) == uid:
            f['mine'] = r['emoji']
    return out


def state(uid):
    from app.game.life import avatars_for
    uid = str(uid)
    m = membership(uid)
    if not m:
        return _empty()
    squad = _squad(m['squad_id'])
    if not squad:
        return _empty()
    squad = _settle(squad)
    sid, ws = squad['id'], week_start()

    members = _members(sid)
    member_ids = [str(x['user_id']) for x in members]
    profiles = _profiles(member_ids)
    rows = _ensure_rows(sid, member_ids, profiles, ws)
    looks = avatars_for(member_ids)
    last_mvp = squad.get('last_mvp')
    if not last_mvp or last_mvp.get('week_start') != (ws - timedelta(days=7)).isoformat():
        last_mvp = None

    people = []
    for x in members:
        pid = str(x['user_id'])
        p = profiles.get(pid, {})
        r = rows.get(pid, {})
        look = looks.get(pid) or {}
        people.append({
            'user_id': pid, 'username': p.get('username', 'Someone'), 'profile_picture_url': p.get('profile_picture_url'),
            'avatar': look.get('avatar'), 'age': look.get('age'), 'sanity': p.get('sanity'),
            'net_worth': _nw(p), 'growth': round(_nw(p) - float(r.get('start_net_worth') or 0), 2),
            'weeks_played': int(r.get('weeks_played') or 0), 'role': x.get('role', 'member'),
            'is_me': pid == uid, 'is_mvp': bool(last_mvp and last_mvp.get('user_id') == pid),
        })
    people.sort(key=lambda p: (-p['growth'], -p['net_worth']))

    feed_rows = supabase.table('squad_feed').select('*').eq('squad_id', sid) \
        .order('created_at', desc=True).limit(FEED_LIMIT).execute().data or []
    missing = {str(f['user_id']) for f in feed_rows if f.get('user_id')} - set(profiles)
    names = {**profiles, **_profiles(missing)}
    reacts = _reaction_summary([str(f['id']) for f in feed_rows], uid)
    feed = [{
        'id': str(f['id']), 'user_id': str(f['user_id']) if f.get('user_id') else None,
        'username': names.get(str(f.get('user_id')), {}).get('username') if f.get('user_id') else None,
        'kind': f['kind'], 'emoji': f['emoji'], 'body': f['body'], 'created_at': f.get('created_at'),
        'reactions': reacts.get(str(f['id']), {}).get('counts', {}),
        'my_reaction': reacts.get(str(f['id']), {}).get('mine'),
    } for f in feed_rows]

    played = sum(p['weeks_played'] for p in people)
    hit = str(squad.get('goal_hit_week')) == ws.isoformat()
    idle = [p['username'] for p in people if p['weeks_played'] < MIN_WEEKS_PER_MEMBER]
    return {
        **_empty(),
        'squad': {
            'id': sid, 'name': squad['name'], 'emoji': squad['emoji'], 'code': squad['code'],
            'is_owner': m.get('role') == 'owner',
            'streak': _effective_streak(squad, ws),
            'week_start': ws.isoformat(),
            'resets_at': f'{(ws + timedelta(days=7)).isoformat()}T00:00:00Z',
            'goal': {
                'played': played, 'target': GOAL_PER_MEMBER * len(people),
                'hit': hit, 'reward_sanity': GOAL_SANITY,
                # Who the squad is still waiting on (every member must play a week)
                'waiting_on': [] if hit else idle,
                'members_played': len(people) - len(idle), 'members_total': len(people),
            },
            'members': people,
            'last_mvp': last_mvp,
            'feed': feed,
        },
    }


# --- actions -------------------------------------------------------------------------

def _clean_name(name):
    name = re.sub(r'\s+', ' ', str(name or '')).strip()
    if not 2 <= len(name) <= 24:
        raise SquadError('INVALID_NAME', 'Squad names are 2 to 24 characters.', 400)
    return name


def _clean_emoji(emoji, strict=False):
    """
    A new squad with no (or an unknown) badge gets the default. On rename (strict) an unknown
    badge is an error: falling back to the default there silently reset the squad's existing
    badge to 🔥.
    """
    if emoji in EMOJIS:
        return emoji
    if strict:   # update() only calls this when a badge was actually sent
        raise SquadError('INVALID_EMOJI', 'Pick one of the squad badges.', 400)
    return EMOJIS[0]


def _new_code():
    for _ in range(8):
        code = ''.join(random.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
        if not supabase.table('squads').select('id').eq('code', code).limit(1).execute().data:
            return code
    raise SquadError('TRY_AGAIN', "Couldn't make a squad code. Try again.", 503)


def create(uid, name, emoji):
    uid = str(uid)
    if membership(uid):
        raise SquadError('ALREADY_IN_SQUAD', 'Leave your squad before starting a new one.', 409)
    squad = supabase.table('squads').insert({
        'name': _clean_name(name), 'emoji': _clean_emoji(emoji), 'code': _new_code(),
        'owner_id': uid, 'settled_week': week_start().isoformat(), 'goal_hit_week': '2000-01-03', 'streak': 0,
    }).execute().data[0]
    try:
        supabase.table('squad_members').insert({'user_id': uid, 'squad_id': squad['id'], 'role': 'owner', 'joined_at': _now()}).execute()
    except Exception as e:
        supabase.table('squads').delete().eq('id', squad['id']).execute()
        if _is_duplicate(e):
            raise SquadError('ALREADY_IN_SQUAD', 'Leave your squad before starting a new one.', 409)
        raise
    _post(squad['id'], uid, 'created', '🚩', 'started the squad')
    return state(uid)


def preview(code):
    code = str(code or '').strip().upper()
    res = supabase.table('squads').select('id, name, emoji').eq('code', code).limit(1).execute()
    if not res.data:
        raise SquadError('NOT_FOUND', 'No squad has that code.', 404)
    s = res.data[0]
    return {'name': s['name'], 'emoji': s['emoji'], 'members': len(_members(s['id'])), 'max_members': MAX_MEMBERS}


def join(uid, code):
    uid = str(uid)
    code = str(code or '').strip().upper()
    res = supabase.table('squads').select('*').eq('code', code).limit(1).execute()
    if not res.data:
        raise SquadError('NOT_FOUND', 'No squad has that code.', 404)
    squad = res.data[0]
    m = membership(uid)
    if m:
        if m['squad_id'] == squad['id']:
            raise SquadError('ALREADY_MEMBER', "You're already in this squad.", 409)
        raise SquadError('ALREADY_IN_SQUAD', 'Leave your squad before joining another.', 409)
    if len(_members(squad['id'])) >= MAX_MEMBERS:
        raise SquadError('SQUAD_FULL', f'That squad is full ({MAX_MEMBERS} max).', 409)
    try:
        supabase.table('squad_members').insert({'user_id': uid, 'squad_id': squad['id'], 'role': 'member', 'joined_at': _now()}).execute()
    except Exception as e:
        if 'SQUAD_FULL' in str(e):
            raise SquadError('SQUAD_FULL', f'That squad is full ({MAX_MEMBERS} max).', 409)
        if _is_duplicate(e):
            raise SquadError('ALREADY_IN_SQUAD', 'Leave your squad before joining another.', 409)
        raise
    _post(squad['id'], uid, 'joined', '👋', 'joined the squad')
    me = _profiles([uid]).get(uid, {}).get('username', 'Someone')
    _push([str(x['user_id']) for x in _members(squad['id']) if str(x['user_id']) != uid],
          f"👋 {me} joined {squad['emoji']} {squad['name']}", 'Your squad goal just got bigger. So did the competition.')
    return state(uid)


def _remove(sid, uid, was_owner):
    supabase.table('squad_members').delete().eq('user_id', uid).eq('squad_id', sid).execute()
    rest = _members(sid)
    if not rest:
        supabase.table('squads').delete().eq('id', sid).execute()
        return False
    if was_owner:
        heir = rest[0]
        supabase.table('squad_members').update({'role': 'owner'}).eq('user_id', heir['user_id']).execute()
        supabase.table('squads').update({'owner_id': heir['user_id']}).eq('id', sid).execute()
    return True


def leave(uid):
    uid = str(uid)
    m = membership(uid)
    if not m:
        raise SquadError('NOT_IN_SQUAD', "You're not in a squad.", 404)
    if _remove(m['squad_id'], uid, m.get('role') == 'owner'):
        _post(m['squad_id'], uid, 'left', '🚪', 'left the squad')
    return state(uid)


def remove_member(uid, target):
    uid = str(uid)
    target = _uuid(target, 404, 'NOT_FOUND', "They're not in your squad.")
    m = membership(uid)
    if not m or m.get('role') != 'owner':
        raise SquadError('NOT_OWNER', 'Only the squad owner can do that.', 403)
    if target == uid:
        raise SquadError('INVALID_TARGET', 'Use Leave to leave your own squad.', 400)
    t = membership(target)
    if not t or t['squad_id'] != m['squad_id']:
        raise SquadError('NOT_FOUND', "They're not in your squad.", 404)
    _remove(m['squad_id'], target, False)
    squad = _squad(m['squad_id']) or {}
    supabase.table('notifications').insert({
        'user_id': target, 'type': 'social', 'title': f"You left {squad.get('emoji', '')} {squad.get('name', 'a squad')}",
        'message': 'The squad owner removed you. You can start or join another squad any time.', 'read': False,
    }).execute()
    return state(uid)


def update(uid, name=None, emoji=None):
    uid = str(uid)
    m = membership(uid)
    if not m or m.get('role') != 'owner':
        raise SquadError('NOT_OWNER', 'Only the squad owner can do that.', 403)
    changes = {}
    if name is not None:
        changes['name'] = _clean_name(name)
    if emoji is not None:
        changes['emoji'] = _clean_emoji(emoji, strict=True)
    if changes:
        supabase.table('squads').update(changes).eq('id', m['squad_id']).execute()
    return state(uid)


def invite(uid, target):
    uid = str(uid)
    if not target:
        raise SquadError('INVALID_TARGET', 'Pick a friend to invite.', 400)
    target = _uuid(target, 400, 'INVALID_TARGET', 'Pick a friend to invite.')
    m = membership(uid)
    if not m:
        raise SquadError('NOT_IN_SQUAD', 'Start or join a squad first.', 404)
    if target == uid:
        raise SquadError('INVALID_TARGET', 'Pick a friend to invite.', 400)
    if target not in _profiles([target]):
        raise SquadError('NOT_FOUND', "That player doesn't exist.", 404)
    follows = supabase.table('user_follows').select('id').eq('follower_id', uid).eq('following_id', target).limit(1).execute()
    if not follows.data:
        raise SquadError('NOT_FOLLOWING', 'You can only invite people you follow.', 403)
    t = membership(target)
    if t and t['squad_id'] == m['squad_id']:
        raise SquadError('ALREADY_MEMBER', "They're already in your squad.", 409)
    squad = _squad(m['squad_id'])
    if len(_members(squad['id'])) >= MAX_MEMBERS:
        raise SquadError('SQUAD_FULL', f'Your squad is full ({MAX_MEMBERS} max).', 409)
    sent = supabase.table('notifications').select('id').eq('user_id', target).eq('type', 'social') \
        .ilike('message', f"%code {squad['code']}%").limit(1).execute()
    if sent.data:
        raise SquadError('ALREADY_INVITED', 'You already invited them.', 409)

    me = _profiles([uid]).get(uid, {}).get('username', 'A friend')
    title = f"{squad['emoji']} {me} invited you to {squad['name']}"
    message = f"Join their squad with code {squad['code']}."
    supabase.table('notifications').insert({'user_id': target, 'type': 'social', 'title': title, 'message': message, 'read': False}).execute()
    _push([target], title, message, {'screen': f"/(tabs)/squad?code={squad['code']}"})
    return {'invited': target}


def react(uid, feed_id, emoji):
    uid = str(uid)
    if emoji not in REACTIONS:
        raise SquadError('INVALID_REACTION', 'Pick one of the reactions.', 400)
    feed_id = _uuid(feed_id, 404, 'NOT_FOUND', 'That post is gone.')
    m = membership(uid)
    post = supabase.table('squad_feed').select('id, squad_id').eq('id', feed_id).limit(1).execute().data
    if not m or not post or str(post[0]['squad_id']) != str(m['squad_id']):
        raise SquadError('NOT_FOUND', 'That post is gone.', 404)
    existing = supabase.table('squad_reactions').select('emoji').eq('feed_id', feed_id).eq('user_id', uid).limit(1).execute().data
    supabase.table('squad_reactions').delete().eq('feed_id', feed_id).eq('user_id', uid).execute()
    if not existing or existing[0]['emoji'] != emoji:
        try:
            supabase.table('squad_reactions').insert({'feed_id': feed_id, 'user_id': uid, 'emoji': emoji, 'created_at': _now()}).execute()
        except Exception as e:
            if not _is_duplicate(e):   # a double tap: the other request already stored it
                raise
    summary = _reaction_summary([str(feed_id)], uid).get(str(feed_id), {})
    return {'id': str(feed_id), 'reactions': summary.get('counts', {}), 'my_reaction': summary.get('mine')}
