"""Push notifications: batching, ticket/receipt handling, token ownership."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.push_notification_service import ExpoPushService
from tests.conftest import make_token


class _Resp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code, self.content = payload, status, b'x'

    def json(self):
        return self._payload


@pytest.fixture
def expo(monkeypatch):
    """Capture Expo HTTP calls. `expo.tickets` decides the ticket for each token."""
    class Expo:
        sends, receipt_requests = [], []
        tickets = {}      # token -> ticket dict (default: ok)
        receipts = {}     # ticket_id -> receipt dict
        fail_http = False

    def post(url, json=None, headers=None, timeout=None):
        if Expo.fail_http:
            raise ConnectionError('network down')
        if url == ExpoPushService.EXPO_RECEIPTS_URL:
            Expo.receipt_requests.append(json['ids'])
            return _Resp({'data': {i: Expo.receipts[i] for i in json['ids'] if i in Expo.receipts}})
        Expo.sends.append(json)
        return _Resp({'data': [Expo.tickets.get(m['to'], {'status': 'ok', 'id': 'tk-' + m['to']}) for m in json]})

    monkeypatch.setattr('app.services.push_notification_service.requests.post', post)
    Expo.sends, Expo.receipt_requests, Expo.tickets, Expo.receipts = [], [], {}, {}
    return Expo


def _player(fake, uid, token=None):
    fake.rows('profiles').append({'user_id': uid, 'username': f'p{uid}', 'expo_push_token': token})


def _token(fake, uid):
    return next(p for p in fake.rows('profiles') if p['user_id'] == uid)['expo_push_token']


def test_validate_accepts_both_expo_formats():
    assert ExpoPushService.validate_push_token('ExponentPushToken[abc]')
    assert ExpoPushService.validate_push_token('ExpoPushToken[abc]')
    for bad in (None, '', 'abc', 'ExponentPushToken[abc', 'fcm:xyz', 'ExpoPushToken[' + 'x' * 300 + ']'):
        assert not ExpoPushService.validate_push_token(bad)


def test_batches_of_100_one_token_query(fake_supabase, expo):
    for i in range(250):
        _player(fake_supabase, f'u{i}', f'ExponentPushToken[{i}]')
    _player(fake_supabase, 'no-token')
    result = ExpoPushService.send_notifications_to_users(
        fake_supabase, [{'user_id': f'u{i}', 'title': 't', 'body': 'b'} for i in range(250)]
        + [{'user_id': 'no-token', 'title': 't', 'body': 'b'}], notification_type='week_ready')
    assert result == {'success': 250, 'failed': 0, 'skipped': 1}
    assert [len(batch) for batch in expo.sends] == [100, 100, 50]
    assert len([c for c in fake_supabase.calls if c[:2] == ('select', 'profiles')]) == 2  # 200 ids per query
    assert len(fake_supabase.rows('push_tickets')) == 250


def test_no_http_call_when_nobody_has_a_token(fake_supabase, expo):
    _player(fake_supabase, 'u1')
    assert ExpoPushService.send_notification_to_user(fake_supabase, 'u1', 't', 'b') is False
    assert expo.sends == []


def test_caller_type_wins_over_generic_type(fake_supabase, expo):
    _player(fake_supabase, 'u1', 'ExponentPushToken[1]')
    ExpoPushService.send_notification_to_user(fake_supabase, 'u1', 't', 'b', notification_type='mentor_message',
                                              data={'type': 'mentor', 'mentorId': 'm1'})
    ExpoPushService.send_notification_to_user(fake_supabase, 'u1', 't', 'b', notification_type='follow')
    assert expo.sends[0][0]['data']['type'] == 'mentor'
    assert expo.sends[1][0]['data']['type'] == 'follow'


def test_only_device_not_registered_clears_the_token(fake_supabase, expo):
    _player(fake_supabase, 'gone', 'ExponentPushToken[gone]')
    _player(fake_supabase, 'cfg', 'ExponentPushToken[cfg]')
    expo.tickets = {
        'ExponentPushToken[gone]': {'status': 'error', 'message': 'not registered', 'details': {'error': 'DeviceNotRegistered'}},
        'ExponentPushToken[cfg]': {'status': 'error', 'message': 'bad FCM key', 'details': {'error': 'InvalidCredentials'}},
    }
    result = ExpoPushService.send_notifications_to_users(
        fake_supabase, [{'user_id': 'gone', 'title': 't', 'body': 'b'}, {'user_id': 'cfg', 'title': 't', 'body': 'b'}])
    assert result['failed'] == 2
    assert _token(fake_supabase, 'gone') is None
    assert _token(fake_supabase, 'cfg') == 'ExponentPushToken[cfg]'  # project problem, not the device's


def test_network_failure_fails_softly(fake_supabase, expo):
    _player(fake_supabase, 'u1', 'ExponentPushToken[1]')
    expo.fail_http = True
    assert ExpoPushService.send_notification_to_user(fake_supabase, 'u1', 't', 'b') is False
    assert _token(fake_supabase, 'u1') == 'ExponentPushToken[1]'


def test_receipts_clear_dead_tokens_but_not_re_registered_ones(fake_supabase, expo):
    old = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
    new = datetime.now(timezone.utc).isoformat()
    _player(fake_supabase, 'gone', 'ExponentPushToken[gone]')
    _player(fake_supabase, 'moved', 'ExponentPushToken[new-phone]')  # re-registered since the push
    fake_supabase.rows('push_tickets').extend([
        {'ticket_id': 't1', 'user_id': 'gone', 'token': 'ExponentPushToken[gone]', 'created_at': old},
        {'ticket_id': 't2', 'user_id': 'moved', 'token': 'ExponentPushToken[old-phone]', 'created_at': old},
        {'ticket_id': 't3', 'user_id': 'gone', 'token': 'ExponentPushToken[gone]', 'created_at': old},  # not ready yet
        {'ticket_id': 't4', 'user_id': 'gone', 'token': 'ExponentPushToken[gone]', 'created_at': new},  # too fresh
    ])
    dead = {'status': 'error', 'message': 'gone', 'details': {'error': 'DeviceNotRegistered'}}
    expo.receipts = {'t1': dead, 't2': dead}

    result = ExpoPushService.check_receipts(fake_supabase)

    assert result == {'checked': 2, 'errors': 2, 'dead_tokens_cleared': 2}
    assert _token(fake_supabase, 'gone') is None
    assert _token(fake_supabase, 'moved') == 'ExponentPushToken[new-phone]'
    assert sorted(t['ticket_id'] for t in fake_supabase.rows('push_tickets')) == ['t3', 't4']
    assert expo.receipt_requests == [['t1', 't2', 't3']]


def test_register_token_takes_it_off_the_previous_owner(client, fake_supabase, user_id):
    _player(fake_supabase, user_id)
    _player(fake_supabase, 'previous-owner', 'ExponentPushToken[shared-phone]')
    r = client.post('/api/notifications/register-token/', json={'push_token': 'ExponentPushToken[shared-phone]'},
                    headers={'Authorization': f'Bearer {make_token(user_id)}'})
    assert r.status_code == 200
    assert _token(fake_supabase, user_id) == 'ExponentPushToken[shared-phone]'
    assert _token(fake_supabase, 'previous-owner') is None


def test_register_token_accepts_expo_push_token_form(client, fake_supabase, user_id):
    _player(fake_supabase, user_id)
    r = client.post('/api/notifications/register-token/', json={'push_token': 'ExpoPushToken[xyz]'},
                    headers={'Authorization': f'Bearer {make_token(user_id)}'})
    assert r.status_code == 200


def test_unregister_from_old_phone_keeps_current_phone(client, fake_supabase, user_id):
    _player(fake_supabase, user_id, 'ExponentPushToken[current-phone]')
    h = {'Authorization': f'Bearer {make_token(user_id)}'}
    r = client.delete('/api/notifications/unregister-token/?push_token=ExponentPushToken[old-phone]', headers=h)
    assert r.status_code == 200 and _token(fake_supabase, user_id) == 'ExponentPushToken[current-phone]'
    r = client.delete('/api/notifications/unregister-token/?push_token=ExponentPushToken[current-phone]', headers=h)
    assert r.status_code == 200 and _token(fake_supabase, user_id) is None


def test_followers_get_feed_rows_and_one_batched_push(fake_supabase, expo, monkeypatch):
    monkeypatch.setattr('app.utils.background_task.run_in_background', lambda fn, *a, **k: fn(*a, **k))
    _player(fake_supabase, 'student')
    for i in range(3):
        _player(fake_supabase, f'f{i}', f'ExponentPushToken[f{i}]')
        fake_supabase.rows('user_follows').append({'follower_id': f'f{i}', 'following_id': 'student'})
    _player(fake_supabase, 'f-no-token')
    fake_supabase.rows('user_follows').append({'follower_id': 'f-no-token', 'following_id': 'student'})

    ExpoPushService.notify_followers_of_financial_move(fake_supabase, 'student', 'move_out', 'Studio')  # no amount

    assert len([n for n in fake_supabase.rows('notifications') if n['type'] == 'student_move']) == 4
    assert len(expo.sends) == 1 and len(expo.sends[0]) == 3
    assert expo.sends[0][0]['data']['screen'] == '/profile?id=student'
