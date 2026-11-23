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


def test_a_purchase_that_loses_a_race_for_cash_is_a_clean_refusal(client, market, wallets, monkeypatch):
    uid, h = _player(market)
    wallets[uid] = Decimal('400000')
    from app.services.balance_service import BalanceService

    def broke(*a, **k):
        raise ValueError('Insufficient funds')
    monkeypatch.setattr(BalanceService, 'subtract_balance', staticmethod(broke))
    res = client.post('/api/homes/buy/', json={'home_id': 'h-bungalow'}, headers=h)
    assert res.status_code == 400 and res.get_json()['error'] == 'INSUFFICIENT_FUNDS'
    assert not market.rows('player_homes')


def test_a_mission_that_forbids_selling_blocks_selling_a_home(client, market, wallets, monkeypatch):
    uid, h = _player(market)
    wallets[uid] = Decimal('400000')
    client.post('/api/homes/buy/', json={'home_id': 'h-studio'}, headers=h)
    home_id = market.rows('player_homes')[0]['id']
    monkeypatch.setattr('app.utils.mission_constraints.active_mission_constraints', lambda uid: {'can_sell_assets': False})
    monkeypatch.setattr('app.routes.home_routes.enforce_mission_constraints',
                        __import__('app.utils.mission_constraints', fromlist=['x']).enforce_mission_constraints)
    res = client.post(f'/api/homes/{home_id}/sell/', headers=h)
    assert res.status_code == 403 and market.rows('player_homes')[0]['is_active']


# --- mortgages: 20% down, the home is the security ---------------------------------------------

from app.game import economy  # noqa: E402


def _mortgage_player(market, wallets, cash=30000, income=4000, credit=700):
    uid, h = _player(market, income=income, credit=credit)
    wallets[uid] = Decimal(str(cash))
    return uid, h


def _finance(client, h, home='h-studio', **kw):
    return client.post('/api/homes/buy/', json={'home_id': home, 'finance': True, **kw}, headers=h)


def test_each_home_shows_what_a_mortgage_would_be(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    listings = {l['name']: l for l in client.get('/api/homes/', headers=h).get_json()['data']['listings']}
    studio = listings['Studio Flat']['mortgage']
    assert studio['down_payment'] == 19000 and studio['loan_amount'] == 76000 and studio['rate'] == 7     # credit 700
    assert studio['monthly_payment'] == float(economy.annuity_payment(76000, 7, homes.MORTGAGE_TERM))
    assert studio['qualifies'] and studio['total_interest'] > 0
    bungalow = listings['Bungalow']['mortgage']
    assert bungalow['loan_amount'] == 272000 and not bungalow['qualifies'] and '43%' in bungalow['reason']


def test_better_credit_gets_a_better_rate():
    assert [homes.mortgage_rate(c) for c in (800, 750, 700, 650, 640)] == [5, 5, 7, 9, None]


def test_buying_with_a_mortgage_takes_20_percent_down_and_secures_the_loan(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    res = _finance(client, h).get_json()
    assert res['success'], res
    assert wallets[uid] == Decimal('11000')                           # only the 20% left the account
    home = market.rows('player_homes')[0]
    loan = market.rows('liabilities')[0]
    assert loan['player_home_id'] == home['id'] and loan['name'] == 'Mortgage: Studio Flat' and loan['amount'] == 76000
    assert loan['remaining_balance'] == pytest.approx(76000 + loan['total_interest']) and loan['total_interest'] > 0
    assert loan['monthly_payment'] == float(economy.annuity_payment(76000, 7, homes.MORTGAGE_TERM))
    assert home['lives_in'] and home['purchase_price'] == 95000       # the whole home is yours, not 80% of it


def test_the_down_payment_has_to_be_in_your_account(client, market, wallets):
    uid, h = _mortgage_player(market, wallets, cash=15000)
    res = _finance(client, h)
    body = res.get_json()
    assert res.status_code == 400 and body['error'] == 'INSUFFICIENT_FUNDS'
    assert body['data']['needed'] == 19000 and body['data']['short'] == 4000
    assert not market.rows('player_homes') and not market.rows('liabilities') and wallets[uid] == Decimal('15000')


def test_banks_refuse_low_credit_and_payments_that_are_too_big(client, market, wallets):
    uid, h = _mortgage_player(market, wallets, credit=600)
    assert _finance(client, h).get_json()['error'] == 'MORTGAGE_REFUSED'
    uid2, h2 = _mortgage_player(market, wallets, cash=200000, income=4000, credit=800)
    refused = _finance(client, h2, home='h-bungalow').get_json()
    assert refused['error'] == 'MORTGAGE_REFUSED' and '43%' in refused['message']
    assert not market.rows('player_homes')


def test_a_mortgage_that_cant_be_recorded_undoes_the_purchase(client, market, wallets, monkeypatch):
    uid, h = _mortgage_player(market, wallets)
    real = homes.supabase.table

    def table(name):
        if name == 'liabilities':
            raise RuntimeError('db down')
        return real(name)
    monkeypatch.setattr(homes.supabase, 'table', table)
    assert _finance(client, h).status_code == 500
    monkeypatch.undo()
    assert wallets[uid] == Decimal('30000')
    assert not [x for x in market.rows('player_homes') if x.get('is_active')]


def test_financing_follows_a_missions_loan_rules(client, market, wallets, monkeypatch):
    uid, h = _mortgage_player(market, wallets)
    asked = []
    monkeypatch.setattr('app.routes.home_routes.enforce_mission_constraints', lambda uid, action, data=None: asked.append(action))
    _finance(client, h)
    assert asked == ['buy_asset', 'take_loan']


def test_selling_a_home_pays_off_its_mortgage_from_the_sale(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    _finance(client, h)
    home_id = market.rows('player_homes')[0]['id']
    sold = client.post(f'/api/homes/{home_id}/sell/', headers=h).get_json()
    assert sold['success'], sold
    # $95,000 less 5% fees, less the $76,000 still borrowed (the interest not yet earned is refunded).
    assert sold['data']['mortgage_paid'] == pytest.approx(76000, abs=1)
    assert wallets[uid] == Decimal('11000') + Decimal('90250') - Decimal(str(sold['data']['mortgage_paid']))
    assert not market.rows('liabilities')


def test_you_cant_sell_for_less_than_the_mortgage_unless_you_cover_it(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    _finance(client, h)
    home = market.rows('player_homes')[0]
    home['current_value'] = 60000                                       # the market fell
    wallets[uid] = Decimal('1000')
    refused = client.post(f"/api/homes/{home['id']}/sell/", headers=h).get_json()
    assert refused['error'] == 'UNDERWATER' and home['is_active']
    wallets[uid] = Decimal('30000')
    assert client.post(f"/api/homes/{home['id']}/sell/", headers=h).get_json()['success']
    assert not market.rows('liabilities')


def _run_month(uid):
    return process_month_for_user(uid)


def test_a_paid_instalment_resets_the_missed_count(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    _finance(client, h)
    wallets[uid] = Decimal('0')
    _run_month(uid)
    assert market.rows('liabilities')[0]['missed_streak'] == 1
    wallets[uid] = Decimal('50000')
    _run_month(uid)
    assert market.rows('liabilities')[0]['missed_streak'] == 0


def test_three_missed_paydays_in_a_row_and_the_bank_takes_the_home(client, market, wallets):
    uid, h = _mortgage_player(market, wallets)
    _finance(client, h)
    wallets[uid] = Decimal('0')
    credit_before = market.rows('profiles')[0]['credit_score']
    for expected in (1, 2):
        _run_month(uid)
        assert market.rows('liabilities')[0]['missed_streak'] == expected and market.rows('player_homes')[0]['is_active']
    month = _run_month(uid)
    home = market.rows('player_homes')[0]
    assert not home['is_active'] and not home['lives_in'] and home.get('repossessed_at')
    assert not market.rows('liabilities')                                # the bank's sale cleared the loan
    assert any('Repossessed' in l['label'] for l in month['lines'])
    assert market.rows('profiles')[0]['credit_score'] < credit_before - 90
    assert homes.owned(uid) == []


def test_a_mortgage_counts_as_what_clearing_it_costs_not_the_interest_still_to_come(client, market, wallets, monkeypatch):
    from app.services.profile_service import ProfileService
    import uuid as _uuid
    uid, h = _mortgage_player(market, wallets)
    _finance(client, h)
    monkeypatch.setattr(ProfileService, 'update_net_worth', staticmethod(lambda *a, **k: None))
    worth = ProfileService.recalculate_net_worth(_uuid.UUID(uid))
    assert worth == pytest.approx(11000 + 95000 - 76000, abs=1)     # cash + the home - the $76,000 borrowed
