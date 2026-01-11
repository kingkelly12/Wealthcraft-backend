import json
import uuid
from app.models.profile import Profile

def test_get_profile(client):
    """Test getting a profile"""
    # Create a test profile first
    user_id = str(uuid.uuid4())
    response = client.post('/api/profile/', json={
        'user_id': user_id,
        'username': 'testuser123'
    })
    assert response.status_code == 201
    
    # Get the profile
    response = client.get(f'/api/profile/{user_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['username'] == 'testuser123'
    assert 'credit_score' in data

def test_create_profile(client):
    """Test creating a new profile"""
    user_id = str(uuid.uuid4())
    response = client.post('/api/profile/', json={
        'user_id': user_id,
        'username': 'newuser'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'newuser'
    assert data['credit_score'] == 650  # Default value

def test_create_duplicate_profile(client):
    """Test creating a duplicate profile fails"""
    user_id = str(uuid.uuid4())
    
    # Create first profile
    client.post('/api/profile/', json={
        'user_id': user_id,
        'username': 'duplicate'
    })
    
    # Try to create again
    response = client.post('/api/profile/', json={
        'user_id': user_id,
        'username': 'duplicate2'
    })
    
    assert response.status_code == 400

def test_update_profile(client):
    """Test updating a profile"""
    user_id = str(uuid.uuid4())
    
    # Create profile
    client.post('/api/profile/', json={
        'user_id': user_id,
        'username': 'original'
    })
    
    # Update profile
    response = client.put(f'/api/profile/{user_id}', json={
        'username': 'updated',
        'credit_score': 750
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['username'] == 'updated'
    assert data['credit_score'] == 750

def test_invalid_user_id(client):
    """Test with invalid user ID format"""
    response = client.get('/api/profile/invalid-uuid')
    assert response.status_code == 400
