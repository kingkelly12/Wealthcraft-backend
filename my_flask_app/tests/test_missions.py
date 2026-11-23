"""Missions: status summary, story-event triggering and acknowledgement."""
from decimal import Decimal

import pytest


@pytest.fixture
def active_mission(fake_supabase, user_id):
    progress = {
        'id': 'pm-1', 'player_id': user_id, 'mission_id': 'm-1', 'current_month': 1, 'is_active': True,
        'integrated_missions': {'name': 'First Apartment', 'duration_months': 6},
    }
    fake_supabase.rows('player_mission_progress').append(progress)
    return progress


def _story(fake, **kw):
    row = {
        'id': kw.pop('id'), 'mission_id': 'm-1', 'is_active': True, 'title': 'A story', 'narrative': 'Once…',
        'story_type': 'emotional', 'trigger_type': 'month', 'trigger_value': 1, 'display_order': len(fake.rows('mission_story_events')),
        'immediate_cash': 0, 'happiness_change': 0, 'stress_change': 0, 'motivation_change': 0, **kw,
    }
    fake.rows('mission_story_events').append(row)
    return row


# ---- status ------------------------------------------------------------------

def test_status_without_active_mission(client, auth_headers, fake_supabase):
    fake_supabase.rows('integrated_missions').extend([{'id': 'a'}, {'id': 'b'}])
    res = client.get('/api/missions/status/', headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert data['has_active'] is False
    assert data['available_count'] == 2
    assert data['history_summary']['recent'] == []


def test_status_reports_progress_and_recent_results(client, auth_headers, user_id, fake_supabase, active_mission):
    fake_supabase.rows('mission_completion_results').append(
        {'id': 'r-1', 'player_id': user_id, 'completed': True, 'completed_at': '2026-11-01', 'success_percentage': 100})
    data = client.get('/api/missions/status/', headers=auth_headers).get_json()['data']
    assert data['has_active'] is True
    assert data['active_summary']['progress_text'] == 'Month 1/6'
    # The app's completion watcher relies on these ids.
    assert [r['id'] for r in data['history_summary']['recent']] == ['r-1']


# ---- pending story events ------------------------------------------------------

def test_pending_stories_without_active_mission_is_empty_not_500(client, auth_headers, fake_supabase):
    res = client.get('/api/missions/active/pending-story-events/', headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()['data'] == []


def test_pending_story_triggers(client, auth_headers, fake_supabase, active_mission):
    active_mission['current_month'] = 3
    _story(fake_supabase, id='opening', trigger_type='mission_start')     # month 1 only
    _story(fake_supabase, id='month2', trigger_type='month', trigger_value=2)  # catches up
    _story(fake_supabase, id='month5', trigger_type='month', trigger_value=5)  # not yet
    _story(fake_supabase, id='inactive', trigger_type='month', trigger_value=1, is_active=False)

    data = client.get('/api/missions/active/pending-story-events/', headers=auth_headers).get_json()['data']
    assert [e['id'] for e in data] == ['month2']
    assert data[0]['mission_month'] == 3


def test_viewed_stories_are_not_pending(client, auth_headers, fake_supabase, active_mission):
    _story(fake_supabase, id='s1', trigger_type='mission_start')
    fake_supabase.rows('player_story_progress').append(
        {'player_mission_id': 'pm-1', 'story_event_id': 's1', 'has_been_viewed': True})
    assert client.get('/api/missions/active/pending-story-events/', headers=auth_headers).get_json()['data'] == []


# ---- acknowledge ---------------------------------------------------------------

def _ack(client, headers, event_id):
    return client.post(f'/api/missions/story-events/{event_id}/acknowledge/', json={}, headers=headers)


@pytest.fixture
def profile(fake_supabase, user_id):
    row = {'user_id': user_id, 'sanity': 50}
    fake_supabase.rows('profiles').append(row)
    return row


def test_acknowledge_applies_cash_and_emotions_to_sanity(client, auth_headers, fake_supabase, active_mission, profile, balance):
    # sanity += happiness + motivation/2 - stress  ->  50 + 10 + 3 - 4 = 59
    _story(fake_supabase, id='s1', immediate_cash=250, happiness_change=10, motivation_change=6, stress_change=4)
    res = _ack(client, auth_headers, 's1')
    assert res.status_code == 200
    impacts = res.get_json()['data']['impacts_applied']
    assert impacts['sanity_change'] == 9 and impacts['new_sanity'] == 59
    assert profile['sanity'] == 59
    assert balance['amount'] == Decimal('250')


def test_acknowledge_is_idempotent(client, auth_headers, fake_supabase, active_mission, profile, balance):
    _story(fake_supabase, id='s1', immediate_cash=-100, stress_change=20)
    balance['amount'] = Decimal('1000')
    assert _ack(client, auth_headers, 's1').status_code == 200
    assert _ack(client, auth_headers, 's1').status_code == 200   # retry
    assert profile['sanity'] == 30
    assert balance['amount'] == Decimal('900')


def test_story_sanity_is_clamped(client, auth_headers, fake_supabase, active_mission, profile, balance):
    _story(fake_supabase, id='crash', stress_change=500)
    _ack(client, auth_headers, 'crash')
    assert profile['sanity'] == 0


def test_acknowledge_unknown_event_is_404(client, auth_headers, fake_supabase, active_mission, profile, balance):
    assert _ack(client, auth_headers, 'missing').status_code == 404


def test_acknowledge_without_active_mission_is_404(client, auth_headers, fake_supabase, profile, balance):
    assert _ack(client, auth_headers, 'anything').status_code == 404


def test_story_hit_bigger_than_balance_takes_what_they_have(client, auth_headers, fake_supabase, active_mission, profile, balance):
    _story(fake_supabase, id='fine', immediate_cash=-500)
    balance['amount'] = Decimal('120')
    assert _ack(client, auth_headers, 'fine').status_code == 200
    assert balance['amount'] == Decimal('0')          # was: recorded, then "insufficient funds", never paid


def _earlier_run(fake, user_id, run_id='pm-0'):
    fake.rows('player_mission_progress').append({'id': run_id, 'player_id': user_id, 'mission_id': 'm-1',
                                                 'is_active': False, 'abandoned_at': '2026-10-01T00:00:00+00:00'})


def test_restarted_mission_does_not_repay_story_rewards(client, auth_headers, fake_supabase, active_mission, profile, balance, user_id):
    _story(fake_supabase, id='bonus', immediate_cash=250, happiness_change=10)
    _earlier_run(fake_supabase, user_id)
    fake_supabase.rows('player_story_progress').append(
        {'id': 'old', 'player_mission_id': 'pm-0', 'story_event_id': 'bonus', 'has_been_viewed': True})
    assert _ack(client, auth_headers, 'bonus').status_code == 200
    assert balance['amount'] == Decimal('0') and profile['sanity'] == 50


# ---- decisions --------------------------------------------------------------------

@pytest.fixture
def decision(fake_supabase, active_mission):
    fake_supabase.rows('mission_decision_points').append(
        {'id': 'dp1', 'mission_id': 'm-1', 'month': 1, 'title': 'Paycheck Day', 'description': '...'})
    fake_supabase.rows('mission_decision_options').extend([
        {'id': 'save', 'decision_point_id': 'dp1', 'label': 'Save 20%', 'immediate_cash': 0,
         'happiness_change': 0, 'stress_change': 0, 'motivation_change': 0},
        {'id': 'splurge', 'decision_point_id': 'dp1', 'label': 'Treat yourself', 'immediate_cash': -300,
         'happiness_change': 8, 'stress_change': 0, 'motivation_change': 0},
        {'id': 'gig', 'decision_point_id': 'dp1', 'label': 'Side gig', 'immediate_cash': 250,
         'happiness_change': 0, 'stress_change': 6, 'motivation_change': 4},
    ])


def _decide(client, headers, option, point='dp1'):
    return client.post('/api/missions/decision/', json={'decision_point_id': point, 'option_id': option}, headers=headers)


def test_decision_applies_cash_and_sanity(client, auth_headers, fake_supabase, decision, profile, balance):
    r = _decide(client, auth_headers, 'gig')
    assert r.status_code == 200
    assert balance['amount'] == Decimal('250')
    assert profile['sanity'] == 46 and r.get_json()['data']['sanity_change'] == -4   # 0 + 4/2 - 6
    assert _decide(client, auth_headers, 'gig').status_code == 400                    # once only


def test_unaffordable_option_is_refused_and_not_recorded(client, auth_headers, fake_supabase, decision, profile, balance):
    balance['amount'] = Decimal('100')
    r = _decide(client, auth_headers, 'splurge')
    assert r.status_code == 400 and r.get_json()['error'] == 'INSUFFICIENT_FUNDS'
    assert fake_supabase.rows('player_mission_decisions') == []    # still decidable
    assert _decide(client, auth_headers, 'save').status_code == 200


def test_restarted_mission_does_not_repay_decision_rewards(client, auth_headers, fake_supabase, decision, profile, balance, user_id):
    _earlier_run(fake_supabase, user_id)
    fake_supabase.rows('player_mission_decisions').append(
        {'id': 'old', 'player_mission_id': 'pm-0', 'decision_point_id': 'dp1', 'chosen_option_id': 'gig'})
    r = _decide(client, auth_headers, 'gig')
    assert r.status_code == 200 and r.get_json()['data']['repeat_run'] is True
    assert balance['amount'] == Decimal('0')       # no second +$250
    assert profile['sanity'] == 46                 # the setback still applies


def test_a_missed_decision_is_still_offered(client, auth_headers, fake_supabase, decision, active_mission):
    active_mission['current_month'] = 2            # month 1's decision was never made
    data = client.get('/api/missions/active/', headers=auth_headers).get_json()['data']
    assert data['next_decision']['id'] == 'dp1'


def test_future_decision_is_not_due(client, auth_headers, fake_supabase, decision, profile, balance):
    fake_supabase.rows('mission_decision_points')[0]['month'] = 3
    assert _decide(client, auth_headers, 'save').get_json()['error'] == 'DECISION_NOT_DUE'


# ---- missions and lives --------------------------------------------------------------------

def _current_life(fake, user_id, started='2026-11-20T00:00:00+00:00', background='scholarship'):
    fake.rows('player_lives').append({'id': 'life2', 'user_id': user_id, 'life_number': 2, 'background': background,
                                      'is_current': True, 'started_at': started})


def test_missions_completed_in_a_past_life_can_be_played_again(client, auth_headers, fake_supabase, user_id):
    fake_supabase.rows('profiles').append({'user_id': user_id, 'net_worth': 0})
    fake_supabase.rows('integrated_missions').extend([
        {'id': 'm-old', 'name': 'Done Last Life', 'description': '', 'category': 'x', 'difficulty': 'beginner', 'duration_months': 3},
        {'id': 'm-new', 'name': 'Done This Life', 'description': '', 'category': 'x', 'difficulty': 'beginner', 'duration_months': 3},
    ])
    _current_life(fake_supabase, user_id)
    fake_supabase.rows('mission_completion_results').extend([
        {'id': 'r1', 'player_id': user_id, 'mission_id': 'm-old', 'completed': True, 'completed_at': '2026-11-10T00:00:00+00:00'},
        {'id': 'r2', 'player_id': user_id, 'mission_id': 'm-new', 'completed': True, 'completed_at': '2026-11-25T00:00:00+00:00'},
    ])
    data = client.get('/api/missions/available/?compact=true', headers=auth_headers).get_json()['data']
    assert [m['id'] for m in data['missions']] == ['m-old']             # was: both hidden forever
    status = client.get('/api/missions/status/', headers=auth_headers).get_json()['data']
    assert status['history_summary']['total_completed'] == 1


def test_a_new_life_pays_decision_rewards_again(client, auth_headers, fake_supabase, decision, profile, balance, user_id):
    _current_life(fake_supabase, user_id)
    fake_supabase.rows('player_mission_progress').append({'id': 'pm-0', 'player_id': user_id, 'mission_id': 'm-1', 'is_active': False,
                                                          'started_at': '2026-11-01T00:00:00+00:00'})   # played in the PREVIOUS life
    fake_supabase.rows('player_mission_decisions').append(
        {'id': 'old', 'player_mission_id': 'pm-0', 'decision_point_id': 'dp1', 'chosen_option_id': 'gig'})
    r = _decide(client, auth_headers, 'gig')
    assert r.status_code == 200 and r.get_json()['data']['repeat_run'] is False
    assert balance['amount'] == Decimal('250')
