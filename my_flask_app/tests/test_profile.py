"""Profiles (SQLAlchemy-backed): create, read, update and ownership rules."""
import uuid

from tests.conftest import make_token


def _create(client, headers, username='player_one'):
    return client.post('/api/profile/', json={'username': username}, headers=headers)


def test_create_profile_with_defaults(client, auth_headers, user_id):
    res = _create(client, auth_headers)
    assert res.status_code == 201
    body = res.get_json()
    assert body['user_id'] == user_id          # always the caller, never the payload
    assert body['username'] == 'player_one'
    assert body['credit_score'] == 650
    assert body['has_completed_onboarding'] is False


def test_create_ignores_user_id_in_payload(client, auth_headers, user_id):
    res = client.post('/api/profile/', json={'username': 'sneaky', 'user_id': str(uuid.uuid4())}, headers=auth_headers)
    assert res.status_code == 201
    assert res.get_json()['user_id'] == user_id


def test_create_duplicate_profile_fails(client, auth_headers):
    assert _create(client, auth_headers).status_code == 201
    assert _create(client, auth_headers, username='player_two').status_code == 400


def test_username_must_be_unique(client, auth_headers):
    assert _create(client, auth_headers, username='taken').status_code == 201
    other = {'Authorization': f'Bearer {make_token()}'}
    assert _create(client, other, username='taken').status_code == 400


def test_create_validates_username(client, auth_headers):
    assert _create(client, auth_headers, username='ab').status_code == 400


def test_get_profile_includes_balance(client, auth_headers, user_id, balance):
    _create(client, auth_headers)
    balance['amount'] = balance['amount'] + 1234
    res = client.get(f'/api/profile/{user_id}/', headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['username'] == 'player_one'
    assert data['account_balance'] == 1234


def test_get_missing_profile_is_404(client, auth_headers, balance):
    assert client.get(f'/api/profile/{uuid.uuid4()}/', headers=auth_headers).status_code == 404


def test_get_invalid_user_id_is_400(client, auth_headers):
    assert client.get('/api/profile/not-a-uuid/', headers=auth_headers).status_code == 400


def test_update_own_profile(client, auth_headers, user_id):
    _create(client, auth_headers)
    res = client.put(f'/api/profile/{user_id}/', json={'username': 'renamed', 'has_completed_onboarding': True}, headers=auth_headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body['username'] == 'renamed'
    assert body['has_completed_onboarding'] is True


def test_update_ignores_game_stats(client, auth_headers, user_id):
    _create(client, auth_headers)
    res = client.put(f'/api/profile/{user_id}/', json={'net_worth': 9_999_999, 'credit_score': 850}, headers=auth_headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body['net_worth'] == 0
    assert body['credit_score'] == 650


def test_cannot_update_someone_elses_profile(client, auth_headers):
    res = client.put(f'/api/profile/{uuid.uuid4()}/', json={'username': 'hijack'}, headers=auth_headers)
    assert res.status_code == 403


def test_update_rejects_invalid_username(client, auth_headers, user_id):
    _create(client, auth_headers)
    res = client.put(f'/api/profile/{user_id}/', json={'username': 'bad name!'}, headers=auth_headers)
    assert res.status_code == 400
