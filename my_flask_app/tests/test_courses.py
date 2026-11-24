"""Courses on game time: matched to jobs and gigs, counting as experience and paying bonuses."""
from decimal import Decimal

import pytest

from app.game import careers, courses, week_service
from jobs.monthly_loan_deductions import process_month_for_user
from tests.test_economy import _lines, _player, wallets  # noqa: F401 (fixture)

CERT = {'id': 'c-cert', 'title': 'Bookkeeping & Accounting Certificate', 'industry': 'Finance', 'tier': 'certificate', 'weeks': 3, 'cost': 450,
        'experience_months': 3, 'pay_bonus_pct': 0.03, 'min_months': 0, 'target_job': 'Junior Accountant'}
DIPLOMA = {'id': 'c-dip', 'title': 'Financial Modelling Diploma', 'industry': 'Finance', 'tier': 'diploma', 'weeks': 8, 'cost': 3500,
           'experience_months': 4, 'pay_bonus_pct': 0.05, 'min_months': 6, 'target_job': 'Financial Analyst'}
EXEC = {'id': 'c-exec', 'title': 'Finance Executive Program', 'industry': 'Finance', 'tier': 'executive', 'weeks': 12, 'cost': 28000,
        'experience_months': 9, 'pay_bonus_pct': 0.06, 'min_months': 36, 'target_job': 'Chief Financial Officer'}
GIG = {'id': 'c-gig', 'title': 'Advanced Driving & Rideshare Course', 'industry': None, 'tier': 'skill', 'weeks': 1, 'cost': 300,
       'experience_months': 0, 'pay_bonus_pct': 0, 'min_months': 0, 'target_gig': 'Rideshare Driver', 'gig_bonus_pct': 0.15}
TECH = {'id': 'c-tech', 'title': 'Full-Stack Coding Bootcamp', 'industry': 'Tech', 'tier': 'certificate', 'weeks': 10, 'cost': 6000,
        'experience_months': 3, 'pay_bonus_pct': 0.03, 'min_months': 0, 'target_job': 'Junior Developer'}


@pytest.fixture
def school(fake_supabase, wallets):
    fake_supabase.rows('courses').extend([dict(c) for c in (CERT, DIPLOMA, EXEC, GIG, TECH)])
    return fake_supabase


def _week(fake, uid, week):
    rows = [c for c in fake.rows('player_game_clock') if c['user_id'] == uid]
    if rows:
        rows[0]['week'] = week
    else:
        fake.rows('player_game_clock').append({'user_id': uid, 'week': week})


def _enroll(client, h, cid):
    return client.post('/api/education/enroll/', json={'course_id': cid}, headers=h)


def test_enrolling_costs_money_and_starts_on_the_game_clock(client, school, wallets):
    uid, h = _player(school)
    _week(school, uid, 5)
    wallets[uid] = Decimal('1000')
    res = _enroll(client, h, 'c-cert').get_json()
    assert res['success'] and wallets[uid] == Decimal('550')
    row = school.rows('user_courses')[0]
    assert row['started_week'] == 5 and row['progress'] == 0
    cert = next(c for c in res['data']['courses'] if c['id'] == 'c-cert')
    assert cert['status'] == 'studying' and cert['weeks_left'] == 3 and cert['target_job'] == 'Junior Accountant'
    assert _enroll(client, h, 'c-cert').status_code == 409                       # once per life


def test_enrolling_is_refused_without_money_experience_or_room(client, school, wallets):
    uid, h = _player(school)
    _week(school, uid, 1)
    wallets[uid] = Decimal('100')
    poor = _enroll(client, h, 'c-cert')
    assert poor.status_code == 402 and poor.get_json()['data']['short'] == 350
    wallets[uid] = Decimal('100000')
    locked = _enroll(client, h, 'c-exec')
    assert locked.status_code == 409 and locked.get_json()['error'] == 'NOT_ELIGIBLE'
    assert _enroll(client, h, 'c-cert').status_code == 200
    assert _enroll(client, h, 'c-gig').status_code == 200
    full = _enroll(client, h, 'c-tech')                                            # two at once is the limit
    assert full.status_code == 409 and full.get_json()['error'] == 'TOO_MANY'


def test_weeks_pass_sanity_dips_and_the_course_finishes(client, school, wallets):
    uid, h = _player(school, sanity=60)
    _week(school, uid, 1)
    wallets[uid] = Decimal('1000')
    _enroll(client, h, 'c-cert')
    _week(school, uid, 3)                                                          # two weeks in
    assert courses.after_week(uid) == []
    assert school.rows('user_courses')[0]['progress'] == 66
    early = client.post('/api/education/complete/', json={'user_course_id': school.rows('user_courses')[0]['id']}, headers=h)
    assert early.status_code == 409 and early.get_json()['data']['weeks_left'] == 1
    _week(school, uid, 4)                                                          # three weeks: done
    done = courses.after_week(uid)
    assert [d['title'] for d in done] == ['Bookkeeping & Accounting Certificate'] and done[0]['experience_months'] == 3
    assert school.rows('user_courses')[0]['completed_at'] and school.rows('user_courses')[0]['progress'] == 100
    assert school.rows('profiles')[0]['sanity'] == 58                              # 1 sanity a week while studying
    assert courses.after_week(uid) == []                                           # finished once


def _finished(fake, uid, *course_ids):
    for cid in course_ids:
        fake.rows('user_courses').append({'id': f'uc-{cid}', 'user_id': uid, 'course_id': cid, 'progress': 100, 'started_week': 1,
                                          'completed_at': '2026-11-01T00:00:00+00:00'})


def test_finished_courses_count_as_experience_in_their_industry(school, wallets):
    uid, _ = _player(school)
    school.rows('jobs').append({'user_id': uid, 'title': 'Bank Teller', 'industry': 'Finance', 'months_worked': 3, 'kind': 'job', 'is_current': True})
    _finished(school, uid, 'c-cert')
    exp = careers.experience(uid)
    assert exp == {'Finance': 6}                                                   # 3 worked + 3 from the course
    assert careers.check({'industry': 'Finance', 'level': 'junior'}, exp)['eligible']   # Junior Accountant unlocked


def test_overview_says_what_a_course_unlocks(school, wallets):
    uid, _ = _player(school)
    school.rows('jobs').append({'user_id': uid, 'title': 'Bank Teller', 'industry': 'Finance', 'months_worked': 3, 'kind': 'job', 'is_current': True})
    data = courses.overview(uid)
    cert = next(c for c in data['courses'] if c['id'] == 'c-cert')
    assert cert['unlocks'] == 'Junior Finance roles' and cert['kind'] == 'career'
    gig = next(c for c in data['courses'] if c['id'] == 'c-gig')
    assert gig['kind'] == 'gig' and gig['gig_bonus_pct'] == 15.0
    assert next(c for c in data['courses'] if c['id'] == 'c-exec')['eligible'] is False


def test_payday_bonus_only_while_working_in_that_industry(school, wallets):
    uid, _ = _player(school, income=0)
    _finished(school, uid, 'c-cert', 'c-dip', 'c-tech')
    school.rows('jobs').append({'id': 'j1', 'user_id': uid, 'title': 'Financial Analyst', 'industry': 'Finance', 'salary': 60000, 'kind': 'job', 'is_current': True})
    month = process_month_for_user(uid, game_years=0)
    bonus = _lines(month)['Certification bonus']
    assert bonus['amount'] == 400.0                                                # 5000/mo x (3% + 5%); the Tech course doesn't count
    assert 'Bookkeeping & Accounting Certificate' in bonus['note']
    school.rows('jobs')[0]['industry'] = 'Retail'                                  # change careers: no bonus
    assert 'Certification bonus' not in _lines(process_month_for_user(uid, game_years=0))


def test_payday_bonus_is_capped(school, wallets):
    uid, _ = _player(school, income=0)
    school.rows('courses').extend([{'id': f'x{i}', 'title': f'Extra {i}', 'industry': 'Finance', 'weeks': 1, 'pay_bonus_pct': 0.1} for i in range(4)])
    _finished(school, uid, 'x0', 'x1', 'x2', 'x3')
    pct, _ = courses.pay_bonus(uid, 'Finance')
    assert pct == Decimal('0.20')


def test_side_hustle_course_raises_that_gigs_weekly_pay(school, wallets):
    uid, _ = _player(school)
    school.rows('jobs').extend([
        {'id': 'g1', 'user_id': uid, 'title': 'Rideshare Driver', 'kind': 'gig', 'weekly_pay': 140, 'sanity_per_week': 0, 'is_current': True},
        {'id': 'g2', 'user_id': uid, 'title': 'Dog Walker & Pet Sitter', 'kind': 'gig', 'weekly_pay': 80, 'sanity_per_week': 0, 'is_current': True},
    ])
    _finished(school, uid, 'c-gig')
    paid = {g['title']: g for g in week_service._pay_gigs(uid)}
    assert paid['Rideshare Driver']['pay'] == 161.0 and paid['Rideshare Driver']['bonus_from'] == ['Advanced Driving & Rideshare Course']
    assert paid['Dog Walker & Pet Sitter']['pay'] == 80.0 and 'bonus_pct' not in paid['Dog Walker & Pet Sitter']
    assert wallets[uid] == Decimal('241')
