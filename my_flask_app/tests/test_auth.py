import json

def test_register_user(client):
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['username'] == 'testuser'
    assert 'id' in data

def test_register_duplicate_user(client):
    # Create first user
    client.post('/api/auth/register', json={
        'username': 'duplicate',
        'email': 'dup@example.com',
        'password': 'password123'
    })
    
    # Try to create same user again
    response = client.post('/api/auth/register', json={
        'username': 'duplicate',
        'email': 'dup@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 400
