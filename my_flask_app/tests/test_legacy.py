"""Legacy: achievements, starting bonus and unlockable backgrounds carry between lives."""
from decimal import Decimal

import pytest

from app.game import legacy, life
from tests.test_life import _begin, _get, _with_progress, player  # noqa: F401 (fixture)


def _summary(n, bg='scholarship', **kw):
    base = {'life_number': n, 'background': {'key': bg}, 'reason': 'started_over', 'net_worth': 2000, 'debt': 500,
            'sanity': 50, 'credit_score': 650, 'owns_business': False, 'owns_home': False, 'owns_aircraft': False,
            'job_level': 'entry', 'ending': {'key': 'getting_by'}}
    return {**base, **kw}


def _past(fake, uid, *summaries):
    for s in summaries:
        fake.rows('player_lives').append({'id': f"l{s['life_number']}", 'user_id': uid, 'life_number': s['life_number'],
                                          'background': s['background']['key'], 'is_current': False,
                                          'ending': s['ending']['key'], 'summary': s, 'ended_at': '2026-11-20T00:00:00+00:00'})


def test_achievements_come_from_how_lives_end():
    got = legacy.earned([
        _summary(1),
        _summary(2, reason='max_age', net_worth=150_000, owns_home=True, sanity=85),
        _summary(3, bg='moved_out_17', net_worth=60_000, debt=0, job_level='executive', credit_score=780),
    ])
    assert got == {'first_life': 1, 'made_it_to_30': 2, 'six_figures': 2, 'homeowner': 2, 'zen': 2,
                   'corner_office': 3, 'debt_free': 3, 'credit_legend': 3, 'against_the_odds': 3}
    assert legacy.bonus_cash(got) == 9 * 200
    assert legacy.unlocked_backgrounds(got) == {'inheritance', 'connected'}


def test_living_every_background_counts():
    lives = [_summary(i + 1, bg=bg) for i, bg in enumerate(legacy.BASE_BACKGROUNDS)]
    assert legacy.earned(lives[:3]).get('tried_everything') is None
    assert legacy.earned(lives)['tried_everything'] == 4


def test_old_summaries_without_new_fields_still_work():
    old = {'life_number': 1, 'background': {'key': 'rich_parents'}, 'reason': 'max_age', 'net_worth': 120000}
    assert set(legacy.earned([old])) == {'first_life', 'made_it_to_30', 'six_figures'}


def test_every_unlockable_background_is_complete():
    for key, bg in life.UNLOCKABLE_BACKGROUNDS.items():
        for field in ('name', 'emoji', 'tagline', 'description', 'cash', 'sanity', 'start_age', 'difficulty', 'requires', 'perks'):
            assert field in bg, (key, field)
        assert bg['requires'] in legacy.ACHIEVEMENT_KEYS


def test_locked_backgrounds_are_refused_until_earned(client, auth_headers, player, fake_supabase, user_id):
    _past(fake_supabase, user_id, _summary(1))
    res = _begin(client, auth_headers, 'inheritance')
    assert res.status_code == 403 and res.get_json()['error'] == 'LOCKED_BACKGROUND'
    assert 'Homeowner' in res.get_json()['message']
    state = _get(client, auth_headers)
    locked = {b['key']: b for b in state['backgrounds'] if b['locked']}
    assert set(locked) == set(life.UNLOCKABLE_BACKGROUNDS)
    assert locked['inheritance']['unlock_hint'].startswith('🏡 Homeowner')
    assert state['legacy'] == {'level': 1, 'bonus_cash': 200, 'achievements_total': len(legacy.ACHIEVEMENTS)}


def test_the_inheritance_starts_rent_free_with_the_legacy_bonus(client, auth_headers, player, fake_supabase, user_id, balance):
    _past(fake_supabase, user_id, _summary(1, owns_home=True, reason='max_age'))   # first_life, made_it_to_30, homeowner
    fake_supabase.rows('home_listings').append({'id': 'h-studio', 'name': 'Studio Flat', 'price': 95000, 'market_rent': 950})
    res = _begin(client, auth_headers, 'inheritance')
    assert res.status_code == 200, res.get_json()
    assert balance['amount'] == Decimal('500') + 3 * 200
    home = fake_supabase.rows('player_homes')[0]
    assert home['lives_in'] and home['player_id'] == user_id and home['current_value'] == 95000


def test_family_business_and_connected_head_starts(client, auth_headers, player, fake_supabase, user_id):
    from app.game import careers
    fake_supabase.rows('assets').append({'id': 'a-vend', 'name': 'Vending Machine', 'category': 'business', 'price': 2800})
    _past(fake_supabase, user_id, _summary(1, owns_business=True), _summary(2, job_level='executive'))
    assert _begin(client, auth_headers, 'family_business').status_code == 200
    holding = fake_supabase.rows('user_assets')[0]
    assert holding['name'] == 'Vending Machine' and holding['asset_type'] == 'business'
    # Next life: The Connected One.
    fake_supabase.rows('player_lives')[-1]['is_current'] = False
    fake_supabase.rows('player_lives')[-1]['summary'] = _summary(3)
    assert _begin(client, auth_headers, 'connected').status_code == 200
    assert careers.experience(user_id) == {'Finance': 18}


def test_ending_a_life_reports_what_it_added(client, auth_headers, player, fake_supabase, user_id):
    _with_progress(fake_supabase, user_id)
    fake_supabase.rows('player_homes').append({'player_id': user_id, 'home_id': 'h1', 'lives_in': True, 'is_active': True})
    _begin(client, auth_headers, 'original')
    fake_supabase.rows('player_game_clock')[0]['week'] = 60          # a full year and more
    summary = client.post('/api/life/end/', headers=auth_headers).get_json()['data']
    assert summary['owns_home'] and summary['has_home']
    added = summary['legacy']
    assert [a['key'] for a in added['achievements']] == ['first_life', 'homeowner']
    assert added['unlocked_backgrounds'] == [{'key': 'inheritance', 'name': 'The Inheritance', 'emoji': '🏡'}]
    assert added['bonus_added'] == 400 and added['bonus_cash'] == 400


def test_ending_a_life_after_a_few_weeks_only_earns_one_down(client, auth_headers, player, fake_supabase, user_id):
    _with_progress(fake_supabase, user_id)
    fake_supabase.rows('player_homes').append({'player_id': user_id, 'home_id': 'h1', 'lives_in': True, 'is_active': True})
    _begin(client, auth_headers, 'original')
    summary = client.post('/api/life/end/', headers=auth_headers).get_json()['data']      # week 9: 8 weeks lived
    assert [a['key'] for a in summary['legacy']['achievements']] == ['first_life']


def test_hall_of_lives(client, auth_headers, player, fake_supabase, user_id):
    _past(fake_supabase, user_id, _summary(1, ending={'key': 'drowning'}, net_worth=-500),
          _summary(2, reason='max_age', ending={'key': 'six_figures'}, net_worth=140000))
    hall = client.get('/api/life/legacy/', headers=auth_headers).get_json()['data']
    assert hall['level'] == 3 and hall['bonus_cash'] == 600
    earned = {a['key']: a for a in hall['achievements'] if a['earned']}
    assert earned['six_figures']['earned_in_life'] == 2
    endings = {e['key']: e for e in hall['endings']}
    assert endings['drowning']['collected'] and endings['six_figures']['times'] == 1 and not endings['millionaire']['collected']
    assert '{age}' not in endings['millionaire']['title']
    assert [l['life_number'] for l in hall['lives']] == [2, 1]
    assert hall['lives'][0]['achievements'] == ['made_it_to_30', 'six_figures']


def test_a_life_cut_short_only_earns_one_down():
    short = _summary(1, weeks_lived=4, net_worth=15_000, debt=0, credit_score=800, owns_home=True)
    assert legacy.earned([short]) == {'first_life': 1}
    full = {**short, 'weeks_lived': 52}
    assert set(legacy.earned([full])) == {'first_life', 'homeowner', 'debt_free', 'credit_legend'}


def test_short_lives_dont_count_towards_living_every_background():
    lives = [_summary(i + 1, bg=bg, weeks_lived=4 if bg == 'rich_parents' else 60) for i, bg in enumerate(legacy.BASE_BACKGROUNDS)]
    assert 'tried_everything' not in legacy.earned(lives)
    lives[2]['weeks_lived'] = 60
    assert legacy.earned(lives)['tried_everything'] == 4
