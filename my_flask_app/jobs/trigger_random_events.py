"""
Random Event Trigger Job (daily, /api/cron/random-events/)

1. Auto-resolve: a life event left unanswered past its time limit
   (life_events.time_limit_seconds, 7 days by default) is answered for the
   player with the "do nothing" choice (see life_events.default_choice), marked
   was_auto_selected, and the player is told what ignoring it cost them.
2. Assign: calendar-time players without a pending event get a new one every
   4 days (players on game time get events in their weekly deck instead).

Uses Supabase client directly (not SQLAlchemy ORM) for reliable production execution.
"""

from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta, timezone
import logging
import random

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


def trigger_random_events():
    """
    Check all active users and trigger a life event if they haven't had one in 4 days.
    Uses Supabase client for all database operations.
    """
    logger.info("Starting random event trigger job...")

    # Get Supabase client from Flask app context
    from app import supabase
    if not supabase:
        logger.error("Supabase client not initialized")
        return {'error': 'Supabase client not initialized', 'events_triggered': 0, 'skipped': 0, 'errors': 0}

    now = datetime.now(timezone.utc)

    # 0. Expired events first, so a player unblocked here can get a new one below.
    try:
        auto = auto_resolve_expired_events(supabase, now)
    except Exception as e:
        logger.error(f"Auto-resolve step failed: {e}", exc_info=True)
        auto = {'auto_resolved': 0, 'auto_resolve_errors': 1}

    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # 1. Get active profiles (active in last 30 days)
    try:
        profiles_res = supabase.table('profiles').select('user_id, username, last_active_at') \
            .gte('last_active_at', thirty_days_ago) \
            .limit(500) \
            .execute()
        active_profiles = profiles_res.data or []
        logger.info(f"Found {len(active_profiles)} active profiles")
    except Exception as e:
        logger.error(f"Error fetching active profiles: {e}")
        return {'error': str(e), 'events_triggered': 0, 'skipped': 0, 'errors': 0, **auto}

    # 2. Get all active life events (fetch once, reuse for all users)
    try:
        events_res = supabase.table('life_events').select('id, title, description, released_at, season_start, season_end') \
            .eq('is_active', True) \
            .execute()
        # Same rules as the weekly deck: released already, and in season if it has one.
        from datetime import datetime as _dt, timezone as _tz
        from app.game.week_service import in_season, released
        _now = _dt.now(_tz.utc)
        available_events = [e for e in (events_res.data or []) if released(e, _now) and in_season(e, _now.date())]
        logger.info(f"Found {len(available_events)} active life events")
        if not available_events:
            logger.warning("No active life events found in database.")
            return {'events_triggered': 0, 'skipped': len(active_profiles), 'errors': 0, 'messages_sent': 0, **auto}
    except Exception as e:
        logger.error(f"Error fetching life events: {e}")
        return {'error': str(e), 'events_triggered': 0, 'skipped': 0, 'errors': 0, **auto}

    # Players on game time get life events in their weekly deck instead.
    try:
        clocked = {str(r['user_id']) for r in (supabase.table('player_game_clock').select('user_id').execute().data or [])}
    except Exception as e:
        logger.warning(f"Could not read player_game_clock ({e}); assuming no players on game time")
        clocked = set()
    active_profiles = [p for p in active_profiles if str(p['user_id']) not in clocked]

    events_triggered = 0
    errors = 0
    skipped = len(clocked)
    notifications_to_send = []

    for profile in active_profiles:
        user_id = profile['user_id']
        username = profile.get('username', 'Unknown')

        try:
            # 3a. Don't stack events: wait until the last one is answered.
            #     (A new event + push every 4 days piled up unanswered events.)
            still_pending = supabase.table('user_life_events').select('id') \
                .eq('user_id', user_id).is_('choice_id', 'null').limit(1).execute()
            if still_pending.data:
                skipped += 1
                continue

            # 3b. Check 4-day cooldown — get most recent event for this user
            last_event_res = supabase.table('user_life_events').select('life_event_id, created_at') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()

            last_event_id = None
            if last_event_res.data and len(last_event_res.data) > 0:
                last_event = last_event_res.data[0]
                last_created = last_event['created_at']

                # Compare timestamps (Supabase returns ISO format with timezone)
                if datetime.fromisoformat(last_created.replace('Z', '+00:00')) > now - timedelta(days=4):
                    skipped += 1
                    continue

                last_event_id = last_event['life_event_id']

            # 4. Select a random event, excluding the last one to avoid repeats
            candidates = [e for e in available_events if e['id'] != last_event_id] if last_event_id else available_events
            if not candidates:
                candidates = available_events  # Fallback if only 1 event exists

            selected_event = random.choice(candidates)

            # 5. Create UserLifeEvent record (pending — no choice made yet)
            import uuid
            new_event_id = str(uuid.uuid4())
            supabase.table('user_life_events').insert({
                'id': new_event_id,
                'user_id': user_id,
                'life_event_id': selected_event['id'],
                'choice_id': None,
            }).execute()

            events_triggered += 1
            logger.info(f"Triggered event '{selected_event['title']}' for user {username}")

            # 6. Queue push notification
            message_body = (
                selected_event['description'][:100] + "..."
                if len(selected_event['description']) > 100
                else selected_event['description']
            )
            notifications_to_send.append({
                'user_id': str(user_id),
                'title': f"⚡ Life Update: {selected_event['title']}",
                'body': message_body,
                'data': {
                    'screen': f"/life-events/{selected_event['id']}",
                    'eventId': str(selected_event['id']),
                    'userEventId': new_event_id
                }
            })

        except Exception as e:
            errors += 1
            logger.error(f"Error processing profile {username}: {str(e)}")
            continue

    # 7. Batch-send all push notifications
    if notifications_to_send:
        results = ExpoPushService.send_notifications_to_users(
            supabase_client=supabase,
            user_notifications=notifications_to_send,
            notification_type='life_event'
        )
        logger.info(
            f"Push results — Sent: {results['success']}, "
            f"Failed: {results['failed']}, Skipped: {results['skipped']}"
        )

    logger.info(
        f"Job Complete. Triggered: {events_triggered}, Skipped (Cooldown): {skipped}, Errors: {errors}"
    )

    return {
        'events_triggered': events_triggered,
        'skipped': skipped,
        'errors': errors,
        'messages_sent': len(notifications_to_send),
        **auto,
    }

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        trigger_random_events()
