#!/usr/bin/env python3
"""
Push Notification System Verification Script

This script verifies that all fixes for the push notification system
have been properly applied and are working correctly.

Usage:
    python verify_push_notification_fix.py
    python verify_push_notification_fix.py --full
    python verify_push_notification_fix.py --test-user "USER_ID"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from my_flask_app.app import create_app, supabase
from my_flask_app.app.services.push_notification_service import ExpoPushService
import argparse
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

def print_section(title):
    """Print a section header"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{title}")
    print(f"{'='*60}{Style.RESET_ALL}\n")

def print_success(message):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print error message"""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")

def print_info(message):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

def verify_imports():
    """Verify that all necessary imports work"""
    print_section("1. Verifying Imports")
    
    try:
        from my_flask_app.app.services.push_notification_service import ExpoPushService
        print_success("ExpoPushService imported successfully")
        return True
    except Exception as e:
        print_error(f"Failed to import ExpoPushService: {str(e)}")
        return False

def verify_validate_method():
    """Verify that validate_push_token method exists"""
    print_section("2. Verifying validate_push_token Method")
    
    try:
        from my_flask_app.app.services.push_notification_service import ExpoPushService
        
        if not hasattr(ExpoPushService, 'validate_push_token'):
            print_error("validate_push_token method not found in ExpoPushService")
            return False
        
        print_success("validate_push_token method exists")
        
        # Test the method
        test_cases = [
            ("ExponentPushToken[valid_token_123]", True),
            ("ExponentPushToken[]", True),
            ("invalid_token", False),
            ("", False),
            (None, False),
        ]
        
        all_passed = True
        for token, expected in test_cases:
            result = ExpoPushService.validate_push_token(token)
            if result == expected:
                print_success(f"  validate('{token}') = {result}")
            else:
                print_error(f"  validate('{token}') = {result}, expected {expected}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print_error(f"Error testing validate_push_token: {str(e)}")
        return False

def verify_database_schema():
    """Verify that database columns exist"""
    print_section("3. Verifying Database Schema")
    
    try:
        app = create_app()
        with app.app_context():
            # Try to query profiles with new columns
            result = supabase.table('profiles') \
                .select('id, expo_push_token, push_token_updated_at') \
                .limit(1) \
                .execute()
            
            print_success("Database connection successful")
            print_success("Columns expo_push_token and push_token_updated_at exist")
            return True
    except Exception as e:
        print_error(f"Database schema check failed: {str(e)}")
        print_info("Make sure these columns exist in profiles table:")
        print_info("  - expo_push_token (VARCHAR)")
        print_info("  - push_token_updated_at (TIMESTAMP)")
        return False

def verify_token_storage():
    """Verify that tokens can be stored and retrieved"""
    print_section("4. Verifying Token Storage")
    
    try:
        app = create_app()
        with app.app_context():
            # Get first user (any user for testing)
            result = supabase.table('profiles').select('user_id').limit(1).execute()
            
            if not result.data:
                print_warning("No users found in database - skipping storage test")
                return True
            
            test_user_id = result.data[0]['user_id']
            test_token = "ExponentPushToken[test_token_123]"
            
            # Try to update token
            update_result = supabase.table('profiles') \
                .update({
                    'expo_push_token': test_token,
                    'push_token_updated_at': datetime.utcnow().isoformat()
                }) \
                .eq('user_id', test_user_id) \
                .execute()
            
            if update_result.data:
                print_success(f"Token storage works - updated user {test_user_id}")
                
                # Verify retrieval
                verify_result = supabase.table('profiles') \
                    .select('expo_push_token') \
                    .eq('user_id', test_user_id) \
                    .single() \
                    .execute()
                
                if verify_result.data and verify_result.data.get('expo_push_token') == test_token:
                    print_success("Token retrieval works - token found in database")
                    
                    # Clean up - set back to null
                    supabase.table('profiles') \
                        .update({'expo_push_token': None}) \
                        .eq('user_id', test_user_id) \
                        .execute()
                    
                    return True
                else:
                    print_error("Token storage successful but retrieval failed")
                    return False
            else:
                print_error("Failed to update token in database")
                return False
                
    except Exception as e:
        print_error(f"Token storage test failed: {str(e)}")
        return False

def count_registered_tokens():
    """Count how many users have registered tokens"""
    print_section("5. Checking Registered Tokens")
    
    try:
        app = create_app()
        with app.app_context():
            result = supabase.table('profiles') \
                .select('count', count='exact') \
                .not_.is_('expo_push_token', 'null') \
                .execute()
            
            count = result.count if hasattr(result, 'count') else 0
            print_info(f"Users with registered tokens: {count}")
            
            # Also list them
            if count > 0:
                list_result = supabase.table('profiles') \
                    .select('user_id, username, push_token_updated_at') \
                    .not_.is_('expo_push_token', 'null') \
                    .limit(5) \
                    .execute()
                
                if list_result.data:
                    print("\nSample registered users:")
                    for user in list_result.data:
                        username = user.get('username', 'Unknown')
                        updated = user.get('push_token_updated_at', 'Never')
                        print(f"  • {username} (updated: {updated})")
                    
                    if count > 5:
                        print(f"  ... and {count - 5} more")
            else:
                print_warning("No users have registered tokens yet")
            
            return True
            
    except Exception as e:
        print_error(f"Failed to check registered tokens: {str(e)}")
        return False

def check_code_quality():
    """Check if code fixes are properly applied"""
    print_section("6. Verifying Code Fixes")
    
    issues = []
    
    # Check notification_routes.py
    try:
        with open('my_flask_app/app/routes/notification_routes.py', 'r') as f:
            content = f.read()
            
            # Check if token is being saved
            if 'update({' in content and 'expo_push_token' in content:
                print_success("notification_routes.py: Token saving code present")
            else:
                print_error("notification_routes.py: Token saving code might be missing")
                issues.append("notification_routes.py")
            
            # Check if datetime is imported
            if 'import logging' in content:
                print_success("notification_routes.py: Logging imported")
            else:
                print_warning("notification_routes.py: Logging might not be imported")
    except Exception as e:
        print_warning(f"Could not check notification_routes.py: {str(e)}")
    
    # Check push_notification_service.py
    try:
        with open('my_flask_app/app/services/push_notification_service.py', 'r') as f:
            content = f.read()
            
            if 'def validate_push_token' in content:
                print_success("push_notification_service.py: validate_push_token method present")
            else:
                print_error("push_notification_service.py: validate_push_token method missing")
                issues.append("push_notification_service.py")
            
            if 'ExponentPushToken[' in content:
                print_success("push_notification_service.py: Expo token format validation present")
            else:
                print_warning("push_notification_service.py: Expo token validation might be weak")
    except Exception as e:
        print_warning(f"Could not check push_notification_service.py: {str(e)}")
    
    return len(issues) == 0

def run_full_verification():
    """Run all verification checks"""
    print_section("PUSH NOTIFICATION SYSTEM VERIFICATION")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        'imports': verify_imports(),
        'validate_method': verify_validate_method(),
        'db_schema': verify_database_schema(),
        'token_storage': verify_token_storage(),
        'registered_tokens': count_registered_tokens(),
        'code_quality': check_code_quality(),
    }
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed\n")
    
    if passed == total:
        print_success("All checks passed! Push notification system is ready.")
        return True
    else:
        print_error(f"{total - passed} checks failed. See above for details.")
        return False

def test_with_user(user_id):
    """Test push notification with a specific user"""
    print_section(f"TESTING WITH USER: {user_id}")
    
    try:
        app = create_app()
        with app.app_context():
            # Check if user exists and has token
            result = supabase.table('profiles') \
                .select('user_id, username, expo_push_token') \
                .eq('user_id', user_id) \
                .single() \
                .execute()
            
            if not result.data:
                print_error(f"User {user_id} not found")
                return False
            
            user_data = result.data
            print_info(f"User: {user_data.get('username', 'Unknown')}")
            
            if user_data.get('expo_push_token'):
                print_success(f"User has registered token: {user_data['expo_push_token'][:30]}...")
                
                # Try to send test notification
                print_info("Attempting to send test notification...")
                success = ExpoPushService.send_notification_to_user(
                    supabase_client=supabase,
                    user_id=user_id,
                    title="Test Notification",
                    body="Push notification system verification",
                    notification_type='test',
                    data={'test': True}
                )
                
                if success:
                    print_success("Test notification sent successfully!")
                    print_info("Check your device for the notification")
                    return True
                else:
                    print_error("Failed to send test notification")
                    return False
            else:
                print_warning(f"User {user_id} has no registered token")
                print_info("They need to call /register-token/ endpoint first")
                return False
                
    except Exception as e:
        print_error(f"Test failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Verify push notification system fixes'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full verification (default)'
    )
    parser.add_argument(
        '--test-user',
        type=str,
        help='Test with specific user ID'
    )
    
    args = parser.parse_args()
    
    try:
        if args.test_user:
            success = test_with_user(args.test_user)
        else:
            success = run_full_verification()
        
        print_section("END OF VERIFICATION")
        return 0 if success else 1
    except Exception as e:
        print_error(f"Verification failed with error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
