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
    Apply market price changes for global assets and update user portfolios.
    Sends push notifications for significant movers.
    """
    logger.info("Starting market fluctuation and portfolio update...")

    try:
        # 1. Fetch global assets that are volatile
        fluctuating_categories = ['stocks', 'crypto', 'investments']
        assets_result = supabase.table('assets').select('*').in_('category', fluctuating_categories).execute()

        if not assets_result.data:
            logger.info("No volatile market assets found")
            return

        global_changes = {}
        for asset in assets_result.data:
            cat = asset.get('category')
            current_price = float(asset.get('price', 0))
            
            if current_price <= 0:
                continue

            # Random changes
            if cat == 'crypto':
                price_change_pct = random.uniform(-10, 10)
            else:
                price_change_pct = random.uniform(-5, 5)

            new_price = current_price * (1 + price_change_pct / 100)
            new_price = max(1.0, float(new_price)) # prevent $0 or negative

            # Update global asset
            supabase.table('assets').update({'price': new_price}).eq('id', asset['id']).execute()

            global_changes[asset['name']] = {
                'new_price': new_price,
                'change_pct': price_change_pct,
                'old_price': current_price,
                'type': cat
            }

        if not global_changes:
            return

        # 2. Fetch user portfolios containing these assets
        affected_types = ['stocks', 'crypto'] 
        user_assets_result = supabase.table('user_assets').select(
            'id, user_id, name, asset_type, quantity, value'
        ).in_('asset_type', affected_types).execute()

        user_updates = {}
        
        if user_assets_result.data:
            for ua in user_assets_result.data:
                asset_name = ua.get('name')
                if asset_name in global_changes:
                    change_data = global_changes[asset_name]
                    new_price = change_data['new_price']
                    quantity = float(ua.get('quantity', 1))
                    new_value = new_price * quantity
                    
                    # Update user's specific asset value in database
                    supabase.table('user_assets').update({'value': new_value}).eq('id', ua['id']).execute()

                    # Record for notifications
                    user_id = ua['user_id']
                    if user_id not in user_updates:
                        user_updates[user_id] = []
                        
                    user_updates[user_id].append({
                        'name': asset_name,
                        'type': ua.get('asset_type'),
                        'change_pct': change_data['change_pct'],
                        'value_change': new_value - float(ua.get('value', 0))
                    })

            logger.info(f"Updated portfolios for {len(user_updates)} users")

        # 3. Build and send notifications
        notifications_to_send = []
        for user_id, changes in user_updates.items():
            # Sync Net Worth for all affected users so leaderboard reflects market moves
            try:
                from app.services.profile_service import ProfileService
                import uuid
                ProfileService.recalculate_net_worth(uuid.UUID(user_id))
            except Exception as e:
                logger.error(f"Failed to sync net worth for user {user_id}: {e}")

            # Filter for significant changes, e.g. > 3%
            significant_changes = [c for c in changes if abs(c['change_pct']) >= 3.0]
            
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
                        'screen': "/(tabs)/investments",
                        'category': most_significant['type'],
                        'changes': significant_changes[:3],
                    }
                })

        if notifications_to_send:
            success_count = 0
            failed_count = 0
            for notif in notifications_to_send:
                try:
                    res = ExpoPushService.send_notification_to_user(
                        supabase_client=supabase,
                        user_id=notif['user_id'],
                        title=notif['title'],
                        body=notif['body'],
                        notification_type='market_fluctuation',
                        data=notif.get('data')
                    )
                    if res:
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Error sending push: {e}")
                    failed_count += 1
                    
            logger.info(f"Market monitor complete. Sent: {success_count}, Failed: {failed_count}")
        else:
            logger.info("No significant market changes to notify about")

    except Exception as e:
        import traceback
        logger.error(f"Critical error in market monitor: {str(e)}\n{traceback.format_exc()}")
        raise


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        simulate_market_fluctuation()
