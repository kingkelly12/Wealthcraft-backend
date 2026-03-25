"""
Simulated Market Fluctuation Monitoring Job

This job monitors user asset holdings and sends push notifications
when SIMULATED price changes exceed defined thresholds.

Note: This uses simulated price changes, not real-world market data.
Run this job every hour via cron/scheduler.
"""

from app import supabase
from app.services.push_notification_service import ExpoPushService
from datetime import datetime
import logging
import random

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_market_fluctuation():
    """
    Simulate market price changes for user assets and send notifications
    when price changes exceed thresholds (±5% for stocks, ±10% for crypto)
    """
    logger.info("Starting simulated market fluctuation monitoring...")

    try:
        # Get all user assets
        assets_result = supabase.table('user_assets').select(
            'id, user_id, asset_name, asset_type, purchase_price, quantity, value'
        ).execute()

        if not assets_result.data:
            logger.info("No user assets found to monitor")
            return

        # Group assets by user to batch notifications
        user_assets = {}
        for asset in assets_result.data:
            user_id = asset['user_id']
            if user_id not in user_assets:
                user_assets[user_id] = []
            user_assets[user_id].append(asset)

        logger.info(f"Monitoring assets for {len(user_assets)} users")

        # --- Build notification list (no API calls yet) ---
        notifications_to_send = []

        for user_id, assets in user_assets.items():
            significant_changes = []

            for asset in assets:
                if asset['asset_type'] == 'stock':
                    price_change_pct = random.uniform(-5, 5)
                    threshold = 3.0
                elif asset['asset_type'] == 'crypto':
                    price_change_pct = random.uniform(-10, 10)
                    threshold = 5.0
                else:
                    price_change_pct = random.uniform(-2, 2)
                    threshold = 2.0

                if abs(price_change_pct) >= threshold:
                    current_value = asset.get('value', 0)
                    value_change = current_value * (price_change_pct / 100)

                    significant_changes.append({
                        'name': asset['asset_name'],
                        'type': asset['asset_type'],
                        'change_pct': price_change_pct,
                        'value_change': value_change
                    })

            if significant_changes:
                most_significant = max(significant_changes, key=lambda x: abs(x['change_pct']))
                emoji = "📈" if most_significant['change_pct'] > 0 else "📉"
                sign = "+" if most_significant['change_pct'] > 0 else ""

                title = f"{emoji} Market Update: {most_significant['name']}"
                body = f"{sign}{most_significant['change_pct']:.1f}% change (${most_significant['value_change']:.2f})"
                if len(significant_changes) > 1:
                    body += f" and {len(significant_changes) - 1} other assets"

                notifications_to_send.append({
                    'user_id': user_id,
                    'title': title,
                    'body': body,
                    'data': {
                        'screen': f"/invest?category={most_significant['type']}",
                        'category': most_significant['type'],
                        'changes': significant_changes[:3],
                    }
                })

        # --- Send all notifications in one batch ---
        if notifications_to_send:
            results = ExpoPushService.send_notifications_to_users(
                supabase_client=supabase,
                user_notifications=notifications_to_send,
                notification_type='market_fluctuation'
            )
            logger.info(
                f"Market monitor complete. "
                f"Sent: {results['success']}, Failed: {results['failed']}, Skipped: {results['skipped']}"
            )
        else:
            logger.info("No significant market changes to notify about")

    except Exception as e:
        logger.error(f"Error in market fluctuation monitoring: {str(e)}")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        simulate_market_fluctuation()
