"""
Test script for mentor API routes
Run this to verify the endpoints work correctly
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
# You'll need to get a valid JWT token from your Supabase auth
AUTH_TOKEN = "YOUR_JWT_TOKEN_HERE"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_mentors():
    """Test GET /api/social/mentors"""
    print("\n=== Testing GET /api/social/mentors ===")
    response = requests.get(f"{BASE_URL}/api/social/mentors")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_interactions():
    """Test GET /api/social/interactions"""
    print("\n=== Testing GET /api/social/interactions ===")
    response = requests.get(
        f"{BASE_URL}/api/social/interactions",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mark_as_read(interaction_id):
    """Test PUT /api/social/interactions/<id>/read"""
    print(f"\n=== Testing PUT /api/social/interactions/{interaction_id}/read ===")
    response = requests.put(
        f"{BASE_URL}/api/social/interactions/{interaction_id}/read",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_mark_advice_followed(interaction_id):
    """Test POST /api/social/interactions/<id>/action"""
    print(f"\n=== Testing POST /api/social/interactions/{interaction_id}/action ===")
    response = requests.post(
        f"{BASE_URL}/api/social/interactions/{interaction_id}/action",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_mentor_interactions(mentor_id):
    """Test GET /api/mentors/<mentor_id>/interactions"""
    print(f"\n=== Testing GET /api/mentors/{mentor_id}/interactions ===")
    response = requests.get(
        f"{BASE_URL}/api/mentors/{mentor_id}/interactions",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_get_stats():
    """Test GET /api/mentors/stats"""
    print("\n=== Testing GET /api/mentors/stats ===")
    response = requests.get(
        f"{BASE_URL}/api/mentors/stats",
        headers=headers
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

if __name__ == "__main__":
    print("=" * 60)
    print("MENTOR API ROUTES TEST")
    print("=" * 60)
    
    # Test 1: Get all mentors (no auth required)
    mentors_data = test_get_mentors()
    
    # Test 2: Get player interactions (requires auth)
    if AUTH_TOKEN != "YOUR_JWT_TOKEN_HERE":
        interactions_data = test_get_interactions()
        
        # Test 3: Get stats
        test_get_stats()
        
        # If there are interactions, test marking as read and following advice
        if interactions_data.get('success') and interactions_data.get('data'):
            first_interaction = interactions_data['data'][0]
            interaction_id = first_interaction['id']
            
            # Test 4: Mark as read
            test_mark_as_read(interaction_id)
            
            # Test 5: Mark advice followed (only if not already followed)
            if not first_interaction.get('action_taken'):
                test_mark_advice_followed(interaction_id)
        
        # If there are mentors, test getting mentor-specific interactions
        if mentors_data.get('success') and mentors_data.get('data'):
            first_mentor = mentors_data['data'][0]
            mentor_id = first_mentor['id']
            
            # Test 6: Get mentor-specific interactions
            test_get_mentor_interactions(mentor_id)
    else:
        print("\n⚠️  Please set AUTH_TOKEN to test authenticated endpoints")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
