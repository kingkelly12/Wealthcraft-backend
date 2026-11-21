#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite for Dashboard Consolidation
Tests API call reduction, response times, and data integrity
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Configuration
BACKEND_URL = "http://localhost:5000"
TEST_USER_ID = "test-user-123"  # Will need to be replaced with real user ID from auth

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        
    def add_test(self, name: str, passed: bool, details: str = "", duration: float = 0):
        self.tests.append({
            "name": name,
            "passed": passed,
            "details": details,
            "duration_ms": round(duration * 1000, 2)
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*80)
        print("REGRESSION TEST RESULTS")
        print("="*80)
        for test in self.tests:
            status = "✅ PASS" if test["passed"] else "❌ FAIL"
            print(f"\n{status}: {test['name']} ({test['duration_ms']}ms)")
            if test["details"]:
                print(f"   {test['details']}")
        
        print("\n" + "-"*80)
        print(f"Total: {self.passed + self.failed} tests | Passed: {self.passed} | Failed: {self.failed}")
        print("="*80 + "\n")
        
        return self.failed == 0

results = TestResults()

def get_auth_token() -> str:
    """Get JWT token from Supabase (for testing purposes)"""
    # This would need to be set via environment variable or from a login endpoint
    # For now, we'll read from Supabase client if available
    try:
        import os
        return os.getenv("SUPABASE_JWT", "")
    except:
        return ""

def test_dashboard_consolidated_endpoint():
    """Test 1: Consolidated dashboard endpoint returns all data in one call"""
    print("\n📊 TEST 1: Consolidated Dashboard Endpoint")
    print("-" * 60)
    
    start_time = time.time()
    try:
        # Note: This needs a real JWT token
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.get(
            f"{BACKEND_URL}/api/dashboard/consolidated/",
            headers=headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 401:
            results.add_test(
                "Dashboard Consolidated Endpoint",
                False,
                "Auth required - no JWT token available"
            )
            return None
        
        if response.status_code != 200:
            results.add_test(
                "Dashboard Consolidated Endpoint",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return None
        
        data = response.json()
        
        # Verify response structure
        required_fields = ['success', 'data']
        if not all(field in data for field in required_fields):
            results.add_test(
                "Dashboard Consolidated Endpoint",
                False,
                f"Missing fields. Got: {list(data.keys())}"
            )
            return None
        
        dashboard_data = data.get('data', {})
        expected_categories = ['profile', 'account_balance', 'portfolio', 'liabilities', 'jobs', 'rental', 'missions', 'leaderboard']
        
        missing_categories = [cat for cat in expected_categories if cat not in dashboard_data]
        
        if missing_categories:
            results.add_test(
                "Dashboard Consolidated Endpoint",
                False,
                f"Missing data categories: {missing_categories}"
            )
            return None
        
        results.add_test(
            "Dashboard Consolidated Endpoint",
            True,
            f"All 8 data categories present. Response time: {duration:.2f}s",
            duration
        )
        
        return dashboard_data
        
    except requests.exceptions.Timeout:
        results.add_test(
            "Dashboard Consolidated Endpoint",
            False,
            "Request timeout (>10s)"
        )
        return None
    except Exception as e:
        results.add_test(
            "Dashboard Consolidated Endpoint",
            False,
            f"Exception: {str(e)[:100]}"
        )
        return None

def test_dashboard_data_integrity(dashboard_data):
    """Test 2: Verify dashboard data has expected structure"""
    print("\n✔️ TEST 2: Dashboard Data Integrity")
    print("-" * 60)
    
    if not dashboard_data:
        results.add_test("Profile Data", False, "No dashboard data available")
        return False
    
    all_passed = True
    
    # Test profile
    if 'profile' in dashboard_data and dashboard_data['profile']:
        profile = dashboard_data['profile']
        required_profile_fields = ['id', 'username', 'account_balance']
        missing = [f for f in required_profile_fields if f not in profile]
        if missing:
            results.add_test("Profile Data", False, f"Missing fields: {missing}")
            all_passed = False
        else:
            results.add_test("Profile Data", True, f"Profile complete with {len(profile)} fields")
    else:
        results.add_test("Profile Data", False, "Profile is empty or missing")
        all_passed = False
    
    # Test portfolio (assets)
    portfolio = dashboard_data.get('portfolio', [])
    if isinstance(portfolio, list):
        results.add_test("Portfolio Data", True, f"{len(portfolio)} assets loaded")
    else:
        results.add_test("Portfolio Data", False, "Portfolio is not a list")
        all_passed = False
    
    # Test liabilities
    liabilities = dashboard_data.get('liabilities', [])
    if isinstance(liabilities, list):
        results.add_test("Liabilities Data", True, f"{len(liabilities)} liabilities loaded")
    else:
        results.add_test("Liabilities Data", False, "Liabilities is not a list")
        all_passed = False
    
    # Test jobs
    jobs = dashboard_data.get('jobs', [])
    if isinstance(jobs, list):
        results.add_test("Jobs Data", True, f"{len(jobs)} jobs loaded")
    else:
        results.add_test("Jobs Data", False, "Jobs is not a list")
        all_passed = False
    
    # Test missions
    missions = dashboard_data.get('missions', {})
    if isinstance(missions, dict) and 'active_count' in missions:
        active = missions.get('active_count', 0)
        results.add_test("Missions Data", True, f"{active} active missions")
    else:
        results.add_test("Missions Data", False, "Missions structure invalid")
        all_passed = False
    
    # Test leaderboard
    leaderboard = dashboard_data.get('leaderboard', [])
    if isinstance(leaderboard, list):
        results.add_test("Leaderboard Data", True, f"{len(leaderboard)} leaderboard entries (target: 5)")
        if len(leaderboard) > 5:
            results.add_test("Leaderboard Limit", False, f"Should be max 5, got {len(leaderboard)}")
            all_passed = False
        elif len(leaderboard) <= 5:
            results.add_test("Leaderboard Limit", True, "Within 5-player limit")
    else:
        results.add_test("Leaderboard Data", False, "Leaderboard is not a list")
        all_passed = False
    
    return all_passed

def test_education_overview():
    """Test 3: Education overview endpoint (FK fix verification)"""
    print("\n🎓 TEST 3: Education Overview Endpoint")
    print("-" * 60)
    
    start_time = time.time()
    try:
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.get(
            f"{BACKEND_URL}/api/education/overview/",
            headers=headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 401:
            results.add_test(
                "Education Overview",
                False,
                "Auth required - no JWT token available"
            )
            return False
        
        if response.status_code != 200:
            results.add_test(
                "Education Overview",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return False
        
        data = response.json()
        if data.get('success') and 'data' in data:
            edu_data = data['data']
            available = edu_data.get('available', [])
            enrolled = edu_data.get('enrolled', [])
            
            results.add_test(
                "Education Overview",
                True,
                f"{len(available)} available courses, {len(enrolled)} enrolled",
                duration
            )
            return True
        else:
            results.add_test(
                "Education Overview",
                False,
                "Response missing success or data field"
            )
            return False
            
    except Exception as e:
        results.add_test(
            "Education Overview",
            False,
            f"Exception: {str(e)[:100]}"
        )
        return False

def test_education_enrolled():
    """Test 4: Education enrolled endpoint (FK fix verification)"""
    print("\n📚 TEST 4: Education Enrolled Endpoint")
    print("-" * 60)
    
    start_time = time.time()
    try:
        headers = {"Authorization": f"Bearer {get_auth_token()}"}
        response = requests.get(
            f"{BACKEND_URL}/api/education/enrolled/",
            headers=headers,
            timeout=10
        )
        duration = time.time() - start_time
        
        if response.status_code == 401:
            results.add_test(
                "Education Enrolled",
                False,
                "Auth required - no JWT token available"
            )
            return False
        
        if response.status_code != 200:
            results.add_test(
                "Education Enrolled",
                False,
                f"Status {response.status_code}: {response.text[:200]}"
            )
            return False
        
        data = response.json()
        if data.get('success') and isinstance(data.get('data'), list):
            enrolled = data['data']
            
            # Check if course details are joined in
            has_course_details = all('courses' in item for item in enrolled if enrolled)
            
            detail = f"{len(enrolled)} courses enrolled"
            if enrolled and has_course_details:
                detail += " with course details joined"
            
            results.add_test(
                "Education Enrolled",
                True,
                detail,
                duration
            )
            return True
        else:
            results.add_test(
                "Education Enrolled",
                False,
                "Response missing success or data field"
            )
            return False
            
    except Exception as e:
        results.add_test(
            "Education Enrolled",
            False,
            f"Exception: {str(e)[:100]}"
        )
        return False

def test_load_time_improvement():
    """Test 5: Verify load time improvement (target: 2-3s vs 8+s)"""
    print("\n⚡ TEST 5: Load Time Performance")
    print("-" * 60)
    
    # Measure multiple calls to get average
    times = []
    for i in range(3):
        start = time.time()
        try:
            headers = {"Authorization": f"Bearer {get_auth_token()}"}
            response = requests.get(
                f"{BACKEND_URL}/api/dashboard/consolidated/",
                headers=headers,
                timeout=10
            )
            if response.status_code in [200, 401]:
                times.append(time.time() - start)
        except:
            pass
    
    if times:
        avg_time = sum(times) / len(times)
        target_max = 3.0  # 3 seconds is acceptable
        
        if avg_time <= target_max:
            results.add_test(
                "Dashboard Load Time",
                True,
                f"Average: {avg_time:.2f}s (target: ≤{target_max}s) ✓",
                avg_time
            )
            return True
        else:
            results.add_test(
                "Dashboard Load Time",
                False,
                f"Average: {avg_time:.2f}s (target: ≤{target_max}s) ✗"
            )
            return False
    else:
        results.add_test(
            "Dashboard Load Time",
            False,
            "Could not measure load time (auth issue)"
        )
        return False

def check_backend_running():
    """Verify Flask backend is running"""
    print("\n🔍 PRE-TEST: Checking Backend Connection")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        print(f"✓ Backend is running at {BACKEND_URL}")
        return True
    except:
        print(f"❌ Backend not responding at {BACKEND_URL}")
        print(f"   Make sure Flask is running: python /home/kelly_koome/Devops/adulting/my_flask_app/run.py")
        return False

def main():
    print("\n" + "="*80)
    print("ADULTING APP - REGRESSION TEST SUITE")
    print("Testing Dashboard Consolidation & Education FK Fix")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Pre-flight check
    if not check_backend_running():
        print("\n⚠️  Cannot proceed without backend. Please start Flask server.")
        sys.exit(1)
    
    print("\n📋 Running tests...")
    
    # Run tests
    dashboard_data = test_dashboard_consolidated_endpoint()
    
    if dashboard_data:
        test_dashboard_data_integrity(dashboard_data)
        test_load_time_improvement()
    
    test_education_overview()
    test_education_enrolled()
    
    # Print results
    success = results.print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
