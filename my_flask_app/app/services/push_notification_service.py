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
        supabase_client,  # Maintained for backwards compatibility with existing route calls
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
