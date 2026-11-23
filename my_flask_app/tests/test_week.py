"""This Week: the game clock, the weekly deck and the month on payday weeks."""
from datetime import timedelta
from decimal import Decimal

import pytest

from app.game import week_service
from app.game.weekly_cards import CARDS


# --- card library invariants ------------------------------------------------------

def test_card_keys_are_unique():
    keys = [c['key'] for c in CARDS]
    assert len(keys) == len(set(keys))


@pytest.mark.parametrize('card', CARDS, ids=lambda c: c['key'])
def test_every_card_has_a_free_way_out(card):
    # A broke player must never be stuck on a card.
    assert card['left'].get('cash', 0) >= 0 or card['right'].get('cash', 0) >= 0
    for side in ('left', 'right'):
        assert card[side]['label'] and card[side]['outcome']
    assert card['title'] and card['body'] and card['teaser'] and card['icon']
    assert card.get('requires') in (None, 'job', 'no_job', 'rental', 'no_rental')


def test_week_meta():
    assert week_service.week_meta(1) == {'week': 1, 'month': 1, 'week_of_month': 1, 'is_payday_week': False, 'weeks_lived': 0}
    assert week_service.week_meta(4)['is_payday_week']
    assert week_service.week_meta(5)['month'] == 2


# --- helpers -------------------------------------------------------------------

@pytest.fixture
def player(fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    fake_supabase.rows('profiles').append({
        'user_id': user_id, 'username': 'tester', 'sanity': 60,
        'monthly_income': 0, 'base_monthly_income': 0, 'credit_score': 650,
    })
    balance['amount'] = Decimal('1000')
    return fake_supabase.rows('profiles')[0]


def _get(client, headers):
    res = client.get('/api/week/', headers=headers)
    assert res.status_code == 200, res.get_json()
    return res.get_json()['data']


def _choose(client, headers, card_id, choice):
    return client.post(f'/api/week/cards/{card_id}/choose/', json={'choice_id': choice}, headers=headers)


def _free_side(card):
    return next(c['id'] for c in card['choices'] if c['cash'] >= 0)


def _play_week(client, headers):
    data = _get(client, headers)
    for card in data['deck']['cards']:
        assert _choose(client, headers, card['id'], _free_side(card)).status_code == 200
    return client.post('/api/week/complete/', headers=headers)


def _shift_days(monkeypatch, days):
    today = week_service._today()
    monkeypatch.setattr(week_service, '_today', lambda: today + timedelta(days=days))


# --- clock and deck ----------------------------------------------------------------

def test_first_visit_starts_the_clock_and_deals_a_week(client, auth_headers, player, fake_supabase, user_id):
    data = _get(client, auth_headers)
    assert data['week'] == 1 and data['month'] == 1
    assert data['can_play'] and data['banked_weeks'] == week_service.WEEKS_PER_DAY
    assert data['deck']['total'] == week_service.CARDS_PER_WEEK == data['deck']['remaining']
    assert data['teaser']
    assert len(fake_supabase.rows('player_game_clock')) == 1
    # Dealing is idempotent.
    assert _get(client, auth_headers)['deck']['cards'] == data['deck']['cards']
    assert len(fake_supabase.rows('player_weeks')) == 1


def test_choosing_applies_cash_and_sanity(client, auth_headers, player, balance):
    card = _get(client, auth_headers)['deck']['cards'][0]
    choice = card['choices'][1]
    res = _choose(client, auth_headers, card['id'], 'right')
    assert res.status_code == 200
    result = res.get_json()['data']['result']
    assert result['cash'] == choice['cash']
    assert balance['amount'] == Decimal('1000') + Decimal(str(choice['cash']))
    assert player['sanity'] == max(0, min(100, 60 + choice['sanity']))
    assert result['outcome'] == choice['outcome']


def test_a_card_can_only_be_chosen_once(client, auth_headers, player, balance):
    card = _get(client, auth_headers)['deck']['cards'][0]
    assert _choose(client, auth_headers, card['id'], 'left').status_code == 200
    after_first = balance['amount']
    res = _choose(client, auth_headers, card['id'], 'right')
    assert res.status_code == 409 and res.get_json()['error'] == 'ALREADY_CHOSEN'
    assert balance['amount'] == after_first


def test_unaffordable_choice_is_refused_when_a_free_one_exists(client, auth_headers, player, balance, fake_supabase):
    balance['amount'] = Decimal('0')
    cards = _get(client, auth_headers)['deck']['cards']
    paid = next(((c, ch) for c in cards for ch in c['choices'] if ch['cash'] < 0), None)
    if paid is None:
        pytest.skip('deck dealt no paid choice')
    card, choice = paid
    res = _choose(client, auth_headers, card['id'], choice['id'])
    assert res.status_code == 400 and res.get_json()['error'] == 'INSUFFICIENT_FUNDS'
    # Not claimed: the free side still works.
    assert _choose(client, auth_headers, card['id'], _free_side(card)).status_code == 200


def test_week_cannot_end_with_cards_left(client, auth_headers, player):
    _get(client, auth_headers)
    res = client.post('/api/week/complete/', headers=auth_headers)
    assert res.status_code == 400 and res.get_json()['error'] == 'CARDS_REMAINING'


def test_completing_a_week_advances_the_clock_and_locks_until_tomorrow(client, auth_headers, player):
    assert _play_week(client, auth_headers).status_code == 200      # today's first week...
    res = _play_week(client, auth_headers)                            # ...and its second
    assert res.status_code == 200
    body = res.get_json()['data']
    assert body['receipt']['week'] == 2 and len(body['receipt']['cards']) == week_service.CARDS_PER_WEEK
    assert body['receipt']['month_summary'] is None  # not a payday week
    nxt = body['next']
    assert nxt['week'] == 3 and not nxt['can_play'] and nxt['next_unlock_at']
    assert nxt['teaser']                              # the cliffhanger is already dealt
    assert nxt['last_receipt']['week'] == 2

    card = nxt['deck']['cards'][0]
    assert _choose(client, auth_headers, card['id'], 'left').status_code == 403
    assert client.post('/api/week/complete/', headers=auth_headers).status_code in (400, 403)


def test_two_weeks_a_day_and_missed_days_bank_up_to_seven(client, auth_headers, player, monkeypatch):
    assert week_service.WEEKS_PER_DAY == 2 and week_service.MAX_BANKED == 7
    assert _get(client, auth_headers)['banked_weeks'] == 2           # day one: two weeks
    assert _play_week(client, auth_headers).status_code == 200
    assert _play_week(client, auth_headers).status_code == 200
    assert not _get(client, auth_headers)['can_play']                # that's today's two
    _shift_days(monkeypatch, 1)
    assert _get(client, auth_headers)['banked_weeks'] == 2
    _shift_days(monkeypatch, 5)                                       # away for a long weekend
    data = _get(client, auth_headers)
    assert data['can_play'] and data['banked_weeks'] == 7 and data['weeks_per_day'] == 2
    for _ in range(7):
        assert _play_week(client, auth_headers).status_code == 200
    assert not _get(client, auth_headers)['can_play']


def test_topped_up_is_capped():
    assert week_service.topped_up(0, 1) == 2
    assert week_service.topped_up(3, 1) == 5
    assert week_service.topped_up(6, 3) == 7
    assert week_service.topped_up(1, 0) == 1


def test_unlimited_mode_for_playtesting(client, auth_headers, player, monkeypatch):
    monkeypatch.setenv('GAME_CLOCK_UNLIMITED', '1')
    for _ in range(3):
        assert _play_week(client, auth_headers).status_code == 200
    assert _get(client, auth_headers)['week'] == 4


def test_everyday_cards_respect_requirements(client, auth_headers, player):
    # No job and no rental: job/rental-only cards must never be dealt.
    keys = {c.get('key') for c in _get(client, auth_headers)['deck']['cards']}
    gated = {c['key'] for c in CARDS if c.get('requires') in ('job', 'rental')}
    assert not keys & gated


# --- life events in the deck ---------------------------------------------------------

def _life_event(fake, eid='ev1'):
    fake.rows('life_events').append({
        'id': eid, 'title': 'The Dental Gamble', 'description': 'Pay now or pray later?',
        'event_type': 'challenge', 'impact_sanity': -10, 'impact_income': 0, 'is_active': True,
    })
    fake.rows('life_event_choices').extend([
        {'id': f'{eid}-a', 'life_event_id': eid, 'choice_label': 'Ignore it', 'outcome_description': 'Music up.',
         'cost': 0, 'benefit': 0, 'choice_order': 1, 'impact_sanity': 0, 'impact_income': 0},
        {'id': f'{eid}-b', 'life_event_id': eid, 'choice_label': 'Dentist', 'outcome_description': 'You survive.',
         'cost': 200, 'benefit': 5, 'choice_order': 2, 'impact_sanity': 5, 'impact_income': 0},
    ])


def test_pending_life_event_is_dealt_and_resolved(client, auth_headers, player, fake_supabase, user_id, balance):
    _life_event(fake_supabase)
    fake_supabase.rows('user_life_events').append(
        {'id': 'ule1', 'user_id': user_id, 'life_event_id': 'ev1', 'choice_id': None, 'created_at': '2026-11-01T00:00:00+00:00'})
    cards = _get(client, auth_headers)['deck']['cards']
    card = next(c for c in cards if c['kind'] == 'life_event')
    assert 'user_life_event_id' not in card and all('choice_id' not in ch for ch in card['choices'])
    assert card['choices'][1]['cash'] == -195.0 and card['choices'][1]['sanity'] == 5
    assert card['choices'][0]['sanity'] == 0          # the choice's own value; no fallback to the event's -10

    assert _choose(client, auth_headers, card['id'], 'right').status_code == 200
    assert fake_supabase.rows('user_life_events')[0]['choice_id'] == 'ev1-b'
    assert balance['amount'] == Decimal('805')


# --- the month on payday weeks ----------------------------------------------------------

def test_fourth_week_runs_the_players_month(client, auth_headers, player, fake_supabase, user_id, balance, monkeypatch):
    monkeypatch.setenv('GAME_CLOCK_UNLIMITED', '1')
    player['monthly_income'] = 3000
    fake_supabase.rows('jobs').append({'user_id': user_id, 'title': 'Barista', 'salary': 36000, 'is_current': True})
    fake_supabase.rows('player_rentals').append({
        'id': 'r1', 'player_id': user_id, 'monthly_rent': 900, 'is_active': True, 'rental_properties': {'name': 'Studio'}})

    for _ in range(3):
        body = _play_week(client, auth_headers).get_json()['data']
        assert body['receipt']['month_summary'] is None
    body = _play_week(client, auth_headers).get_json()['data']
    month = body['receipt']['month_summary']
    assert body['receipt']['month'] == 1
    assert body['receipt']['is_payday_week']
    labels = {l['label']: l['amount'] for l in month['lines']}
    assert labels['Salary'] == 3000.0
    assert labels['Rent: Studio'] == -900.0
    assert labels['Groceries'] == pytest.approx(-360.0, abs=2)                  # 12% of income (+ a month of inflation)
    assert labels['Electricity, water & Wi-Fi'] == pytest.approx(-81.0, abs=1)  # unknown home: scaled from the $900 rent
    assert body['next']['month'] == 2
    assert ('add', Decimal('3000.00'), 'Monthly salary') in balance['log']


# --- robustness and economy fixes ------------------------------------------------------

def _set_deck(fake, cards):
    deck = fake.rows('player_weeks')[0]
    for i, c in enumerate(cards):
        c['id'], c['chosen'], c['result'] = f'x{i}', None, None
    deck['cards'] = cards
    return deck


def _card(key):
    return week_service._everyday_card(next(c for c in CARDS if c['key'] == key))


def test_raise_goes_on_the_job_not_permanent_income(client, auth_headers, player, fake_supabase, user_id):
    fake_supabase.rows('jobs').append({'id': 'j1', 'user_id': user_id, 'salary': 36000, 'is_current': True, 'kind': 'job'})
    _get(client, auth_headers)
    _set_deck(fake_supabase, [_card('ask_raise')])
    r = _choose(client, auth_headers, 'x0', 'right')
    assert r.status_code == 200 and r.get_json()['data']['result']['income'] == 100
    assert fake_supabase.rows('jobs')[0]['salary'] == 37200
    assert player['base_monthly_income'] == 0          # quitting the job loses the raise


def test_raise_without_a_job_now_does_nothing(client, auth_headers, player, fake_supabase):
    _get(client, auth_headers)
    _set_deck(fake_supabase, [_card('ask_raise')])
    assert _choose(client, auth_headers, 'x0', 'right').get_json()['data']['result']['income'] == 0


def test_raise_card_is_not_dealt_again_within_a_year(fake_supabase, user_id):
    fake_supabase.rows('player_weeks').append(
        {'user_id': user_id, 'week': 10, 'cards': [{'kind': 'everyday', 'key': 'ask_raise'}, {'kind': 'everyday', 'key': 'found_twenty'}]})
    recent = week_service._recent_everyday_keys(user_id, 40)
    assert 'ask_raise' in recent and 'found_twenty' not in recent      # 30 weeks later: only the raise is cooling down
    assert 'ask_raise' not in week_service._recent_everyday_keys(user_id, 63)


def test_two_cards_played_at_once_both_keep_their_results(client, auth_headers, player, fake_supabase, user_id, balance, monkeypatch):
    from app.services.balance_service import BalanceService
    _get(client, auth_headers)
    _set_deck(fake_supabase, [_card('found_twenty'), _card('found_twenty')])
    real_add = BalanceService.add_balance
    state = {'nested': False}

    def add_and_play_the_other_card(user, amount, reason, category='balance_adjustment'):
        out = real_add(user, amount, reason, category)
        if not state['nested']:           # while card 1's payment is in flight, card 2 is played
            state['nested'] = True
            week_service.choose(user_id, 'x1', 'left')
        return out
    monkeypatch.setattr(BalanceService, 'add_balance', staticmethod(add_and_play_the_other_card))

    assert _choose(client, auth_headers, 'x0', 'left').status_code == 200
    cards = fake_supabase.rows('player_weeks')[0]['cards']
    assert all(c['chosen'] == 'left' and c['result'] for c in cards)    # card 1's result used to be dropped


def test_cast_failure_does_not_strand_the_week(client, auth_headers, player, fake_supabase, monkeypatch):
    from app.game import cast
    monkeypatch.setattr(cast, 'react_to_week', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom')))
    assert _play_week(client, auth_headers).status_code == 200
    week1 = next(w for w in fake_supabase.rows('player_weeks') if w['week'] == 1)
    assert week1['status'] == 'completed' and week1['receipt']['texts'] == []


def test_receipt_falls_back_to_listed_effects_when_a_result_is_missing(client, auth_headers, player, fake_supabase):
    _get(client, auth_headers)
    deck = _set_deck(fake_supabase, [_card('found_twenty')])
    deck['cards'][0]['chosen'] = 'left'           # chosen, result never stored
    r = client.post('/api/week/complete/', headers=auth_headers)
    line = r.get_json()['data']['receipt']['cards'][0]
    assert line['cash'] == deck['cards'][0]['choices'][0]['cash'] == 20
