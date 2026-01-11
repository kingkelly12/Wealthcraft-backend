"""
Push Notification Service for Expo Push Notifications

This service handles sending push notifications to mobile devices via the Expo Push API.
It supports single and batch notification sending with proper error handling.
"""
import requests
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExpoPushService:
    """Service for sending push notifications via Expo Push Notification Service"""
    
    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    MAX_BATCH_SIZE = 100  # Expo's recommended batch size
    
    @staticmethod
    def validate_push_token(token: str) -> bool:
        """
        Validate Expo push token format
        
        Valid formats:
        - ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]
        - ExpoPushToken[xxxxxxxxxxxxxxxxxxxxxx]
        
        Args:
            token: Push token to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not token:
            return False
        
        return (
            token.startswith('ExponentPushToken[') or 
            token.startswith('ExpoPushToken[')
        ) and token.endswith(']')
    
    @classmethod
    def send_push_notification(
        cls,
        push_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        sound: str = 'default',
        priority: str = 'high',
        channel_id: str = 'default'
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a push notification to a single device
        
        Args:
            push_token: Expo push token for the device
            title: Notification title
            body: Notification body text
            data: Optional custom data payload
            sound: Sound to play ('default' or custom sound name)
            priority: Notification priority ('default', 'normal', 'high')
            channel_id: Android notification channel ID
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        if not cls.validate_push_token(push_token):
            logger.warning(f"Invalid push token format: {push_token[:20]}...")
            return False, "Invalid push token format"
        
        message = {
            "to": push_token,
            "sound": sound,
            "title": title,
            "body": body,
            "data": data or {},
            "priority": priority,
            "channelId": channel_id
        }
        
        try:
            response = requests.post(
                cls.EXPO_PUSH_URL,
                json=[message],
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check for errors in response
            if result.get('data') and len(result['data']) > 0:
                ticket = result['data'][0]
                
                if ticket.get('status') == 'error':
                    error_msg = ticket.get('message', 'Unknown error')
                    logger.error(f"Push notification error: {error_msg}")
                    return False, error_msg
                
                logger.info(f"Push notification sent successfully to {push_token[:20]}...")
                return True, None
            
            return False, "No response data from Expo"
            
        except requests.exceptions.Timeout:
            logger.error("Push notification request timed out")
            return False, "Request timeout"
        except requests.exceptions.RequestException as e:
            logger.error(f"Push notification request failed: {str(e)}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {str(e)}")
            return False, str(e)
    
    @classmethod
    def send_batch_notifications(
        cls,
        notifications: List[Dict[str, any]]
    ) -> Dict[str, int]:
        """
        Send multiple push notifications in a batch
        
        Args:
            notifications: List of notification dictionaries, each containing:
                - push_token: str
                - title: str
                - body: str
                - data: Optional[Dict]
                - sound: Optional[str] (default: 'default')
                - priority: Optional[str] (default: 'high')
                - channel_id: Optional[str] (default: 'default')
        
        Returns:
            Dictionary with counts: {'success': int, 'failed': int}
        """
        if not notifications:
            return {'success': 0, 'failed': 0}
        
        # Validate and prepare messages
        messages = []
        for notif in notifications:
            push_token = notif.get('push_token')
            
            if not cls.validate_push_token(push_token):
                logger.warning(f"Skipping invalid push token: {push_token[:20] if push_token else 'None'}...")
                continue
            
            messages.append({
                "to": push_token,
                "sound": notif.get('sound', 'default'),
                "title": notif.get('title', ''),
                "body": notif.get('body', ''),
                "data": notif.get('data', {}),
                "priority": notif.get('priority', 'high'),
                "channelId": notif.get('channel_id', 'default')
            })
        
        if not messages:
            logger.warning("No valid push tokens to send notifications to")
            return {'success': 0, 'failed': 0}
        
        # Send in batches
        success_count = 0
        failed_count = 0
        
        for i in range(0, len(messages), cls.MAX_BATCH_SIZE):
            batch = messages[i:i + cls.MAX_BATCH_SIZE]
            
            try:
                response = requests.post(
                    cls.EXPO_PUSH_URL,
                    json=batch,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Count successes and failures
                if result.get('data'):
                    for ticket in result['data']:
                        if ticket.get('status') == 'ok':
                            success_count += 1
                        else:
                            failed_count += 1
                            logger.warning(f"Batch notification failed: {ticket.get('message')}")
                
            except Exception as e:
                logger.error(f"Batch notification request failed: {str(e)}")
                failed_count += len(batch)
        
        logger.info(f"Batch notifications sent: {success_count} success, {failed_count} failed")
        return {'success': success_count, 'failed': failed_count}
    
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
        Convenience method to send notification to a user by user_id
        Fetches push token from database and sends notification
        
        Args:
            supabase_client: Supabase client instance
            user_id: User ID to send notification to
            title: Notification title
            body: Notification body
            notification_type: Type of notification for data payload
            data: Additional custom data
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Fetch user's push token
            result = supabase_client.table('profiles').select('push_token').eq('user_id', user_id).execute()
            
            if not result.data or len(result.data) == 0:
                logger.warning(f"No profile found for user_id: {user_id}")
                return False
            
            push_token = result.data[0].get('push_token')
            
            if not push_token:
                logger.info(f"User {user_id} has no push token registered")
                return False
            
            # Prepare data payload
            notification_data = data or {}
            notification_data['type'] = notification_type
            notification_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Send notification
            success, error = cls.send_push_notification(
                push_token=push_token,
                title=title,
                body=body,
                data=notification_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            return False
