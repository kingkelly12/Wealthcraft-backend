"""Sanity recovery: costs, caps and validation."""
from decimal import Decimal

import pytest


@pytest.fixture
def player(fake_supabase, user_id):
    fake_supabase.rows('profiles').append({'user_id': user_id, 'sanity': 40})
    return fake_supabase.rows('profiles')[0]


def _recover(client, headers, action):
    return client.post('/api/sanity/recover/', json={'action': action}, headers=headers)


def test_touch_grass_is_free(client, auth_headers, player, balance):
    res = _recover(client, auth_headers, 'touch_grass')
    assert res.status_code == 200
    assert res.get_json()['new_sanity'] == 45
    assert player['sanity'] == 45
    assert balance['log'] == []


def test_therapy_costs_money(client, auth_headers, player, balance):
    balance['amount'] = Decimal('500')
    res = _recover(client, auth_headers, 'therapy')
    assert res.status_code == 200
    assert player['sanity'] == 60
    assert balance['amount'] == Decimal('350')


def test_cannot_afford_vacation(client, auth_headers, player, balance):
    balance['amount'] = Decimal('999')
    res = _recover(client, auth_headers, 'vacation')
    assert res.status_code == 400
    assert player['sanity'] == 40               # unchanged
    assert balance['amount'] == Decimal('999')  # not charged


def test_sanity_caps_at_100(client, auth_headers, player, balance):
    player['sanity'] = 90
    balance['amount'] = Decimal('5000')
    assert _recover(client, auth_headers, 'vacation').get_json()['new_sanity'] == 100


def test_unknown_action_rejected(client, auth_headers, player, balance):
    assert _recover(client, auth_headers, 'nap').status_code == 400


def test_requires_auth(client, player):
    assert client.post('/api/sanity/recover/', json={'action': 'touch_grass'}).status_code == 401
