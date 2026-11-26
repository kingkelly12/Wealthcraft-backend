"""
Money rules shared by the game week, the game month and the API.

* Gigs: part-time work beside your main job, paid every game week.
* Lifestyle items: an annual depreciation rate, monthly running costs (fuel,
  insurance, crew...), a periodic service bill, and leasing for income.
* Assets: income per week / month / year, and appreciation on game months.
  Businesses' profit swings month to month by risk level.
* Household bills: groceries plus electricity, water and Wi-Fi for the home
  you rent. Roommates split the home bills and save on groceries.
* Loans: friend (P2P) loan maths, limits, and who counts as a friend.
"""
import math
import random
from decimal import Decimal, ROUND_HALF_UP, ROUND_UP

from app import supabase

CENT = Decimal('0.01')
WEEKS_PER_YEAR = 52


def money(x) -> Decimal:
    return Decimal(str(x or 0)).quantize(CENT, rounding=ROUND_HALF_UP)


def monthly_rate(annual) -> Decimal:
    """The monthly rate that compounds to `annual` over 12 months."""
    a = float(annual or 0)
    if a <= 0:
        return Decimal('0')
    return Decimal(str(1 - (1 - min(a, 0.99)) ** (1 / 12)))


# --- Jobs and gigs --------------------------------------------------------------------
MAX_MAIN_JOBS = 1
MAX_GIGS = 2


def weekly_to_monthly(weekly) -> Decimal:
    return money(Decimal(str(weekly or 0)) * WEEKS_PER_YEAR / 12)


def current_gigs(uid):
    return supabase.table('jobs').select('id, title, weekly_pay, sanity_per_week') \
        .eq('user_id', str(uid)).eq('is_current', True).eq('kind', 'gig').execute().data or []


# --- Lifestyle items ------------------------------------------------------------------
VALUE_FLOOR = Decimal('0.05')         # items never fall below 5% of what you paid
LEASE_BOOKED = (0.55, 1.0)            # share of the month a leased item is booked


def item_of(pliab):
    item = pliab.get('liability_items') or {}
    if isinstance(item, list):
        item = item[0] if item else {}
    return item


def running_costs(pliab):
    """[(label, monthly)] for an owned item. Older items without a breakdown use monthly_cost."""
    item = item_of(pliab)
    costs = [(c.get('label', 'Upkeep'), money(c.get('monthly'))) for c in (item.get('costs') or []) if float(c.get('monthly') or 0) > 0]
    if costs:
        return costs
    legacy = money(pliab.get('monthly_cost') or item.get('monthly_cost'))
    return [('Upkeep', legacy)] if legacy > 0 else []


def service_due(pliab, months_owned):
    item = item_of(pliab)
    every = int(item.get('service_every_months') or 0)
    cost = money(item.get('service_cost'))
    return cost if every > 0 and cost > 0 and months_owned > 0 and months_owned % every == 0 else Decimal('0')


def annual_depreciation(pliab):
    """This item's depreciation a year, plus extra wear while it's leased out."""
    item = item_of(pliab)
    rate = float(item.get('depreciation_rate') if item.get('depreciation_rate') is not None else 0.125)
    if pliab.get('is_leased'):
        rate += float(item.get('lease_wear') or 0)
    return rate


def depreciate(pliab):
    """New value after one month."""
    price = money(pliab.get('purchase_price'))
    value = money(pliab.get('current_value') if pliab.get('current_value') is not None else price)
    rate = monthly_rate(annual_depreciation(pliab))
    if rate <= 0:
        return value
    return max(money(value * (1 - rate)), money(price * VALUE_FLOOR))


def lease_income(pliab, rng=random):
    """(income, booked share) for a leased item this month."""
    item = item_of(pliab)
    gross = money(item.get('lease_income'))
    if not pliab.get('is_leased') or gross <= 0:
        return Decimal('0'), 0.0
    booked = round(rng.uniform(*LEASE_BOOKED), 2)
    return money(gross * Decimal(str(booked))), booked


def item_economics(item, owned=None):
    """What an item really costs (and can earn), for the shop and your garage."""
    monthly = sum((money(c.get('monthly')) for c in (item.get('costs') or [])), Decimal('0')) or money(item.get('monthly_cost'))
    every = int(item.get('service_every_months') or 0)
    service = money(item.get('service_cost'))
    service_monthly = money(service / every) if every else Decimal('0')
    rate = float(item.get('depreciation_rate') if item.get('depreciation_rate') is not None else 0.125)
    price = money(item.get('base_price') or (owned or {}).get('purchase_price'))
    lease = money(item.get('lease_income'))
    avg_booked = Decimal(str(sum(LEASE_BOOKED) / 2))
    out = {
        'costs': item.get('costs') or ([{'label': 'Upkeep', 'monthly': float(monthly)}] if monthly else []),
        'monthly_running': float(monthly),
        'service_cost': float(service),
        'service_every_months': every,
        'depreciation_rate': rate,
        'first_year_value_loss': float(money(price * Decimal(str(rate)))),
        'true_monthly_cost': float(monthly + service_monthly + money(price * Decimal(str(rate)) / 12)),
        'leasable': lease > 0,
        'lease_label': item.get('lease_label'),
        'lease_income': float(lease),
        'lease_income_expected': float(money(lease * avg_booked)),
        'lease_wear': float(item.get('lease_wear') or 0),
    }
    if lease > 0:
        expected = money(lease * avg_booked)
        extra_wear = money(price * Decimal(str(item.get('lease_wear') or 0)) / 12)
        out['lease_net_monthly'] = float(expected - monthly - service_monthly - extra_wear)
    return out


# --- Showcase -------------------------------------------------------------------------
# The things players buy to show off, shown on their profile: cars, motorbikes,
# boats, helicopters and private jets (and other aircraft). Accessories and gadgets
# aren't part of it. 'vehicle' and 'boat' are the names before migration 20261213000000.
SHOWCASE_KINDS = {'cars': 'cars', 'motorbikes': 'motorbikes', 'boats': 'boats', 'aircraft': 'aircraft',
                  'vehicle': 'cars', 'boat': 'boats'}
_MOTORBIKE_WORDS = ('bike', 'motorcycle', 'scooter')
_EMOJI_BY_NAME = [
    ('jet ski', '🌊'), ('superyacht', '🛥️'), ('catamaran', '⛵'), ('boat', '🚤'),
    ('helicopter', '🚁'), ('jet', '🛩️'), ('aircraft', '🛩️'),
    ('supercar', '🏎️'), ('sports', '🏎️'), ('bike', '🏍️'), ('suv', '🚙'), ('convertible', '🚘'),
    ('electric', '🚘'),
]
_EMOJI_BY_KIND = {'cars': '🚗', 'motorbikes': '🏍️', 'boats': '🚤', 'aircraft': '✈️'}


def showcase(owned):
    """A player's flex items, most valuable first, with totals by kind."""
    items = []
    for pl in owned or []:
        item = item_of(pl)
        kind = SHOWCASE_KINDS.get((item.get('category') or '').lower())
        if not kind or pl.get('is_active') is False:
            continue
        name = item.get('name') or pl.get('name') or 'Item'
        low = name.lower()
        if kind == 'cars' and any(w in low for w in _MOTORBIKE_WORDS):
            kind = 'motorbikes'
        price = money(pl.get('purchase_price') or item.get('base_price'))
        value = money(pl.get('current_value') if pl.get('current_value') is not None else price)
        items.append({
            'id': pl.get('id'),
            'name': name,
            'kind': kind,
            'emoji': next((e for key, e in _EMOJI_BY_NAME if key in low), _EMOJI_BY_KIND[kind]),
            'image_url': item.get('image_url'),
            'value': float(value),
            'purchase_price': float(price),
            'is_leased': bool(pl.get('is_leased')),
            'lease_label': item.get('lease_label') if pl.get('is_leased') else None,
            'since': pl.get('purchase_date'),
        })
    items.sort(key=lambda i: i['value'], reverse=True)
    counts = {k: sum(1 for i in items if i['kind'] == k) for k in ('cars', 'motorbikes', 'boats', 'aircraft')}
    return {'items': items, 'total_value': float(sum(Decimal(str(i['value'])) for i in items)), 'counts': counts}


# --- Assets ---------------------------------------------------------------------------
APPRECIATING = ('real_estate', 'business', 'property')
APPRECIATION_YEAR_1 = Decimal('0.005')     # a month (~6% a year)
APPRECIATION_LATER = Decimal('0.0025')     # a month (~3% a year)
APPRECIATION_CEILING = Decimal('2.0')      # never above 2x what you paid


def appreciates(asset_type):
    return (asset_type or '').lower() in APPRECIATING


def appreciate(ua):
    """(new holding value, months held) after one month for property and businesses.

    `value` is for the whole holding and `purchase_price` per unit, so the ceiling is 2x the
    price of every unit held."""
    held = int(ua.get('months_held') or 0) + 1
    value = money(ua.get('value'))
    basis = money(ua.get('purchase_price')) * Decimal(str(ua.get('quantity') or 1))
    if basis <= 0 or value <= 0:
        return value, held
    rate = APPRECIATION_YEAR_1 if held <= 12 else APPRECIATION_LATER
    return min(money(value * (1 + rate)), money(basis * APPRECIATION_CEILING)), held


# --- Business profit ------------------------------------------------------------------
# A business doesn't pay the same every month: some months are great, some are
# dead. Profit is the listed monthly income times a swing drawn from this band
# (by risk level). Each band averages about 1.0, so the listed figure is the
# expected month.
PROFIT_SWING = {
    'low':       (0.85, 1.15),
    'medium':    (0.70, 1.30),
    'high':      (0.50, 1.50),
    'very_high': (0.20, 1.80),
}


def is_business(category) -> bool:
    return (category or '').lower() == 'business'


def swing_band(risk_level):
    return PROFIT_SWING.get((risk_level or 'medium').lower(), PROFIT_SWING['medium'])


def profit_swing(risk_level, rng=None) -> Decimal:
    """This month's multiplier on a business's listed profit."""
    lo, hi = swing_band(risk_level)
    return Decimal(str(round((rng or random).uniform(lo, hi), 2)))


def month_mood(swing: Decimal) -> str:
    if swing >= Decimal('1.2'):
        return 'great month'
    if swing >= Decimal('0.95'):
        return 'good month'
    if swing >= Decimal('0.7'):
        return 'slow month'
    return 'rough month'


def income_figures(monthly_per_unit, quantity=1, cost_basis_per_unit=None, category=None, risk_level=None):
    """Income per week / month / year, the yield on what you paid, and expected growth."""
    monthly = money(Decimal(str(monthly_per_unit or 0)) * Decimal(str(quantity or 1)))
    annual = monthly * 12
    basis = money(Decimal(str(cost_basis_per_unit or 0)) * Decimal(str(quantity or 1)))
    growth = 6.0 if appreciates(category) else None
    yield_pct = float(round(annual / basis * 100, 1)) if basis > 0 else None
    return {
        'income_weekly': float(money(annual / WEEKS_PER_YEAR)),
        'income_monthly': float(monthly),
        'income_annual': float(annual),
        'yield_pct': yield_pct,
        'growth_pct': growth,              # property & businesses; markets move on their own
        'total_return_pct': (yield_pct or 0) + growth if growth is not None and yield_pct is not None else yield_pct,
        # Businesses: what a bad and a great month pay (the figures above are the average).
        'profit_range': ({'low': float(money(monthly * Decimal(str(swing_band(risk_level)[0])))),
                          'high': float(money(monthly * Decimal(str(swing_band(risk_level)[1]))))}
                         if is_business(category) and monthly > 0 else None),
        # Months of income to earn back what you paid (ignoring growth).
        'payback_months': math.ceil(basis / monthly) if monthly > 0 and basis > 0 else None,
    }


# --- Household bills ------------------------------------------------------------------
GROCERIES_SHARE = Decimal('0.12')          # of monthly income
GROCERIES_MIN = Decimal('120')             # even with no income you eat (only charged with income)
SHARED_GROCERIES = Decimal('0.80')         # cooking together: 20% cheaper each
PARENTS_SHARE = Decimal('0.05')            # chipping in at home when you live with your parents
INFLATION = 1.05                           # a game year

# Electricity / water / Wi-Fi a month, by home.
HOME_BILLS = {
    'room':      {'Electricity': 25,  'Water': 10, 'Wi-Fi': 15},
    'studio':    {'Electricity': 45,  'Water': 15, 'Wi-Fi': 30},
    'apartment': {'Electricity': 70,  'Water': 25, 'Wi-Fi': 35},
    'condo':     {'Electricity': 110, 'Water': 35, 'Wi-Fi': 45},
    'house':     {'Electricity': 140, 'Water': 45, 'Wi-Fi': 45},
    'penthouse': {'Electricity': 300, 'Water': 80, 'Wi-Fi': 60},
}


def _inflate(amount, years):
    return money(Decimal(str(amount)) * Decimal(str(INFLATION ** min(max(float(years or 0), 0), 20))))


def home_bills(rental, years=0):
    """{'Electricity', 'Water', 'Wi-Fi'} for a rented home."""
    prop = (rental or {}).get('rental_properties') or {}
    if isinstance(prop, list):
        prop = prop[0] if prop else {}
    table = HOME_BILLS.get((prop.get('property_type') or '').lower())
    if not table:  # unknown home: scale with the rent
        rent = float((rental or {}).get('monthly_rent') or prop.get('monthly_rent') or 0)
        table = {'Electricity': rent * 0.045, 'Water': rent * 0.015, 'Wi-Fi': min(60.0, max(15.0, rent * 0.03))}
    return {k: _inflate(v, years) for k, v in table.items()}


def groceries(monthly_income, years=0, shared=False):
    income = Decimal(str(monthly_income or 0))
    if income <= 0:
        return Decimal('0')
    cost = _inflate(max(income * GROCERIES_SHARE, GROCERIES_MIN), years)
    return money(cost * SHARED_GROCERIES) if shared else cost


def parents_contribution(monthly_income, years=0):
    income = Decimal(str(monthly_income or 0))
    return _inflate(income * PARENTS_SHARE, years) if income > 0 else Decimal('0')


# --- Loans ----------------------------------------------------------------------------
P2P_MAX_AMOUNT = Decimal('10000')          # friends lend small; banks lend big
P2P_MAX_RATE = Decimal('60')               # % a year
MAX_DTI = Decimal('0.43')                  # all loan payments / monthly income


def p2p_terms(amount, annual_rate_pct, term_months):
    """Simple interest a year: what a friend loan costs in total and per month."""
    amount = money(amount)
    interest = money(amount * Decimal(str(annual_rate_pct)) / 100 * Decimal(term_months) / 12)
    total = amount + interest
    return {'interest': interest, 'total': total, 'monthly': money(total / int(term_months))}


def loan_terms(loan):
    """Terms of an existing p2p_loans row (older rows used a flat total %)."""
    if loan.get('rate_basis') == 'total':
        amount = money(loan['amount'])
        interest = money(amount * Decimal(str(loan['interest_rate'])) / 100)
        return {'interest': interest, 'total': amount + interest, 'monthly': money((amount + interest) / int(loan['term_months']))}
    return p2p_terms(loan['amount'], loan['interest_rate'], loan['term_months'])


PAYDAYS_PER_YEAR = 13                      # a game year is 52 weeks, and every 4th week is payday


def payoff_amount(loan) -> Decimal:
    """
    What clearing a loan costs today. Interest is added to the balance when a loan starts, so paying
    early would still cost all of it; instead the interest not yet earned is refunded, in proportion
    to what is left. Late fees (a balance above what was first owed) earn no refund.
    """
    remaining = money(loan.get('remaining_balance'))
    interest = money(loan.get('total_interest'))
    first_owed = money(loan.get('amount')) + interest
    if remaining <= 0 or interest <= 0 or first_owed <= 0:
        return remaining
    rebate = money(interest * min(remaining, first_owed) / first_owed)
    return max(Decimal('0'), remaining - rebate)


def amortised_loan(principal, annual_pct, payment, payments_per_year=PAYDAYS_PER_YEAR) -> dict:
    """
    A loan repaid at a fixed `payment` each payday, with interest on what is still owed:
    {'term' (payments), 'total' (all of it paid back), 'interest'}. The last payment is smaller.
    """
    principal, payment = money(principal), money(payment)
    rate = Decimal(str(annual_pct)) / 100 / payments_per_year
    balance, total, term = principal, Decimal('0'), 0
    if payment <= principal * rate:
        raise ValueError('The payment does not even cover the interest')
    while balance > 0 and term < 1200:
        balance = money(balance * (1 + rate))
        paid = min(payment, balance)
        balance -= paid
        total += paid
        term += 1
    return {'term': term, 'total': total, 'interest': total - principal}


def are_friends(a, b):
    """People who know each other in the game: a follow either way, same squad, or roommates."""
    a, b = str(a), str(b)
    if a == b:
        return False
    for x, y in ((a, b), (b, a)):
        if supabase.table('user_follows').select('id').eq('follower_id', x).eq('following_id', y).limit(1).execute().data:
            return True
    sa = supabase.table('squad_members').select('squad_id').eq('user_id', a).limit(1).execute().data
    sb = supabase.table('squad_members').select('squad_id').eq('user_id', b).limit(1).execute().data
    if sa and sb and sa[0]['squad_id'] == sb[0]['squad_id']:
        return True
    rm = supabase.table('roommates').select('id').eq('status', 'active') \
        .or_(f'leaseholder_id.eq.{a},roommate_id.eq.{a}').execute().data or []
    return any(True for r in rm if b in (str(r.get('leaseholder_id')), str(r.get('roommate_id'))))


def repayment_record(uid):
    """How reliably someone has repaid friend loans: {'made', 'missed', 'loans'}."""
    rows = supabase.table('p2p_loans').select('payments_made, payments_missed, status') \
        .eq('borrower_id', str(uid)).in_('status', ['active', 'completed', 'defaulted']).execute().data or []
    return {
        'made': sum(int(r.get('payments_made') or 0) for r in rows),
        'missed': sum(int(r.get('payments_missed') or 0) for r in rows),
        'loans': len(rows),
        'repaid': sum(1 for r in rows if r.get('status') == 'completed'),
    }


def finances(uid):
    """(monthly income, what you already pay on loans each month), for borrowing checks."""
    prof = supabase.table('profiles').select('monthly_income').eq('user_id', str(uid)).limit(1).execute().data
    income = Decimal(str((prof[0] if prof else {}).get('monthly_income') or 0))
    debts = supabase.table('liabilities').select('monthly_payment').eq('user_id', str(uid)).gt('remaining_balance', 0).execute().data or []
    return income, sum((Decimal(str(d.get('monthly_payment') or 0)) for d in debts), Decimal('0'))


def dti_problem(income, current_payments, extra_monthly):
    """None if the new payment fits (debt-to-income at most MAX_DTI), else the reason."""
    income = Decimal(str(income or 0))
    if income <= 0:
        return "You need a monthly income to borrow."
    dti = (Decimal(str(current_payments)) + Decimal(str(extra_monthly))) / income
    if dti > MAX_DTI:
        return (f"Your loan payments would be {dti * 100:.0f}% of your income "
                f"(lenders allow {MAX_DTI * 100:.0f}%). Borrow less or for longer.")
    return None


def affordability(uid, extra_monthly):
    """None if the new payment fits (debt-to-income at most MAX_DTI), else the reason."""
    income, payments = finances(uid)
    return dti_problem(income, payments, extra_monthly)


def annuity_payment(principal, annual_pct, payments, payments_per_year=PAYDAYS_PER_YEAR) -> Decimal:
    """The fixed payment that repays `principal` in `payments` paydays (rounded up to the cent)."""
    principal = Decimal(str(principal))
    rate = Decimal(str(annual_pct)) / 100 / payments_per_year
    if rate <= 0:
        return (principal / payments).quantize(CENT, rounding=ROUND_UP)
    pay = principal * rate / (1 - (1 + rate) ** -payments)
    return pay.quantize(CENT, rounding=ROUND_UP)
