"""
Push Notification Service for Expo Push Notifications

This service handles sending push notifications to mobile devices via the Expo Push API.
It supports single and batch notification sending with proper error handling.
"""
import requests
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import os

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
            # Prepare headers with optional Expo Access Token
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Add Expo Access Token if available (for better rate limits)
            expo_token = os.getenv('EXPO_ACCESS_TOKEN')
            if expo_token:
                headers["Authorization"] = f"Bearer {expo_token}"
            
            response = requests.post(
                cls.EXPO_PUSH_URL,
                json=[message],
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Check for errors in response
            if result.get('data') and len(result['data']) > 0:
                ticket = result['data'][0]
                
                if ticket.get('status') == 'error':
                    error_msg = ticket.get('message', 'Unknown error')
                    error_details = ticket.get('details', {})
                    
                    logger.error(f"Push notification error: {error_msg}")
                    
                    # Return error type for caller to handle (e.g., DeviceNotRegistered)
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
                # Prepare headers with optional Expo Access Token
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                
                expo_token = os.getenv('EXPO_ACCESS_TOKEN')
                if expo_token:
                    headers["Authorization"] = f"Bearer {expo_token}"
                
                response = requests.post(
                    cls.EXPO_PUSH_URL,
                    json=batch,
                    headers=headers,
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
                            error_msg = ticket.get('message', 'Unknown error')
                            logger.warning(f"Batch notification failed: {error_msg}")
                
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
            notification_data = dict(data) if data else {}
            notification_data['type'] = notification_type
            notification_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Send notification
            success, error = cls.send_push_notification(
                push_token=push_token,
                title=title,
                body=body,
                data=notification_data
            )
            
            # Handle DeviceNotRegistered error - clean up invalid token
            if not success and error and 'DeviceNotRegistered' in error:
                logger.warning(f"Removing invalid push token for user {user_id}: DeviceNotRegistered")
                try:
                    # Remove invalid token from database
                    supabase_client.table('profiles').update({
                        'push_token': None,
                        'push_token_updated_at': datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).execute()
                    logger.info(f"Successfully removed invalid token for user {user_id}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup invalid token for user {user_id}: {str(cleanup_error)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {str(e)}")
            return False

    @classmethod
    def send_notifications_to_users(
        cls,
        supabase_client,
        user_notifications: List[Dict],
        notification_type: str = 'system'
    ) -> Dict[str, int]:
        """
        Batch-send notifications to multiple users efficiently.

        Instead of making one Supabase request per user (N requests), this
        fetches all push tokens in a SINGLE query and sends all notifications
        in batches of 100 to the Expo API.

        Args:
            supabase_client: Supabase client instance
            user_notifications: List of dicts, each containing:
                - user_id: str  (required)
                - title: str    (required)
                - body: str     (required)
                - data: Optional[Dict]
            notification_type: Type added to every notification's data payload

        Returns:
            Dictionary with counts: {'success': int, 'failed': int, 'skipped': int}
        """
        if not user_notifications:
            return {'success': 0, 'failed': 0, 'skipped': 0}

        # 1. Collect all unique user_ids
        user_ids = list({n['user_id'] for n in user_notifications})

        # 2. Fetch ALL push tokens in ONE Supabase request
        try:
            result = supabase_client.table('profiles').select(
                'user_id, push_token'
            ).in_('user_id', user_ids).execute()
        except Exception as e:
            logger.error(f"Failed to fetch push tokens in batch: {str(e)}")
            return {'success': 0, 'failed': len(user_notifications), 'skipped': 0}

        # 3. Build a lookup map: user_id -> push_token
        token_map = {
            row['user_id']: row.get('push_token')
            for row in (result.data or [])
        }

        # 4. Build the batch payload, skipping users with no/invalid tokens
        batch_payload = []
        skipped = 0
        now = datetime.utcnow().isoformat()

        for notif in user_notifications:
            user_id = notif['user_id']
            push_token = token_map.get(user_id)

            if not push_token:
                logger.info(f"User {user_id} has no push token — skipping")
                skipped += 1
                continue

            if not cls.validate_push_token(push_token):
                logger.warning(f"Invalid push token format for user {user_id} — skipping")
                skipped += 1
                continue

            notification_data = dict(notif.get('data') or {})
            notification_data['type'] = notification_type
            notification_data['timestamp'] = now

            batch_payload.append({
                'push_token': push_token,
                'title': notif['title'],
                'body': notif['body'],
                'data': notification_data,
            })

        if not batch_payload:
            logger.warning("No valid push tokens found for batch send")
            return {'success': 0, 'failed': 0, 'skipped': skipped}

        # 5. Send via the existing batch sender
        result_counts = cls.send_batch_notifications(batch_payload)
        result_counts['skipped'] = skipped

        # 6. Handle DeviceNotRegistered in bulk
        #    (send_batch_notifications logs per-ticket errors; we do a best-effort cleanup)
        #    Advanced: parse receipts to find DeviceNotRegistered tokens and null them here.
        #    For now, invalid tokens are skipped on future runs until cleaned by the
        #    single-user send_notification_to_user path which handles DeviceNotRegistered.

        logger.info(
            f"Batch send complete — success: {result_counts['success']}, "
            f"failed: {result_counts['failed']}, skipped: {skipped}"
        )
        return result_counts
