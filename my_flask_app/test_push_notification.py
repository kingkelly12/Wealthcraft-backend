"""
Test Script for Push Notifications

This script allows you to test push notifications without going through
the full application flow. Useful for debugging.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, supabase
from app.services.push_notification_service import ExpoPushService
import argparse


def test_push_notification(user_id: str = None, title: str = None, body: str = None, notification_type: str = 'test'):
    """Send a test push notification to a specific user"""
    app = create_app()
    
    with app.app_context():
        if not user_id:
            # Get first user with push token
            result = supabase.table('profiles').select('user_id, username, push_token').not_.is_('push_token', 'null').limit(1).execute()
            
            if not result.data or len(result.data) == 0:
                print("❌ No users with push tokens found")
                return False
            
            user_id = result.data[0]['user_id']
            print(f"📱 Sending test notification to: {result.data[0]['username']} ({user_id})")
        else:
            print(f"📱 Sending test notification to user: {user_id}")
        
        # Set defaults
        title = title or "🔔 Test Notification"
        body = body or "This is a test push notification from the backend"
        
        # Send notification
        success = ExpoPushService.send_notification_to_user(
            supabase_client=supabase,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            data={
                'type': notification_type,
                'screen': '/(tabs)/',
                'test': True
            }
        )
        
        if success:
            print("✅ Notification sent successfully!")
            return True
        else:
            print("❌ Failed to send notification")
            return False


def list_users_with_tokens():
    """List all users who have push tokens registered"""
    app = create_app()
    
    with app.app_context():
        result = supabase.table('profiles').select('user_id, username, push_token, push_token_updated_at').not_.is_('push_token', 'null').execute()
        
        if not result.data or len(result.data) == 0:
            print("No users with push tokens found")
            return
        
        print(f"\n📱 Users with Push Tokens ({len(result.data)}):\n")
        print(f"{'Username':<20} {'User ID':<40} {'Updated At'}")
        print("-" * 90)
        
        for user in result.data:
            username = user.get('username', 'Unknown')
            user_id = user.get('user_id', '')
            updated_at = user.get('push_token_updated_at', 'Never')
            print(f"{username:<20} {user_id:<40} {updated_at}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Push Notifications')
    parser.add_argument('--list', action='store_true', help='List users with push tokens')
    parser.add_argument('--user-id', type=str, help='User ID to send notification to')
    parser.add_argument('--title', type=str, help='Notification title')
    parser.add_argument('--body', type=str, help='Notification body')
    parser.add_argument('--type', type=str, default='test', help='Notification type')
    
    args = parser.parse_args()
    
    if args.list:
        list_users_with_tokens()
    else:
        test_push_notification(
            user_id=args.user_id,
            title=args.title,
            body=args.body,
            notification_type=args.type
        )
