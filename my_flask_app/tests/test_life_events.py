"""Life events: the event-screen route, its interplay with the weekly deck, and the calendar cron."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest


@pytest.fixture
def setup(fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    fake_supabase.rows('profiles').append({'user_id': user_id, 'username': 'tester', 'sanity': 60,
                                           'monthly_income': 0, 'base_monthly_income': 0, 'credit_score': 650})
    fake_supabase.rows('life_events').append({'id': 'ev1', 'title': 'The Dental Gamble', 'description': 'Pay or pray?',
                                              'event_type': 'challenge', 'impact_sanity': -10, 'impact_income': 0,
                                              'impact_cash': -200, 'is_active': True})
    fake_supabase.rows('life_event_choices').extend([
        {'id': 'free', 'life_event_id': 'ev1', 'choice_label': 'Ignore it', 'outcome_description': 'Music up.',
         'cost': 0, 'benefit': 0, 'choice_order': 1, 'impact_sanity': 0, 'impact_income': 0},
        {'id': 'paid', 'life_event_id': 'ev1', 'choice_label': 'Dentist', 'outcome_description': 'Fixed.',
         'cost': 200, 'benefit': 0, 'choice_order': 2, 'impact_sanity': 6, 'impact_income': 0},
    ])
    fake_supabase.rows('life_events').append({'id': 'ev2', 'title': 'Rich Uncle', 'description': '...',
                                              'event_type': 'opportunity', 'is_active': True})
    fake_supabase.rows('life_event_choices').append(
        {'id': 'jackpot', 'life_event_id': 'ev2', 'choice_label': 'Take it', 'outcome_description': '$$$',
         'cost': 0, 'benefit': 800, 'choice_order': 1, 'impact_sanity': 0, 'impact_income': 0})
    balance['amount'] = Decimal('1000')
    return fake_supabase


def _assign(fake, user_id, row_id='ule1', created='2026-11-01T00:00:00+00:00', choice=None):
    fake.rows('user_life_events').append({'id': row_id, 'user_id': user_id, 'life_event_id': 'ev1',
                                          'choice_id': choice, 'created_at': created})


def _choose(client, headers, choice, event='ev1'):
    return client.post('/api/events/make-choice/', json={'event_id': event, 'choice_id': choice}, headers=headers)


def _sanity(fake, uid):
    return next(p for p in fake.rows('profiles') if p['user_id'] == uid)['sanity']


def test_choice_applies_only_its_own_effects(client, auth_headers, setup, user_id, balance):
    _assign(setup, user_id)
    r = _choose(client, auth_headers, 'free')
    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    # Event-level impact_sanity (-10) and impact_cash (-200) must NOT leak in
    assert body['sanity_change'] == 0 and body['balance_change'] == 0
    assert _sanity(setup, user_id) == 60 and balance['amount'] == Decimal('1000')


def test_replay_and_foreign_choice_are_rejected(client, auth_headers, setup, user_id, balance):
    _assign(setup, user_id)
    assert _choose(client, auth_headers, 'jackpot').status_code == 404       # choice from another event
    assert _choose(client, auth_headers, 'paid').status_code == 200
    assert _choose(client, auth_headers, 'paid').status_code == 400          # already answered
    assert balance['amount'] == Decimal('800')
    assert _choose(client, auth_headers, 'jackpot', event='ev2').status_code == 400  # never dealt to this player


def test_unaffordable_choice_with_free_alternative_leaves_event_open(client, auth_headers, setup, user_id, balance):
    _assign(setup, user_id)
    balance['amount'] = Decimal('50')
    r = _choose(client, auth_headers, 'paid')
    assert r.status_code == 400 and r.get_json()['error'] == 'INSUFFICIENT_FUNDS'
    assert setup.rows('user_life_events')[0]['choice_id'] is None   # still answerable (used to be stuck "resolved" for free)
    assert _choose(client, auth_headers, 'free').status_code == 200


def test_no_free_option_pays_what_you_have(client, auth_headers, setup, user_id, balance):
    setup.rows('life_event_choices')[0]['cost'] = 100   # both choices now cost money
    _assign(setup, user_id)
    balance['amount'] = Decimal('60')
    r = _choose(client, auth_headers, 'paid')
    assert r.status_code == 200 and r.get_json()['balance_change'] == -60
    assert balance['amount'] == Decimal('0')


def test_only_the_oldest_pending_copy_is_answered(client, auth_headers, setup, user_id):
    _assign(setup, user_id, 'old', '2026-11-01T00:00:00+00:00')
    _assign(setup, user_id, 'new', '2026-11-05T00:00:00+00:00')
    assert _choose(client, auth_headers, 'free').status_code == 200
    by_id = {r['id']: r['choice_id'] for r in setup.rows('user_life_events')}
    assert by_id == {'old': 'free', 'new': None}


def test_details_prefers_the_unanswered_copy(client, auth_headers, setup, user_id):
    _assign(setup, user_id, 'answered', '2026-10-01T00:00:00+00:00', choice='free')
    _assign(setup, user_id, 'pending', '2026-11-01T00:00:00+00:00')
    data = client.get('/api/events/ev1/', headers=auth_headers).get_json()['data']
    assert data['is_completed'] is False and data['user_choice'] is None and data['is_assigned'] is True


def test_sanity_change_reports_the_clamped_delta(client, auth_headers, setup, user_id):
    next(p for p in setup.rows('profiles') if p['user_id'] == user_id)['sanity'] = 98
    _assign(setup, user_id)
    body = _choose(client, auth_headers, 'paid').get_json()
    assert body['new_sanity'] == 100 and body['sanity_change'] == 2   # not the requested +6


def test_event_answered_on_screen_is_not_paid_again_in_the_deck(client, auth_headers, setup, user_id, balance, monkeypatch):
    monkeypatch.setenv('GAME_CLOCK_UNLIMITED', '1')
    _assign(setup, user_id)
    cards = client.get('/api/week/', headers=auth_headers).get_json()['data']['deck']['cards']
    card = next(c for c in cards if c['kind'] == 'life_event')

    assert _choose(client, auth_headers, 'paid').status_code == 200      # answered via the old push link
    assert balance['amount'] == Decimal('800')

    r = client.post(f"/api/week/cards/{card['id']}/choose/", json={'choice_id': 'right'}, headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()['data']['result']['cash'] == 0
    assert balance['amount'] == Decimal('800')                              # not charged/paid twice


def test_cron_does_not_stack_events(app, setup, user_id, monkeypatch):
    from jobs import trigger_random_events as job
    monkeypatch.setattr(job.ExpoPushService, 'send_notifications_to_users', staticmethod(lambda **kw: {'success': 0, 'failed': 0, 'skipped': 0}))
    next(p for p in setup.rows('profiles') if p['user_id'] == user_id)['last_active_at'] = '2099-01-01T00:00:00+00:00'
    two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    _assign(setup, user_id, created=two_days_ago)   # unanswered, still within its 7 days
    with app.app_context():
        result = job.trigger_random_events()
    assert result['events_triggered'] == 0 and result['auto_resolved'] == 0
    assert len(setup.rows('user_life_events')) == 1


# --- auto-resolve after the time limit -----------------------------------------------------



def _ago(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


@pytest.fixture
def pushes(monkeypatch):
    from jobs import trigger_random_events as job
    sent = []
    monkeypatch.setattr(job.ExpoPushService, 'send_notifications_to_users',
                        staticmethod(lambda **kw: sent.extend(kw['user_notifications']) or {'success': len(kw['user_notifications']), 'failed': 0, 'skipped': 0}))
    return sent


def test_default_choice_is_free_and_carries_the_cost_of_ignoring():
    from app.game.life_events import default_choice
    dental = [
        {'id': 'pray', 'cost': 0, 'benefit': 0, 'impact_sanity': -8, 'choice_order': 1},
        {'id': 'dentist', 'cost': 200, 'benefit': 0, 'impact_sanity': 6, 'choice_order': 2},
    ]
    assert default_choice(dental)['id'] == 'pray'
    two_free = [
        {'id': 'tidy', 'cost': 0, 'benefit': 0, 'impact_sanity': 4, 'choice_order': 1},
        {'id': 'doomscroll', 'cost': 0, 'benefit': 0, 'impact_sanity': -4, 'choice_order': 2},
    ]
    assert default_choice(two_free)['id'] == 'doomscroll'
    both_cost = [
        {'id': 'big', 'cost': 2000, 'benefit': 0, 'impact_sanity': 12, 'choice_order': 1},
        {'id': 'small', 'cost': 50, 'benefit': 0, 'impact_sanity': -4, 'choice_order': 2},
    ]
    assert default_choice(both_cost)['id'] == 'small'


def test_expired_event_is_answered_for_the_player(app, setup, user_id, balance, pushes):
    from jobs.trigger_random_events import auto_resolve_expired_events
    setup.rows('life_event_choices')[0]['impact_sanity'] = -8      # "ignore it" hurts
    _assign(setup, user_id, created=_ago(8))
    with app.app_context():
        result = auto_resolve_expired_events(setup)
    row = setup.rows('user_life_events')[0]
    assert result['auto_resolved'] == 1
    assert row['choice_id'] == 'free' and row['was_auto_selected'] is True
    assert _sanity(setup, user_id) == 52 and balance['amount'] == Decimal('1000')
    feed = [n for n in setup.rows('notifications') if n['user_id'] == user_id]
    assert feed and feed[0]['title'] == '⌛ You ignored The Dental Gamble' and '-8 sanity' in feed[0]['message']
    assert pushes and pushes[0]['data']['screen'] == '/life-events/ev1'


def test_events_within_their_time_limit_are_left_alone(app, setup, user_id, pushes):
    from jobs.trigger_random_events import auto_resolve_expired_events
    _assign(setup, user_id, created=_ago(2))
    with app.app_context():
        assert auto_resolve_expired_events(setup)['auto_resolved'] == 0
    assert setup.rows('user_life_events')[0]['choice_id'] is None and pushes == []


def test_each_events_own_time_limit_is_used(app, setup, user_id, pushes):
    from jobs.trigger_random_events import auto_resolve_expired_events
    setup.rows('life_events')[0]['time_limit_seconds'] = 24 * 3600   # a 1-day event
    _assign(setup, user_id, created=_ago(2))
    with app.app_context():
        assert auto_resolve_expired_events(setup)['auto_resolved'] == 1


def test_broke_player_with_no_free_option_pays_what_they_have(app, setup, user_id, balance, pushes):
    from jobs.trigger_random_events import auto_resolve_expired_events
    setup.rows('life_event_choices')[0]['cost'] = 100
    balance['amount'] = Decimal('30')
    _assign(setup, user_id, created=_ago(8))
    with app.app_context():
        assert auto_resolve_expired_events(setup)['auto_resolved'] == 1
    assert balance['amount'] == Decimal('0')
    assert '-$30' in pushes[0]['body']


def test_auto_resolved_event_in_a_deck_is_not_paid_again(client, auth_headers, app, setup, user_id, balance, pushes, monkeypatch):
    from jobs.trigger_random_events import auto_resolve_expired_events
    monkeypatch.setenv('GAME_CLOCK_UNLIMITED', '1')
    _assign(setup, user_id, created=_ago(8))
    cards = client.get('/api/week/', headers=auth_headers).get_json()['data']['deck']['cards']
    card = next(c for c in cards if c['kind'] == 'life_event')
    with app.app_context():
        auto_resolve_expired_events(setup)
    r = client.post(f"/api/week/cards/{card['id']}/choose/", json={'choice_id': 'right'}, headers=auth_headers)
    assert r.get_json()['data']['result']['cash'] == 0 and balance['amount'] == Decimal('1000')


def test_ignored_event_unblocks_the_next_one_in_the_same_run(app, setup, user_id, pushes):
    from jobs import trigger_random_events as job
    next(p for p in setup.rows('profiles') if p['user_id'] == user_id)['last_active_at'] = '2099-01-01T00:00:00+00:00'
    _assign(setup, user_id, created=_ago(8))
    with app.app_context():
        result = job.trigger_random_events()
    assert result['auto_resolved'] == 1 and result['events_triggered'] == 1
    rows = setup.rows('user_life_events')
    assert len(rows) == 2 and sum(r['choice_id'] is None for r in rows) == 1


def test_event_screen_reports_an_auto_resolved_event(client, auth_headers, app, setup, user_id, pushes):
    from jobs.trigger_random_events import auto_resolve_expired_events
    _assign(setup, user_id, created=_ago(8))
    with app.app_context():
        auto_resolve_expired_events(setup)
    data = client.get('/api/events/ev1/', headers=auth_headers).get_json()['data']
    assert data['is_completed'] is True and data['was_auto_selected'] is True and data['user_choice'] == 'free'
