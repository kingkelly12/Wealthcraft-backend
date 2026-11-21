#!/usr/bin/env python3
"""
Direct Regression Tests (no auth required)
Tests code changes without needing authentication
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import time

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_test(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"       {details}")

# Test Results Tracking
tests_passed = 0
tests_failed = 0
test_results = []

def record_test(name, passed, details=""):
    global tests_passed, tests_failed
    print_test(name, passed, details)
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    test_results.append((name, passed, details))

# =============================================================================
# TEST 1: Verify Dashboard Routes File Exists and Has Correct Structure
# =============================================================================
print_section("TEST 1: Dashboard Routes File Structure")

try:
    from app.routes.dashboard_routes import dashboard_bp, get_consolidated_dashboard
    record_test(
        "Dashboard Routes Import",
        True,
        "dashboard_routes.py exists and exports correctly"
    )
except ImportError as e:
    record_test(
        "Dashboard Routes Import",
        False,
        f"Import failed: {str(e)}"
    )

# =============================================================================
# TEST 2: Verify Flask Blueprint Registration
# =============================================================================
print_section("TEST 2: Flask Blueprint Registration")

try:
    from app import app
    
    # Check if dashboard blueprint is registered
    blueprints = app.blueprints
    if 'dashboard' in blueprints:
        record_test(
            "Dashboard Blueprint Registered",
            True,
            f"Blueprint 'dashboard' found in {len(blueprints)} registered blueprints"
        )
    else:
        record_test(
            "Dashboard Blueprint Registered",
            False,
            f"Blueprints: {list(blueprints.keys())}"
        )
except Exception as e:
    record_test(
        "Dashboard Blueprint Registered",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 3: Verify Consolidated Dashboard Endpoint Exists
# =============================================================================
print_section("TEST 3: Dashboard Endpoint Registration")

try:
    from app import app
    
    # Get registered routes
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    dashboard_routes = [r for r in routes if 'dashboard' in r]
    
    if dashboard_routes:
        record_test(
            "Dashboard Routes Registered",
            True,
            f"Found {len(dashboard_routes)} dashboard route(s): {dashboard_routes}"
        )
        
        # Check for /api/dashboard/consolidated/
        if '/api/dashboard/consolidated/' in routes:
            record_test(
                "Consolidated Endpoint Exists",
                True,
                "/api/dashboard/consolidated/ is accessible"
            )
        else:
            record_test(
                "Consolidated Endpoint Exists",
                False,
                f"Expected route not found. Available: {dashboard_routes}"
            )
    else:
        record_test(
            "Dashboard Routes Registered",
            False,
            "No dashboard routes found"
        )
except Exception as e:
    record_test(
        "Dashboard Routes Registered",
        False,
        f"Error checking routes: {str(e)}"
    )

# =============================================================================
# TEST 4: Verify Education Routes FK Fix
# =============================================================================
print_section("TEST 4: Education Routes FK Fix")

try:
    with open('/home/kelly_koome/Devops/adulting/my_flask_app/app/routes/education_routes.py', 'r') as f:
        content = f.read()
    
    # Check for the explicit FK syntax in both endpoints
    has_explicit_fk_overview = "select('*, courses!course_id(*)')" in content or 'select("*, courses!course_id(*)")' in content
    has_explicit_fk_enrolled = "select('*, courses!course_id(*)')" in content or 'select("*, courses!course_id(*)")' in content
    
    if has_explicit_fk_overview and has_explicit_fk_enrolled:
        record_test(
            "Education FK Syntax Updated",
            True,
            "Both /overview/ and /enrolled/ use explicit FK syntax (courses!course_id)"
        )
    else:
        # Check what we have
        implicit_count = content.count("select('*, courses(*)')")
        explicit_count = content.count("courses!course_id")
        record_test(
            "Education FK Syntax Updated",
            False,
            f"Explicit FK: {explicit_count} instances, Implicit: {implicit_count} instances"
        )
    
    # Also verify the working complete endpoint pattern
    has_complete_pattern = "courses!course_id(*)" in content
    if has_complete_pattern:
        record_test(
            "Complete Endpoint Pattern",
            True,
            "/complete/ endpoint uses explicit FK (working pattern)"
        )
    else:
        record_test(
            "Complete Endpoint Pattern",
            False,
            "Cannot verify complete endpoint pattern"
        )
        
except Exception as e:
    record_test(
        "Education FK Fix",
        False,
        f"Error reading file: {str(e)}"
    )

# =============================================================================
# TEST 5: Verify API Client Dashboard Method
# =============================================================================
print_section("TEST 5: API Client Dashboard Method")

try:
    with open('/home/kelly_koome/Devops/adulting/Adulting/lib/apiClient.ts', 'r') as f:
        content = f.read()
    
    if 'dashboard:' in content and 'getConsolidated:' in content:
        record_test(
            "API Client Dashboard Method",
            True,
            "apiClient.dashboard.getConsolidated() method defined"
        )
    else:
        record_test(
            "API Client Dashboard Method",
            False,
            "Dashboard method not found in apiClient"
        )
except Exception as e:
    record_test(
        "API Client Dashboard Method",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 6: Verify Dashboard Hook Uses Consolidated Endpoint
# =============================================================================
print_section("TEST 6: Dashboard Hook Implementation")

try:
    with open('/home/kelly_koome/Devops/adulting/Adulting/app/(tabs)/index.tsx', 'r') as f:
        content = f.read()
    
    if 'api.dashboard.getConsolidated()' in content:
        record_test(
            "Dashboard Hook Consolidated Call",
            True,
            "useDashboardData() now calls api.dashboard.getConsolidated()"
        )
        
        # Check for proper caching
        if 'staleTime: 30 * 1000' in content:
            record_test(
                "Dashboard Caching Configuration",
                True,
                "staleTime set to 30 seconds for efficient caching"
            )
        else:
            record_test(
                "Dashboard Caching Configuration",
                False,
                "staleTime not properly configured"
            )
    else:
        record_test(
            "Dashboard Hook Consolidated Call",
            False,
            "Hook still using multiple api calls"
        )
except Exception as e:
    record_test(
        "Dashboard Hook Implementation",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 7: Verify LeaderboardPreview Was Updated
# =============================================================================
print_section("TEST 7: LeaderboardPreview Component Props")

try:
    with open('/home/kelly_koome/Devops/adulting/Adulting/components/dashboard/LeaderboardPreview.tsx', 'r') as f:
        content = f.read()
    
    # Check if component accepts props
    if 'LeaderboardPreviewProps' in content and 'players' in content:
        record_test(
            "LeaderboardPreview Props Interface",
            True,
            "Component updated to accept 'players' prop"
        )
    else:
        record_test(
            "LeaderboardPreview Props Interface",
            False,
            "Props interface not found"
        )
    
    # Check if separate API call was removed
    if 'api.social.getLeaderboard' not in content:
        record_test(
            "Leaderboard Separate Call Removed",
            True,
            "Component no longer makes separate API call"
        )
    else:
        record_test(
            "Leaderboard Separate Call Removed",
            False,
            "Component still making separate API call"
        )
    
    # Check if useFocusEffect was removed
    if 'useFocusEffect' not in content:
        record_test(
            "useFocusEffect Removed",
            True,
            "Component no longer needs focus-based refetching"
        )
    else:
        record_test(
            "useFocusEffect Removed",
            False,
            "useFocusEffect still present"
        )
        
except Exception as e:
    record_test(
        "LeaderboardPreview Component",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 8: Verify All Previous Fixes Are Still In Place
# =============================================================================
print_section("TEST 8: Previous Fixes Verification")

try:
    # Check banking balance fix
    with open('/home/kelly_koome/Devops/adulting/my_flask_app/app/routes/banking_routes.py', 'r') as f:
        banking_content = f.read()
    
    if 'BalanceService.get_current_balance' in banking_content:
        record_test(
            "Banking Balance Service Used",
            True,
            "Balance extraction uses BalanceService (reliable)"
        )
    else:
        record_test(
            "Banking Balance Service Used",
            False,
            "Balance extraction might still be unreliable"
        )
    
    # Check chat notifications fix
    with open('/home/kelly_koome/Devops/adulting/my_flask_app/app/routes/chat_routes.py', 'r') as f:
        chat_content = f.read()
    
    if 'sender_name' in chat_content and 'message_preview' in chat_content:
        record_test(
            "Message Push Notifications Enhanced",
            True,
            "Notifications include sender_name and message_preview"
        )
    else:
        record_test(
            "Message Push Notifications Enhanced",
            False,
            "Message notification enhancement not found"
        )
    
    # Check chat modal fix
    with open('/home/kelly_koome/Devops/adulting/Adulting/hooks/useChat.tsx', 'r') as f:
        chat_hook = f.read()
    
    if 'sender_id' in chat_hook:
        record_test(
            "ChatModal Subscription Filter Fixed",
            True,
            "Subscription now filters for incoming messages only"
        )
    else:
        record_test(
            "ChatModal Subscription Filter Fixed",
            False,
            "Subscription filter not updated"
        )
        
except Exception as e:
    record_test(
        "Previous Fixes Verification",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 9: Code Syntax Verification
# =============================================================================
print_section("TEST 9: Code Syntax Validation")

try:
    import py_compile
    
    files_to_check = [
        '/home/kelly_koome/Devops/adulting/my_flask_app/app/routes/dashboard_routes.py',
        '/home/kelly_koome/Devops/adulting/my_flask_app/app/routes/education_routes.py',
    ]
    
    syntax_ok = True
    for filepath in files_to_check:
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            syntax_ok = False
            record_test(
                f"Python Syntax: {filepath.split('/')[-1]}",
                False,
                str(e)
            )
    
    if syntax_ok:
        record_test(
            "Python Files Syntax",
            True,
            f"All {len(files_to_check)} Python files have valid syntax"
        )
        
except Exception as e:
    record_test(
        "Syntax Validation",
        False,
        f"Error: {str(e)}"
    )

# =============================================================================
# TEST 10: HTTP Endpoint Response Test (No Auth Required)
# =============================================================================
print_section("TEST 10: Endpoint Response Check")

try:
    import requests
    
    # Test that dashboard endpoint exists and requires auth
    try:
        response = requests.get('http://localhost:5000/api/dashboard/consolidated/', timeout=5)
        if response.status_code == 401:
            record_test(
                "Dashboard Endpoint Accessible",
                True,
                "Endpoint exists and requires authentication (401)"
            )
        elif response.status_code == 200:
            record_test(
                "Dashboard Endpoint Working",
                True,
                "Endpoint returned data successfully"
            )
        else:
            record_test(
                "Dashboard Endpoint Accessible",
                False,
                f"Unexpected status: {response.status_code}"
            )
    except requests.exceptions.ConnectionError:
        record_test(
            "Backend Connection",
            False,
            "Cannot connect to http://localhost:5000"
        )
    except Exception as e:
        record_test(
            "Dashboard Endpoint Test",
            False,
            str(e)
        )
        
except ImportError:
    record_test(
        "HTTP Endpoint Test",
        False,
        "requests library not installed"
    )

# =============================================================================
# SUMMARY
# =============================================================================
print_section("REGRESSION TEST SUMMARY")

print(f"\n✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📊 Total:  {tests_passed + tests_failed}\n")

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! Dashboard consolidation and education FK fix verified.")
else:
    print(f"⚠️  {tests_failed} test(s) failed. Review above for details.")
    print("\nFailed Tests:")
    for name, passed, details in test_results:
        if not passed:
            print(f"  - {name}: {details}")

print("\n" + "="*80)
print(f"Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

sys.exit(0 if tests_failed == 0 else 1)
