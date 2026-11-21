"""
"Your week is ready" nudge, sent by a cast member. Run DAILY (pg_cron).

Rules (the game's no-dark-patterns promise):
  * at most one push per player per day (player_game_clock.last_nudged_on);
  * only when a week is actually waiting to be played;
  * never between lives or after a life is over;
  * the message is about something real: the week's teaser or payday.
"""
import logging
import random
from datetime import date, datetime, timezone

from app import supabase
from app.game.cast import CAST, relationships
from app.game.week_service import MAX_BANKED
from app.services.push_notification_service import ExpoPushService

logger = logging.getLogger(__name__)


def _available_weeks(clock, today):
    last = date.fromisoformat(str(clock['bank_updated_on'])[:10])
    return min(MAX_BANKED, int(clock['banked_weeks']) + max(0, (today - last).days))


def _teaser(uid, week):
    res = supabase.table('player_weeks').select('cards').eq('user_id', uid).eq('week', week).limit(1).execute().data
    cards = (res[0].get('cards') if res else None) or []
    return next((c.get('teaser') for c in cards if not c.get('chosen')), None)


def _message(uid, week, teaser, rng):
    payday = week % 4 == 0
    rel = relationships(uid)
    if payday:
        who = 'mom'
        body = f"it's payday week, sweetie 💸 week {week} is ready. pay rent FIRST ok?"
    else:
        who = 'bestie' if rel['bestie'] >= rel['mom'] or rng.random() < 0.5 else 'mom'
        hook = f" {teaser}" if teaser else ''
        body = (f"week {week} just dropped.{hook}" if who == 'bestie'
                else f"your week {week} is ready honey.{hook} call me after ❤️")
    c = CAST[who]
    return f"{c['emoji']} {c['name']}", body


def run_week_ready_nudge():
    from jobs.run_guard import claim_daily_run
    period = claim_daily_run('week_ready_nudge')
    if not period:
        return {'skipped': True}

    today = datetime.now(timezone.utc).date()
    clocks = supabase.table('player_game_clock').select('*').execute().data or []
    ids = [str(c['user_id']) for c in clocks]
    if not ids:
        return {'sent': 0, 'eligible': 0}
    tokens = {str(p['user_id']) for p in (supabase.table('profiles').select('user_id, expo_push_token')
                                           .in_('user_id', ids).execute().data or []) if p.get('expo_push_token')}
    current_lives = {str(l['user_id']): l for l in (supabase.table('player_lives').select('user_id, start_age')
                                                     .in_('user_id', ids).eq('is_current', True).execute().data or [])}
    ever_lived = {str(l['user_id']) for l in (supabase.table('player_lives').select('user_id')
                                              .in_('user_id', ids).execute().data or [])}

    from app.game.life import MAX_AGE, age_at
    sent = eligible = 0
    batch = []
    for clock in clocks:
        uid = str(clock['user_id'])
        if uid not in tokens or str(clock.get('last_nudged_on') or '')[:10] == today.isoformat():
            continue
        if _available_weeks(clock, today) < 1:
            continue
        week = int(clock['week'])
        life = current_lives.get(uid)
        if uid in ever_lived and not life:
            continue  # between lives
        if life and age_at(week, life['start_age'])['years'] >= MAX_AGE:
            continue  # life over: nothing to play
        eligible += 1

        claimed = supabase.table('player_game_clock').update({'last_nudged_on': today.isoformat()}) \
            .eq('user_id', uid).execute()
        if not claimed.data:
            continue
        title, body = _message(uid, week, _teaser(uid, week), random.Random(f'{uid}:{today}'))
        batch.append({'user_id': uid, 'title': title, 'body': body, 'data': {'screen': '/week'}})

    for i in range(0, len(batch), 50):
        result = ExpoPushService.send_notifications_to_users(
            supabase_client=supabase, user_notifications=batch[i:i + 50], notification_type='week_ready')
        sent += (result or {}).get('success', 0)
    logger.info(f'Week-ready nudge: {eligible} eligible, {len(batch)} queued, {sent} sent')
    return {'eligible': eligible, 'queued': len(batch), 'sent': sent}
