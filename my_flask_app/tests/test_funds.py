"""Bonds and funds: bought like shares, pay income every payday, count towards income and net worth."""
import re
from decimal import Decimal
from pathlib import Path

import pytest

from app.game import market
from app.routes.asset_routes import VOLATILE_TYPES, _asset_type_for
from jobs.monthly_loan_deductions import process_month_for_user
from tests.test_economy import _lines, _player, wallets  # noqa: F401 (fixture)

SQL = (Path(__file__).resolve().parents[2] / 'supabase/migrations/20261216000000_funds_and_bonds.sql').read_text()
ROW = re.compile(r"\('([^']+)', '(\w+)', (\d+), ([\d.]+), ([\d.]+), ([\d.]+), '\w+', ([\d.]+),")
SEEDED = [{'id': f'a-{c}', 'name': n, 'category': c, 'price': float(p), 'monthly_income': float(i),
           'annual_drift': float(d), 'annual_volatility': float(v), 'roi': float(roi)}
          for n, c, p, i, d, v, roi in ROW.findall(SQL)]


def test_every_new_kind_is_seeded_and_priced_by_the_market():
    assert {a['category'] for a in SEEDED} == set(market.FUNDS)
    for a in SEEDED:
        assert a['category'] in market.TRADED
        assert _asset_type_for(a['category']) in VOLATILE_TYPES


@pytest.mark.parametrize('asset', SEEDED, ids=lambda a: a['category'])
def test_income_plus_growth_matches_the_yearly_rate(asset):
    income_yield = asset['monthly_income'] * 12 / asset['price']
    assert (income_yield + asset['annual_drift']) * 100 == pytest.approx(asset['roi'], abs=0.05)


def test_a_fund_pays_income_on_payday(fake_supabase, wallets):
    uid, _ = _player(fake_supabase)
    fund = next(a for a in SEEDED if a['category'] == 'special_funds')
    fake_supabase.rows('assets').append(dict(fund))
    fake_supabase.rows('user_assets').append({'id': 'u1', 'user_id': uid, 'name': fund['name'], 'asset_type': 'stocks',
                                              'quantity': 3, 'value': 6000, 'purchase_price': 2000})
    lines = _lines(process_month_for_user(uid))
    assert lines[f"{fund['name']} yield"]['amount'] == 30.0
    assert wallets[uid] >= Decimal('0')


def test_a_stock_crash_reaches_funds_gently_and_misses_bonds():
    crash = {'category': 'stocks', 'shock_pct': -20.0}
    by = {a['category']: a for a in SEEDED}
    assert not market._applies(crash, by['bonds'])
    assert market.shock_for(crash, by['mutual_funds']) == pytest.approx(-0.12)
    assert market.shock_for(crash, by['hedge_funds']) == pytest.approx(-0.06)


def test_the_big_funds_are_the_reward():
    rate = {a['category']: a['roi'] for a in SEEDED}
    assert (rate['hedge_funds'], rate['private_capital']) == (13.0, 15.0)
    assert min(rate['hedge_funds'], rate['private_capital']) > max(rate['bonds'], rate['mutual_funds'], rate['special_funds'])


def test_private_capital_is_locked_for_three_game_years(client, fake_supabase, wallets, monkeypatch):
    from app.routes import asset_routes
    from app.services.profile_service import ProfileService
    monkeypatch.setattr(asset_routes, 'enforce_mission_constraints', lambda *a, **k: None)
    for name in ('recalculate_monthly_income', 'recalculate_net_worth', 'update_trading_profits'):
        monkeypatch.setattr(ProfileService, name, staticmethod(lambda *a: 0))
    monkeypatch.setattr(asset_routes.ExpoPushService, 'notify_followers_of_financial_move', staticmethod(lambda **k: None))
    monkeypatch.setattr(asset_routes.MentorService, 'check_real_time_triggers', staticmethod(lambda **k: None))
    monkeypatch.setattr(asset_routes, 'resolve_user_ids', lambda uid: [uid])

    uid, headers = _player(fake_supabase)
    wallets[uid] = Decimal('250000')
    fund = next(a for a in SEEDED if a['category'] == 'private_capital')
    fake_supabase.rows('assets').append(dict(fund))
    fake_supabase.rows('player_game_clock').append({'user_id': uid, 'week': 10})

    assert client.post('/api/assets/purchase/', json={'asset_id': fund['id'], 'quantity': 1}, headers=headers).status_code == 200
    holding = fake_supabase.rows('user_assets')[0]
    assert holding['locked_until_week'] == 10 + 156

    fake_supabase.rows('player_game_clock')[0]['week'] = 165
    res = client.post('/api/assets/sell/', json={'asset_id': holding['id']}, headers=headers)
    assert res.status_code == 400 and res.get_json()['message'].endswith('locked for 1 more game week.')
    assert wallets[uid] == Decimal('0')

    fake_supabase.rows('player_game_clock')[0]['week'] = 166
    assert client.post('/api/assets/sell/', json={'asset_id': holding['id']}, headers=headers).status_code == 200
    assert wallets[uid] == Decimal('250000')
