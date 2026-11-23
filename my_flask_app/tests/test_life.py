"""Lives: age, backgrounds, the new-life reset, endings and birthdays."""
from decimal import Decimal

import pytest

from app.game import life


# --- pure rules ---------------------------------------------------------------------

def test_age_from_game_weeks():
    assert life.age_at(1, 18) == {'years': 18, 'months': 0, 'chapter': 'Fresh out of school', 'weeks_to_birthday': 52}
    assert life.age_at(53, 18)['years'] == 19
    assert life.age_at(27, 18)['months'] == 6
    assert life.age_at(1, 17)['chapter'] == 'Too young to rent a car'
    assert life.age_at(1 + 52 * 6, 18)['chapter'] == 'Quarter-life crisis'


def test_birthday_detection():
    assert life.birthday_between(52, 53, 18) == 19
    assert life.birthday_between(51, 52, 18) is None


def test_avatar_is_sanitised():
    assert life.clean_avatar({'skin': 3, 'hair': 99, 'eyes': 'x', 'evil': 1}) == {
        'skin': 3, 'hair': 0, 'hairColor': 0, 'eyes': 0, 'accessory': 0, 'bg': 0}


def _snap(**kw):
    base = {'net_worth': 2000, 'debt': 500, 'owns_business': False, 'has_home': True, 'job': 'Barista', 'sanity': 50}
    return {**base, **kw}


@pytest.mark.parametrize('snap,age,reason,expected', [
    (_snap(), 23, 'burnout', 'burnout'),
    (_snap(net_worth=1_500_000), 29, 'started_over', 'millionaire'),
    (_snap(owns_business=True), 25, 'started_over', 'business'),
    (_snap(debt=0, net_worth=20_000), 25, 'started_over', 'debt_free'),
    (_snap(net_worth=150_000), 27, 'started_over', 'six_figures'),
    (_snap(net_worth=-3000), 22, 'started_over', 'drowning'),
    (_snap(has_home=False), 24, 'started_over', 'moved_back_home'),
    (_snap(job=None), 20, 'started_over', 'unemployed'),
    (_snap(), 20, 'started_over', 'getting_by'),
])
def test_endings(snap, age, reason, expected):
    ending = life.pick_ending(snap, age, reason)
    assert ending['key'] == expected
    assert '{age}' not in ending['title']


def test_every_background_is_complete():
    for key, bg in life.BACKGROUNDS.items():
        for field in ('name', 'emoji', 'tagline', 'description', 'cash', 'sanity', 'start_age', 'difficulty'):
            assert field in bg, (key, field)
        assert 0 < bg['sanity'] <= 100


# --- endpoints -----------------------------------------------------------------------

@pytest.fixture
def player(fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    fake_supabase.rows('profiles').append({
        'user_id': user_id, 'username': 'tester', 'sanity': 55, 'net_worth': 4000,
        'monthly_income': 3000, 'base_monthly_income': 100, 'credit_score': 700,
    })
    balance['amount'] = Decimal('4000')
    return fake_supabase.rows('profiles')[0]


def _get(client, headers):
    res = client.get('/api/life/', headers=headers)
    assert res.status_code == 200, res.get_json()
    return res.get_json()['data']


def _begin(client, headers, background, avatar=None):
    return client.post('/api/life/begin/', json={'background': background, 'avatar': avatar or {'skin': 2}}, headers=headers)


def _with_progress(fake, uid):
    fake.rows('jobs').append({'id': 'j1', 'user_id': uid, 'title': 'Barista', 'salary': 36000, 'is_current': True})
    fake.rows('player_rentals').append({'id': 'r1', 'player_id': uid, 'monthly_rent': 900, 'is_active': True})
    fake.rows('user_assets').append({'id': 'a1', 'user_id': uid, 'name': 'ACME', 'asset_type': 'stocks', 'value': 500})
    fake.rows('liabilities').append({'id': 'l1', 'user_id': uid, 'name': 'Car loan', 'liability_type': 'bank_loan', 'remaining_balance': 8000})
    fake.rows('player_mission_progress').append({'id': 'pm1', 'player_id': uid, 'is_active': True})
    fake.rows('player_game_clock').append({'user_id': uid, 'week': 9, 'banked_weeks': 1, 'bank_updated_on': '2026-11-21'})
    fake.rows('player_weeks').append({'id': 'w8', 'user_id': uid, 'week': 8, 'status': 'completed', 'cards': [], 'receipt': {'totals': {'cash': 50}, 'cards': [{}, {}]}})


def test_new_player_must_set_up_a_life(client, auth_headers, player):
    data = _get(client, auth_headers)
    assert data['needs_setup'] and data['current'] is None
    assert not data['can_keep_current']                     # nothing to keep yet
    assert {b['key'] for b in data['backgrounds'] if not b['locked']} == set(life.BACKGROUNDS)
    assert {b['key'] for b in data['backgrounds'] if b['locked']} == set(life.UNLOCKABLE_BACKGROUNDS)


def test_keeping_the_current_life_changes_nothing(client, auth_headers, player, fake_supabase, user_id, balance):
    _with_progress(fake_supabase, user_id)
    assert _get(client, auth_headers)['can_keep_current']
    res = _begin(client, auth_headers, 'original')
    assert res.status_code == 200
    cur = res.get_json()['data']
    assert cur['background']['key'] == 'original' and cur['life_number'] == 1
    assert cur['age']['years'] == 18 and cur['avatar']['skin'] == 2
    assert balance['amount'] == Decimal('4000')
    assert fake_supabase.rows('jobs')[0]['is_current'] is True
    assert fake_supabase.rows('player_game_clock')[0]['week'] == 9


def test_a_background_resets_the_run_and_keeps_the_person(client, auth_headers, player, fake_supabase, user_id, balance):
    _with_progress(fake_supabase, user_id)
    res = _begin(client, auth_headers, 'student_loans')
    assert res.status_code == 200, res.get_json()

    assert balance['amount'] == Decimal('3000')
    assert fake_supabase.rows('jobs') == []                      # job history goes with the run
    assert fake_supabase.rows('player_rentals')[0]['is_active'] is False
    assert fake_supabase.rows('user_assets') == []
    debts = fake_supabase.rows('liabilities')
    assert [d['name'] for d in debts] == ['Student loan'] and debts[0]['amount'] == 24000
    # 5% a year is baked into what's owed (like bank loans): $24,000 borrowed, more to pay back.
    assert debts[0]['total_interest'] > 5000 and debts[0]['remaining_balance'] == 24000 + debts[0]['total_interest']
    assert debts[0]['monthly_payment'] == 250 and debts[0]['remaining_term'] > 96
    assert fake_supabase.rows('player_mission_progress')[0]['is_active'] is False
    assert fake_supabase.rows('player_game_clock')[0]['week'] == 1
    assert fake_supabase.rows('player_weeks') == []
    assert player['sanity'] == 70 and player['base_monthly_income'] == 0 and player['credit_score'] == 650
    assert player['username'] == 'tester'


def test_moved_out_at_17_starts_younger(client, auth_headers, player):
    assert _begin(client, auth_headers, 'moved_out_17').get_json()['data']['age']['years'] == 17


def test_only_one_life_at_a_time(client, auth_headers, player):
    assert _begin(client, auth_headers, 'scholarship').status_code == 200
    res = _begin(client, auth_headers, 'rich_parents')
    assert res.status_code == 409 and res.get_json()['error'] == 'LIFE_IN_PROGRESS'


def test_unknown_background_is_refused(client, auth_headers, player):
    assert _begin(client, auth_headers, 'billionaire_heir').status_code == 400


def test_open_p2p_loans_block_a_new_life(client, auth_headers, player, fake_supabase, user_id, balance):
    fake_supabase.rows('p2p_loans').append({'id': 'p1', 'lender_id': user_id, 'borrower_id': 'someone', 'status': 'active'})
    res = _begin(client, auth_headers, 'scholarship')
    assert res.status_code == 409 and res.get_json()['error'] == 'P2P_OPEN'
    assert balance['amount'] == Decimal('4000')          # nothing was reset


def test_cannot_reroll_on_day_one(client, auth_headers, player):
    _begin(client, auth_headers, 'scholarship')
    res = client.post('/api/life/end/', headers=auth_headers)
    assert res.status_code == 400 and res.get_json()['error'] == 'TOO_SOON'


def test_ending_a_life_records_the_summary_and_allows_a_new_one(client, auth_headers, player, fake_supabase, user_id):
    _with_progress(fake_supabase, user_id)
    _begin(client, auth_headers, 'original')
    res = client.post('/api/life/end/', headers=auth_headers)
    assert res.status_code == 200, res.get_json()
    summary = res.get_json()['data']
    assert summary['reason'] == 'started_over' and summary['weeks_lived'] == 8
    assert summary['ending']['key'] == 'getting_by'
    assert summary['weeks_played'] == 1 and summary['cards_played'] == 2 and summary['best_week'] == 50

    data = _get(client, auth_headers)
    assert data['needs_setup'] and not data['can_keep_current']
    assert data['past_lives'][0]['ending'] == 'getting_by'
    assert _begin(client, auth_headers, 'original').status_code == 400   # 'original' is first-life only
    nxt = _begin(client, auth_headers, 'rich_parents').get_json()['data']
    assert nxt['life_number'] == 2


def test_burnout_ends_a_life_at_any_time(client, auth_headers, player):
    _begin(client, auth_headers, 'scholarship')
    player['sanity'] = 0
    summary = client.post('/api/life/end/', headers=auth_headers).get_json()['data']
    assert summary['ending']['key'] == 'burnout' and summary['ending']['title'] == 'Burnout at 18'


# --- age in the weekly loop --------------------------------------------------------------

def test_birthday_lands_on_the_receipt(client, auth_headers, player, fake_supabase, user_id, monkeypatch):
    monkeypatch.setenv('GAME_CLOCK_UNLIMITED', '1')
    _begin(client, auth_headers, 'scholarship')
    fake_supabase.rows('player_game_clock')[0]['week'] = 52
    deck = client.get('/api/week/', headers=auth_headers).get_json()['data']
    assert deck['age']['years'] == 18 and deck['has_life']
    for card in deck['deck']['cards']:
        free = next(c['id'] for c in card['choices'] if c['cash'] >= 0)
        client.post(f"/api/week/cards/{card['id']}/choose/", json={'choice_id': free}, headers=auth_headers)
    body = client.post('/api/week/complete/', headers=auth_headers).get_json()['data']
    assert body['receipt']['birthday'] == 19
    assert body['next']['age']['years'] == 19


def test_life_is_over_at_max_age(client, auth_headers, player, fake_supabase):
    _begin(client, auth_headers, 'scholarship')
    fake_supabase.rows('player_game_clock')[0]['week'] = 1 + 52 * 12   # 30th birthday
    data = client.get('/api/week/', headers=auth_headers).get_json()['data']
    assert data['life_over'] and not data['can_play']
    card = data['deck']['cards'][0]
    res = client.post(f"/api/week/cards/{card['id']}/choose/", json={'choice_id': 'left'}, headers=auth_headers)
    assert res.status_code == 409 and res.get_json()['error'] == 'LIFE_OVER'
    summary = client.post('/api/life/end/', headers=auth_headers).get_json()['data']
    assert summary['reason'] == 'max_age' and summary['end_age'] == 30


def test_old_run_is_frozen_between_lives(client, auth_headers, player, fake_supabase, user_id):
    _with_progress(fake_supabase, user_id)
    _begin(client, auth_headers, 'original')
    client.post('/api/life/end/', headers=auth_headers)
    data = client.get('/api/week/', headers=auth_headers).get_json()['data']
    assert data['needs_new_life'] and not data['can_play']
    card = data['deck']['cards'][0]
    res = client.post(f"/api/week/cards/{card['id']}/choose/", json={'choice_id': 'left'}, headers=auth_headers)
    assert res.get_json()['error'] in ('NEEDS_NEW_LIFE', 'WEEK_LOCKED')
    _begin(client, auth_headers, 'scholarship')
    data = client.get('/api/week/', headers=auth_headers).get_json()['data']
    assert not data['needs_new_life'] and data['can_play'] and data['week'] == 1


# --- debugging pass ----------------------------------------------------------------------

def _clock(fake, uid, week=10):
    for row in fake.rows('player_game_clock'):          # the reset already made one: move it on
        if row['user_id'] == uid:
            row['week'] = week
            return
    fake.rows('player_game_clock').append({'user_id': uid, 'week': week, 'banked_weeks': 1, 'bank_updated_on': '2026-11-21'})


def _p2p_mess(fake, user_id):
    fake.rows('p2p_loans').extend([
        {'id': 'owed', 'lender_id': 'friend', 'borrower_id': user_id, 'status': 'active'},
        {'id': 'lent', 'lender_id': user_id, 'borrower_id': 'pal', 'status': 'active'},
        {'id': 'offer', 'lender_id': user_id, 'borrower_id': None, 'status': 'pending'},
        {'id': 'ask', 'lender_id': 'friend', 'borrower_id': user_id, 'status': 'requested'},
    ])
    fake.rows('liabilities').append({'id': 'pal-debt', 'user_id': 'pal', 'name': 'P2P', 'p2p_loan_id': 'lent', 'remaining_balance': 900})


def test_burnout_with_open_p2p_loans_does_not_lock_the_player_out(client, auth_headers, player, fake_supabase, user_id, balance):
    _begin(client, auth_headers, 'scholarship')
    _p2p_mess(fake_supabase, user_id)
    player['sanity'] = 0
    assert client.post('/api/life/end/', headers=auth_headers).status_code == 200
    # Frozen between lives, the player can neither play nor earn to repay: used to be a permanent soft-lock.
    assert _begin(client, auth_headers, 'rich_parents').status_code == 200
    status = {l['id']: l['status'] for l in fake_supabase.rows('p2p_loans')}
    assert status == {'owed': 'defaulted', 'lent': 'defaulted', 'offer': 'cancelled', 'ask': 'cancelled'}
    assert not [l for l in fake_supabase.rows('liabilities') if l['user_id'] == 'pal']      # the borrower's debt dies with the lender's life
    told = {n['user_id'] for n in fake_supabase.rows('notifications')}
    assert {'pal', 'friend'} <= told


def test_a_voluntary_restart_is_still_blocked_while_a_p2p_loan_is_open(client, auth_headers, player, fake_supabase, user_id):
    _begin(client, auth_headers, 'scholarship')
    _clock(fake_supabase, user_id)
    fake_supabase.rows('p2p_loans').append({'id': 'p1', 'lender_id': user_id, 'borrower_id': 'pal', 'status': 'active'})
    res = client.post('/api/life/end/', headers=auth_headers)
    assert res.status_code == 409 and res.get_json()['error'] == 'P2P_OPEN'
    assert _get(client, auth_headers)['current'] is not None            # still playing: nothing was closed


def test_a_new_life_starts_clean(client, auth_headers, player, fake_supabase, user_id):
    fake_supabase.rows('user_courses').extend([
        {'id': 'c1', 'user_id': user_id, 'course_id': 'excel', 'completed_at': '2026-11-01T00:00:00+00:00'},
        {'id': 'c2', 'user_id': user_id, 'course_id': 'budget', 'completed_at': None},
    ])
    fake_supabase.rows('jobs').extend([
        {'id': 'old', 'user_id': user_id, 'title': 'Barista', 'job_market_id': 'm1', 'is_current': False, 'months_worked': 30},
        {'id': 'cur', 'user_id': user_id, 'title': 'Analyst', 'job_market_id': 'm2', 'is_current': True, 'months_worked': 12},
    ])
    fake_supabase.rows('user_life_events').extend([
        {'id': 'e1', 'user_id': user_id, 'life_event_id': 'ev1', 'choice_id': None},
        {'id': 'e2', 'user_id': user_id, 'life_event_id': 'ev2', 'choice_id': 'x'},
    ])
    player['trading_profits'] = 500
    assert _begin(client, auth_headers, 'rich_parents').status_code == 200
    assert fake_supabase.rows('user_courses') == []                    # completed ones blocked re-enrolling, for no benefit
    assert fake_supabase.rows('jobs') == []                            # old listings pay their signing bonus again
    from app.game import careers
    assert careers.experience(user_id) == {}                           # and the career ladder starts over
    assert [e['id'] for e in fake_supabase.rows('user_life_events')] == ['e2']   # an unanswered event doesn't follow you
    assert player['trading_profits'] == 0


def test_living_with_a_roommate_counts_as_a_home_for_the_ending(player, fake_supabase, user_id):
    from app.game import life
    assert life._snapshot(user_id)['has_home'] is False
    fake_supabase.rows('roommates').append({'id': 'r', 'leaseholder_id': 'pal', 'roommate_id': user_id, 'status': 'active'})
    assert life._snapshot(user_id)['has_home'] is True                 # was "moved back home" for every roommate


def test_legacy_in_the_life_screen_counts_every_finished_life_not_just_the_latest_20(client, auth_headers, player, fake_supabase, user_id):
    from app.game import legacy
    rich = {'life_number': 1, 'background': {'key': 'scholarship'}, 'reason': 'started_over', 'net_worth': 2_000_000, 'debt': 5}
    for n in range(1, 23):
        fake_supabase.rows('player_lives').append({
            'id': f'l{n}', 'user_id': user_id, 'life_number': n, 'background': 'scholarship', 'is_current': False,
            'ending': 'getting_by', 'ended_at': f'2026-10-{n:02d}T00:00:00+00:00',
            'summary': rich if n == 1 else {'life_number': n, 'background': {'key': 'scholarship'}, 'reason': 'started_over', 'net_worth': 10, 'debt': 5},
        })
    everything = legacy.earned([r['summary'] for r in fake_supabase.rows('player_lives')])
    assert 'millionaire' in everything
    assert _get(client, auth_headers)['legacy']['level'] == len(everything)


def test_avatar_lookup_ignores_malformed_ids(client, auth_headers, player, fake_supabase):
    fake_supabase.calls.clear()
    res = client.get('/api/life/avatars/?ids=not-a-uuid,,12345', headers=auth_headers)
    assert res.status_code == 200 and res.get_json()['data'] == {}
    assert fake_supabase.calls == []                                   # Postgres would 500 on a non-uuid


def test_new_life_cash_is_not_income_or_spending_for_the_mentors():
    from app.services import mentor_service
    assert 'new_life' in mentor_service.NON_OPERATING_INCOME and 'new_life' in mentor_service.NON_OPERATING_EXPENSE
