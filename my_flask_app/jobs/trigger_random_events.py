"""
Random Event Trigger Job
Analyzes active players and triggers random life events every 4 days.
Run this job DAILY via cron/scheduler.

Uses Supabase client directly (not SQLAlchemy ORM) for reliable production execution.
"""

from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta
import logging
import random
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

    now = datetime.utcnow()
    four_days_ago = (now - timedelta(days=4)).isoformat()
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
        return {'error': str(e), 'events_triggered': 0, 'skipped': 0, 'errors': 0}

    # 2. Get all active life events (fetch once, reuse for all users)
    try:
        events_res = supabase.table('life_events').select('id, title, description') \
            .eq('is_active', True) \
            .execute()
        available_events = events_res.data or []
        logger.info(f"Found {len(available_events)} active life events")
        if not available_events:
            logger.warning("No active life events found in database.")
            return {'events_triggered': 0, 'skipped': len(active_profiles), 'errors': 0, 'messages_sent': 0}
    except Exception as e:
        logger.error(f"Error fetching life events: {e}")
        return {'error': str(e), 'events_triggered': 0, 'skipped': 0, 'errors': 0}

    events_triggered = 0
    errors = 0
    skipped = 0
    notifications_to_send = []

    for profile in active_profiles:
        user_id = profile['user_id']
        username = profile.get('username', 'Unknown')

        try:
            # 3. Check 4-day cooldown — get most recent event for this user
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
                if last_created > four_days_ago:
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
                'was_auto_selected': False
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
        'messages_sent': len(notifications_to_send)
    }

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        trigger_random_events()
