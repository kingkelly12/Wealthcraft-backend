"""
Push Notification Service for Native Notify

This service handles sending push notifications to mobile devices via the Native Notify API.
We act as a drop-in replacement for the previous Expo Push Service so existing routes work out of the box.
"""
import requests
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExpoPushService:
    """Service for sending push notifications via Native Notify Indie Push API"""
    
    APP_ID = 33561
    APP_TOKEN = "zHkkW0NtIsUe14PaWbYzcv"
    NATIVE_NOTIFY_INDIE_URL = "https://app.nativenotify.com/api/indie/notification"
    
    @classmethod
    def send_notification_to_user(
        cls,
        supabase_client,
        user_id: str,
        title: str,
        body: str,
        notification_type: str = 'system',
        data: Optional[Dict] = None
    ) -> bool:
        """
        Send an Indie Push Notification via Native Notify using the user ID as subID.
        """
        try:
            # Prepare data payload
            notification_data = dict(data) if data else {}
            notification_data['type'] = notification_type
            notification_data['timestamp'] = datetime.utcnow().isoformat()
            
            payload = {
                "subID": str(user_id),
                "appId": cls.APP_ID,
                "appToken": cls.APP_TOKEN,
                "title": title,
                "message": body,
                "pushData": notification_data
            }
            
            response = requests.post(
                cls.NATIVE_NOTIFY_INDIE_URL,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Native Notify Push sent successfully to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending Native Notify notification to user {user_id}: {str(e)}")
            return False

    @classmethod
    def send_notifications_to_users(
        cls,
        supabase_client,
        user_notifications: List[Dict],
        notification_type: str = 'system'
    ) -> Dict[str, int]:
        """
        Batch-send notifications. Native Notify Indie API handles messages individually via HTTP post per user.
        """
        if not user_notifications:
            return {'success': 0, 'failed': 0, 'skipped': 0}

        success_count = 0
        failed_count = 0

        for notif in user_notifications:
            user_id = notif.get('user_id')
            if not user_id:
                failed_count += 1
                continue
                
            success = cls.send_notification_to_user(
                supabase_client=supabase_client,
                user_id=user_id,
                title=notif.get('title', ''),
                body=notif.get('body', ''),
                notification_type=notification_type,
                data=notif.get('data')
            )
            
            if success:
                success_count += 1
            else:
                failed_count += 1

        logger.info(
            f"Native Notify batch send complete — success: {success_count}, failed: {failed_count}"
        )
        return {'success': success_count, 'failed': failed_count, 'skipped': 0}

    @classmethod
    def notify_followers_of_financial_move(
        cls,
        supabase_client,
        user_id: str,
        move_type: str,
        item_name: str,
        amount: Optional[float] = None,
        profit: Optional[float] = None
    ) -> None:
        """
        Notify all followers (mentors) about a user's financial move using a background thread.
        Provides engaging copy to trigger mentorship intervention or praise.
        """
        from app.utils.background_task import run_in_background
        
        def background_task():
            try:
                # Get user's username
                profile_res = supabase_client.table('profiles').select('username').eq('user_id', user_id).single().execute()
                username = profile_res.data.get('username', 'Your student') if profile_res.data else 'Your student'

                # Get all followers 
                followers_res = supabase_client.table('user_follows').select('follower_id').eq('following_id', user_id).execute()
                followers = followers_res.data if followers_res.data else []

                if not followers:
                    return

                # Craft notification copy based on move type
                if move_type == 'buy_asset':
                    title = '📊 Student Move'
                    body = f'{username} just invested in {item_name}. Are you keeping up?'
                elif move_type == 'sell_asset' and profit is not None and profit >= 0:
                    title = '💰 Student Win'
                    body = f'{username} sold {item_name} for a ${profit:,.2f} profit. Impressive moves.'
                elif move_type == 'sell_asset':
                    title = '📉 Student Alert'
                    body = f'{username} panic-sold {item_name} at a loss. Mentor them?'
                elif move_type == 'buy_liability':
                    title = '🚗 Student Splurge'
                    body = f'{username} just bought {item_name} for ${amount:,.2f}. Will this ruin their budget?'
                elif move_type == 'sell_liability':
                    title = '🔄 Student Downsized'
                    body = f'{username} just sold their {item_name}. Smart move or forced cut?'
                elif move_type == 'take_loan':
                    title = '💳 Student Debt'
                    body = f'{username} took out a {item_name} loan for ${amount:,.2f}. Keep an eye on them.'
                elif move_type == 'repay_loan':
                    title = '📉 Debt Reduced'
                    body = f'{username} just paid off ${amount:,.2f} of their {item_name}. Building financial freedom.'
                elif move_type == 'post_p2p_offer':
                    title = '🤝 Student Lending'
                    body = f'{username} is offering ${amount:,.2f} as a P2P loan. Playing the bank today?'
                elif move_type == 'rent_property':
                    title = '🏠 Student Housing Move'
                    body = f'{username} just rented {item_name} at ${amount:,.2f}/month. Watching their burn rate?'
                elif move_type == 'move_out':
                    title = '📦 Student Relocated'
                    body = f'{username} just moved out of {item_name}. Living situation changed.'
                elif move_type == 'new_job':
                    title = '💼 Student Employed'
                    body = f'{username} started as a {item_name}. Salary incoming!'
                elif move_type == 'quit_job':
                    title = '👋 Student Resigned'
                    body = f'{username} quit their job as {item_name}. Planning their next move?'
                elif move_type == 'enroll_course':
                    title = '🎓 Student Enrolled'
                    body = f'{username} started {item_name}. Investing in their future.'
                elif move_type == 'complete_course':
                    title = '📜 Student Graduated'
                    body = f'{username} completed {item_name}! Their earning potential just went up.'
                elif move_type == 'life_event':
                    title = '🎲 Student Decision'
                    body = f'{username} made a choice: "{item_name}". How will it impact them?'
                else:
                    title = '💵 Financial Move'
                    body = f'{username} made a financial move involving {item_name}.'

                for f in followers:
                    follower_id = f['follower_id']
                    try:
                        # PUSH notification first (primary delivery method for followers)
                        push_success = cls.send_notification_to_user(
                            supabase_client=supabase_client,
                            user_id=follower_id,
                            title=title,
                            body=body,
                            notification_type='student_move',
                            data={
                                'type': 'student_move',
                                'student_id': user_id,
                                'screen': f'/profile?id={user_id}'
                            }
                        )
                        
                        # Only create in-app notification if push fails or as backup
                        # This prevents duplicate notifications
                        if not push_success:
                            logger.warning(f"Push failed for follower {follower_id}, creating in-app backup")
                            supabase_client.table('notifications').insert({
                                'user_id': follower_id,
                                'type': 'student_move',
                                'title': title,
                                'message': body,
                                'related_user_id': user_id,
                                'read': False
                            }).execute()
                    except Exception as e:
                        logger.error(f"Failed to notify mentor {follower_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to notify mentors/followers of move: {str(e)}")

        run_in_background(background_task)
