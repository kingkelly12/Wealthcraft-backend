"""
Inactive Users Monitor Job
Identifies users inactive for 7 days and sends targeted Native Notify push notifications.
Run this daily via cron or task scheduler.
"""

from app import db, supabase
from app.models.profile import Profile
from app.models.user import User
from app.services.push_notification_service import ExpoPushService
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_inactive_users_monitor():
    """Run daily check for users who haven't opened the app in 7 days"""
    logger.info("Starting inactive users monitor...")

    # Calculate 7 days ago
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # We query profiles where:
    # 1. last_active_at < 7 days ago
    # 2. They haven't been pinged OR the last ping was BEFORE their last activity
    # This ensures they only get 1 ping per 7-day inactivity cycle.
    inactive_profiles = Profile.query.filter(
        Profile.last_active_at <= seven_days_ago,
        db.or_(
            Profile.last_inactivity_ping_sent_at == None,
            Profile.last_inactivity_ping_sent_at < Profile.last_active_at
        )
    ).all()

    logger.info(f"Found {len(inactive_profiles)} inactive users needing a win-back ping.")

    messages_sent = 0
    errors = 0
    now = datetime.utcnow()

    for profile in inactive_profiles:
        try:
            # Determine dynamic notification variant
            
            # Variant B: The Financial Reality (If they have assets/net worth > 0)
            if profile.net_worth > 0 or profile.monthly_income > 0:
                title = "📈 The markets didn't sleep..."
                body = "A week went by. Your net worth has been doing something interesting while you were away."
                data = {"type": "market", "screen": "/profile"}
                
            # Variant A: The Mentor's Whisper (If beginner or no assets but they started)
            elif profile.has_completed_onboarding:
                title = "📝 Note on your desk..."
                body = "Your mentor dropped by and left a sticky note on your desk. Might want to see what they found."
                data = {"type": "mentor", "screen": "/mentors"}
                
            # Variant C: The Void (Fallback)
            else:
                title = "👀 Meanwhile, in the Void..."
                body = "People have been making moves. Time to check the temperature and see where you stand."
                data = {"type": "social", "screen": "/(tabs)/void"}
                
            # Send Notification via Native Notify Indie Push
            # Note: We must use str(profile.user_id) because Indie ID expects strings.
            success = ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=str(profile.user_id),
                title=title,
                body=body,
                notification_type=data["type"],
                data=data
            )
            
            if success:
                # Update ping tracker so they don't get spammed tomorrow
                profile.last_inactivity_ping_sent_at = now
                messages_sent += 1
            else:
                errors += 1
                
        except Exception as e:
            errors += 1
            logger.error(f"Error processing inactive user {profile.user_id}: {str(e)}")
            continue
            
    # Commit all the ping tracker timestamp updates
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to commit db session for ping trackers: {str(e)}")
        db.session.rollback()

    logger.info(
        f"Inactive users monitor complete. "
        f"Messages sent: {messages_sent}, Errors: {errors}"
    )

    return {
        'messages_sent': messages_sent,
        'errors': errors,
        'users_processed': len(inactive_profiles)
    }

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        run_inactive_users_monitor()
