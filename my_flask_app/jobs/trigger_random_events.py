"""
Random Event Trigger Job
Analyzes active players and triggers random life events every 4 days.
Run this job DAILY (or hourly) via cron/scheduler.
"""

from app import create_app, db
from app.models.user import User
from app.models.life_event import LifeEvent
from app.models.user_life_event import UserLifeEvent
from app.models.profile import Profile
from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta
from sqlalchemy import func
import logging
import random

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
    app = create_app()
    
    with app.app_context():
        logger.info("Starting random event trigger job...")
        
        # 1. Define time windows
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        four_days_ago = now - timedelta(days=4)
        
        # 2. Get all profiles (Source of Truth for UUID user_ids)
        active_profiles = Profile.query.all()
        
        logger.info(f"Found {len(active_profiles)} active profiles")
        
        events_triggered = 0
        errors = 0
        skipped = 0
        
        # 3. Process each profile
        for profile in active_profiles:
            try:
                user_id = profile.user_id # This is the UUID
                
                # Check 4-day cooldown
                last_event = UserLifeEvent.query.filter_by(user_id=user_id)\
                    .order_by(UserLifeEvent.created_at.desc())\
                    .first()
                
                if last_event and last_event.created_at > four_days_ago:
                    skipped += 1
                    continue
                
                # Check for push token (redundant check but safe)
                if not profile.push_token:
                    # We can still trigger the event for in-app logic, but log it
                    pass

                # 4. Select a random event
                # Filter out the SPECIFIC event they just had
                query = LifeEvent.query.filter_by(is_active=True)
                if last_event:
                    query = query.filter(LifeEvent.id != last_event.life_event_id)
                
                available_events = query.all()
                
                if not available_events:
                    logger.warning("No active life events found in database.")
                    break
                
                selected_event = random.choice(available_events)
                
                # 5. Create UserLifeEvent record (Pending)
                new_user_event = UserLifeEvent(
                    user_id=user_id,
                    life_event_id=selected_event.id,
                    choice_id=None, # Pending choice
                    was_auto_selected=False
                )
                
                db.session.add(new_user_event)
                db.session.commit()
                
                # 6. Send Push Notification
                message_body = selected_event.description[:100] + "..." if len(selected_event.description) > 100 else selected_event.description
                
                if profile.push_token:
                    # Using local Supabase client to trigger push
                    from supabase import create_client
                    import os
                    supabase_url = os.getenv('SUPABASE_URL')
                    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    
                    if supabase_url and supabase_key:
                        sb = create_client(supabase_url, supabase_key)
                        ExpoPushService.send_notification_to_user(
                            supabase_client=sb,
                            user_id=str(user_id),
                            title=f"Life Update: {selected_event.title}",
                            body=message_body,
                            notification_type="life_event",
                            data={
                                "type": "life_event",
                                "eventId": str(selected_event.id),
                                "userEventId": str(new_user_event.id)
                            }
                        )

                events_triggered += 1
                logger.info(f"Triggered event '{selected_event.title}' for user {profile.username}")
                
            except Exception as e:
                db.session.rollback()
                errors += 1
                logger.error(f"Error processing profile {profile.username}: {str(e)}")
                continue
        
        logger.info(
            f"Job Complete. Triggered: {events_triggered}, Skipped (Cooldown): {skipped}, Errors: {errors}"
        )

if __name__ == '__main__':
    trigger_random_events()
