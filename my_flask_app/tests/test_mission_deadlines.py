"""Mission decision deadlines: day-based auto-decide, required decisions at month end."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

NOW = datetime(2026, 12, 10, 12, 0, tzinfo=timezone.utc)


def _iso(days_ago):
    return (NOW - timedelta(days=days_ago)).isoformat()


@pytest.fixture
def mission(fake_supabase, user_id, balance, monkeypatch):
    from app.services.push_notification_service import ExpoPushService
    sent = []
    monkeypatch.setattr(ExpoPushService, 'send_notifications_to_users',
                        classmethod(lambda cls, **kw: sent.extend(kw['user_notifications']) or {'success': 1}))
    fake_supabase.rows('profiles').append({'user_id': user_id, 'sanity': 50})
    progress = {'id': 'pm-1', 'player_id': user_id, 'mission_id': 'm-1', 'current_month': 1, 'is_active': True,
                'started_at': _iso(10), 'month_started_at': _iso(10),
                'integrated_missions': {'name': 'Emergency Fund', 'duration_months': 3}}
    fake_supabase.rows('player_mission_progress').append(progress)
    fake_supabase.rows('mission_decision_points').append(
        {'id': 'dp1', 'mission_id': 'm-1', 'month': 1, 'title': 'Paycheck Day', 'description': '...',
         'is_required': False, 'auto_resolve_after_days': 7, 'auto_resolve_option_id': None})
    fake_supabase.rows('mission_decision_options').extend([
        {'id': 'save', 'decision_point_id': 'dp1', 'label': 'Save 20%', 'immediate_cash': 0, 'option_order': 1,
         'happiness_change': 2, 'stress_change': 0, 'motivation_change': 0},
        {'id': 'drift', 'decision_point_id': 'dp1', 'label': 'Do nothing', 'immediate_cash': 0, 'option_order': 2,
         'happiness_change': 0, 'stress_change': 4, 'motivation_change': 0},
        {'id': 'splurge', 'decision_point_id': 'dp1', 'label': 'Treat yourself', 'immediate_cash': -300, 'option_order': 3,
         'happiness_change': 8, 'stress_change': 0, 'motivation_change': 0},
    ])
    balance['amount'] = Decimal('1000')
    return {'progress': progress, 'sent': sent}


def _decisions(fake):
    return fake.rows('player_mission_decisions')


def test_expired_decision_is_made_with_the_do_nothing_option(fake_supabase, mission, user_id):
    from app.game.mission_decisions import run_mission_deadlines
    result = run_mission_deadlines(now=NOW)          # due 10 days ago, deadline 7 days
    assert result['auto_decided'] == 1
    d = _decisions(fake_supabase)[0]
    assert d['chosen_option_id'] == 'drift' and d['decision_data']['auto_resolved'] is True   # free + worst sanity
    assert next(p for p in fake_supabase.rows('profiles') if p['user_id'] == user_id)['sanity'] == 46
    assert fake_supabase.rows('notifications')[0]['title'] == '⌛ Decided for you: Paycheck Day'
    assert mission['sent'][0]['data']['screen'] == '/missions'


def test_decision_within_its_deadline_is_left_alone(fake_supabase, mission):
    from app.game.mission_decisions import run_mission_deadlines
    mission['progress']['month_started_at'] = _iso(3)
    mission['progress']['started_at'] = _iso(3)
    assert run_mission_deadlines(now=NOW)['auto_decided'] == 0 and _decisions(fake_supabase) == []


def test_named_auto_resolve_option_wins_and_broke_player_pays_what_they_have(fake_supabase, mission, balance):
    from app.game.mission_decisions import run_mission_deadlines
    fake_supabase.rows('mission_decision_points')[0]['auto_resolve_option_id'] = 'splurge'
    balance['amount'] = Decimal('120')
    run_mission_deadlines(now=NOW)
    assert _decisions(fake_supabase)[0]['chosen_option_id'] == 'splurge'
    assert balance['amount'] == Decimal('0')


def test_already_decided_points_are_skipped(fake_supabase, mission):
    from app.game.mission_decisions import run_mission_deadlines
    fake_supabase.rows('player_mission_decisions').append(
        {'player_mission_id': 'pm-1', 'decision_point_id': 'dp1', 'chosen_option_id': 'save'})
    assert run_mission_deadlines(now=NOW)['auto_decided'] == 0


def test_month_end_decides_required_but_leaves_optional_open(fake_supabase, mission):
    from app.game.mission_decisions import auto_decide
    point = fake_supabase.rows('mission_decision_points')[0]
    point['auto_resolve_after_days'] = None
    assert auto_decide([mission['progress']], now=NOW, month_end=True) == []   # optional: lapses, not forced
    point['is_required'] = True
    assert len(auto_decide([mission['progress']], now=NOW, month_end=True)) == 1


def test_future_month_points_are_never_auto_decided(fake_supabase, mission):
    from app.game.mission_decisions import run_mission_deadlines
    fake_supabase.rows('mission_decision_points')[0]['month'] = 2
    assert run_mission_deadlines(now=NOW)['auto_decided'] == 0


def test_active_mission_reports_the_deadline(client, auth_headers, fake_supabase, mission):
    data = client.get('/api/missions/active/', headers=auth_headers).get_json()['data']
    assert data['next_decision']['deadline_at'] == (datetime.fromisoformat(_iso(10)) + timedelta(days=7)).isoformat()
    assert data['next_decision']['decides_at_month_end'] is False


def test_rollover_decides_required_and_restarts_the_month_clock(fake_supabase, mission, balance):
    from jobs import monthly_loan_deductions as job
    point = fake_supabase.rows('mission_decision_points')[0]
    point['auto_resolve_after_days'], point['is_required'] = None, True
    old_clock = mission['progress']['month_started_at']
    job._advance_missions()
    assert _decisions(fake_supabase)[0]['decision_data']['auto_resolved'] is True
    progress = mission['progress']
    assert progress['current_month'] == 2 and progress['month_started_at'] != old_clock
    assert datetime.fromisoformat(progress['month_started_at']) > datetime.now(timezone.utc) - timedelta(minutes=1)


def test_cron_endpoint(client, fake_supabase, mission, app):
    app.config['CRON_SECRET'] = 's3cret'
    r = client.post('/api/cron/mission-deadlines/', headers={'Authorization': 'Bearer s3cret'})
    assert r.status_code == 200 and r.get_json()['data']['active_missions'] == 1
