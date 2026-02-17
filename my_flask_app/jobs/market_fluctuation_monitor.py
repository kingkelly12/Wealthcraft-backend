"""
Simulated Market Fluctuation Monitoring Job

This job monitors user asset holdings and sends push notifications
when SIMULATED price changes exceed defined thresholds.

Note: This uses simulated price changes, not real-world market data.
Run this job every hour via cron/scheduler.
"""

from app import create_app, supabase
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
    app = create_app()
    
    with app.app_context():
        logger.info("Starting simulated market fluctuation monitoring...")
        
        try:
            # Get all user assets
            assets_result = supabase.table('user_assets').select(
                'id, user_id, asset_name, asset_type, purchase_price, quantity, value'
            ).execute()
            
            if not assets_result.data:
                logger.info("No user assets found to monitor")
                return
            
            notifications_sent = 0
            
            # Group assets by user to batch notifications
            user_assets = {}
            for asset in assets_result.data:
                user_id = asset['user_id']
                if user_id not in user_assets:
                    user_assets[user_id] = []
                user_assets[user_id].append(asset)
            
            logger.info(f"Monitoring assets for {len(user_assets)} users")
            
            # Process each user's assets
            for user_id, assets in user_assets.items():
                significant_changes = []
                
                for asset in assets:
                    # Simulate price change
                    if asset['asset_type'] == 'stock':
                        # Stocks: -5% to +5% daily fluctuation
                        price_change_pct = random.uniform(-5, 5)
                        threshold = 3.0  # Notify on ±3% change
                    elif asset['asset_type'] == 'crypto':
                        # Crypto: -10% to +10% daily fluctuation
                        price_change_pct = random.uniform(-10, 10)
                        threshold = 5.0  # Notify on ±5% change
                    else:
                        # Other assets: minimal fluctuation
                        price_change_pct = random.uniform(-2, 2)
                        threshold = 2.0
                    
                    # Only notify if change exceeds threshold
                    if abs(price_change_pct) >= threshold:
                        current_value = asset.get('value', 0)
                        simulated_new_value = current_value * (1 + price_change_pct / 100)
                        value_change = simulated_new_value - current_value
                        
                        significant_changes.append({
                            'name': asset['asset_name'],
                            'type': asset['asset_type'],
                            'change_pct': price_change_pct,
                            'value_change': value_change
                        })
                
                # Send notification if there are significant changes
                if significant_changes:
                    # Take the most significant change for the notification
                    most_significant = max(significant_changes, key=lambda x: abs(x['change_pct']))
                    
                    emoji = "📈" if most_significant['change_pct'] > 0 else "📉"
                    sign = "+" if most_significant['change_pct'] > 0 else ""
                    
                    title = f"{emoji} Market Update: {most_significant['name']}"
                    body = f"{sign}{most_significant['change_pct']:.1f}% change (${most_significant['value_change']:.2f})"
                    
                    if len(significant_changes) > 1:
                        body += f" and {len(significant_changes) - 1} other assets"
                    
                    # Send notification
                    success = ExpoPushService.send_notification_to_user(
                        supabase_client=supabase,
                        user_id=user_id,
                        title=title,
                        body=body,
                        notification_type='market_fluctuation',
                        data={
                            'type': 'market_fluctuation',
                            'screen': f"/invest?category={most_significant['type']}",
                            'category': most_significant['type'],
                            'changes': significant_changes[:3],  # Include up to 3 changes
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    )
                    
                    if success:
                        notifications_sent += 1
                        logger.info(f"Sent market notification to user {user_id}: {most_significant['name']} {sign}{most_significant['change_pct']:.1f}%")
            
            logger.info(f"Market fluctuation monitoring complete. Sent {notifications_sent} notifications")
            
        except Exception as e:
            logger.error(f"Error in market fluctuation monitoring: {str(e)}")


if __name__ == '__main__':
    simulate_market_fluctuation()
