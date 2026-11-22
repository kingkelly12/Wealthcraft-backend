"""Careers are ladders: higher rungs need experience in the same industry."""
import uuid

import pytest

from app.game import careers
from jobs.monthly_loan_deductions import process_month_for_user
from tests.test_economy import _player, wallets  # noqa: F401 (fixture)

IDS = {k: str(uuid.uuid4()) for k in ('teller', 'junior_acc', 'cfo', 'barista', 'gig')}


@pytest.fixture
def market(fake_supabase, monkeypatch):
    from app.services.profile_service import ProfileService
    monkeypatch.setattr(ProfileService, 'recalculate_monthly_income', staticmethod(lambda uid: 0))
    fake_supabase.rows('job_market').extend([
        {'id': IDS['teller'], 'title': 'Bank Teller', 'company': 'FHB', 'industry': 'Finance', 'salary': 32000, 'level': 'entry', 'experience_months': 0, 'kind': 'job'},
        {'id': IDS['junior_acc'], 'title': 'Junior Accountant', 'company': 'Ledger', 'industry': 'Finance', 'salary': 52000, 'level': 'junior', 'experience_months': 6, 'kind': 'job'},
        {'id': IDS['cfo'], 'title': 'Chief Financial Officer', 'company': 'Summit', 'industry': 'Finance', 'salary': 220000, 'level': 'executive', 'experience_months': 60, 'kind': 'job'},
        {'id': IDS['barista'], 'title': 'Barista', 'company': 'Bean', 'industry': 'Hospitality', 'salary': 28000, 'level': 'entry', 'experience_months': 0, 'kind': 'job'},
        {'id': IDS['gig'], 'title': 'Dog Walker', 'company': 'Self', 'industry': 'Care', 'salary': 0, 'level': 'entry', 'kind': 'gig', 'weekly_pay': 80},
    ])
    return fake_supabase


def _apply(client, h, key):
    return client.post('/api/jobs/apply/', json={'job_id': IDS[key]}, headers=h)


def test_a_new_player_starts_at_the_bottom(client, market, wallets):
    uid, h = _player(market)
    res = _apply(client, h, 'cfo')
    body = res.get_json()
    assert res.status_code == 403 and body['error'] == 'NEEDS_EXPERIENCE'
    assert body['message'].startswith('Executive roles in Finance need 5 years of experience. You have 0 months')
    assert _apply(client, h, 'gig').get_json()['success']          # gigs need no experience
    assert _apply(client, h, 'teller').get_json()['success']       # entry level is open to anyone


def test_paydays_build_experience_that_unlocks_the_next_rung(client, market, wallets):
    uid, h = _player(market, income=0)
    _apply(client, h, 'teller')
    assert _apply(client, h, 'junior_acc').status_code in (400, 403)
    for _ in range(6):
        process_month_for_user(uid)
    teller = next(j for j in market.rows('jobs') if j['title'] == 'Bank Teller')
    assert teller['months_worked'] == 6 and teller['industry'] == 'Finance'
    teller['is_current'] = False                                    # quit to move up
    assert _apply(client, h, 'junior_acc').get_json()['success']


def test_other_industries_count_for_a_third():
    exp = {'Hospitality': 9, 'Finance': 3}
    assert careers.effective_months(exp, 'Finance') == 6
    assert careers.check({'industry': 'Finance', 'level': 'junior', 'experience_months': 6}, exp)['eligible']
    assert not careers.check({'industry': 'Finance', 'level': 'mid', 'experience_months': 18}, exp)['eligible']
    # The level sets a floor even if a listing forgot its requirement.
    assert careers.required_months({'level': 'senior', 'experience_months': 0}) == 36


def test_gigs_dont_count_as_experience(market):
    uid, _ = _player(market)
    market.rows('jobs').extend([
        {'user_id': uid, 'industry': 'Care', 'kind': 'gig', 'months_worked': 20},
        {'user_id': uid, 'industry': 'Retail', 'kind': 'job', 'months_worked': 4},
    ])
    assert careers.experience(uid) == {'Retail': 4}


def test_the_job_board_says_what_you_can_apply_for(client, market, wallets):
    uid, h = _player(market)
    market.rows('jobs').append({'user_id': uid, 'industry': 'Finance', 'kind': 'job', 'months_worked': 7, 'is_current': False})
    data = client.get('/api/jobs/overview/', headers=h).get_json()['data']
    board = {j['title']: j for j in data['market']}
    assert board['Junior Accountant']['eligible'] and board['Junior Accountant']['level_label'] == 'Junior'
    assert not board['Chief Financial Officer']['eligible'] and board['Chief Financial Officer']['needed_months'] == 60
    assert data['experience'] == {'Finance': 7}
    titles = [j['title'] for j in data['market']]
    assert titles.index('Bank Teller') < titles.index('Junior Accountant') < titles.index('Chief Financial Officer')
    assert titles[-1] == 'Dog Walker'                               # gigs last


def test_experience_resets_with_a_new_life(market):
    uid, _ = _player(market)
    market.rows('jobs').append({'user_id': uid, 'industry': 'Finance', 'kind': 'job', 'months_worked': 30})
    careers.reset_for_new_life(uid)
    assert careers.experience(uid) == {}
