"""
Daily Mentor Analysis Job

For every player active in the last 30 days: compute their financial metrics,
find mentor triggers that are not on cooldown, and send at most one message per
mentor (max 2 per player per day). Runs once per UTC day even if the scheduler
calls it repeatedly.
"""
import logging
from datetime import datetime, timedelta, timezone

from app import db, supabase
from app.models.profile import Profile
from app.services.mentor_service import MentorService

logger = logging.getLogger(__name__)

MAX_MESSAGES_PER_PLAYER = 2


def run_daily_mentor_analysis():
    """Run daily financial analysis for all active players."""
    from jobs.run_guard import claim_daily_run

    logger.info("Starting daily mentor analysis...")
    period = claim_daily_run('daily_mentor_analysis')
    if not period:
        logger.warning("Daily mentor analysis already ran today; skipping.")
        return {'skipped': True}

    try:
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        # Load only what we need; the ORM objects would otherwise go stale
        # after the per-player commits/rollbacks below.
        active_players = [
            (p.user_id, p.username)
            for p in Profile.query.with_entities(Profile.user_id, Profile.username)
                                  .filter(Profile.last_active_at >= thirty_days_ago).all()
        ]
        logger.info(f"Found {len(active_players)} active users")
    except Exception as e:
        logger.error(f"Error fetching active profiles: {e}")
        return {'error': str(e), 'processed': 0}

    messages_sent = 0
    errors = 0

    for user_id, username in active_players:
        try:
            metrics = MentorService.analyze_player_finances(user_id)
            if not metrics:
                continue

            triggers = MentorService.check_triggers(user_id, metrics)
            for trigger in MentorService.pick_daily_triggers(user_id, triggers, MAX_MESSAGES_PER_PLAYER):
                mentor_data = MentorService.generate_personalized_message(user_id, trigger, username)
                if not mentor_data:
                    continue
                MentorService.send_mentor_message(user_id, mentor_data, metrics, supabase_client=supabase)
                messages_sent += 1
                logger.info(f"Sent {trigger['type']} message to {username}")

        except Exception as e:
            # A failed flush leaves the session unusable; without a rollback
            # every remaining player in this run would fail too.
            db.session.rollback()
            errors += 1
            logger.error(f"Error processing profile {username}: {e}", exc_info=True)

    logger.info(f"Daily mentor analysis complete. Messages sent: {messages_sent}, Errors: {errors}")
    return {
        'period': period,
        'messages_sent': messages_sent,
        'errors': errors,
        'users_processed': len(active_players),
    }


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        run_daily_mentor_analysis()
