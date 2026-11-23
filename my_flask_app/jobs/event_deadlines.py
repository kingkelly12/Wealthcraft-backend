"""
Life event deadlines (daily, /api/cron/event-deadlines/)

A life event left unanswered past its time limit (life_events.time_limit_seconds,
7 days by default) is answered for the player with the "do nothing" choice (see
life_events.default_choice), marked was_auto_selected, and the player is told what
ignoring it cost them.

New events are not assigned here: every player is on game time and gets them as
cards in their weekly deck (app/game/week_service.py).
"""

from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta, timezone
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def auto_resolve_expired_events(supabase, now=None) -> dict:
    """Answer life events left pending past their time limit. Returns counts."""
    from app.game.life_events import (DEFAULT_TIME_LIMIT_SECONDS, AlreadyResolved,
                                      default_choice, resolve)

    now = now or datetime.now(timezone.utc)
    # Nothing can expire sooner than the shortest limit; 1 hour is a safe floor
    # for the query, and each row is then checked against its own event's limit.
    pending = supabase.table('user_life_events').select('id, user_id, life_event_id, created_at') \
        .is_('choice_id', 'null').lt('created_at', (now - timedelta(hours=1)).isoformat()) \
        .order('created_at').limit(2000).execute().data or []
    if not pending:
        return {'auto_resolved': 0, 'auto_resolve_errors': 0}

    event_ids = list({r['life_event_id'] for r in pending})
    events = {e['id']: e for e in (supabase.table('life_events').select('*')
                                   .in_('id', event_ids).execute().data or [])}
    choices = {}
    for c in supabase.table('life_event_choices').select('*').in_('life_event_id', event_ids).execute().data or []:
        choices.setdefault(c['life_event_id'], []).append(c)

    resolved = errors = 0
    notifications = []
    for row in pending:
        event = events.get(row['life_event_id'])
        options = choices.get(row['life_event_id']) or []
        if not event or not options:
            continue
        limit = int(event.get('time_limit_seconds') or DEFAULT_TIME_LIMIT_SECONDS)
        created = datetime.fromisoformat(str(row['created_at']).replace('Z', '+00:00'))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if now - created < timedelta(seconds=limit):
            continue

        choice = default_choice(options)
        try:
            fx = resolve(supabase, str(row['user_id']), row['id'], event, choice, options, auto=True)
        except AlreadyResolved:
            continue  # answered in the meantime
        except Exception as e:
            errors += 1
            logger.error(f"Auto-resolve failed for {row['id']}: {e}")
            continue
        resolved += 1

        parts = []
        if fx['cash']:
            parts.append(f"{'+' if fx['cash'] > 0 else '-'}${abs(fx['cash']):,.0f}")
        sanity_change = fx['new_sanity'] - fx['sanity_before']
        if sanity_change:
            parts.append(f"{'+' if sanity_change > 0 else ''}{sanity_change} sanity")
        if fx['income']:
            parts.append(f"{'+' if fx['income'] > 0 else '-'}${abs(fx['income']):,.0f}/mo")
        outcome = choice.get('outcome_description') or 'Life went on without you.'
        body = outcome + (f" ({', '.join(parts)})" if parts else '')
        title = f"⌛ You ignored {event['title']}"

        try:
            supabase.table('notifications').insert({
                'user_id': row['user_id'], 'type': 'life_event', 'title': title,
                'message': body, 'read': False,
            }).execute()
        except Exception as e:
            logger.warning(f"Could not record auto-resolve notification: {e}")
        notifications.append({
            'user_id': str(row['user_id']), 'title': title, 'body': body[:180],
            'data': {'screen': f"/life-events/{event['id']}", 'eventId': str(event['id']), 'auto_resolved': True},
        })

    if notifications:
        ExpoPushService.send_notifications_to_users(
            supabase_client=supabase, user_notifications=notifications, notification_type='life_event')
    logger.info(f"Auto-resolved {resolved} expired life events ({errors} errors)")
    return {'auto_resolved': resolved, 'auto_resolve_errors': errors}


def run_event_deadlines():
    """Daily job: auto-resolve every expired life event."""
    logger.info("Starting life event deadlines job...")
    from app import supabase
    if not supabase:
        logger.error("Supabase client not initialized")
        return {'error': 'Supabase client not initialized', 'auto_resolved': 0, 'auto_resolve_errors': 0}
    try:
        return auto_resolve_expired_events(supabase, datetime.now(timezone.utc))
    except Exception as e:
        logger.error(f"Auto-resolve step failed: {e}", exc_info=True)
        return {'auto_resolved': 0, 'auto_resolve_errors': 1}


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        run_event_deadlines()
