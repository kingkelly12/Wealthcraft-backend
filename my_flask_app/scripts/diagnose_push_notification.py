#!/usr/bin/env python3
"""
Expo Push Token Diagnostic Tool

Deep analysis to determine why notifications aren't reaching a device
even though the token is registered.

Checks:
1. Token format validity
2. Expo API responses
3. Token registration status
4. Device online/offline status (inferred)
5. Notification payload validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
import argparse
import json
from datetime import datetime

def validate_token_format(token: str) -> tuple:
    """Check if token has valid Expo format"""
    print(f"\n{'='*60}")
    print("STEP 1: TOKEN FORMAT VALIDATION")
    print(f"{'='*60}\n")
    
    print(f"Token provided: {token}\n")
    
    # Check basic format
    if not token:
        print("❌ Token is empty")
        return False, "Token is empty"
    
    if not isinstance(token, str):
        print(f"❌ Token is not a string: {type(token)}")
        return False, f"Token type is {type(token)}, not string"
    
    # Check prefix
    if not token.startswith('ExponentPushToken['):
        print(f"❌ Token doesn't start with 'ExponentPushToken['")
        return False, "Invalid prefix"
    
    print("✅ Token starts with 'ExponentPushToken['")
    
    # Check suffix
    if not token.endswith(']'):
        print(f"❌ Token doesn't end with ']'")
        return False, "Invalid suffix"
    
    print("✅ Token ends with ']'")
    
    # Extract content
    content = token[len('ExponentPushToken['):-1]
    print(f"✅ Token content length: {len(content)} characters")
    print(f"   Content: {content}\n")
    
    # Check content length (should be substantial)
    if len(content) < 10:
        print(f"⚠️  Token content seems very short ({len(content)} chars)")
        print("   Might still work, but unusual\n")
    
    # Check for valid characters (alphanumeric, dash, underscore)
    invalid_chars = [c for c in content if not (c.isalnum() or c in '-_')]
    if invalid_chars:
        print(f"⚠️  Token contains unusual characters: {set(invalid_chars)}")
        print("   This might cause issues\n")
    else:
        print("✅ Token contains only valid characters (alphanumeric, -, _)\n")
    
    print("✅ TOKEN FORMAT IS VALID\n")
    return True, "Valid format"


def check_database_registration(username: str, token: str):
    """Check if token is correctly saved in database"""
    print(f"{'='*60}")
    print("STEP 2: DATABASE REGISTRATION CHECK")
    print(f"{'='*60}\n")
    
    app = create_app()
    with app.app_context():
        from my_flask_app.app import supabase
        
        try:
            # Get user
            user_res = supabase.table('profiles') \
                .select('user_id, username, expo_push_token, push_token_updated_at') \
                .eq('username', username) \
                .single() \
                .execute()
            
            if not user_res.data:
                print(f"❌ User '{username}' not found in database\n")
                return False
            
            user = user_res.data
            print(f"✅ User found: {username}")
            print(f"   User ID: {user['user_id']}\n")
            
            db_token = user.get('expo_push_token')
            db_updated = user.get('push_token_updated_at')
            
            if not db_token:
                print(f"❌ User has NO token in database!")
                print(f"   expo_push_token column is NULL\n")
                return False
            
            print(f"✅ User has token in database:")
            print(f"   Token: {db_token}")
            print(f"   Updated at: {db_updated}\n")
            
            # Check if tokens match
            if db_token == token:
                print(f"✅ PROVIDED TOKEN MATCHES DATABASE TOKEN\n")
                return True
            else:
                print(f"❌ PROVIDED TOKEN DOESN'T MATCH DATABASE!")
                print(f"   Provided: {token}")
                print(f"   Database: {db_token}\n")
                return False
                
        except Exception as e:
            print(f"❌ Error checking database: {str(e)}\n")
            return False


def test_send_notification(username: str, token: str):
    """Attempt to send a test notification and capture full response"""
    print(f"{'='*60}")
    print("STEP 3: SEND TEST NOTIFICATION")
    print(f"{'='*60}\n")
    
    app = create_app()
    with app.app_context():
        from my_flask_app.app import supabase
        from my_flask_app.app.services.push_notification_service import ExpoPushService
        import requests
        
        # Get user_id
        user_res = supabase.table('profiles') \
            .select('user_id') \
            .eq('username', username) \
            .single() \
            .execute()
        
        if not user_res.data:
            print(f"❌ User not found\n")
            return False
        
        user_id = user_res.data['user_id']
        
        # Prepare notification payload (same as service would send)
        payload = {
            "to": token,
            "title": "🔍 Diagnostic Test",
            "body": "Testing push notification delivery",
            "data": {
                'type': 'diagnostic_test',
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id
            },
            "sound": "default",
            "priority": "high",
            "channelId": "default",
        }
        
        print("📤 Sending notification to Expo API...\n")
        print("Payload being sent:")
        print(json.dumps(payload, indent=2))
        print()
        
        try:
            response = requests.post(
                ExpoPushService.EXPO_PUSH_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip, deflate",
                },
                timeout=10
            )
            
            print(f"HTTP Status Code: {response.status_code}\n")
            
            # Get response
            result = response.json()
            print("📥 Response from Expo API:\n")
            print(json.dumps(result, indent=2))
            print()
            
            # Analyze response
            if response.status_code != 200:
                print(f"❌ Expo API returned status code {response.status_code}")
                if 'errors' in result:
                    print("   Errors:")
                    for error in result.get('errors', []):
                        print(f"   - {error}")
                print()
                return False
            
            # Check the ticket response
            ticket_data = result.get('data', [{}])[0] if isinstance(result.get('data'), list) else result.get('data', {})
            
            print("📋 Ticket Details:")
            print(f"   Status: {ticket_data.get('status')}")
            print(f"   ID: {ticket_data.get('id')}")
            
            if ticket_data.get('status') == 'ok':
                print(f"\n✅ NOTIFICATION ACCEPTED BY EXPO")
                print(f"   Ticket ID: {ticket_data.get('id')}")
                print(f"   This means Expo accepted it and will try to deliver\n")
                return True
            else:
                print(f"\n❌ EXPO REJECTED THE NOTIFICATION")
                error_msg = ticket_data.get('message', 'Unknown error')
                error_detail = ticket_data.get('details', {})
                print(f"   Error: {error_msg}")
                print(f"   Details: {error_detail}\n")
                
                # Analyze specific errors
                if error_detail.get('error') == 'DeviceNotRegistered':
                    print("🔴 DIAGNOSIS: Device is not registered with Expo")
                    print("   - Token might be from a different app/project")
                    print("   - Token might be expired")
                    print("   - Device was uninstalled/token revoked\n")
                    return False
                elif error_detail.get('error') == 'InvalidCredentials':
                    print("🔴 DIAGNOSIS: Invalid credentials")
                    print("   - Backend credentials might be wrong")
                    print("   - Expo project ID might be misconfigured\n")
                    return False
                
                return False
                
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out")
            print("   Expo API is not responding\n")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {str(e)}\n")
            return False
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False


def check_token_lifecycle(username: str):
    """Check when token was registered and if it might be stale"""
    print(f"{'='*60}")
    print("STEP 4: TOKEN LIFECYCLE ANALYSIS")
    print(f"{'='*60}\n")
    
    app = create_app()
    with app.app_context():
        from my_flask_app.app import supabase
        from datetime import datetime, timedelta
        
        user_res = supabase.table('profiles') \
            .select('push_token_updated_at') \
            .eq('username', username) \
            .single() \
            .execute()
        
        if not user_res.data:
            print("❌ User not found\n")
            return
        
        updated_at = user_res.data.get('push_token_updated_at')
        
        if not updated_at:
            print("⚠️  push_token_updated_at is NULL")
            print("   Token registration timestamp was not recorded\n")
            return
        
        # Parse timestamp
        try:
            token_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            now = datetime.now(token_time.tzinfo) if token_time.tzinfo else datetime.utcnow()
            age = now - token_time
            
            print(f"Token registered at: {updated_at}")
            print(f"Current time: {now.isoformat()}")
            print(f"Token age: {age}\n")
            
            if age > timedelta(days=30):
                print(f"⚠️  Token is {age.days} days old")
                print("   Expo tokens can expire after ~30 days of inactivity")
                print("   Consider reinstalling app to get fresh token\n")
            else:
                print(f"✅ Token is relatively fresh ({age.days} days old)\n")
        except Exception as e:
            print(f"⚠️  Could not parse timestamp: {str(e)}\n")


def diagnose_device_issues():
    """Provide guidance on device-side issues"""
    print(f"{'='*60}")
    print("STEP 5: DEVICE-SIDE TROUBLESHOOTING")
    print(f"{'='*60}\n")
    
    print("If Expo accepted the notification (Step 3: ✅) but you didn't receive it:")
    print()
    print("🔹 Check Device Settings:")
    print("   1. Go to Settings → Apps → Adulting")
    print("   2. Tap Permissions")
    print("   3. Find 'Notifications' and make sure it's ✅ ALLOWED\n")
    
    print("🔹 Check App Settings:")
    print("   1. Open Adulting app")
    print("   2. Go to Settings (if available)")
    print("   3. Look for notification permissions/settings")
    print("   4. Make sure notifications are enabled ✅\n")
    
    print("🔹 Check Device Notifications:")
    print("   1. Device notifications might be globally muted")
    print("   2. Check if phone is in 'Do Not Disturb' mode")
    print("   3. Check volume settings\n")
    
    print("🔹 Check Background Restrictions:")
    print("   1. Some phones restrict background app activity")
    print("   2. Go to Settings → Battery/Power Management")
    print("   3. Find Adulting app and check if it's restricted")
    print("   4. Add it to exception list if possible\n")
    
    print("🔹 Network Issues:")
    print("   1. Make sure device has active internet connection")
    print("   2. Push notifications require internet (WiFi or cellular)")
    print("   3. Check if you're behind a restrictive firewall\n")
    
    print("🔹 Last Resort:")
    print("   1. Restart device")
    print("   2. Uninstall and reinstall Adulting app")
    print("   3. Contact Expo support if still not working\n")


def generate_summary(token: str, format_valid: bool, db_registered: bool, notification_sent: bool):
    """Generate diagnostic summary"""
    print(f"{'='*60}")
    print("DIAGNOSTIC SUMMARY")
    print(f"{'='*60}\n")
    
    print("Status of each check:\n")
    print(f"1. Token Format:        {'✅ VALID' if format_valid else '❌ INVALID'}")
    print(f"2. Database Register:   {'✅ FOUND' if db_registered else '❌ NOT FOUND'}")
    print(f"3. Expo Accept:         {'✅ ACCEPTED' if notification_sent else '❌ REJECTED'}")
    print()
    
    if format_valid and db_registered and notification_sent:
        print("🟢 FULL CHAIN WORKING")
        print()
        print("Backend → Expo chain is operational!")
        print("Problem is likely on DEVICE SIDE:")
        print()
        print("Most likely causes:")
        print("  1. ❌ Device notifications are DISABLED in app/system settings")
        print("  2. ❌ Device is in 'Do Not Disturb' mode")
        print("  3. ❌ App has been put in background by OS restrictions")
        print("  4. ❌ Device doesn't have active internet connection")
        print()
        print("Action: Check the device troubleshooting section above ☝️\n")
    
    elif format_valid and db_registered and not notification_sent:
        print("🟡 BACKEND CHAIN BROKEN AT EXPO")
        print()
        print("Token is valid and registered, but Expo rejected it")
        print()
        print("Most likely causes:")
        print("  1. 🔴 Token is from DIFFERENT APP/PROJECT")
        print("  2. 🔴 Token is EXPIRED or INVALID")
        print("  3. 🔴 Backend EXPO CREDENTIALS are WRONG")
        print("  4. 🔴 User uninstalled/reinstalled but used old token")
        print()
        print("Actions:")
        print("  - Reinstall app → opens app → gets NEW token")
        print("  - Then try again")
        print("  - Check Expo dashboard for credential errors\n")
    
    elif format_valid and not db_registered:
        print("🟡 TOKEN NOT IN DATABASE")
        print()
        print("Token format is valid but not registered with backend")
        print()
        print("Most likely cause:")
        print("  1. ❓ Token wasn't properly sent to registration endpoint")
        print()
        print("Actions:")
        print("  - Restart app (it auto-registers token)")
        print("  - Check app logs to verify registration happened")
        print("  - Try opening Settings → manually trigger registration\n")
    
    else:
        print("🔴 TOKEN IS INVALID")
        print()
        print("Token format doesn't match Expo standard")
        print()
        print("Must be: ExponentPushToken[content]\n")


def main():
    parser = argparse.ArgumentParser(
        description='Deep diagnostic analysis for push notification issues'
    )
    parser.add_argument(
        'username',
        nargs='?',
        help='Username to diagnose'
    )
    parser.add_argument(
        '--token',
        type=str,
        help='Push token to test'
    )
    
    args = parser.parse_args()
    
    if not args.username:
        parser.print_help()
        return 1
    
    username = args.username
    token = args.token
    
    if not token:
        print("❌ Token must be provided with --token\n")
        print("Usage:")
        print("  python diagnose_push_notification.py <username> --token 'ExponentPushToken[...]'\n")
        return 1
    
    print("\n" + "="*60)
    print("PUSH NOTIFICATION DIAGNOSTIC ANALYSIS")
    print("="*60)
    print(f"Username: {username}")
    print(f"Token: {token[:40]}...")
    print("="*60 + "\n")
    
    # Run checks
    format_valid, _ = validate_token_format(token)
    db_registered = check_database_registration(username, token)
    notification_sent = test_send_notification(username, token)
    check_token_lifecycle(username)
    diagnose_device_issues()
    
    # Summary
    generate_summary(token, format_valid, db_registered, notification_sent)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
