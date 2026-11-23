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


def test_goal_tracking_is_refreshed_every_month(job, fake_supabase):
    _mission(fake_supabase, month=1)
    _criteria(fake_supabase, ('net_worth', 'greater_than', 4000))
    job._advance_missions()
    tracking = fake_supabase.rows('player_mission_success_tracking')[0]
    assert tracking['current_value'] == 5000 and tracking['is_met'] is True   # was only written at the end


def test_asset_debt_and_passive_goals_are_evaluated(job, fake_supabase, balance):
    _mission(fake_supabase, month=3)
    fake_supabase.rows('user_assets').extend([
        {'user_id': 'u-1', 'name': 'VTI', 'asset_type': 'stocks', 'value': 3000, 'quantity': 10},
        {'user_id': 'u-1', 'name': 'Food Truck', 'asset_type': 'business', 'value': 45000, 'quantity': 1},
    ])
    fake_supabase.rows('assets').extend([{'name': 'VTI', 'monthly_income': 1}, {'name': 'Food Truck', 'monthly_income': 900}])
    fake_supabase.rows('liabilities').append({'user_id': 'u-1', 'monthly_payment': 60, 'remaining_balance': 500})
    _criteria(fake_supabase,
              ('asset_value', 'greater_than', 40000),
              ('business_value', 'greater_than', 40000),
              ('passive_income', 'greater_than', 900),     # 10*1 + 900 = 910
              ('debt_ratio', 'less_than', 0.25))           # 60 / 300 = 0.2
    job._advance_missions()
    result = fake_supabase.rows('mission_completion_results')[0]
    assert (result['criteria_met'], result['criteria_total']) == (4, 4) and result['completed'] is True


def test_custom_goals_still_cannot_be_met(job):
    assert job._criterion_met({'metric': 'custom', 'comparison': 'greater_than', 'target': 0}, {'custom': 5}) == (False, None)


def test_mission_income_multiplier_applies_to_payday(job, fake_supabase, balance, monkeypatch):
    monkeypatch.setattr('app.game.careers.add_month_worked', lambda *a, **k: None, raising=False)
    fake_supabase.rows('jobs').append({'id': 'j1', 'user_id': 'u-1', 'salary': 36000, 'is_current': True, 'kind': 'job'})
    fake_supabase.rows('player_mission_progress').append(
        {'player_id': 'u-1', 'is_active': True, 'constraints_applied': {'income_multiplier': 0.8, 'expense_multiplier': 1.2}})
    summaries = {}
    job._pay_salaries(job._Scope(only_user='u-1'), {'u-1': {'base_monthly_income': 0}},
                      lambda uid: summaries.setdefault(uid, job._MonthSummary()))
    assert balance['amount'] == Decimal('2400.00')     # 3000 * 80%
