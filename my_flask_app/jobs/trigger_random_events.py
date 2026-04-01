"""
Random Event Trigger Job
Analyzes active players and triggers random life events every 4 days.
Run this job DAILY (or hourly) via cron/scheduler.
"""

from app import db
from app.models.user import User
from app.models.life_event import LifeEvent
from app.models.user_life_event import UserLifeEvent
from app.models.profile import Profile
from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta
from sqlalchemy import func
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
    """
    logger.info("Starting random event trigger job...")

    now = datetime.utcnow()
    four_days_ago = now - timedelta(days=4)

    active_profiles = Profile.query.all()
    logger.info(f"Found {len(active_profiles)} active profiles")

    events_triggered = 0
    errors = 0
    skipped = 0

    # --- Collect notifications to batch-send after DB work is done ---
    notifications_to_send = []

    for profile in active_profiles:
        try:
            user_id = profile.user_id

            # Check 4-day cooldown
            last_event = UserLifeEvent.query.filter_by(user_id=user_id)\
                .order_by(UserLifeEvent.created_at.desc())\
                .first()

            if last_event and last_event.created_at > four_days_ago:
                skipped += 1
                continue

            # Select a random event, excluding the last one
            query = LifeEvent.query.filter_by(is_active=True)
            if last_event:
                query = query.filter(LifeEvent.id != last_event.life_event_id)

            available_events = query.all()
            if not available_events:
                logger.warning("No active life events found in database.")
                break

            selected_event = random.choice(available_events)

            # Create UserLifeEvent record (Pending)
            new_user_event = UserLifeEvent(
                user_id=user_id,
                life_event_id=selected_event.id,
                choice_id=None,
                was_auto_selected=False
            )
            db.session.add(new_user_event)
            db.session.commit()

            events_triggered += 1
            logger.info(f"Triggered event '{selected_event.title}' for user {profile.username}")

            message_body = (
                selected_event.description[:100] + "..."
                if len(selected_event.description) > 100
                else selected_event.description
            )
            notifications_to_send.append({
                'user_id': str(user_id),
                'title': f"Life Update: {selected_event.title}",
                'body': message_body,
                'data': {
                    'screen': f"/life-events/{selected_event.id}",
                    'eventId': str(selected_event.id),
                    'userEventId': str(new_user_event.id)
                }
            })

        except Exception as e:
            db.session.rollback()
            errors += 1
            logger.error(f"Error processing profile {profile.username}: {str(e)}")
            continue

    # --- Batch-send all notifications in one round-trip ---
    if notifications_to_send:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if supabase_url and supabase_key:
            from supabase import create_client
            sb = create_client(supabase_url, supabase_key)
            results = ExpoPushService.send_notifications_to_users(
                supabase_client=sb,
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

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        trigger_random_events()
