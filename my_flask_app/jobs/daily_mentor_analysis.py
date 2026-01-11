"""
Daily Mentor Analysis Job
Analyzes all active players' financial data and sends mentor messages
Run this daily via cron or task scheduler
"""

from app import create_app, db
from app.services.mentor_service import MentorService
from app.models.profile import Profile
from app.models.user import User
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
    app = create_app()
    
    with app.app_context():
        logger.info("Starting daily mentor analysis...")
        
        # Get all active users (logged in within last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = User.query.filter(
            User.last_login >= thirty_days_ago
        ).all()
        
        logger.info(f"Found {len(active_users)} active users")
        
        messages_sent = 0
        errors = 0
        
        for user in active_users:
            try:
                # Get profile
                profile = Profile.query.filter_by(user_id=user.id).first()
                if not profile:
                    continue
                
                # Analyze finances
                metrics = MentorService.analyze_player_finances(user.id)
                if not metrics:
                    continue
                
                # Check triggers
                triggers = MentorService.check_triggers(user.id, metrics)
                
                # Sort by priority (highest first)
                triggers.sort(key=lambda x: x['priority'], reverse=True)
                
                # Send top 1-2 messages (don't overwhelm)
                for trigger in triggers[:2]:
                    mentor_data = MentorService.generate_personalized_message(
                        user.id,
                        trigger,
                        profile.username
                    )
                    
                    if mentor_data:
                        MentorService.send_mentor_message(
                            user.id,
                            mentor_data,
                            metrics
                        )
                        messages_sent += 1
                        logger.info(
                            f"Sent {trigger['type']} message to {profile.username}"
                        )
                
            except Exception as e:
                errors += 1
                logger.error(f"Error processing user {user.id}: {str(e)}")
                continue
        
        logger.info(
            f"Daily mentor analysis complete. "
            f"Messages sent: {messages_sent}, Errors: {errors}"
        )
        
        return {
            'messages_sent': messages_sent,
            'errors': errors,
            'users_processed': len(active_users)
        }

if __name__ == '__main__':
    run_daily_mentor_analysis()
