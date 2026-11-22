"""Money realism: gigs, lifestyle running costs & leasing, asset growth, household bills, friend loans."""
import random
import uuid
from decimal import Decimal

import pytest

from app.game import economy
from jobs.monthly_loan_deductions import process_month_for_user
from tests.conftest import make_token


@pytest.fixture
def wallets(monkeypatch):
    """One wallet per player: {user_id: Decimal}, plus a log."""
    from app.services.balance_service import BalanceService
    w = {'log': []}

    def get(uid):
        return w.get(str(uid), Decimal('0'))

    def add(user_id, amount, reason, category='x'):
        w[str(user_id)] = get(user_id) + Decimal(str(amount))
        w['log'].append((str(user_id), Decimal(str(amount)), reason))
        return {'new_balance': w[str(user_id)]}

    def sub(user_id, amount, reason, category='x'):
        amount = Decimal(str(amount))
        if amount > get(user_id):
            raise ValueError('Insufficient funds')
        w[str(user_id)] = get(user_id) - amount
        w['log'].append((str(user_id), -amount, reason))
        return {'new_balance': w[str(user_id)]}

    monkeypatch.setattr(BalanceService, 'get_current_balance', staticmethod(get))
    monkeypatch.setattr(BalanceService, 'add_balance', staticmethod(add))
    monkeypatch.setattr(BalanceService, 'subtract_balance', staticmethod(sub))
    from app.services.push_notification_service import ExpoPushService
    monkeypatch.setattr(ExpoPushService, 'send_notification_to_user', classmethod(lambda cls, *a, **k: True))
    monkeypatch.setattr(ExpoPushService, 'notify_followers_of_financial_move', staticmethod(lambda **k: True))
    return w


def _player(fake, name='me', income=3000, credit=700, sanity=60, uid=None):
    uid = uid or str(uuid.uuid4())
    fake.rows('profiles').append({'user_id': uid, 'username': name, 'monthly_income': income, 'base_monthly_income': 0,
                                  'credit_score': credit, 'sanity': sanity, 'net_worth': 0})
    return uid, {'Authorization': f'Bearer {make_token(uid)}'}


def _lines(month):
    return {l['label']: l for l in month['lines']}


# --- gigs -----------------------------------------------------------------------------------

IDS = {k: str(uuid.uuid4()) for k in ('m1', 'm2', 'g0', 'g1', 'g2', 'mortgage')}


def _market(fake):
    main = {'id': IDS['m1'], 'title': 'Barista', 'company': 'Bean', 'salary': 36000, 'kind': 'job'}
    gigs = [{'id': IDS[f'g{i}'], 'title': t, 'company': 'Self', 'salary': 0, 'kind': 'gig', 'weekly_pay': p, 'sanity_per_week': s}
            for i, (t, p, s) in enumerate([('Rideshare', 140, -2), ('Tutor', 85, 0), ('Reseller', 70, 1)])]
    fake.rows('job_market').extend([main, {**main, 'id': IDS['m2'], 'title': 'Clerk'}, *gigs])


def test_one_main_job_and_two_gigs(client, fake_supabase, wallets, monkeypatch):
    from app.services.profile_service import ProfileService
    monkeypatch.setattr(ProfileService, 'recalculate_monthly_income', staticmethod(lambda uid: 0))
    _market(fake_supabase)
    uid, h = _player(fake_supabase)
    apply = lambda jid: client.post('/api/jobs/apply/', json={'job_id': IDS[jid]}, headers=h).get_json()
    assert apply('m1')['success']
    assert apply('m2')['error'] == 'JOB_LIMIT_REACHED'
    gig = apply('g0')
    assert gig['success'] and gig['signing_bonus'] == 0 and gig['weekly_pay'] == 140
    assert apply('g1')['success']
    assert apply('g2')['error'] == 'GIG_LIMIT_REACHED'
    rows = [j for j in fake_supabase.rows('jobs') if j['kind'] == 'gig']
    assert {j['salary'] for j in rows} == {0}


def test_gigs_pay_every_week_and_cost_a_little_sanity(client, fake_supabase, wallets, monkeypatch):
    from tests.test_week import _play_week
    monkeypatch.delenv('GAME_CLOCK_UNLIMITED', raising=False)
    uid, h = _player(fake_supabase, sanity=60)
    wallets[uid] = Decimal('500')
    fake_supabase.rows('jobs').extend([
        {'user_id': uid, 'title': 'Rideshare Driver', 'kind': 'gig', 'weekly_pay': 140, 'sanity_per_week': -2, 'is_current': True, 'salary': 0},
        {'user_id': uid, 'title': 'Online Reseller', 'kind': 'gig', 'weekly_pay': 70, 'sanity_per_week': 1, 'is_current': True, 'salary': 0},
    ])
    receipt = _play_week(client, h).get_json()['data']['receipt']
    assert receipt['gigs'] == [{'title': 'Rideshare Driver', 'pay': 140.0, 'sanity': -2}, {'title': 'Online Reseller', 'pay': 70.0, 'sanity': 1}]
    assert (uid, Decimal('140.00'), 'Gig: Rideshare Driver') in wallets['log']


def test_game_month_salary_leaves_gigs_to_the_week(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=0)
    fake_supabase.rows('jobs').extend([
        {'user_id': uid, 'title': 'Barista', 'salary': 36000, 'is_current': True},
        {'user_id': uid, 'title': 'Tutor', 'kind': 'gig', 'weekly_pay': 85, 'salary': 0, 'is_current': True},
    ])
    month = process_month_for_user(uid, game_years=0)
    assert _lines(month)['Salary']['amount'] == 3000.0
    assert not any(l.startswith('Gig') for l in _lines(month))


# --- lifestyle items ------------------------------------------------------------------------

JET = {'name': 'Private Jet', 'category': 'aircraft', 'base_price': 4500000, 'monthly_cost': 38000, 'depreciation_rate': 0.07,
       'costs': [{'label': 'Fuel', 'monthly': 12000}, {'label': 'Insurance', 'monthly': 6000}, {'label': 'Crew', 'monthly': 15000}, {'label': 'Hangar', 'monthly': 5000}],
       'service_cost': 90000, 'service_every_months': 6, 'lease_income': 140000, 'lease_label': 'Lease it', 'lease_wear': 0.05}
SEDAN = {'name': 'Used Sedan', 'category': 'vehicle', 'base_price': 9000, 'monthly_cost': 180, 'depreciation_rate': 0.15,
         'costs': [{'label': 'Fuel', 'monthly': 110}, {'label': 'Insurance', 'monthly': 55}, {'label': 'Parking', 'monthly': 15}],
         'service_cost': 250, 'service_every_months': 6, 'lease_income': 420, 'lease_wear': 0.10}


def _own(fake, uid, item, **kw):
    row = {'id': str(uuid.uuid4()), 'player_id': uid, 'liability_id': 'li', 'purchase_price': item['base_price'],
           'current_value': item['base_price'], 'monthly_cost': item['monthly_cost'], 'is_active': True,
           'months_owned': 0, 'liability_items': item, **kw}
    fake.rows('player_liabilities').append(row)
    return row


def test_running_costs_are_itemised_and_service_comes_every_6_months(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=0)
    wallets[uid] = Decimal('10000')
    car = _own(fake_supabase, uid, SEDAN, months_owned=4)
    month = process_month_for_user(uid)
    line = _lines(month)['Used Sedan running costs']
    assert line['amount'] == -180.0 and line['note'] == 'Fuel $110 · Insurance $55 · Parking $15'
    assert car['months_owned'] == 5 and car['current_value'] == pytest.approx(9000 * (0.85 ** (1 / 12)), abs=0.01)
    month = process_month_for_user(uid)                          # month 6: service due
    assert _lines(month)['Used Sedan running costs']['amount'] == -430.0
    assert 'Service $250' in _lines(month)['Used Sedan running costs']['note']


def test_a_rolex_holds_its_value(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=0)
    wallets[uid] = Decimal('1000')
    watch = _own(fake_supabase, uid, {'name': 'Rolex', 'base_price': 14000, 'monthly_cost': 15, 'depreciation_rate': 0.0,
                                      'costs': [{'label': 'Insurance', 'monthly': 15}]})
    process_month_for_user(uid)
    assert watch['current_value'] == 14000


def test_leasing_a_jet_earns_income_and_wears_it_faster(client, fake_supabase, wallets, monkeypatch):
    uid, h = _player(fake_supabase, income=0)
    wallets[uid] = Decimal('500000')
    jet = _own(fake_supabase, uid, JET)
    idle = _own(fake_supabase, uid, {**JET, 'name': 'Spare Jet'})
    assert client.post(f"/api/liabilities/luxury/{jet['id']}/lease/", json={'leased': True}, headers=h).get_json()['data']['is_leased']
    monkeypatch.setattr(economy.random, 'uniform', lambda a, b: 0.8)
    month = process_month_for_user(uid)
    leased = _lines(month)['Private Jet leased out']
    assert leased['amount'] == 112000.0 and leased['note'] == '80% booked'
    assert 'Spare Jet leased out' not in _lines(month)
    assert jet['current_value'] < idle['current_value']        # extra wear while leased
    phone = _own(fake_supabase, uid, {'name': 'Phone', 'base_price': 1200, 'monthly_cost': 40, 'lease_income': 0})
    assert client.post(f"/api/liabilities/luxury/{phone['id']}/lease/", json={'leased': True}, headers=h).get_json()['error'] == 'NOT_LEASABLE'


def test_item_economics_shows_the_true_cost():
    e = economy.item_economics(JET)
    assert e['monthly_running'] == 38000 and e['leasable'] and e['lease_income_expected'] == 108500
    assert e['first_year_value_loss'] == 315000
    assert e['true_monthly_cost'] == pytest.approx(38000 + 15000 + 26250)
    assert e['lease_net_monthly'] == pytest.approx(108500 - 38000 - 15000 - 18750)


# --- assets ---------------------------------------------------------------------------------

def test_property_grows_on_game_months_and_stocks_dont(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=0)
    fake_supabase.rows('assets').extend([{'name': 'Duplex', 'monthly_income': 1900}, {'name': 'VTI', 'monthly_income': 0.75}])
    house = {'id': 'a1', 'user_id': uid, 'name': 'Duplex', 'asset_type': 'real_estate', 'value': 240000, 'purchase_price': 240000, 'quantity': 1}
    stock = {'id': 'a2', 'user_id': uid, 'name': 'VTI', 'asset_type': 'stocks', 'value': 250, 'purchase_price': 250, 'quantity': 10}
    fake_supabase.rows('user_assets').extend([house, stock])
    month = process_month_for_user(uid)
    assert _lines(month)['Duplex yield']['amount'] == 1900.0 and _lines(month)['VTI yield']['amount'] == 7.5
    assert house['value'] == 241200.0 and house['months_held'] == 1
    assert stock['value'] == 250


def test_income_figures_per_week_month_year():
    f = economy.income_figures(1900, 1, 240000, 'real_estate')
    assert f['income_monthly'] == 1900 and f['income_annual'] == 22800 and f['income_weekly'] == 438.46
    assert f['yield_pct'] == 9.5 and f['growth_pct'] == 6.0 and f['total_return_pct'] == 15.5
    assert economy.income_figures(0, 3, 60000, 'crypto')['growth_pct'] is None


# --- household bills ------------------------------------------------------------------------

def _rent(fake, uid, rent=950, ptype='studio'):
    fake.rows('player_rentals').append({'id': f'r-{uid[:5]}', 'player_id': uid, 'monthly_rent': rent, 'is_active': True,
                                        'rental_properties': {'name': 'Studio', 'property_type': ptype}})


def test_renters_pay_groceries_and_home_bills(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=2000)
    wallets[uid] = Decimal('5000')
    _rent(fake_supabase, uid)
    lines = _lines(process_month_for_user(uid))
    assert lines['Groceries']['amount'] == -240.0
    assert lines['Electricity, water & Wi-Fi']['amount'] == -90.0
    assert lines['Electricity, water & Wi-Fi']['note'] == 'Electricity $45 · Water $15 · Wi-Fi $30'


def test_living_with_parents_means_chipping_in(fake_supabase, wallets):
    uid, _ = _player(fake_supabase, income=2000)
    wallets[uid] = Decimal('5000')
    lines = _lines(process_month_for_user(uid))
    assert lines['Chipping in at home']['amount'] == -100.0 and 'Electricity, water & Wi-Fi' not in lines


def test_roommates_split_rent_and_bills_and_save_on_groceries(fake_supabase, wallets):
    holder, _ = _player(fake_supabase, 'holder', income=2000)
    mate, _ = _player(fake_supabase, 'mate', income=2000)
    wallets[holder] = wallets[mate] = Decimal('5000')
    _rent(fake_supabase, holder)
    fake_supabase.rows('roommates').append({'id': 'rm', 'leaseholder_id': holder, 'roommate_id': mate, 'status': 'active', 'rent_share': 0.5})

    mine = _lines(process_month_for_user(mate))
    assert mine['Rent share: Studio']['amount'] == -475.0
    assert mine['Bills share: Studio']['amount'] == -45.0
    assert mine['Groceries']['amount'] == -192.0                       # 20% cheaper together
    assert 'Chipping in at home' not in mine and 'Electricity, water & Wi-Fi' not in mine
    assert wallets[holder] == Decimal('5000') + 475 + 45

    theirs = _lines(process_month_for_user(holder))
    assert theirs['Groceries']['amount'] == -192.0
    assert theirs['Electricity, water & Wi-Fi']['note'].endswith('(your roommate pays you half)')


# --- friend loans ---------------------------------------------------------------------------

def _friends(fake, a, b):
    fake.rows('user_follows').append({'id': str(uuid.uuid4()), 'follower_id': a, 'following_id': b})


def test_friend_offers_are_capped_and_can_be_private(client, fake_supabase, wallets):
    lender, lh = _player(fake_supabase, 'lender')
    friend, fh = _player(fake_supabase, 'friend')
    stranger, sh = _player(fake_supabase, 'stranger')
    wallets[lender] = Decimal('20000')
    offer = lambda **kw: client.post('/api/loans/p2p/offer/', json={'amount': 1000, 'interest_rate': 10, 'term_months': 12, **kw}, headers=lh).get_json()
    assert offer(amount=15000)['error'] == 'TOO_BIG'
    assert offer(offered_to=friend)['error'] == 'NOT_FRIENDS'
    _friends(fake_supabase, friend, lender)                     # a follow either way counts
    loan_id = offer(offered_to=friend)['loan_id']
    assert wallets[lender] == Decimal('19000')                 # escrowed
    seen = lambda h: [l['id'] for l in client.get('/api/loans/p2p/available/', headers=h).get_json()['data']]
    assert loan_id in seen(fh) and loan_id not in seen(sh)
    assert client.post('/api/loans/p2p/accept/', json={'loan_id': loan_id}, headers=sh).status_code == 404
    res = client.post('/api/loans/p2p/accept/', json={'loan_id': loan_id}, headers=fh).get_json()
    assert res['success'] and wallets[friend] == Decimal('1000')
    debt = fake_supabase.rows('liabilities')[0]
    assert debt['remaining_balance'] == 1100.0 and debt['monthly_payment'] == pytest.approx(91.67)   # 10% a year for 1 year


def test_ask_a_friend_and_they_lend(client, fake_supabase, wallets):
    borrower, bh = _player(fake_supabase, 'borrower')
    lender, lh = _player(fake_supabase, 'lender')
    _friends(fake_supabase, borrower, lender)
    ask = client.post('/api/loans/p2p/request/', json={'lender_id': lender, 'amount': 2400, 'interest_rate': 8, 'term_months': 24, 'purpose': 'Car repair'}, headers=bh).get_json()
    assert ask['success']
    mine = client.get('/api/loans/p2p/mine/', headers=lh).get_json()['data']
    req = mine['requests_to_me'][0]
    assert req['with']['username'] == 'borrower' and req['total_interest'] == 384.0 and req['borrower_record']['missed'] == 0
    assert client.post(f"/api/loans/p2p/requests/{req['id']}/approve/", headers=lh).get_json()['error'] == 'INSUFFICIENT_FUNDS'
    wallets[lender] = Decimal('5000')
    assert client.post(f"/api/loans/p2p/requests/{req['id']}/approve/", headers=lh).get_json()['success']
    assert wallets[lender] == Decimal('2600') and wallets[borrower] == Decimal('2400')
    assert client.get('/api/loans/p2p/mine/', headers=bh).get_json()['data']['borrowed'][0]['monthly_payment'] == 116.0


def test_friends_get_paid_first_and_short_months_pay_what_they_can(fake_supabase, wallets):
    borrower, _ = _player(fake_supabase, 'borrower', income=0)
    lender, _ = _player(fake_supabase, 'lender', income=0)
    fake_supabase.rows('p2p_loans').append({'id': 'p1', 'lender_id': lender, 'borrower_id': borrower, 'status': 'active',
                                           'amount': 1000, 'interest_rate': 10, 'term_months': 12, 'remaining_balance': 1100})
    fake_supabase.rows('liabilities').extend([
        {'id': 'bank', 'user_id': borrower, 'name': 'Personal Loan', 'liability_type': 'bank_loan', 'monthly_payment': 200, 'remaining_balance': 2000},
        {'id': 'friend', 'user_id': borrower, 'name': 'Friend loan', 'liability_type': 'p2p_loan', 'p2p_loan_id': 'p1', 'monthly_payment': 100, 'remaining_balance': 1100},
    ])
    wallets[borrower] = Decimal('150')
    process_month_for_user(borrower)
    assert wallets[lender] == Decimal('100')                  # the friend was paid in full, first
    loan = fake_supabase.rows('p2p_loans')[0]
    assert loan['payments_made'] == 1 and loan['payments_missed'] == 0
    bank = next(l for l in fake_supabase.rows('liabilities') if l['id'] == 'bank')
    assert bank['remaining_balance'] == pytest.approx(2000 - 50 + 7.5)    # $50 paid, $150 short + 5% fee

    wallets[borrower] = Decimal('40')
    process_month_for_user(borrower)
    assert wallets[lender] == Decimal('140') and loan['payments_missed'] == 1


def test_banks_check_you_can_afford_it(client, fake_supabase, wallets):
    uid, h = _player(fake_supabase, income=2000, credit=800)
    fake_supabase.rows('bank_loans').append({'id': IDS['mortgage'], 'borrower_id': None, 'type': 'Mortgage', 'amount': 250000, 'interest_rate': 0.13,
                                            'term': 180, 'monthly_payment': 3163.11, 'total_interest': 319358.98, 'credit_required': 720, 'collateral': 'property'})
    res = client.post('/api/loans/apply/', json={'loan_id': IDS['mortgage']}, headers=h).get_json()
    assert res['error'] == 'CANT_AFFORD' and '43%' in res['message']
