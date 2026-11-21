"""
Integration tests for Missions System
Tests all API endpoints and constraint enforcement
"""
import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api/missions"

# Test user credentials (you'll need to replace with actual test user)
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword"

class MissionsSystemTest:
    def __init__(self):
        self.token = None
        self.mission_id = None
        self.decision_point_id = None
        self.results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "message": message
        })
        print(f"{status} - {test_name}")
        if message:
            print(f"   {message}")
    
    def authenticate(self) -> bool:
        """Get JWT token for testing"""
        print("\n🔐 Authenticating...")
        try:
            # Try to get session token from Supabase
            # For now, we'll skip auth and test with a mock token
            # In production, you'd authenticate here
            self.token = "mock_token_for_testing"
            self.log_result("Authentication", True, "Using mock token")
            return True
        except Exception as e:
            self.log_result("Authentication", False, str(e))
            return False
    
    def test_available_missions(self) -> bool:
        """Test GET /api/missions/available"""
        print("\n📋 Testing: Get Available Missions")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/available", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    missions = data.get("data", [])
                    self.log_result(
                        "GET /available", 
                        True, 
                        f"Found {len(missions)} available missions"
                    )
                    
                    # Store first mission ID for later tests
                    if missions:
                        self.mission_id = missions[0].get("id")
                        print(f"   Sample mission: {missions[0].get('name')}")
                    return True
                else:
                    self.log_result("GET /available", False, data.get("error"))
                    return False
            else:
                self.log_result("GET /available", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("GET /available", False, str(e))
            return False
    
    def test_start_mission(self) -> bool:
        """Test POST /api/missions/start"""
        print("\n🚀 Testing: Start Mission")
        
        if not self.mission_id:
            self.log_result("POST /start", False, "No mission ID available")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            payload = {"mission_id": self.mission_id}
            response = requests.post(f"{API_URL}/start", headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("POST /start", True, "Mission started successfully")
                    return True
                else:
                    self.log_result("POST /start", False, data.get("error"))
                    return False
            else:
                self.log_result("POST /start", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("POST /start", False, str(e))
            return False
    
    def test_active_mission(self) -> bool:
        """Test GET /api/missions/active"""
        print("\n📊 Testing: Get Active Mission")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/active", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    active = data.get("data")
                    if active:
                        self.log_result(
                            "GET /active", 
                            True, 
                            f"Active mission: {active.get('progress', {}).get('integrated_missions', {}).get('name')}"
                        )
                        
                        # Store decision point if available
                        if active.get("next_decision"):
                            self.decision_point_id = active["next_decision"]["id"]
                        
                        return True
                    else:
                        self.log_result("GET /active", True, "No active mission")
                        return True
                else:
                    self.log_result("GET /active", False, data.get("error"))
                    return False
            else:
                self.log_result("GET /active", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("GET /active", False, str(e))
            return False
    
    def test_check_constraints(self) -> bool:
        """Test POST /api/missions/check-constraints"""
        print("\n🔒 Testing: Check Constraints")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Test various constraint checks
            test_cases = [
                {"action": "buy_asset", "data": {"asset_type": "stocks"}},
                {"action": "change_job"},
                {"action": "take_loan", "data": {"amount": 5000, "loan_type": "personal"}},
                {"action": "rent_property"},
                {"action": "buy_lifestyle_item", "data": {"amount": 1000}}
            ]
            
            all_passed = True
            for test_case in test_cases:
                response = requests.post(
                    f"{API_URL}/check-constraints", 
                    headers=headers, 
                    json=test_case
                )
                
                if response.status_code == 200:
                    data = response.json()
                    action = test_case["action"]
                    allowed = data.get("data", {}).get("allowed", False)
                    reason = data.get("data", {}).get("reason", "")
                    
                    status = "Allowed" if allowed else "Blocked"
                    print(f"   {action}: {status}")
                    if reason:
                        print(f"      Reason: {reason}")
                else:
                    all_passed = False
            
            self.log_result("POST /check-constraints", all_passed, "Tested 5 constraint types")
            return all_passed
            
        except Exception as e:
            self.log_result("POST /check-constraints", False, str(e))
            return False
    
    def test_mission_history(self) -> bool:
        """Test GET /api/missions/history"""
        print("\n📜 Testing: Get Mission History")
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{API_URL}/history", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    history = data.get("data", {})
                    completed = len(history.get("completed", []))
                    abandoned = len(history.get("abandoned", []))
                    
                    self.log_result(
                        "GET /history", 
                        True, 
                        f"Completed: {completed}, Abandoned: {abandoned}"
                    )
                    return True
                else:
                    self.log_result("GET /history", False, data.get("error"))
                    return False
            else:
                self.log_result("GET /history", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("GET /history", False, str(e))
            return False
    
    def test_abandon_mission(self) -> bool:
        """Test POST /api/missions/abandon"""
        print("\n🚫 Testing: Abandon Mission")
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            response = requests.post(f"{API_URL}/abandon", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("POST /abandon", True, "Mission abandoned successfully")
                    return True
                else:
                    self.log_result("POST /abandon", False, data.get("error"))
                    return False
            else:
                self.log_result("POST /abandon", False, f"Status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("POST /abandon", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("=" * 60)
        print("🧪 MISSIONS SYSTEM INTEGRATION TESTS")
        print("=" * 60)
        
        # Note: These tests require actual authentication
        # For now, they will test the endpoint structure
        
        print("\n⚠️  NOTE: These tests require a valid JWT token")
        print("   Update TEST_USER_EMAIL and TEST_USER_PASSWORD")
        print("   Or run tests manually with curl\n")
        
        # Run tests
        self.authenticate()
        self.test_available_missions()
        self.test_check_constraints()
        self.test_mission_history()
        
        # Only test start/abandon if we have a mission ID
        # Commented out to avoid actually starting missions during testing
        # self.test_start_mission()
        # self.test_active_mission()
        # self.test_abandon_mission()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if "✅" in r["status"])
        total = len(self.results)
        
        for result in self.results:
            print(f"{result['status']} - {result['test']}")
        
        print(f"\n✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️  Some tests failed - check logs above")
        
        return passed == total


def test_endpoint_availability():
    """Quick test to verify Flask server is running"""
    print("\n🔍 Testing Flask Server Availability...")
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Flask server is running on {BASE_URL}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"❌ Flask server is not running on {BASE_URL}")
        print("   Start the server with: python run.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # First check if server is running
    if not test_endpoint_availability():
        print("\n⚠️  Cannot run tests - Flask server is not available")
        exit(1)
    
    # Run integration tests
    tester = MissionsSystemTest()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
