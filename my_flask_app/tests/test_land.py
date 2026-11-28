"""Land: buying a plot, offers arriving, answering them, leases and the fake developer."""
from decimal import Decimal

import pytest

from app.game import land
from jobs.monthly_loan_deductions import process_month_for_user
from tests.test_economy import _lines, _player, wallets  # noqa: F401 (fixture)


class Rng:
    """Fixed luck: `roll` for random(), the low end for ranges."""
    def __init__(self, roll):
        self.roll = roll

    def random(self):
        return self.roll

    def randint(self, a, _b):
        return a


@pytest.fixture
def world(fake_supabase, monkeypatch):
    monkeypatch.setattr(land, '_recalc', lambda uid: None)
    monkeypatch.setattr(land, '_alert', lambda *a: None)
    monkeypatch.setattr('app.routes.land_routes.enforce_mission_constraints', lambda *a, **k: None)
    return fake_supabase


def _with_offer(world, wallets, plot='river_flats', cash=200000):
    uid, headers = _player(world)
    wallets[uid] = Decimal(cash)
    land.buy(uid, plot, rng=Rng(0.99))
    row = world.rows('player_land')[0]
    row['fate'] = {'offer_month': 3}
    for _ in range(3):
        process_month_for_user(uid)
    return uid, headers, world.rows('player_land')[0]


def test_buying_takes_the_price_and_hides_the_fate(client, world, wallets):
    uid, h = _player(world)
    wallets[uid] = Decimal('40000')
    res = client.post('/api/land/buy/', json={'plot_key': 'river_flats'}, headers=h).get_json()
    assert res['success'] and wallets[uid] == Decimal('10000')
    body = client.get('/api/land/', headers=h).get_data(as_text=True)
    for secret in ('fate', 'offer_month', 'scam', 'chance', 'annual'):
        assert secret not in body


def test_each_plot_once_even_after_selling(client, world, wallets):
    uid, h = _player(world)
    wallets[uid] = Decimal('100000')
    row = land.buy(uid, 'river_flats', rng=Rng(0.99))
    assert land.sell(uid, row['id'])['proceeds'] == 28500.0
    res = client.post('/api/land/buy/', json={'plot_key': 'river_flats'}, headers=h)
    assert res.status_code == 409 and wallets[uid] == Decimal('98500')


def test_offer_arrives_on_its_payday_and_lapses_without_selling(world, wallets):
    uid, _, row = _with_offer(world, wallets)
    assert row['offer']['type'] == 'real' and row['offer']['expires_month'] == 5
    process_month_for_user(uid)
    assert world.rows('player_land')[0]['offer']
    lines = _lines(process_month_for_user(uid))
    assert 'Offer lapsed' in lines
    row = world.rows('player_land')[0]
    assert row['offer'] is None and row['status'] == 'owned' and row['is_active']


def test_selling_to_the_company_pays_once(client, world, wallets):
    uid, h, row = _with_offer(world, wallets)
    before = wallets[uid]
    url = f"/api/land/{row['id']}/respond/"
    assert client.post(url, json={'action': 'sell'}, headers=h).get_json()['data']['cash'] == 67500.0
    assert client.post(url, json={'action': 'sell'}, headers=h).status_code == 404
    assert wallets[uid] == before + 67500


def test_lease_pays_every_payday_and_blocks_selling(world, wallets):
    uid, _, row = _with_offer(world, wallets)
    land.respond(uid, row['id'], 'lease')
    lines = _lines(process_month_for_user(uid))
    assert lines['Land lease: River Flats']['amount'] == 1153.85
    assert lines['Land rates: River Flats']['amount'] == -60.0
    with pytest.raises(land.LandError):
        land.sell(uid, row['id'])


def test_lease_runs_out_or_the_company_pulls_out():
    lease = land.new_lease(13000)
    for n in range(1, 40):
        pay, lease, ended = land.lease_payday(lease, Rng(0.99))
        assert pay == Decimal('1000.00')
    assert n == 39 and lease is None and ended == 'ran out'
    lease = land.new_lease(13000)
    for n in range(1, 14):
        _, lease, ended = land.lease_payday(lease, Rng(0.0))
    assert lease is None and ended == 'pulled out'


def test_negotiating_improves_the_terms_once(world, wallets):
    uid, _, row = _with_offer(world, wallets)
    before = wallets[uid]
    land.respond(uid, row['id'], 'negotiate', rng=Rng(0.0))
    assert wallets[uid] == before - 750
    assert world.rows('player_land')[0]['offer']['annual'] == 19500.0
    with pytest.raises(land.LandError):
        land.respond(uid, row['id'], 'negotiate')


def test_negotiating_can_lose_the_deal(world, wallets):
    uid, _, row = _with_offer(world, wallets)
    land.respond(uid, row['id'], 'negotiate', rng=Rng(0.99))
    assert world.rows('player_land')[0]['offer'] is None


def test_a_declined_offer_can_come_back_better_once(world, wallets):
    uid, _, row = _with_offer(world, wallets)
    land.respond(uid, row['id'], 'decline', rng=Rng(0.0))
    for _ in range(3):
        process_month_for_user(uid)
    offer = world.rows('player_land')[0]['offer']
    assert offer['returned'] and offer['annual'] == 18000.0
    land.respond(uid, row['id'], 'decline', rng=Rng(0.0))
    assert world.rows('player_land')[0]['fate']['return_month'] == 6      # not scheduled again


@pytest.mark.parametrize('action, cost', [('pay', 2500), ('check', 300), ('ignore', 0)])
def test_the_fake_developer(world, wallets, action, cost):
    uid, _ = _player(world)
    wallets[uid] = Decimal('100000')
    land.buy(uid, 'river_flats', rng=Rng(0.99))
    world.rows('player_land')[0]['fate'] = {'offer_month': None, 'scam_month': 1}
    process_month_for_user(uid)
    row = world.rows('player_land')[0]
    assert row['offer']['type'] == 'scam'
    before = wallets[uid]
    land.respond(uid, row['id'], action)
    assert wallets[uid] == before - cost
    process_month_for_user(uid)
    assert world.rows('player_land')[0]['offer'] is None                  # only ever once


def test_a_new_life_clears_the_land(world, wallets):
    uid, _ = _player(world)
    wallets[uid] = Decimal('100000')
    land.buy(uid, 'river_flats', rng=Rng(0.99))
    land.clear_for_new_life(uid)
    assert not world.rows('player_land')
