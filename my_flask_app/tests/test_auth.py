"""Auth: token verification (require_auth) and the register/login routes."""
import types

import pytest

from tests.conftest import make_token

PROTECTED = '/api/profile/me/'


def test_protected_route_rejects_missing_token(client):
    res = client.get(PROTECTED)
    assert res.status_code == 401
    assert res.get_json()['error'] == 'UNAUTHORIZED'


@pytest.mark.parametrize('header', ['Token abc', 'Bearer', 'Bearer a b'])
def test_protected_route_rejects_malformed_header(client, header):
    assert client.get(PROTECTED, headers={'Authorization': header}).status_code == 401


@pytest.mark.parametrize('token_kwargs', [
    {'secret': 'wrong-secret-wrong-secret-wrong-secret'},  # forged signature
    {'expires_in': -60},                                    # expired
    {'audience': 'anon'},                                   # wrong audience
])
def test_protected_route_rejects_bad_tokens(client, token_kwargs):
    res = client.get(PROTECTED, headers={'Authorization': f'Bearer {make_token(**token_kwargs)}'})
    assert res.status_code == 401
    assert res.get_json()['error'] == 'INVALID_TOKEN'


def test_valid_token_reaches_handler(client, auth_headers, balance):
    # No profile exists yet, so the handler itself answers 404: auth passed.
    assert client.get(PROTECTED, headers=auth_headers).status_code == 404


@pytest.mark.parametrize('payload', [
    {},
    {'username': 'ab', 'email': 'a@b.co', 'password': 'secret1'},          # username too short
    {'username': 'player', 'email': 'not-an-email', 'password': 'secret1'},
    {'username': 'player', 'email': 'a@b.co', 'password': '123'},           # password too short
])
def test_register_validates_input(client, payload):
    assert client.post('/api/auth/register/', json=payload).status_code == 400


def test_register_returns_user_and_session(client, monkeypatch):
    from app.services.user_service import UserService
    user = types.SimpleNamespace(id='u-1', email='p@example.com', user_metadata={'username': 'player'}, created_at='2026-01-01')
    session = types.SimpleNamespace(access_token='access', refresh_token='refresh')
    monkeypatch.setattr(UserService, 'create_user', staticmethod(lambda data: types.SimpleNamespace(user=user, session=session)))

    res = client.post('/api/auth/register/', json={'username': 'player', 'email': 'p@example.com', 'password': 'secret1'})
    assert res.status_code in (200, 201)
    body = res.get_json()['data']
    assert body['user']['username'] == 'player'
    assert body['token'] == 'access'


def test_login_requires_credentials(client):
    assert client.post('/api/auth/login/', json={'email': 'p@example.com'}).status_code == 400


def test_login_bad_credentials_is_401(client, monkeypatch):
    from app.services.user_service import UserService

    def fail(email, password):
        raise ValueError('Invalid login credentials')

    monkeypatch.setattr(UserService, 'authenticate', staticmethod(fail))
    res = client.post('/api/auth/login/', json={'email': 'p@example.com', 'password': 'nope123'})
    assert res.status_code == 401
