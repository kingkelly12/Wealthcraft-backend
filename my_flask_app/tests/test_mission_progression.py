"""The monthly mission step in jobs/monthly_loan_deductions.py (one mission month per game month)."""
from decimal import Decimal

import pytest


@pytest.fixture
def job(fake_supabase, balance):
    from jobs import monthly_loan_deductions
    return monthly_loan_deductions


def _mission(fake, month, duration=3, reward=500):
    fake.rows('player_mission_progress').append({
        'id': 'pm-1', 'player_id': 'u-1', 'mission_id': 'm-1', 'current_month': month, 'is_active': True,
        'game_state_snapshot': {'net_worth': 1000, 'monthly_income': 200, 'credit_score': 600},
        'integrated_missions': {'name': 'Debt Free', 'duration_months': duration, 'completion_reward': reward},
    })
    fake.rows('profiles').append({'user_id': 'u-1', 'net_worth': 5000, 'monthly_income': 300, 'credit_score': 640})
    return fake.rows('player_mission_progress')[0]


def _criteria(fake, *specs):
    for i, (metric, comparison, target) in enumerate(specs):
        fake.rows('mission_success_criteria').append(
            {'id': f'c{i}', 'mission_id': 'm-1', 'metric': metric, 'comparison': comparison, 'target': target})
        fake.rows('player_mission_success_tracking').append(
            {'player_mission_id': 'pm-1', 'criteria_id': f'c{i}', 'is_met': False})


@pytest.mark.parametrize('comparison,target,expected', [
    ('greater_than', 4999, True), ('greater_than', 5000, False),
    ('less_than', 5001, True), ('equals', 5000, True),
])
def test_criterion_comparisons(job, comparison, target, expected):
    ok, value = job._criterion_met({'metric': 'net_worth', 'comparison': comparison, 'target': target}, {'net_worth': 5000})
    assert ok is expected and value == Decimal('5000')


def test_unknown_metric_counts_as_not_met(job):
    assert job._criterion_met({'metric': 'happiness', 'comparison': 'greater_than', 'target': 1}, {}) == (False, None)


def test_mid_mission_advances_one_month(job, fake_supabase):
    progress = _mission(fake_supabase, month=1)
    job._advance_missions()
    assert progress['current_month'] == 2 and progress['is_active'] is True
    assert fake_supabase.rows('mission_completion_results') == []


def test_final_month_with_goals_met_completes_and_pays(job, fake_supabase, balance):
    progress = _mission(fake_supabase, month=3)
    _criteria(fake_supabase, ('net_worth', 'greater_than', 4000), ('credit_score', 'greater_than', 620))
    job._advance_missions()

    assert progress['is_active'] is False and progress['is_completed'] is True
    result = fake_supabase.rows('mission_completion_results')[0]
    assert result['completed'] is True and result['failed'] is False
    assert (result['criteria_met'], result['criteria_total']) == (2, 2)
    assert result['net_worth_change'] == 4000 and result['income_change'] == 100 and result['credit_score_change'] == 40
    assert result['total_cash_reward'] == 500
    assert balance['amount'] == Decimal('500')
    assert fake_supabase.rows('notifications')[0]['title'].startswith('🏆')


def test_final_month_with_goals_missed_fails_without_reward(job, fake_supabase, balance):
    progress = _mission(fake_supabase, month=3)
    _criteria(fake_supabase, ('net_worth', 'greater_than', 4000), ('monthly_income', 'greater_than', 1000))
    job._advance_missions()

    assert progress['is_active'] is False and progress['is_failed'] is True
    result = fake_supabase.rows('mission_completion_results')[0]
    assert result['failed'] is True and (result['criteria_met'], result['criteria_total']) == (1, 2)
    assert result['success_percentage'] == 50.0
    assert result['total_cash_reward'] == 0 and balance['amount'] == 0
