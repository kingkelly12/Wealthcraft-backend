"""
Daily Mentor Analysis Job
Analyzes all active players' financial data and sends mentor messages
Run this daily via cron or task scheduler
"""

from app import db, supabase
from app.services.mentor_service import MentorService
from app.models.profile import Profile
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_daily_mentor_analysis():
    """Run daily financial analysis for all active players"""
    logger.info("Starting daily mentor analysis...")

    try:
        # Get all active users (last active within last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_profiles = Profile.query.filter(
            Profile.last_active_at >= thirty_days_ago
        ).all()
        
        logger.info(f"Found {len(active_profiles)} active users")
    except Exception as e:
        logger.error(f"Error fetching active profiles: {e}")
        return {'error': str(e), 'processed': 0}

    messages_sent = 0
    errors = 0

    for profile in active_profiles:
        try:
            # Analyze finances
            metrics = MentorService.analyze_player_finances(profile.user_id)
            if not metrics:
                continue

            # Check triggers
            triggers = MentorService.check_triggers(profile.user_id, metrics)

            # Sort by priority (highest first)
            triggers.sort(key=lambda x: x['priority'], reverse=True)

            # Send top 1-2 messages (don't overwhelm)
            for trigger in triggers[:2]:
                mentor_data = MentorService.generate_personalized_message(
                    profile.user_id,
                    trigger,
                    profile.username
                )

                if mentor_data:
                    MentorService.send_mentor_message(
                        profile.user_id,
                        mentor_data,
                        metrics,
                        supabase_client=supabase
                    )
                    messages_sent += 1
                    logger.info(
                        f"Sent {trigger['type']} message to {profile.username}"
                    )

        except Exception as e:
            errors += 1
            logger.error(f"Error processing profile {profile.username}: {str(e)}")
            continue

    logger.info(
        f"Daily mentor analysis complete. "
        f"Messages sent: {messages_sent}, Errors: {errors}"
    )

    return {
        'messages_sent': messages_sent,
        'errors': errors,
        'users_processed': len(active_profiles)
    }

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        run_daily_mentor_analysis()
