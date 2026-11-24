"""The Showroom's server side: wishlist + alerts, "since you passed on it", deals, friends' buys."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.game import showroom
from tests.test_economy import _player, wallets  # noqa: F401 (fixture)

HOME = {'id': 'h1', 'name': 'Bungalow', 'home_type': 'bungalow', 'price': 340000, 'market_rent': 2700, 'location': 'Leafy',
        'upkeep': [{'label': 'Insurance', 'monthly': 60}, {'label': 'Maintenance', 'monthly': 140}]}
CHEAP_HOME = {'id': 'h2', 'name': 'Studio Flat', 'home_type': 'studio', 'price': 60000, 'market_rent': 600, 'location': 'Downtown', 'upkeep': []}
BIZ = {'id': 'b1', 'name': 'Coffee Kiosk', 'category': 'business', 'price': 22000, 'monthly_income': 520, 'risk_level': 'high'}
STOCK = {'id': 's1', 'name': 'Index Fund', 'category': 'stocks', 'price': 100}
CAR = {'id': 'i1', 'name': 'Supercar', 'category': 'vehicle', 'base_price': 380000, 'monthly_cost': 2600, 'depreciation_rate': 0.10,
       'costs': [{'label': 'Fuel', 'monthly': 600}, {'label': 'Insurance', 'monthly': 2000}]}
SCOOTER = {'id': 'i2', 'name': 'City Scooter', 'category': 'vehicle', 'base_price': 2400, 'monthly_cost': 40, 'depreciation_rate': 0.14,
           'costs': [{'label': 'Fuel', 'monthly': 40}]}


@pytest.fixture
def world(fake_supabase, wallets, monkeypatch):  # after wallets: it stubs pushes too
    fake_supabase.rows('home_listings').extend([dict(HOME), dict(CHEAP_HOME)])
    fake_supabase.rows('assets').extend([dict(BIZ), dict(STOCK)])
    fake_supabase.rows('liability_items').extend([dict(CAR), dict(SCOOTER)])
    pushes = []
    from app.services.push_notification_service import ExpoPushService
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user',
                        classmethod(lambda cls, sb, uid, title, body, **kw: pushes.append((uid, title, body)) or True))
    fake_supabase.pushes = pushes
    return fake_supabase


def _at_week(fake, uid, week, life=1):
    clocks = [c for c in fake.rows('player_game_clock') if c['user_id'] == uid]
    if clocks:
        clocks[0]['week'] = week
    else:
        fake.rows('player_game_clock').append({'user_id': uid, 'week': week})
    if not any(l['user_id'] == uid for l in fake.rows('player_lives')):
        fake.rows('player_lives').append({'user_id': uid, 'life_number': life, 'is_current': True})


# --- Wishlist --------------------------------------------------------------------------------------

def test_wishlist_add_list_remove(client, world, wallets):
    uid, h = _player(world)
    wallets[uid] = Decimal('1200')
    res = client.post('/api/showroom/wishlist/', json={'kind': 'item', 'item_id': 'i2'}, headers=h).get_json()
    assert res['success'] and res['data'][0]['name'] == 'City Scooter'
    assert res['data'][0]['progress_pct'] == 50.0 and not res['data'][0]['affordable']
    # Adding twice keeps one.
    client.post('/api/showroom/wishlist/', json={'kind': 'item', 'item_id': 'i2'}, headers=h)
    assert len(world.rows('showroom_wishlist')) == 1
    assert client.delete('/api/showroom/wishlist/item/i2/', headers=h).get_json()['data'] == []


def test_wishlist_rejects_unknown_items_and_kinds(client, world, wallets):
    uid, h = _player(world)
    assert client.post('/api/showroom/wishlist/', json={'kind': 'item', 'item_id': 'nope'}, headers=h).status_code == 404
    assert client.post('/api/showroom/wishlist/', json={'kind': 'stock', 'item_id': 's1'}, headers=h).status_code == 400
    assert client.post('/api/showroom/wishlist/', json={}, headers=h).status_code == 400


def test_a_home_on_the_wishlist_counts_the_deposit(world, wallets):
    uid, _ = _player(world)
    wallets[uid] = Decimal('70000')
    showroom.wishlist_add(uid, 'home', 'h1')
    w = showroom.wishlist(uid)[0]
    assert w['cash_needed'] == 68000 and w['affordable']


def test_affordable_alert_once_then_again_after_slipping_out_of_reach(world, wallets):
    uid, _ = _player(world)
    showroom.wishlist_add(uid, 'item', 'i2')
    wallets[uid] = Decimal('100')
    assert showroom.after_week(uid) == [] and world.pushes == []
    wallets[uid] = Decimal('3000')
    assert [n['name'] for n in showroom.after_week(uid)] == ['City Scooter']
    assert len(world.pushes) == 1 and 'City Scooter' in world.pushes[0][2]
    assert showroom.after_week(uid) == [] and len(world.pushes) == 1      # not again
    wallets[uid] = Decimal('50')
    showroom.after_week(uid)                                               # out of reach: reset
    wallets[uid] = Decimal('3000')
    assert len(showroom.after_week(uid)) == 1 and len(world.pushes) == 2


# --- Seen and "since you passed on it" --------------------------------------------------------------

def test_seen_keeps_the_first_week_only(client, world, wallets):
    uid, h = _player(world)
    _at_week(world, uid, 3)
    body = {'items': [{'kind': 'home', 'item_id': 'h1'}, {'kind': 'item', 'item_id': 'i1'}, {'kind': 'stock', 'item_id': 's1'}]}
    assert client.post('/api/showroom/seen/', json=body, headers=h).get_json()['data']['recorded'] == 2
    _at_week(world, uid, 9)
    assert client.post('/api/showroom/seen/', json=body, headers=h).get_json()['data']['recorded'] == 0
    assert {r['first_seen_week'] for r in world.rows('showroom_seen')} == {3}


def test_passed_shows_growth_earnings_and_dodged_costs(world, wallets):
    uid, _ = _player(world)
    _at_week(world, uid, 1)
    showroom.mark_seen(uid, [{'kind': 'home', 'item_id': 'h1'}, {'kind': 'business', 'item_id': 'b1'}, {'kind': 'item', 'item_id': 'i1'}])
    _at_week(world, uid, 3)
    assert showroom.passed(uid, showroom._catalog(), set()) == []         # under a game month: nothing yet
    _at_week(world, uid, 25)                                               # 24 weeks = 6 game months
    got = {p['kind']: p for p in showroom.passed(uid, showroom._catalog(), set())}
    home = got['home']
    assert home['mode'] == 'grew' and home['weeks_ago'] == 24
    assert home['amount'] == pytest.approx(340000 * (1.005 ** 6 - 1), abs=1)
    assert got['business']['mode'] == 'earned' and got['business']['amount'] == 520 * 6
    car = got['item']
    lost = 380000 * (1 - 0.9 ** 0.5)
    assert car['mode'] == 'cost' and car['amount'] == pytest.approx(lost + 2600 * 6, abs=1)


def test_passed_skips_things_you_own(world, wallets):
    uid, _ = _player(world)
    _at_week(world, uid, 1)
    showroom.mark_seen(uid, [{'kind': 'item', 'item_id': 'i1'}])
    _at_week(world, uid, 30)
    assert showroom.passed(uid, showroom._catalog(), {('item', 'i1')}) == []


# --- Deals ----------------------------------------------------------------------------------------------

def test_deals_are_fixed_for_the_window_and_only_homes_and_items(world, wallets):
    uid, _ = _player(world, income=3000)
    wallets[uid] = Decimal('5000')
    _at_week(world, uid, 5)
    first = showroom.deals(uid, today=date(2026, 3, 1))
    assert 1 <= len(first) <= 3 and {d['kind'] for d in first} <= {'home', 'item'}
    assert all(d['label'] == 'Deal' for d in first)
    _at_week(world, uid, 6)                                                # same window (weeks 5-6)
    assert [d['item_id'] for d in showroom.deals(uid, today=date(2026, 3, 1))] == [d['item_id'] for d in first]
    for d in first:
        lo, hi = (4, 8) if d['kind'] == 'home' else (10, 20)
        assert lo <= d['discount_pct'] <= hi
    # Next window: never the same item twice in a life.
    _at_week(world, uid, 7)
    again = showroom.deals(uid, today=date(2026, 3, 1))
    assert not ({d['item_id'] for d in again} & {d['item_id'] for d in first})


def test_seasonal_deals_are_labelled_and_bigger(world, wallets):
    uid, _ = _player(world)
    _at_week(world, uid, 1)
    got = showroom.deals(uid, today=date(2026, 11, 27))
    assert got and all(d['label'] == 'Black Friday' and d['emoji'] == '🛍️' for d in got)
    assert all(d['discount_pct'] >= (8 if d['kind'] == 'home' else 15) for d in got)
    assert showroom.season(date(2026, 3, 1)) is None


def _deal_on(world, uid, kind, item_id, pct=0.2, created_at='2026-01-01T00:00:00+00:00', week=1):
    world.rows('showroom_deals').append({'id': f'd-{item_id}', 'user_id': uid, 'life_number': 1, 'window_start_week': week,
                                         'ends_week': week + 1, 'kind': kind, 'item_id': item_id, 'discount_pct': pct,
                                         'label': 'Deal', 'emoji': '🔥', 'created_at': created_at, 'redeemed_at': None})


def test_redeeming_pays_the_discount_and_lowers_the_value(client, world, wallets):
    uid, h = _player(world)
    _at_week(world, uid, 1)
    _deal_on(world, uid, 'item', 'i2', pct=0.2)
    world.rows('player_liabilities').append({'id': 'pl1', 'player_id': uid, 'liability_id': 'i2', 'purchase_price': 2400,
                                             'current_value': 2400, 'is_active': True, 'purchase_date': '2026-01-02T00:00:00+00:00'})
    res = client.post('/api/showroom/deals/redeem/', json={'kind': 'item', 'item_id': 'i2'}, headers=h).get_json()
    assert res['success'] and res['data']['saving'] == 480
    assert wallets[uid] == Decimal('480')
    owned = world.rows('player_liabilities')[0]
    assert owned['purchase_price'] == 1920 and owned['current_value'] == 1920   # reselling can't cash the deal out
    again = client.post('/api/showroom/deals/redeem/', json={'kind': 'item', 'item_id': 'i2'}, headers=h)
    assert again.status_code == 409 and wallets[uid] == Decimal('480')


def test_redeeming_needs_a_purchase_made_after_the_deal(client, world, wallets):
    uid, h = _player(world)
    _at_week(world, uid, 1)
    _deal_on(world, uid, 'home', 'h2', created_at='2026-05-01T00:00:00+00:00')
    world.rows('player_homes').append({'id': 'ph1', 'player_id': uid, 'home_id': 'h2', 'purchase_price': 60000, 'current_value': 60000,
                                       'is_active': True, 'purchased_at': '2026-04-01T00:00:00+00:00'})
    res = client.post('/api/showroom/deals/redeem/', json={'kind': 'home', 'item_id': 'h2'}, headers=h)
    assert res.status_code == 409 and res.get_json()['error'] == 'NOT_BOUGHT'


def test_expired_deals_and_businesses_cannot_be_redeemed(client, world, wallets):
    uid, h = _player(world)
    _at_week(world, uid, 1)
    _deal_on(world, uid, 'item', 'i1', week=1)
    _at_week(world, uid, 3)                                                # window 1-2 is over
    assert client.post('/api/showroom/deals/redeem/', json={'kind': 'item', 'item_id': 'i1'}, headers=h).status_code == 404
    assert client.post('/api/showroom/deals/redeem/', json={'kind': 'business', 'item_id': 'b1'}, headers=h).status_code == 404


# --- Friends -------------------------------------------------------------------------------------------------

def test_friends_latest_buys_from_people_you_follow(world, wallets):
    uid, _ = _player(world)
    amina, _ = _player(world, name='amina')
    kofi, _ = _player(world, name='kofi')
    stranger, _ = _player(world, name='stranger')
    world.rows('user_follows').extend([{'follower_id': uid, 'following_id': amina}, {'follower_id': uid, 'following_id': kofi}])
    now = datetime.now(timezone.utc)
    recent, older, old = (now - timedelta(days=1)).isoformat(), (now - timedelta(days=3)).isoformat(), (now - timedelta(days=40)).isoformat()
    world.rows('player_homes').append({'player_id': amina, 'home_id': 'h1', 'purchased_at': older, 'is_active': True})
    world.rows('player_liabilities').append({'player_id': amina, 'liability_id': 'i1', 'purchase_date': recent, 'is_active': True})
    world.rows('user_assets').append({'user_id': kofi, 'asset_id': 'b1', 'created_at': old})                 # too long ago
    world.rows('player_liabilities').append({'player_id': stranger, 'liability_id': 'i2', 'purchase_date': recent, 'is_active': True})
    got = showroom.friends(uid, showroom._catalog())
    assert [(f['username'], f['name']) for f in got] == [('amina', 'Supercar')]   # one card per friend: the latest


def test_state_and_new_life(client, world, wallets):
    uid, h = _player(world)
    _at_week(world, uid, 1)
    showroom.wishlist_add(uid, 'item', 'i2')
    showroom.mark_seen(uid, [{'kind': 'item', 'item_id': 'i1'}])
    data = client.get('/api/showroom/', headers=h).get_json()['data']
    assert set(data) >= {'wishlist', 'deals', 'passed', 'friends', 'season', 'balance', 'week'}
    assert world.rows('showroom_deals')
    showroom.clear_for_new_life(uid)
    assert not world.rows('showroom_seen') and not world.rows('showroom_deals')
    assert len(world.rows('showroom_wishlist')) == 1                      # the wishlist carries over
