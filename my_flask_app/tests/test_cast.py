"""The cast (texts, relationships, gated cards), roommate co-op, avatars and the daily nudge."""
import uuid
from decimal import Decimal

import pytest

from app.game import cast, roommates, week_service
from app.game.weekly_cards import CARDS
from tests.conftest import make_token


@pytest.fixture
def player(fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    fake_supabase.rows('profiles').append({'user_id': user_id, 'username': 'me', 'sanity': 50, 'monthly_income': 0, 'base_monthly_income': 0})
    balance['amount'] = Decimal('1000')
    return fake_supabase.rows('profiles')[0]


def _friend(fake, name='alex'):
    uid = str(uuid.uuid4())
    fake.rows('profiles').append({'user_id': uid, 'username': name, 'sanity': 70, 'monthly_income': 0, 'base_monthly_income': 0})
    return uid


def _rent(fake, uid, rent=1000, name='Studio'):
    rid = f'r-{uid[:6]}'
    fake.rows('player_rentals').append({'id': rid, 'player_id': uid, 'monthly_rent': rent, 'is_active': True, 'rental_properties': {'name': name}})
    return rid


# --- avatars ---------------------------------------------------------------------------

def test_search_and_lookup_include_other_players_avatars(client, auth_headers, player, fake_supabase):
    friend = _friend(fake_supabase, 'alexis')
    fake_supabase.rows('player_lives').append({'user_id': friend, 'life_number': 1, 'background': 'scholarship', 'start_age': 18, 'avatar': {'skin': 4}, 'is_current': True})
    fake_supabase.rows('player_game_clock').append({'user_id': friend, 'week': 60, 'banked_weeks': 0, 'bank_updated_on': '2026-11-21'})
    found = client.get('/api/social/search/?query=alex', headers=auth_headers).get_json()['data']
    row = next(r for r in found if r['user_id'] == friend)
    assert row['avatar'] == {'skin': 4} and row['age'] == 19
    _friend(fake_supabase, 'alex_no_life')
    found = client.get('/api/social/search/?query=alex', headers=auth_headers).get_json()['data']
    assert next(r for r in found if r['username'] == 'alex_no_life')['avatar'] is None   # app shows the photo

    looked_up = client.get(f'/api/life/avatars/?ids={friend}', headers=auth_headers).get_json()['data']
    assert looked_up[friend]['background_emoji'] == '🎓'


# --- texts -----------------------------------------------------------------------------

def test_first_visit_gets_intro_texts(client, auth_headers, player):
    data = client.get('/api/texts/', headers=auth_headers).get_json()['data']
    keys = [t['character'] for t in data['threads']]
    assert set(keys) == {'mom', 'bestie', 'ex'}           # no roommate without a rental
    assert data['unread'] == 2


def test_replying_applies_effects_once(client, auth_headers, player, fake_supabase, user_id, balance):
    client.get('/api/texts/', headers=auth_headers)
    msg = next(m for m in fake_supabase.rows('cast_messages') if m['character'] == 'mom')
    res = client.post(f"/api/texts/messages/{msg['id']}/reply/", json={'reply_id': 'a'}, headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()['data']['relationship']['score'] == 53
    thread = client.get('/api/texts/mom/', headers=auth_headers).get_json()['data']
    bodies = [(m['from_player'], m['body']) for m in thread['messages']]
    assert (True, 'Yes mom ❤️') in bodies and (False, 'good. eat a vegetable too') in bodies
    again = client.post(f"/api/texts/messages/{msg['id']}/reply/", json={'reply_id': 'b'}, headers=auth_headers)
    assert again.status_code == 409
    assert cast.relationships(user_id)['mom'] == 53


def test_week_texts_react_to_what_happened(player, fake_supabase, user_id):
    receipt = {'week': 52, 'birthday': 19, 'is_payday_week': True, 'totals': {'cash': -300, 'sanity': -10},
               'month_summary': {'lines': [{'label': 'Missed rent: Studio', 'missed': True}]}, 'cards': []}
    assert cast.react_to_week(user_id, receipt) == cast.MAX_TEXTS_PER_WEEK
    sent = fake_supabase.rows('cast_messages')
    assert {m['character'] for m in sent} == {'mom', 'bestie'}
    assert 'BIRTHDAY' in sent[0]['body']


def test_birthday_gift_pays_out_on_reply(client, auth_headers, player, user_id, fake_supabase, balance):
    cast.react_to_week(user_id, {'week': 52, 'birthday': 19, 'totals': {}, 'cards': []})
    msg = next(m for m in fake_supabase.rows('cast_messages') if m['character'] == 'mom')
    client.post(f"/api/texts/messages/{msg['id']}/reply/", json={'reply_id': 'a'}, headers=auth_headers)
    assert balance['amount'] == Decimal('1050')
    assert player['sanity'] == 55


# --- the cast in the deck --------------------------------------------------------------------

def test_relationship_gates_cards(player, fake_supabase, user_id):
    keys = lambda: {c.get('key') for w in range(1, 30) for c in week_service.build_deck(user_id, w)}
    assert 'mom_care_package' not in keys()
    fake_supabase.rows('player_relationships').append({'user_id': user_id, 'character': 'mom', 'score': 80})
    assert 'mom_care_package' in keys()
    assert 'mom_worried' not in keys()


def test_cast_cards_change_relationships(client, auth_headers, player, fake_supabase, user_id, monkeypatch):
    monkeypatch.setattr(week_service, 'build_deck', lambda uid, week: [
        {**week_service._everyday_card(next(c for c in CARDS if c['key'] == 'birthday_dinner')), 'id': 'c1', 'chosen': None, 'result': None}])
    deck = client.get('/api/week/', headers=auth_headers).get_json()['data']['deck']['cards']
    assert deck[0]['character']['name'] == 'Jordan'
    res = client.post('/api/week/cards/c1/choose/', json={'choice_id': 'right'}, headers=auth_headers)
    assert res.get_json()['data']['result']['rel'] == 5
    assert cast.relationships(user_id)['bestie'] == 55


def test_roommate_cards_use_your_real_roommates_name(player, fake_supabase, user_id):
    friend = _friend(fake_supabase, 'alex')
    _rent(fake_supabase, user_id)
    fake_supabase.rows('roommates').append({'id': 'rm1', 'leaseholder_id': user_id, 'roommate_id': friend, 'status': 'active', 'rent_share': 0.5})
    ctx = week_service._player_context(user_id)
    card = week_service._everyday_card(next(c for c in CARDS if c['key'] == 'roommate_party'), ctx)
    assert card['body'].startswith('alex wants to throw a party')
    assert 'roommate' not in cast.present_cast(user_id)       # no fake Sam texting you


# --- roommates -------------------------------------------------------------------------------

def _follow(fake, a, b):
    fake.rows('user_follows').append({'id': str(uuid.uuid4()), 'follower_id': a, 'following_id': b})


def test_invite_rules(client, auth_headers, player, fake_supabase, user_id, monkeypatch):
    from app.services.push_notification_service import ExpoPushService
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user', classmethod(lambda cls, *a, **k: True))
    friend = _friend(fake_supabase)
    post = lambda: client.post('/api/roommates/invite/', json={'user_id': friend}, headers=auth_headers)
    assert post().get_json()['error'] == 'NO_RENTAL'
    _rent(fake_supabase, user_id)
    assert post().get_json()['error'] == 'NOT_FOLLOWING'
    _follow(fake_supabase, user_id, friend)
    res = post()
    assert res.status_code == 200 and res.get_json()['data']['invites_sent'][0]['to']['username'] == 'alex'
    assert post().get_json()['error'] == 'ALREADY_INVITED'
    assert fake_supabase.rows('notifications')[-1]['user_id'] == friend


def test_accept_split_rent_and_leave(client, player, fake_supabase, user_id, balance, monkeypatch):
    from app.services.push_notification_service import ExpoPushService
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user', classmethod(lambda cls, *a, **k: True))
    friend = _friend(fake_supabase)
    _rent(fake_supabase, user_id, rent=1000)
    _follow(fake_supabase, user_id, friend)
    roommates.invite(user_id, friend)
    arr = fake_supabase.rows('roommates')[0]

    friend_headers = {'Authorization': f'Bearer {make_token(friend)}'}
    rid = _rent(fake_supabase, friend, rent=700, name='Own flat')
    res = client.post(f"/api/roommates/{arr['id']}/accept/", headers=friend_headers)
    assert res.get_json()['error'] == 'MOVE_OUT_FIRST'
    next(r for r in fake_supabase.rows('player_rentals') if r['id'] == rid)['is_active'] = False

    res = client.post(f"/api/roommates/{arr['id']}/accept/", headers=friend_headers)
    assert res.status_code == 200
    active = res.get_json()['data']['active']
    assert active['role'] == 'roommate' and active['share_amount'] == 500 and active['with']['username'] == 'me'

    # The roommate's month: they pay $500 to the leaseholder (shared test wallet, so check the log).
    from jobs.monthly_loan_deductions import process_month_for_user
    month = process_month_for_user(friend)
    assert {'label': 'Rent share: Studio', 'amount': -500.0, 'missed': False} in month['lines']
    reasons = [r for _, _, r in balance['log']]
    assert 'Rent share: Studio' in reasons and "Roommate's rent share" in reasons

    assert client.post('/api/roommates/leave/', headers=friend_headers).status_code == 200
    assert roommates.active_for(user_id) is None


def test_new_life_ends_the_arrangement_and_relationships(client, auth_headers, player, fake_supabase, user_id):
    friend = _friend(fake_supabase)
    fake_supabase.rows('roommates').append({'id': 'rm1', 'leaseholder_id': friend, 'roommate_id': user_id, 'status': 'active', 'rent_share': 0.5})
    fake_supabase.rows('player_relationships').append({'user_id': user_id, 'character': 'mom', 'score': 90})
    assert client.post('/api/life/begin/', json={'background': 'scholarship', 'avatar': {}}, headers=auth_headers).status_code == 200
    assert fake_supabase.rows('roommates')[0]['status'] == 'ended'
    assert cast.relationships(user_id)['mom'] == 50


# --- daily nudge -----------------------------------------------------------------------------

def test_week_ready_nudge_is_capped_and_relevant(player, fake_supabase, user_id, monkeypatch):
    from jobs import week_ready_nudge as job
    sent = []
    monkeypatch.setattr(job.ExpoPushService, 'send_notifications_to_users',
                        classmethod(lambda cls, supabase_client, user_notifications, notification_type: sent.extend(user_notifications) or {'success': len(user_notifications)}))
    monkeypatch.setattr('jobs.run_guard.claim_daily_run', lambda name: '2026-11-21')
    player['expo_push_token'] = 'ExponentPushToken[x]'
    idle = _friend(fake_supabase, 'idle')
    fake_supabase.rows('profiles')[-1]['expo_push_token'] = 'ExponentPushToken[y]'
    today = week_service._today().isoformat()
    fake_supabase.rows('player_game_clock').extend([
        {'user_id': user_id, 'week': 4, 'banked_weeks': 1, 'bank_updated_on': today},
        {'user_id': idle, 'week': 2, 'banked_weeks': 0, 'bank_updated_on': today},   # nothing waiting
    ])
    assert job.run_week_ready_nudge()['queued'] == 1
    assert sent[0]['user_id'] == user_id and 'payday' in sent[0]['body']
    assert sent[0]['data'] == {'screen': '/week'}
    sent.clear()
    assert job.run_week_ready_nudge()['queued'] == 0          # already nudged today


# --- housing and texts: loose ends ------------------------------------------------------------

def _roommates_active(fake, holder, mate):
    fake.rows('roommates').append({'id': 'rm9', 'leaseholder_id': holder, 'roommate_id': mate, 'status': 'active', 'rent_share': 0.5})


def test_the_leaseholder_moving_out_ends_the_roommate_arrangement(client, auth_headers, player, fake_supabase, user_id):
    friend = _friend(fake_supabase)
    rid = _rent(fake_supabase, user_id)
    _roommates_active(fake_supabase, user_id, friend)
    fake_supabase.rows('roommates').append({'id': 'rm10', 'leaseholder_id': user_id, 'roommate_id': 'someone', 'status': 'pending', 'rent_share': 0.5})
    res = client.post('/api/rentals/moveout/', json={}, headers=auth_headers)
    assert res.status_code == 200
    assert roommates.active_for(friend) is None and roommates.active_for(user_id) is None
    assert {r['status'] for r in fake_supabase.rows('roommates')} <= {'ended', 'declined'}


def test_a_roommate_who_rents_their_own_place_stops_sharing(client, auth_headers, player, fake_supabase, user_id, balance):
    friend = _friend(fake_supabase)
    _rent(fake_supabase, friend)
    _roommates_active(fake_supabase, friend, user_id)
    fake_supabase.rows('rental_properties').append({'id': '5b1f0d3e-0000-4000-8000-000000000001', 'name': 'Own flat', 'monthly_rent': 400, 'property_type': 'studio'})
    res = client.post('/api/rentals/rent/', json={'property_id': '5b1f0d3e-0000-4000-8000-000000000001'}, headers=auth_headers)
    assert res.status_code == 200, res.get_json()
    assert roommates.active_for(user_id) is None


def test_moving_out_survives_a_rental_whose_property_is_gone(client, auth_headers, player, fake_supabase, user_id):
    fake_supabase.rows('player_rentals').append({'id': 'r-gone', 'player_id': user_id, 'monthly_rent': 500, 'is_active': True, 'rental_properties': None})
    assert client.post('/api/rentals/moveout/', json={}, headers=auth_headers).status_code == 200


def test_unread_badge_ignores_texts_from_people_no_longer_in_your_life(player, fake_supabase, user_id):
    cast.send(user_id, 'roommate', 'band practice friday?')           # Sam, but you don't rent
    cast.send(user_id, 'mom', 'call me')
    assert cast.unread_count(user_id) == 1                            # only Mom's thread can be opened


def test_a_failed_payment_leaves_the_reply_open(client, auth_headers, player, fake_supabase, user_id, balance, monkeypatch):
    msg = cast.send(user_id, 'bestie', 'drinks?', replies=[cast._opt('a', 'Sure', 'yay', rel=3, cash=-15)])
    from app.services.balance_service import BalanceService

    def boom(*a, **k):
        raise RuntimeError('db down')
    monkeypatch.setattr(BalanceService, 'subtract_balance', staticmethod(boom))
    assert client.post(f"/api/texts/messages/{msg['id']}/reply/", json={'reply_id': 'a'}, headers=auth_headers).status_code == 500
    assert next(m for m in fake_supabase.rows('cast_messages') if m['id'] == msg['id'])['replied_with'] is None
    assert cast.relationships(user_id)['bestie'] == 50
