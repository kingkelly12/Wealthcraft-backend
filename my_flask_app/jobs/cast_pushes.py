"""
Cast texts as pushes, an hour later, to bring players back.

A text written when a week ends gets `push_due_at` (cast.PUSH_DELAY from then). This job, every
15 minutes, pushes the ones that are due:

* already read in the app: no push (it did its job);
* the player was in the app in the last ACTIVE_WINDOW: wait for the next run;
* more than STALE_AFTER overdue: drop it, old news;
* at most MAX_PER_PLAYER pushes a run, the newest from each person.

Every text handled is stamped `pushed_at`, claimed first so two runs can't send it twice.
"""
import logging
from datetime import datetime, timedelta, timezone

from app import supabase
from app.game.cast import CAST
from app.services.push_notification_service import ExpoPushService

logger = logging.getLogger(__name__)

ACTIVE_WINDOW = timedelta(minutes=30)
STALE_AFTER = timedelta(hours=24)
MAX_PER_PLAYER = 2


def _time(value):
    if not value:
        return None
    t = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _claim(ids, now):
    """Stamp these texts as handled; returns the ids this run actually got."""
    if not ids:
        return set()
    rows = supabase.table('cast_messages').update({'pushed_at': now.isoformat()}) \
        .in_('id', ids).is_('pushed_at', 'null').execute().data or []
    return {r['id'] for r in rows}


def run_cast_pushes(now=None):
    now = now or datetime.now(timezone.utc)
    due = supabase.table('cast_messages').select('id, user_id, character, body, created_at, read_at, push_due_at') \
        .is_('pushed_at', 'null').lte('push_due_at', now.isoformat()).order('created_at', desc=True).limit(500).execute().data or []
    if not due:
        return {'due': 0, 'queued': 0, 'waiting': 0}

    users = list({str(m['user_id']) for m in due})
    profiles = supabase.table('profiles').select('user_id, last_active_at').in_('user_id', users).execute().data or []
    active = {str(p['user_id']) for p in profiles
              if _time(p.get('last_active_at')) and now - _time(p['last_active_at']) < ACTIVE_WINDOW}

    skip, send, waiting = [], {}, 0
    for m in due:                       # newest first
        uid = str(m['user_id'])
        if m.get('read_at') or now - _time(m['push_due_at']) > STALE_AFTER or m['character'] not in CAST:
            skip.append(m['id'])
        elif uid in active:
            waiting += 1
        else:
            mine = send.setdefault(uid, [])
            if len(mine) < MAX_PER_PLAYER and m['character'] not in {x['character'] for x in mine}:
                mine.append(m)
            else:
                skip.append(m['id'])    # covered by the newer one(s)

    _claim(skip, now)
    claimed = _claim([m['id'] for mine in send.values() for m in mine], now)
    batch = [{
        'user_id': uid, 'title': f"{CAST[m['character']]['emoji']} {CAST[m['character']]['name']}", 'body': m['body'][:180],
        'data': {'type': 'cast', 'character': m['character'], 'screen': f"/texts/{m['character']}"},
    } for uid, mine in send.items() for m in mine if m['id'] in claimed]
    if batch:
        ExpoPushService.send_notifications_to_users(supabase_client=supabase, user_notifications=batch, notification_type='cast')
    logger.info(f'Cast pushes: {len(due)} due, {len(batch)} queued, {waiting} waiting for the player to leave')
    return {'due': len(due), 'queued': len(batch), 'waiting': waiting}
