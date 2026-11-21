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
