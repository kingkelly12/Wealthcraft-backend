import json
import uuid
from app.models.asset import Asset
from app import db

def test_get_marketplace_assets(client, app):
    """Test getting marketplace assets"""
    # Create test assets
    with app.app_context():
        asset1 = Asset(id='STOCK001', name='Tech Corp', category='stocks', price=100.00, risk_level='medium')
        asset2 = Asset(id='CRYPTO001', name='BitCoin', category='crypto', price=50000.00, risk_level='high')
        db.session.add(asset1)
        db.session.add(asset2)
        db.session.commit()
    
    response = client.get('/api/assets/marketplace')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 2

def test_get_marketplace_assets_by_category(client, app):
    """Test filtering marketplace assets by category"""
    with app.app_context():
        asset = Asset(id='STOCK002', name='Finance Corp', category='stocks', price=150.00, risk_level='low')
        db.session.add(asset)
        db.session.commit()
    
    response = client.get('/api/assets/marketplace?category=stocks')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert all(asset['category'] == 'stocks' for asset in data)

def test_buy_asset(client, app):
    """Test purchasing an asset"""
    user_id = str(uuid.uuid4())
    
    # Create test asset
    with app.app_context():
        asset = Asset(id='STOCK003', name='Growth Inc', category='stocks', price=200.00, risk_level='medium')
        db.session.add(asset)
        db.session.commit()
    
    response = client.post(f'/api/assets/buy/{user_id}', json={
        'asset_id': 'STOCK003',
        'quantity': 5
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Growth Inc'
    assert data['quantity'] == 5

def test_get_user_assets(client, app):
    """Test getting user's assets"""
    user_id = str(uuid.uuid4())
    
    # Create and buy asset
    with app.app_context():
        asset = Asset(id='STOCK004', name='Value Co', category='stocks', price=100.00, risk_level='low')
        db.session.add(asset)
        db.session.commit()
    
    client.post(f'/api/assets/buy/{user_id}', json={
        'asset_id': 'STOCK004',
        'quantity': 10
    })
    
    response = client.get(f'/api/assets/user/{user_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert data[0]['name'] == 'Value Co'

def test_sell_asset(client, app):
    """Test selling an asset"""
    user_id = str(uuid.uuid4())
    
    # Create and buy asset
    with app.app_context():
        asset = Asset(id='STOCK005', name='Sell Corp', category='stocks', price=300.00, risk_level='medium')
        db.session.add(asset)
        db.session.commit()
    
    buy_response = client.post(f'/api/assets/buy/{user_id}', json={
        'asset_id': 'STOCK005',
        'quantity': 2
    })
    asset_id = json.loads(buy_response.data)['id']
    
    # Sell the asset
    response = client.delete(f'/api/assets/sell/{user_id}/{asset_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sale_value' in data

def test_buy_nonexistent_asset(client):
    """Test buying an asset that doesn't exist"""
    user_id = str(uuid.uuid4())
    
    response = client.post(f'/api/assets/buy/{user_id}', json={
        'asset_id': 'NONEXISTENT',
        'quantity': 1
    })
    
    assert response.status_code == 400
