"""Owning your home: buy, move in (rent stops), upkeep, letting out, selling."""
from decimal import Decimal

import pytest

from app.game import homes, week_service
from jobs.monthly_loan_deductions import process_month_for_user
from tests.test_economy import _lines, _player, wallets  # noqa: F401 (fixture)

BUNGALOW = {
    'id': 'h-bungalow', 'name': 'Bungalow', 'home_type': 'bungalow', 'bills_type': 'house', 'price': 340000,
    'market_rent': 2700, 'bedrooms': 3, 'location': 'Leafy Suburbs',
    'upkeep': [{'label': 'Insurance', 'monthly': 60}, {'label': 'Property rates', 'monthly': 100}, {'label': 'Garden & maintenance', 'monthly': 180}],
}
STUDIO = {'id': 'h-studio', 'name': 'Studio Flat', 'home_type': 'studio', 'bills_type': 'studio', 'price': 95000,
          'market_rent': 950, 'location': 'Downtown Edge', 'upkeep': [{'label': 'Service charge', 'monthly': 70}]}


@pytest.fixture
def market(fake_supabase, monkeypatch):
    fake_supabase.rows('home_listings').extend([dict(BUNGALOW), dict(STUDIO)])
    monkeypatch.setattr(homes, '_recalc', lambda uid: None)
    monkeypatch.setattr('app.routes.home_routes.enforce_mission_constraints', lambda *a, **k: None)
    return fake_supabase


def _renting(fake, uid, rent=1400):
    fake.rows('player_rentals').append({'id': 'r1', 'player_id': uid, 'monthly_rent': rent, 'is_active': True,
                                        'rental_properties': {'name': 'One-Bedroom Apartment', 'property_type': 'apartment'}})


def test_buying_and_moving_in_ends_the_lease(client, market, wallets):
    uid, h = _player(market, income=4000)
    wallets[uid] = Decimal('400000')
    _renting(market, uid)
    res = client.post('/api/homes/buy/', json={'home_id': 'h-bungalow'}, headers=h).get_json()
    assert res['success'] and res['data']['lives_in'] and res['data']['value'] == 340000
    assert wallets[uid] == Decimal('60000')
    assert not market.rows('player_rentals')[0]['is_active']
    assert client.get('/api/homes/', headers=h).get_json()['data']['living'] == 'own'


def test_owners_pay_upkeep_and_bills_not_rent_and_the_home_grows(client, market, wallets):
    uid, h = _player(market, income=4000)
    wallets[uid] = Decimal('400000')
    _renting(market, uid)
    client.post('/api/homes/buy/', json={'home_id': 'h-bungalow'}, headers=h)
    lines = _lines(process_month_for_user(uid))
    assert not any(l.startswith('Rent') for l in lines)
    assert lines['Upkeep: Bungalow']['amount'] == -340.0
    assert lines['Upkeep: Bungalow']['note'] == 'Insurance $60 · Property rates $100 · Garden & maintenance $180'
    assert lines['Electricity, water & Wi-Fi']['amount'] == -230.0      # a house's bills
    assert 'Chipping in at home' not in lines
    home = market.rows('player_homes')[0]
    assert home['current_value'] == 341700.0 and home['months_held'] == 1


def test_short_of_cash_says_by_how_much(client, market, wallets):
    uid, h = _player(market)
    wallets[uid] = Decimal('20000')
    res = client.post('/api/homes/buy/', json={'home_id': 'h-studio'}, headers=h)
    body = res.get_json()
    assert res.status_code == 400 and body['error'] == 'INSUFFICIENT_FUNDS'
    assert body['data'] == {'needed': 95000.0, 'balance': 20000.0, 'short': 75000.0}
    assert not market.rows('player_homes') and wallets[uid] == Decimal('20000')


def test_a_home_you_dont_live_in_is_let_out(client, market, wallets, monkeypatch):
    uid, h = _player(market, income=4000)
    wallets[uid] = Decimal('100000')
    client.post('/api/homes/buy/', json={'home_id': 'h-studio', 'move_in': False}, headers=h)
    monkeypatch.setattr(homes, 'let_income', lambda listing, rng=None: (Decimal('769.50'), Decimal('0.90')))
    lines = _lines(process_month_for_user(uid))
    assert lines['Tenant rent: Studio Flat']['amount'] == 769.5
    assert lines['Tenant rent: Studio Flat']['note'] == '90% occupied · agent takes 10%'
    assert lines['Upkeep: Studio Flat']['amount'] == -70.0
    assert 'Chipping in at home' in lines        # still living with the parents


def test_let_income_is_rent_after_the_agent_on_occupied_months():
    import random
    income, occupied = homes.let_income(STUDIO, random.Random(1))
    assert Decimal('0.75') <= occupied <= Decimal('1.0')
    assert income == (Decimal('950') * occupied * Decimal('0.9')).quantize(Decimal('0.01'))


def test_selling_pays_the_value_minus_fees_once(client, market, wallets):
    uid, h = _player(market)
    wallets[uid] = Decimal('95000')
    home_id = client.post('/api/homes/buy/', json={'home_id': 'h-studio'}, headers=h).get_json()['data']['id']
    sold = client.post(f'/api/homes/{home_id}/sell/', headers=h).get_json()
    assert sold['success'] and sold['data']['proceeds'] == 90250.0 and sold['data']['fees'] == 4750.0
    assert wallets[uid] == Decimal('90250')
    assert client.post(f'/api/homes/{home_id}/sell/', headers=h).status_code == 404
    assert homes.total_value(uid) == 0


def test_figures_compare_owning_with_renting():
    f = homes.figures(BUNGALOW)
    assert f['upkeep_monthly'] == 340 and f['rent_instead'] == 2700 and f['saving_monthly'] == 2360
    assert f['payback_years'] == 12.0 and f['bills_monthly'] == 230


def test_moving_between_homes_and_out(client, market, wallets):
    uid, h = _player(market)
    wallets[uid] = Decimal('500000')
    a = client.post('/api/homes/buy/', json={'home_id': 'h-studio'}, headers=h).get_json()['data']['id']
    b = client.post('/api/homes/buy/', json={'home_id': 'h-bungalow', 'move_in': False}, headers=h).get_json()['data']['id']
    client.post(f'/api/homes/{b}/move-in/', headers=h)
    lives = {r['id']: r['lives_in'] for r in market.rows('player_homes')}
    assert lives == {a: False, b: True}
    homes.stop_living_in_owned(uid)       # e.g. they rented somewhere
    assert not any(r['lives_in'] for r in market.rows('player_homes'))


def test_owners_get_no_landlord_or_move_back_home_cards():
    owner = {'job': True, 'rental': False, 'owner': True, 'rel': {}}
    landlord = {'key': 'x', 'requires': 'rental'}
    parents = {'key': 'y', 'requires': 'no_rental'}
    assert not week_service._eligible(landlord, owner) and not week_service._eligible(parents, owner)
    assert week_service._eligible(parents, {**owner, 'owner': False})
