"""Squads: create/join/leave, the weekly race and goal, settlement, the feed, and the week hook."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.game import squads
from tests.conftest import make_token
from tests.test_week import _play_week

MONDAY = date(2026, 11, 23)


@pytest.fixture
def player(fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    monkeypatch.setattr(squads, '_today', lambda: MONDAY + timedelta(days=2))
    from app.services.push_notification_service import ExpoPushService
    pushes = []
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user',
                        classmethod(lambda cls, sb, uid, title, body, **k: pushes.append((uid, title)) or True))
    fake_supabase.rows('profiles').append({'user_id': user_id, 'username': 'me', 'sanity': 50, 'net_worth': 1000,
                                           'monthly_income': 0, 'base_monthly_income': 0, 'credit_score': 650})
    balance['amount'] = Decimal('1000')
    return pushes


def _friend(fake, name='alex', net_worth=5000):
    uid = str(uuid.uuid4())
    fake.rows('profiles').append({'user_id': uid, 'username': name, 'sanity': 70, 'net_worth': net_worth})
    return uid, {'Authorization': f'Bearer {make_token(uid)}'}


def _profile(fake, uid):
    return next(p for p in fake.rows('profiles') if p['user_id'] == uid)


def _create(client, headers, name='The Broke Club', emoji='🍕'):
    res = client.post('/api/squads/', json={'name': name, 'emoji': emoji}, headers=headers)
    assert res.status_code == 200, res.get_json()
    return res.get_json()['data']['squad']


def test_no_squad_yet(client, auth_headers, player):
    data = client.get('/api/squads/', headers=auth_headers).get_json()['data']
    assert data['squad'] is None and data['max_members'] == 8 and '🔥' in data['reactions']


def test_create_join_and_one_squad_each(client, auth_headers, player, fake_supabase, user_id):
    squad = _create(client, auth_headers)
    assert squad['is_owner'] and len(squad['code']) == 6 and squad['emoji'] == '🍕'
    assert squad['goal'] == {'played': 0, 'target': 3, 'hit': False, 'reward_sanity': 5}
    assert client.post('/api/squads/', json={'name': 'Again'}, headers=auth_headers).get_json()['error'] == 'ALREADY_IN_SQUAD'

    friend, fh = _friend(fake_supabase)
    preview = client.get(f"/api/squads/preview/?code={squad['code'].lower()}", headers=fh).get_json()['data']
    assert preview == {'name': 'The Broke Club', 'emoji': '🍕', 'members': 1, 'max_members': 8}
    assert client.post('/api/squads/join/', json={'code': 'NOPE00'}, headers=fh).status_code == 404
    joined = client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh).get_json()['data']['squad']
    assert [m['username'] for m in joined['members']] and len(joined['members']) == 2
    assert joined['goal']['target'] == 6 and not joined['is_owner']
    assert client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh).get_json()['error'] == 'ALREADY_MEMBER'
    assert [f['kind'] for f in joined['feed']] == ['joined', 'created']
    assert player[-1] == (user_id, '👋 alex joined 🍕 The Broke Club')     # the owner was told


def test_name_rules(client, auth_headers, player):
    assert client.post('/api/squads/', json={'name': ' a '}, headers=auth_headers).get_json()['error'] == 'INVALID_NAME'
    squad = _create(client, auth_headers, name='  Night   Shift  ', emoji='not-an-emoji')
    assert squad['name'] == 'Night Shift' and squad['emoji'] == squads.EMOJIS[0]


def test_squad_full(client, auth_headers, player, fake_supabase, monkeypatch):
    monkeypatch.setattr(squads, 'MAX_MEMBERS', 2)
    squad = _create(client, auth_headers)
    _, a = _friend(fake_supabase, 'a')
    _, b = _friend(fake_supabase, 'b')
    assert client.post('/api/squads/join/', json={'code': squad['code']}, headers=a).status_code == 200
    assert client.post('/api/squads/join/', json={'code': squad['code']}, headers=b).get_json()['error'] == 'SQUAD_FULL'


def test_race_ranks_by_growth_not_net_worth(client, auth_headers, player, fake_supabase, user_id):
    squad = _create(client, auth_headers)
    rich, rh = _friend(fake_supabase, 'rich', net_worth=50000)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=rh)
    _profile(fake_supabase, user_id)['net_worth'] = 1600       # +600 this week
    _profile(fake_supabase, rich)['net_worth'] = 49800         # -200 this week
    members = client.get('/api/squads/', headers=auth_headers).get_json()['data']['squad']['members']
    assert [(m['username'], m['growth']) for m in members] == [('me', 600), ('rich', -200)]
    assert members[0]['is_me']


def test_goal_rewards_everyone_once_and_builds_a_streak(player, fake_supabase, user_id, client, auth_headers):
    squad = _create(client, auth_headers)
    friend, fh = _friend(fake_supabase)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh)
    receipt = {'cards': [], 'totals': {}}
    for _ in range(5):
        out = squads.record_week(user_id, receipt)
        assert not out['goal_hit']
    out = squads.record_week(friend, receipt)
    assert out['just_hit'] and out['played'] == 6 and out['target'] == 6 and out['streak'] == 1
    assert _profile(fake_supabase, user_id)['sanity'] == 55 and _profile(fake_supabase, friend)['sanity'] == 75
    again = squads.record_week(user_id, receipt)
    assert again['goal_hit'] and not again['just_hit']
    assert _profile(fake_supabase, user_id)['sanity'] == 55          # once a week
    assert any(f['kind'] == 'goal' for f in fake_supabase.rows('squad_feed'))
    assert any(uid == user_id and '🎯' in title for uid, title in player)   # the other member got a push


def test_squad_hopping_cant_farm_the_reward(player, fake_supabase, user_id, client, auth_headers):
    a = _create(client, auth_headers, name='First')
    for _ in range(3):
        squads.record_week(user_id, {'cards': []})
    assert _profile(fake_supabase, user_id)['sanity'] == 55
    client.post('/api/squads/leave/', headers=auth_headers)
    _create(client, auth_headers, name='Second')
    for _ in range(3):
        out = squads.record_week(user_id, {'cards': []})
    assert out['just_hit'] and _profile(fake_supabase, user_id)['sanity'] == 55
    assert a['id'] not in {s['id'] for s in fake_supabase.rows('squads')}   # the empty squad was deleted


def test_new_week_settles_mvp_and_streak(player, fake_supabase, user_id, client, auth_headers, monkeypatch):
    squad = _create(client, auth_headers)
    friend, fh = _friend(fake_supabase)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh)
    for uid in (user_id, user_id, user_id, friend, friend, friend):
        squads.record_week(uid, {'cards': []})
    _profile(fake_supabase, friend)['net_worth'] = 5900     # +900, the most
    _profile(fake_supabase, user_id)['net_worth'] = 1100    # +100

    monkeypatch.setattr(squads, '_today', lambda: MONDAY + timedelta(days=8))
    s = client.get('/api/squads/', headers=auth_headers).get_json()['data']['squad']
    assert s['last_mvp']['username'] == 'alex' and s['last_mvp']['growth'] == 900
    assert next(m for m in s['members'] if m['username'] == 'alex')['is_mvp']
    assert s['streak'] == 1 and s['goal']['played'] == 0 and not s['goal']['hit']
    assert all(m['growth'] == 0 for m in s['members'])        # new baselines
    assert s['feed'][0]['kind'] == 'mvp'
    assert sum(1 for f in fake_supabase.rows('squad_feed') if f['kind'] == 'mvp') == 1
    client.get('/api/squads/', headers=fh)                    # settled once only
    assert sum(1 for f in fake_supabase.rows('squad_feed') if f['kind'] == 'mvp') == 1

    # A whole week without hitting the goal breaks the streak.
    monkeypatch.setattr(squads, '_today', lambda: MONDAY + timedelta(days=15))
    assert client.get('/api/squads/', headers=auth_headers).get_json()['data']['squad']['streak'] == 0


def test_feed_posts_highlights_and_reactions(player, fake_supabase, user_id, client, auth_headers):
    squad = _create(client, auth_headers)
    friend, fh = _friend(fake_supabase)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh)
    squads.record_week(user_id, {
        'birthday': 21, 'month_summary': {'net': 1250},
        'cards': [{'title': 'Side hustle', 'icon': '🧾', 'choice': 'Take it', 'cash': 800}],
    })
    feed = client.get('/api/squads/', headers=fh).get_json()['data']['squad']['feed']
    mine = [f for f in feed if f['username'] == 'me' and f['kind'] in ('birthday', 'payday', 'swing')]
    assert [f['body'] for f in mine] == ['closed the month at +$1,250', 'turned 21']   # max 2: the swing didn't fit
    post = mine[0]['id']
    r = client.post(f'/api/squads/feed/{post}/react/', json={'emoji': '🔥'}, headers=fh).get_json()['data']
    assert r == {'id': post, 'reactions': {'🔥': 1}, 'my_reaction': '🔥'}
    r = client.post(f'/api/squads/feed/{post}/react/', json={'emoji': '💀'}, headers=fh).get_json()['data']
    assert r['reactions'] == {'💀': 1}
    r = client.post(f'/api/squads/feed/{post}/react/', json={'emoji': '💀'}, headers=fh).get_json()['data']
    assert r['reactions'] == {} and r['my_reaction'] is None
    assert client.post(f'/api/squads/feed/{post}/react/', json={'emoji': '🍆'}, headers=fh).status_code == 400
    outsider, oh = _friend(fake_supabase, 'stranger')
    assert client.post(f'/api/squads/feed/{post}/react/', json={'emoji': '🔥'}, headers=oh).status_code == 404


def test_owner_leaving_hands_over_and_owner_can_remove(player, fake_supabase, user_id, client, auth_headers):
    squad = _create(client, auth_headers)
    friend, fh = _friend(fake_supabase)
    other, oh = _friend(fake_supabase, 'sam')
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=oh)
    assert client.post(f'/api/squads/members/{other}/remove/', headers=fh).get_json()['error'] == 'NOT_OWNER'
    assert client.post('/api/squads/leave/', headers=auth_headers).get_json()['data']['squad'] is None
    s = client.get('/api/squads/', headers=fh).get_json()['data']['squad']
    assert s['is_owner'] and len(s['members']) == 2
    assert client.post(f'/api/squads/members/{other}/remove/', headers=fh).status_code == 200
    assert client.get('/api/squads/', headers=oh).get_json()['data']['squad'] is None
    assert fake_supabase.rows('notifications')[-1]['user_id'] == other


def test_invite_needs_a_follow_and_only_once(player, fake_supabase, user_id, client, auth_headers):
    squad = _create(client, auth_headers)
    friend, _ = _friend(fake_supabase)
    post = lambda: client.post('/api/squads/invite/', json={'user_id': friend}, headers=auth_headers)
    assert post().get_json()['error'] == 'NOT_FOLLOWING'
    fake_supabase.rows('user_follows').append({'id': 'f1', 'follower_id': user_id, 'following_id': friend})
    assert post().status_code == 200
    note = fake_supabase.rows('notifications')[-1]
    assert note['user_id'] == friend and squad['code'] in note['message']
    assert player[-1] == (friend, f"🍕 me invited you to The Broke Club")
    assert post().get_json()['error'] == 'ALREADY_INVITED'


def test_finishing_a_week_counts_for_the_squad(client, auth_headers, player, fake_supabase, user_id):
    _create(client, auth_headers)
    res = _play_week(client, auth_headers)
    assert res.status_code == 200, res.get_json()
    sq = res.get_json()['data']['receipt']['squad']
    assert sq['played'] == 1 and sq['target'] == 3 and sq['name'] == 'The Broke Club'
    row = fake_supabase.rows('squad_member_weeks')[0]
    assert row['start_net_worth'] == 1000          # baseline taken before the first card


def test_week_without_a_squad_has_no_squad_block(client, auth_headers, player):
    res = _play_week(client, auth_headers)
    assert res.get_json()['data']['receipt']['squad'] is None


def test_new_life_resets_this_weeks_growth(player, fake_supabase, user_id, client, auth_headers):
    _create(client, auth_headers)
    squads.ensure_baseline(user_id)
    _profile(fake_supabase, user_id)['net_worth'] = 200
    squads.on_life_started(user_id, 2, 'Moved Out at 17', '🎒', reset=True)
    s = client.get('/api/squads/', headers=auth_headers).get_json()['data']['squad']
    assert s['members'][0]['growth'] == 0
    assert s['feed'][0]['body'] == 'started life #2 as Moved Out at 17'


def test_only_the_owner_can_rename(player, fake_supabase, user_id, client, auth_headers):
    squad = _create(client, auth_headers)
    _, fh = _friend(fake_supabase)
    client.post('/api/squads/join/', json={'code': squad['code']}, headers=fh)
    assert client.put('/api/squads/', json={'name': 'Hijacked'}, headers=fh).get_json()['error'] == 'NOT_OWNER'
    assert client.put('/api/squads/', json={'name': 'x'}, headers=auth_headers).get_json()['error'] == 'INVALID_NAME'
    renamed = client.put('/api/squads/', json={'name': '  Night   Shift ', 'emoji': '🦈'}, headers=auth_headers).get_json()['data']['squad']
    assert (renamed['name'], renamed['emoji'], renamed['code']) == ('Night Shift', '🦈', squad['code'])
    assert client.get('/api/squads/', headers=fh).get_json()['data']['squad']['name'] == 'Night Shift'
