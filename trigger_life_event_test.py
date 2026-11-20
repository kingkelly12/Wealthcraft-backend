#!/usr/bin/env python3
"""
Trigger Life Event Push Notification for Testing

This script triggers a life event for a specific user and sends a push notification.
Useful for testing the complete push notification flow end-to-end.

Usage:
    python trigger_life_event_test.py "Tester One"
    python trigger_life_event_test.py --username "Tester One"
    python trigger_life_event_test.py --user-id "8bffcbd1-..."
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_flask_app.app import create_app
import argparse
import uuid
import random
from datetime import datetime

def trigger_life_event_for_user(username: str = None, user_id: str = None):
    """Trigger a life event and send push notification for a specific user"""
    app = create_app()
    
    with app.app_context():
        from my_flask_app.app import supabase
        from my_flask_app.app.services.push_notification_service import ExpoPushService
        
        # 1. Get user
        if username:
            print(f"🔍 Looking up user: {username}")
            user_res = supabase.table('profiles') \
                .select('user_id, username, expo_push_token') \
                .eq('username', username) \
                .single() \
                .execute()
        elif user_id:
            print(f"🔍 Looking up user: {user_id}")
            user_res = supabase.table('profiles') \
                .select('user_id, username, expo_push_token') \
                .eq('user_id', user_id) \
                .single() \
                .execute()
        else:
            print("❌ Either username or user_id must be provided")
            return False
        
        if not user_res.data:
            print("❌ User not found")
            return False
        
        user = user_res.data
        user_id = user['user_id']
        username = user['username']
        
        print(f"✅ Found user: {username} ({user_id})")
        
        if user.get('expo_push_token'):
            print(f"✅ User has push token: {user['expo_push_token'][:30]}...")
        else:
            print("⚠️  User has no push token registered")
            return False
        
        # 2. Get all active life events
        print("\n📚 Fetching active life events...")
        events_res = supabase.table('life_events') \
            .select('id, title, description') \
            .eq('is_active', True) \
            .execute()
        
        events = events_res.data or []
        if not events:
            print("❌ No active life events found in database")
            return False
        
        print(f"✅ Found {len(events)} active life events")
        
        # 3. Select a random event
        selected_event = random.choice(events)
        print(f"\n🎲 Selected event: {selected_event['title']}")
        print(f"   Description: {selected_event['description'][:80]}...")
        
        # 4. Create user_life_event record
        print("\n💾 Creating user life event record...")
        new_event_id = str(uuid.uuid4())
        
        try:
            insert_res = supabase.table('user_life_events').insert({
                'id': new_event_id,
                'user_id': user_id,
                'life_event_id': selected_event['id'],
                'choice_id': None,
                'was_auto_selected': False
            }).execute()
            
            print(f"✅ Created user life event: {new_event_id}")
        except Exception as e:
            print(f"❌ Failed to create user life event: {str(e)}")
            return False
        
        # 5. Send push notification
        print("\n📱 Sending push notification...")
        
        message_body = (
            selected_event['description'][:100] + "..."
            if len(selected_event['description']) > 100
            else selected_event['description']
        )
        
        success = ExpoPushService.send_notification_to_user(
            supabase_client=supabase,
            user_id=user_id,
            title=f"⚡ Life Update: {selected_event['title']}",
            body=message_body,
            notification_type='life_event',
            data={
                'screen': f"/life-events/{selected_event['id']}",
                'eventId': str(selected_event['id']),
                'userEventId': new_event_id
            }
        )
        
        if success:
            print(f"✅ Push notification sent successfully!")
            print(f"\n📊 Summary:")
            print(f"   User: {username} ({user_id})")
            print(f"   Event: {selected_event['title']}")
            print(f"   Event ID: {selected_event['id']}")
            print(f"   User Event ID: {new_event_id}")
            print(f"   Timestamp: {datetime.utcnow().isoformat()}")
            return True
        else:
            print(f"❌ Failed to send push notification")
            print(f"   (User might not have a valid push token registered)")
            return False

def main():
    parser = argparse.ArgumentParser(
        description='Trigger a life event and push notification for testing'
    )
    parser.add_argument(
        'username',
        nargs='?',
        help='Username to trigger event for'
    )
    parser.add_argument(
        '--username',
        type=str,
        help='Username to trigger event for'
    )
    parser.add_argument(
        '--user-id',
        type=str,
        help='User ID to trigger event for'
    )
    
    args = parser.parse_args()
    
    # Use positional or flag argument
    username = args.username or getattr(args, 'username', None)
    user_id = args.user_id
    
    if not username and not user_id:
        parser.print_help()
        return 1
    
    try:
        success = trigger_life_event_for_user(username=username, user_id=user_id)
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
