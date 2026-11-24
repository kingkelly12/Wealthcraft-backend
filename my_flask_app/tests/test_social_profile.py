"""Following, the activity timeline, home moves reaching followers, and the profile overview."""
import uuid
from decimal import Decimal

import pytest

from app import db
from app.models.profile import Profile
from app.services.push_notification_service import ExpoPushService
from tests.conftest import make_token
from tests.test_economy import wallets  # noqa: F401 (fixture)

# The real follower alert, captured before the wallets fixture swaps in a stub.
_REAL_NOTIFY = ExpoPushService.__dict__['notify_followers_of_financial_move']


def _person(fake, name, net_worth=0):
    uid = str(uuid.uuid4())
    fake.rows('profiles').append({'user_id': uid, 'username': name, 'net_worth': net_worth, 'monthly_income': 3000, 'credit_score': 700})
    db.session.add(Profile(user_id=uuid.UUID(uid), username=name, net_worth=net_worth))
    db.session.commit()
    return uid, {'Authorization': f'Bearer {make_token(uid)}'}


@pytest.fixture
def social(fake_supabase, wallets, monkeypatch):  # after wallets: it stubs pushes too
    pushes = []
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user',
                        classmethod(lambda cls, supabase_client=None, user_id=None, title='', body='', **kw: pushes.append((user_id, title, body)) or True))
    monkeypatch.setattr(ExpoPushService, 'send_notifications_to_users',
                        classmethod(lambda cls, supabase_client=None, user_notifications=(), **kw: pushes.extend((n['user_id'], n['title'], n['body']) for n in user_notifications) or {'success': len(user_notifications)}))
    monkeypatch.setattr('app.utils.background_task.run_in_background', lambda fn, *a, **k: fn(*a, **k))
    monkeypatch.setattr(ExpoPushService, 'notify_followers_of_financial_move', _REAL_NOTIFY)
    fake_supabase.pushes = pushes
    return fake_supabase


def test_follow_alert_names_the_follower_and_asks_to_follow_back(client, social):
    amina, ha = _person(social, 'amina')
    kofi, hk = _person(social, 'kofi')
    assert client.post('/api/social/follow/', json={'target_user_id': kofi}, headers=ha).get_json()['success']
    note = social.rows('notifications')[-1]
    assert note['user_id'] == kofi and note['message'] == 'amina started following you. Follow back?'
    assert 'Student' not in note['title'] and 'mentor' not in note['message'].lower()
    assert social.pushes[-1] == (kofi, '👋 New follower', 'amina started following you. Follow back?')
    # Kofi follows back: Amina's alert doesn't ask her to follow back (she already does).
    client.post('/api/social/follow/', json={'target_user_id': amina}, headers=hk)
    assert social.rows('notifications')[-1]['message'] == 'kofi started following you.'


def test_moves_land_on_the_players_timeline_and_reach_followers(client, social):
    amina, _ = _person(social, 'amina')
    kofi, _ = _person(social, 'kofi')
    social.rows('user_follows').append({'follower_id': kofi, 'following_id': amina})
    ExpoPushService.notify_followers_of_financial_move(social, amina, 'buy_home', 'Lakehouse', amount=650000.0)
    act = social.rows('player_activity')[-1]
    assert act['user_id'] == amina and act['text'] == 'Bought the Lakehouse' and act['emoji'] == '🔑' and act['amount'] == 650000.0
    assert social.pushes[-1][0] == kofi and 'amina just bought the Lakehouse' in social.pushes[-1][2]


def test_buying_a_home_tells_followers(client, social, wallets, monkeypatch):
    from app.game import homes
    social.rows('home_listings').append({'id': 'h1', 'name': 'Bungalow', 'home_type': 'bungalow', 'price': 300000, 'market_rent': 2500,
                                         'location': 'Leafy', 'upkeep': []})
    monkeypatch.setattr(homes, '_recalc', lambda uid: None)
    monkeypatch.setattr('app.routes.home_routes.enforce_mission_constraints', lambda *a, **k: None)
    told = []
    monkeypatch.setattr(ExpoPushService, 'notify_followers_of_financial_move',
                        classmethod(lambda cls, **kw: told.append((kw['move_type'], kw['item_name'], kw['amount']))))
    uid, h = _person(social, 'amina')
    wallets[uid] = Decimal('400000')
    assert client.post('/api/homes/buy/', json={'home_id': 'h1'}, headers=h).get_json()['success']
    assert told == [('buy_home', 'Bungalow', 300000.0)]
    # A failed buy tells no one.
    wallets[uid] = Decimal('10')
    client.post('/api/homes/buy/', json={'home_id': 'h1'}, headers=h)
    assert len(told) == 1


def test_profile_overview_has_the_grid_timeline_balance_sheet_and_relationship(client, social, wallets):
    me, hm = _person(social, 'me')
    them, _ = _person(social, 'amina', net_worth=500000)
    wallets[them] = Decimal('12000')
    social.rows('user_follows').append({'follower_id': them, 'following_id': me})          # they follow me, not back
    social.rows('liability_items').append({'id': 'i1', 'name': 'Supercar', 'category': 'vehicle', 'base_price': 380000, 'image_url': 'https://x/car.jpg'})
    social.rows('player_liabilities').append({'id': 'pl1', 'player_id': them, 'liability_id': 'i1', 'purchase_price': 380000, 'current_value': 342000,
                                              'is_active': True, 'liability_items': {'name': 'Supercar', 'category': 'vehicle', 'image_url': 'https://x/car.jpg'}})
    social.rows('assets').extend([{'id': 'b1', 'name': 'Coffee Kiosk', 'category': 'business', 'image_url': 'https://x/kiosk.jpg'},
                                  {'id': 's1', 'name': 'Index Fund', 'category': 'stocks'}])
    social.rows('user_assets').extend([{'id': 'ua1', 'user_id': them, 'asset_id': 'b1', 'value': 22000},
                                       {'id': 'ua2', 'user_id': them, 'asset_id': 's1', 'value': 5000}])
    social.rows('liabilities').append({'user_id': them, 'remaining_balance': 18000})
    social.rows('player_activity').append({'id': 'a1', 'user_id': them, 'kind': 'buy_liability', 'emoji': '🛍️', 'text': 'Bought the Supercar',
                                           'created_at': '2026-11-20T10:00:00+00:00'})
    data = client.get(f'/api/profile/overview/?user_id={them}', headers=hm).get_json()['data']
    assert data['relationship'] == {'is_following': False, 'follows_you': True}
    assert [(t['kind'], t['name'], t['value']) for t in data['owned']] == [('item', 'Supercar', 342000.0), ('business', 'Coffee Kiosk', 22000.0)]
    assert data['owned'][0]['image_url'] == 'https://x/car.jpg'
    assert data['balance_sheet'] == {'cash': 12000.0, 'investments': 5000.0, 'businesses': 22000.0, 'homes': 0, 'possessions': 342000.0, 'debt': 18000.0}
    assert data['activity'][0]['text'] == 'Bought the Supercar'
    # Your own profile has no relationship block.
    assert client.get('/api/profile/overview/', headers=hm).get_json()['data']['relationship'] is None
