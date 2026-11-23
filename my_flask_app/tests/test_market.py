"""The market moves with game weeks: drift, realistic swings, and the odd crash or boom."""
import math
import random
import statistics
from decimal import Decimal

import pytest

from app.game import market
from tests.test_economy import _player, wallets  # noqa: F401 (fixture)

VTI = {'id': 'a-vti', 'name': 'Index Fund (VTI)', 'category': 'stocks', 'price': 250, 'risk_level': 'low',
       'annual_drift': 0.07, 'annual_volatility': 0.15, 'monthly_income': 0.75}
TECH = {'id': 'a-tech', 'name': 'Blue Chip Tech (TECHX)', 'category': 'stocks', 'price': 180, 'risk_level': 'medium',
        'annual_drift': 0.09, 'annual_volatility': 0.28}
YOLO = {'id': 'a-yolo', 'name': 'Meme Stock (YOLO)', 'category': 'stocks', 'price': 15, 'risk_level': 'very_high',
        'annual_drift': -0.05, 'annual_volatility': 0.90}
BTC = {'id': 'a-btc', 'name': 'Bitcoin', 'category': 'crypto', 'price': 60000, 'risk_level': 'high',
       'annual_drift': 0.15, 'annual_volatility': 0.65}
DUPLEX = {'id': 'a-duplex', 'name': 'Duplex', 'category': 'real_estate', 'price': 240000, 'monthly_income': 1900}


def _years(asset, years=40, seed=1):
    """Yearly returns of an asset over many simulated years (ordinary weeks only)."""
    rng = random.Random(seed)
    out = []
    for _ in range(years):
        growth = 1.0
        for _ in range(52):
            growth *= 1 + market.weekly_return(asset, rng)
        out.append(growth - 1)
    return out


def test_an_index_fund_grows_steadily_and_swings_realistically():
    yearly = _years(VTI, years=400)
    typical = math.exp(statistics.mean(math.log(1 + r) for r in yearly)) - 1
    assert 0.04 < typical < 0.09                       # ~7% a year, compounding
    assert 0.11 < statistics.pstdev(yearly) < 0.20     # swings ~15% a year (it was ~135%)


def test_riskier_assets_swing_more():
    spread = {a['name']: statistics.pstdev(_years(a, years=300)) for a in (VTI, TECH, BTC, YOLO)}
    assert spread['Index Fund (VTI)'] < spread['Blue Chip Tech (TECHX)'] < spread['Bitcoin'] < spread['Meme Stock (YOLO)']


def test_defaults_by_category_when_an_asset_sets_none():
    assert market.params({'category': 'crypto'}) == (0.10, 0.70)
    assert market.params({'category': 'forex'}) == (0.0, 0.08)


def test_crashes_and_booms_are_rare_but_happen():
    rng = random.Random(3)
    seen = {}
    weeks = 52 * 200
    for _ in range(weeks):
        for e in market.roll_events(rng):
            seen[e['key']] = seen.get(e['key'], 0) + 1
    assert 30 < seen['stock_crash'] < 90               # ~1 in 200 weeks: every ~4 game years
    assert seen['crypto_winter'] > seen['stock_crash']
    assert all(k in seen for k in ('bull_run', 'crypto_boom', 'meme_squeeze', 'meme_dump', 'currency_shock'))


def test_a_crash_hits_riskier_stocks_harder_and_spares_crypto():
    crash = {'key': 'stock_crash', 'category': 'stocks', 'shock_pct': -20.0}
    assert market.shock_for(crash, VTI) == pytest.approx(-0.20)
    assert market.shock_for(crash, TECH) < -0.25
    assert market._applies(crash, YOLO) and not market._applies(crash, BTC)
    squeeze = {'key': 'meme_squeeze', 'category': 'meme', 'shock_pct': 150.0}
    assert market._applies(squeeze, YOLO) and not market._applies(squeeze, VTI)


@pytest.fixture
def exchange(fake_supabase, monkeypatch):
    fake_supabase.rows('assets').extend([dict(VTI), dict(TECH), dict(BTC), dict(DUPLEX)])
    monkeypatch.setattr('app.routes.asset_routes.enforce_mission_constraints', lambda *a, **k: None)
    return fake_supabase


def test_each_week_moves_your_market_and_revalues_what_you_hold(exchange):
    uid, _ = _player(exchange)
    exchange.rows('user_assets').append({'id': 'h1', 'user_id': uid, 'asset_id': 'a-vti', 'name': 'Index Fund (VTI)',
                                         'asset_type': 'stocks', 'quantity': 10, 'value': 2500, 'purchase_price': 250})
    week1 = market.advance(uid, 1)
    prices = {r['asset_id']: r for r in exchange.rows('player_market_prices')}
    assert set(prices) == {'a-vti', 'a-tech', 'a-btc'}               # property doesn't trade
    vti = Decimal(str(prices['a-vti']['price']))
    assert exchange.rows('user_assets')[0]['value'] == float(vti * 10)
    assert week1['moves'][0]['name'] == 'Index Fund (VTI)'
    assert week1['portfolio_change'] == pytest.approx(float(vti * 10) - 2500)
    # Global catalogue prices are untouched: this is your market.
    assert exchange.rows('assets')[0]['price'] == 250


def test_the_same_week_always_plays_out_the_same(exchange):
    uid, _ = _player(exchange)
    market.advance(uid, 5)
    first = {r['asset_id']: r['price'] for r in exchange.rows('player_market_prices')}
    exchange.rows('player_market_prices').clear()
    market.advance(uid, 5)
    assert {r['asset_id']: r['price'] for r in exchange.rows('player_market_prices')} == first


def test_a_crash_week_is_recorded_and_shows_in_the_news(client, exchange, monkeypatch):
    uid, h = _player(exchange)
    monkeypatch.setattr(market, 'roll_events', lambda rng: [{'key': 'stock_crash', 'category': 'stocks', 'shock_pct': -25.0,
                                                             'emoji': '📉', 'title': 'Stock market crash', 'body': 'Ouch.'}])
    monkeypatch.setattr(market, 'weekly_return', lambda asset, rng: 0.0)
    week = market.advance(uid, 9)
    prices = {r['asset_id']: r['price'] for r in exchange.rows('player_market_prices')}
    assert prices['a-vti'] == 187.5 and prices['a-btc'] == 60000      # stocks crash, crypto doesn't
    assert week['events'][0]['title'] == 'Stock market crash' and 'Bitcoin' not in week['events'][0]['assets']
    data = client.get('/api/assets/overview/', headers=h).get_json()['data']
    assert data['news'][0]['headline'] == '📉 Stock market crash'
    listed = {a['name']: a for a in data['market']}
    assert listed['Index Fund (VTI)']['price'] == 187.5 and listed['Index Fund (VTI)']['price_change_percent'] == -25.0
    assert listed['Index Fund (VTI)']['expected_growth_pct'] == 7.0 and listed['Index Fund (VTI)']['volatility_pct'] == 15


def test_you_buy_and_sell_at_your_own_markets_price(client, exchange, wallets, monkeypatch):
    uid, h = _player(exchange)
    wallets[uid] = Decimal('10000')
    exchange.rows('player_market_prices').append({'user_id': uid, 'asset_id': 'a-vti', 'price': 200, 'prev_price': 250, 'week': 3})
    from app.services.profile_service import ProfileService
    monkeypatch.setattr(ProfileService, 'update_trading_profits', staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(ProfileService, 'recalculate_monthly_income', staticmethod(lambda *a, **k: 0))
    res = client.post('/api/assets/purchase/', json={'asset_id': 'a-vti', 'quantity': 10}, headers=h).get_json()
    assert res['success'], res
    assert wallets[uid] == Decimal('8000')                            # 10 x $200, not $250
    exchange.rows('player_market_prices')[0]['price'] = 260
    holding = exchange.rows('user_assets')[0]
    sold = client.post(f"/api/assets/sell/{holding['id']}/", json={}, headers=h).get_json()
    assert sold['success'], sold
    assert wallets[uid] == Decimal('10600')                           # sold at $260


def test_a_new_life_gets_a_fresh_market(exchange):
    uid, _ = _player(exchange)
    market.advance(uid, 1)
    market.reset_for_new_life(uid)
    assert not [r for r in exchange.rows('player_market_prices') if r['user_id'] == uid]


def test_selling_uses_the_holdings_own_asset_not_a_name_lookalike(client, exchange, wallets, monkeypatch):
    uid, h = _player(exchange)
    wallets[uid] = Decimal('0')
    exchange.rows('assets').insert(0, {**VTI, 'id': 'a-vti2', 'price': 999})      # same name, different asset
    exchange.rows('player_market_prices').append({'user_id': uid, 'asset_id': 'a-vti', 'price': 300, 'prev_price': 250, 'week': 1})
    exchange.rows('user_assets').append({'id': 'h9', 'user_id': uid, 'asset_id': 'a-vti', 'name': VTI['name'],
                                         'asset_type': 'stocks', 'quantity': 1, 'value': 300, 'purchase_price': 250})
    from app.services.profile_service import ProfileService
    monkeypatch.setattr(ProfileService, 'update_trading_profits', staticmethod(lambda *a, **k: None))
    monkeypatch.setattr(ProfileService, 'recalculate_monthly_income', staticmethod(lambda *a, **k: 0))
    sold = client.post('/api/assets/sell/h9/', json={}, headers=h).get_json()
    assert sold['success'] and wallets[uid] == Decimal('300')


def test_a_failed_news_write_is_logged_not_swallowed(exchange, monkeypatch, caplog):
    uid, _ = _player(exchange)
    monkeypatch.setattr(market, 'roll_events', lambda rng: [{'key': 'stock_crash', 'category': 'stocks', 'shock_pct': -20.0,
                                                             'emoji': '📉', 'title': 'Crash', 'body': 'x'}])
    real = market.supabase.table

    def table(name):
        if name == 'player_market_events':
            raise RuntimeError('db down')
        return real(name)
    monkeypatch.setattr(market.supabase, 'table', table)
    with caplog.at_level('WARNING'):
        week = market.advance(uid, 2)
    assert week['events'] and 'db down' in caplog.text
