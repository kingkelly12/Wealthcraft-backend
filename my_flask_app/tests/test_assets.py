"""Asset marketplace (public endpoint)."""


def test_marketplace_lists_assets(client, fake_supabase):
    fake_supabase.rows('assets').extend([
        {'id': 'a1', 'name': 'ACME', 'category': 'stocks'},
        {'id': 'a2', 'name': 'BTC', 'category': 'crypto'},
    ])
    res = client.get('/api/assets/marketplace/')
    assert res.status_code == 200
    assert {a['id'] for a in res.get_json()['data']} == {'a1', 'a2'}


def test_marketplace_filters_by_category(client, fake_supabase):
    fake_supabase.rows('assets').extend([
        {'id': 'a1', 'category': 'stocks'}, {'id': 'a2', 'category': 'crypto'},
    ])
    data = client.get('/api/assets/marketplace/?category=crypto').get_json()['data']
    assert [a['id'] for a in data] == ['a2']


def test_marketplace_empty(client, fake_supabase):
    assert client.get('/api/assets/marketplace/').get_json()['data'] == []
