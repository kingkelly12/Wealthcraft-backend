"""
Owning your home.

Buy a home and move in: your lease ends, so rent stops. You pay the home's
upkeep (rates, insurance, service charge, staff...) and its bills instead.
A home you own but don't live in is let out: tenants pay its market rent,
minus an agent's cut, on months it's occupied. Homes gain value on game
months (like property in the market) and count towards net worth. Selling
costs 5% in agent and legal fees.

Mortgages: buy with 20% down and a bank lends the rest, secured on the home. The loan is a row in
`liabilities` with player_home_id set, so it is paid on payday, shows in Your loans and can be paid off early
like any loan. Selling the home settles it from the sale; miss three paydays in a row and the bank repossesses.

Tables: home_listings (the catalogue) and player_homes (what players own).
Money moves through BalanceService, so the wallet is never overdrawn.
"""
import random
from datetime import datetime, timezone
from decimal import Decimal

from app.utils.perf import parallel
from app import supabase
from app.game import economy
from app.services.balance_service import BalanceService

SELLING_FEES = Decimal('0.05')         # agent + legal fees when you sell
AGENT_CUT = Decimal('0.10')            # of the rent, when you let a home out
OCCUPANCY = (0.75, 1.0)                # share of a month a let home is occupied

DOWN_PAYMENT = Decimal('0.20')         # of the price, paid from your account
MORTGAGE_TERM = 195                    # paydays: 15 game years (13 paydays a year)
# (credit score at least, rate % a year): better credit, cheaper money. Below the last: no mortgage.
MORTGAGE_RATES = ((750, 5), (700, 7), (650, 9))
MISSES_BEFORE_REPOSSESSION = 3
REPOSSESSION_CREDIT_HIT = -100


class HomeError(Exception):
    def __init__(self, code, message, status=400, data=None):
        super().__init__(message)
        self.code, self.message, self.status, self.data = code, message, status, data


def _now():
    return datetime.now(timezone.utc).isoformat()


# --- maths -------------------------------------------------------------------------------

def upkeep(listing) -> list:
    """[(label, monthly)] for a home."""
    out = []
    for c in (listing or {}).get('upkeep') or []:
        amount = economy.money(c.get('monthly'))
        if amount > 0:
            out.append((c.get('label') or 'Upkeep', amount))
    return out


def upkeep_total(listing) -> Decimal:
    return sum((a for _, a in upkeep(listing)), Decimal('0'))


def bills(listing, years=0):
    """Electricity, water and Wi-Fi for living in this home (same rules as renting)."""
    as_rental = {'monthly_rent': listing.get('market_rent'),
                 'rental_properties': {'property_type': listing.get('bills_type') or listing.get('home_type')}}
    return economy.home_bills(as_rental, years)


def mortgage_rate(credit_score):
    """% a year for this credit score, or None if the bank won't lend."""
    score = int(credit_score or 0)
    return next((rate for floor, rate in MORTGAGE_RATES if score >= floor), None)


def mortgage_quote(listing, credit_score, income, current_payments) -> dict:
    """What financing this home means for this player, and whether a bank would say yes."""
    price = economy.money(listing.get('price'))
    down = economy.money(price * DOWN_PAYMENT)
    loan = price - down
    rate = mortgage_rate(credit_score)
    quote = {'down_payment': float(down), 'loan_amount': float(loan), 'rate': rate, 'term': MORTGAGE_TERM,
             'term_years': round(MORTGAGE_TERM / economy.PAYDAYS_PER_YEAR, 1), 'monthly_payment': None,
             'total_interest': None, 'total_repayment': None, 'qualifies': False, 'reason': None}
    if rate is None:
        quote['reason'] = f"Mortgages need a credit score of {MORTGAGE_RATES[-1][0]} or more (yours: {int(credit_score or 0)})."
        return quote
    payment = economy.annuity_payment(loan, rate, MORTGAGE_TERM)
    terms = economy.amortised_loan(loan, rate, payment)
    quote.update(monthly_payment=float(payment), total_interest=float(terms['interest']), total_repayment=float(terms['total']),
                 term=terms['term'])
    quote['reason'] = economy.dti_problem(income, current_payments, payment)
    quote['qualifies'] = quote['reason'] is None
    return quote


def let_income(listing, rng=random):
    """(net rent, occupied share) for a month of letting the home out."""
    rent = economy.money(listing.get('market_rent'))
    occupied = Decimal(str(round(rng.uniform(*OCCUPANCY), 2)))
    return economy.money(rent * occupied * (1 - AGENT_CUT)), occupied


def figures(listing) -> dict:
    """What owning this home means month to month, for the app."""
    rent = economy.money(listing.get('market_rent'))
    keep = upkeep_total(listing)
    home_bills = sum(bills(listing).values(), Decimal('0'))
    price = economy.money(listing.get('price'))
    saving = rent - keep
    expected_let = economy.money(rent * Decimal(str(sum(OCCUPANCY) / 2)) * (1 - AGENT_CUT))
    return {
        'upkeep_monthly': float(keep),
        'upkeep': [{'label': l, 'monthly': float(a)} for l, a in upkeep(listing)],
        'bills_monthly': float(economy.money(home_bills)),
        'rent_instead': float(rent),
        # Living in it: rent you no longer pay, minus upkeep.
        'saving_monthly': float(saving),
        # Letting it out: expected rent after the agent, minus upkeep.
        'let_net_monthly': float(expected_let - keep),
        'growth_pct': 6.0,
        'payback_years': round(float(price / (saving * 12)), 1) if saving > 0 else None,
        'selling_fees_pct': float(SELLING_FEES * 100),
    }


# --- reads -------------------------------------------------------------------------------

def _listings(ids=None):
    q = supabase.table('home_listings').select('*')
    if ids is not None:
        if not ids:
            return {}
        q = q.in_('id', list(ids))
    return {str(r['id']): r for r in q.execute().data or []}


def mortgage_on(player_home_id):
    """The mortgage secured on this home, or None."""
    rows = supabase.table('liabilities').select('*').eq('player_home_id', str(player_home_id)).gt('remaining_balance', 0).limit(1).execute().data
    return rows[0] if rows else None


def owned(uid) -> list:
    """Active homes a player owns, each with its listing under 'home' and any mortgage under 'mortgage'."""
    rows = supabase.table('player_homes').select('*').eq('player_id', str(uid)).eq('is_active', True).execute().data or []
    listings = _listings({str(r['home_id']) for r in rows})
    loans = {}
    if rows:
        for l in supabase.table('liabilities').select('*').in_('player_home_id', [str(r['id']) for r in rows]).gt('remaining_balance', 0).execute().data or []:
            loans[str(l['player_home_id'])] = l
    for r in rows:
        r['home'] = listings.get(str(r['home_id']), {})
        r['mortgage'] = loans.get(str(r['id']))
    return rows


def lived_in(uid):
    """The home the player owns and lives in, or None."""
    return next((h for h in owned(uid) if h.get('lives_in')), None)


def overview(uid) -> dict:
    uid = str(uid)
    catalog, mine, rental, prof, (income, payments), balance = parallel(
        _listings,
        lambda: owned(uid),
        lambda: supabase.table('player_rentals').select('id, monthly_rent').eq('player_id', uid).eq('is_active', True).limit(1).execute().data,
        lambda: supabase.table('profiles').select('credit_score').eq('user_id', uid).limit(1).execute().data,
        lambda: economy.finances(uid),
        lambda: BalanceService.get_current_balance(uid),
    )
    listings = sorted(catalog.values(), key=lambda l: float(l.get('price') or 0))
    credit = (prof[0] if prof else {}).get('credit_score') or 0
    return {
        'listings': [{**l, 'figures': figures(l), 'mortgage': mortgage_quote(l, credit, income, payments),
                      'owned': sum(1 for h in mine if str(h['home_id']) == str(l['id']))} for l in listings],
        'mine': [_view(h) for h in mine],
        'living': ('own' if any(h.get('lives_in') for h in mine) else 'renting' if rental else 'parents'),
        'rent_now': float(rental[0]['monthly_rent']) if rental else 0.0,
        'balance': float(balance),
    }


def _view(h):
    listing = h.get('home') or {}
    value = economy.money(h.get('current_value'))
    paid = economy.money(h.get('purchase_price'))
    loan = h.get('mortgage')
    owed = economy.payoff_amount(loan) if loan else Decimal('0')
    return {
        'mortgage': ({'balance': float(economy.money(loan['remaining_balance'])), 'payoff': float(owed),
                      'monthly_payment': float(economy.money(loan.get('monthly_payment'))), 'remaining_term': int(loan.get('remaining_term') or 0),
                      'missed_streak': int(loan.get('missed_streak') or 0), 'misses_allowed': MISSES_BEFORE_REPOSSESSION} if loan else None),
        'sale_net': float(economy.money(value * (1 - SELLING_FEES)) - owed),
        'id': h['id'], 'home_id': h['home_id'], 'name': listing.get('name'), 'home_type': listing.get('home_type'),
        'location': listing.get('location'), 'image_url': listing.get('image_url'), 'image_credit': listing.get('image_credit'),
        'value': float(value), 'purchase_price': float(paid), 'gain': float(value - paid),
        'lives_in': bool(h.get('lives_in')), 'months_held': int(h.get('months_held') or 0),
        'sale_price': float(economy.money(value * (1 - SELLING_FEES))),
        'figures': figures(listing),
    }


# --- actions -----------------------------------------------------------------------------

def buy(uid, home_id, move_in=True, finance=False) -> dict:
    uid = str(uid)
    listing = _listings([str(home_id)]).get(str(home_id))
    if not listing:
        raise HomeError('HOME_NOT_FOUND', 'That home is no longer for sale.', 404)
    price = economy.money(listing['price'])
    loan = None
    if finance:
        prof = supabase.table('profiles').select('credit_score').eq('user_id', uid).limit(1).execute().data
        income, payments = economy.finances(uid)
        quote = mortgage_quote(listing, (prof[0] if prof else {}).get('credit_score'), income, payments)
        if not quote['qualifies']:
            raise HomeError('MORTGAGE_REFUSED', quote['reason'], 400, data=quote)
        loan = quote
    due = economy.money(quote['down_payment']) if loan else price          # what leaves your account today
    have = BalanceService.get_current_balance(uid)

    def short_of_cash(have):
        short = max(due - have, Decimal('0'))
        what = 'the 20% down payment' if loan else f"the {listing['name']}"
        hint = '' if loan else ' A mortgage from the bank can cover the gap.'
        return HomeError('INSUFFICIENT_FUNDS', f"You're ${short:,.0f} short of {what}.{hint}", 400,
                         data={'needed': float(due), 'balance': float(have), 'short': float(short)})
    if have < due:
        raise short_of_cash(have)
    try:
        BalanceService.subtract_balance(user_id=uid, amount=due, reason=f"{'Down payment on' if loan else 'Bought'} a home: {listing['name']}",
                                        category='home_purchase')
    except Exception as e:
        if 'Insufficient funds' not in str(e):
            raise
        raise short_of_cash(BalanceService.get_current_balance(uid))   # spent elsewhere since the check above
    row = None
    try:
        row = supabase.table('player_homes').insert({
            'player_id': uid, 'home_id': str(listing['id']), 'purchase_price': float(price),
            'current_value': float(price), 'lives_in': False, 'months_held': 0, 'is_active': True,
        }).execute().data[0]
        if loan:
            supabase.table('liabilities').insert({
                'user_id': uid, 'name': f"Mortgage: {listing['name']}", 'liability_type': 'bank_loan',
                'amount': loan['loan_amount'], 'interest_rate': loan['rate'], 'monthly_payment': loan['monthly_payment'],
                'total_interest': loan['total_interest'], 'remaining_balance': loan['total_repayment'],
                'remaining_term': loan['term'], 'player_home_id': row['id'],
            }).execute()
    except Exception:
        if row:
            supabase.table('player_homes').delete().eq('id', row['id']).execute()
        BalanceService.add_balance(user_id=uid, amount=due, reason=f"Refund: {listing['name']}", category='refund')
        raise
    if move_in:
        move_into(uid, row['id'])
        row['lives_in'] = True
    _recalc(uid)
    row['home'] = listing
    row['mortgage'] = mortgage_on(row['id'])
    return _view(row)


def _mine_or_404(uid, player_home_id):
    rows = supabase.table('player_homes').select('*').eq('id', str(player_home_id)).eq('player_id', str(uid)) \
        .eq('is_active', True).limit(1).execute().data
    if not rows:
        raise HomeError('NOT_YOUR_HOME', "You don't own that home.", 404)
    return rows[0]


def move_into(uid, player_home_id) -> None:
    """Live in a home you own: your lease ends and any roommate arrangement with it."""
    uid = str(uid)
    _mine_or_404(uid, player_home_id)
    supabase.table('player_homes').update({'lives_in': False}).eq('player_id', uid).eq('is_active', True).eq('lives_in', True).execute()
    supabase.table('player_rentals').update({'is_active': False, 'ended_at': _now()}).eq('player_id', uid).eq('is_active', True).execute()
    from app.game import roommates
    roommates.end_all_for(uid)
    supabase.table('player_homes').update({'lives_in': True}).eq('id', str(player_home_id)).execute()


def stop_living_in_owned(uid) -> None:
    """You moved somewhere else (e.g. started renting): your own home gets let out."""
    supabase.table('player_homes').update({'lives_in': False}).eq('player_id', str(uid)).eq('is_active', True).eq('lives_in', True).execute()


def move_out(uid, player_home_id) -> None:
    _mine_or_404(uid, player_home_id)
    supabase.table('player_homes').update({'lives_in': False}).eq('id', str(player_home_id)).execute()


def sell(uid, player_home_id) -> dict:
    uid = str(uid)
    row = _mine_or_404(uid, player_home_id)
    value = economy.money(row.get('current_value'))
    sale = economy.money(value * (1 - SELLING_FEES))
    loan = mortgage_on(row['id'])
    owed = economy.payoff_amount(loan) if loan else Decimal('0')
    net = sale - owed                                    # the sale settles the mortgage first
    if net < 0 and BalanceService.get_current_balance(uid) < -net:
        raise HomeError('UNDERWATER', f"The sale brings ${sale:,.0f} but the mortgage is ${owed:,.0f}. "
                                      f"You need ${-net:,.0f} in your account to cover the difference.", 400,
                        data={'sale': float(sale), 'mortgage': float(owed), 'short': float(-net)})
    # Claim the sale first so it can't be paid twice.
    claimed = supabase.table('player_homes').update({'is_active': False, 'lives_in': False, 'sold_at': _now()}) \
        .eq('id', row['id']).eq('is_active', True).execute().data
    if not claimed:
        raise HomeError('ALREADY_SOLD', 'That home was already sold.', 409)
    name = (_listings([str(row['home_id'])]).get(str(row['home_id'])) or {}).get('name', 'your home')
    if loan:
        supabase.table('liabilities').delete().eq('id', loan['id']).execute()
    if net > 0:
        BalanceService.add_balance(user_id=uid, amount=net, reason=f"Sold {name}", category='home_sale')
    elif net < 0:
        BalanceService.subtract_balance(user_id=uid, amount=-net, reason=f"Sold {name}: covered the mortgage", category='home_sale')
    _recalc(uid)
    return {'name': name, 'proceeds': float(net), 'fees': float(value - sale), 'mortgage_paid': float(owed),
            'gain': float(sale - economy.money(row.get('purchase_price')))}


def repossess(uid, player_home_id, summ=None) -> dict:
    """
    The bank takes a home after missed mortgage payments and sells it at its value less the usual fees.
    The sale clears the loan; whatever is left over comes back to you, and a shortfall is written off.
    """
    uid = str(uid)
    rows = supabase.table('player_homes').select('*').eq('id', str(player_home_id)).eq('player_id', uid).eq('is_active', True).limit(1).execute().data
    if not rows:
        return {}
    row = rows[0]
    loan = mortgage_on(row['id'])
    claimed = supabase.table('player_homes').update({'is_active': False, 'lives_in': False, 'sold_at': _now(), 'repossessed_at': _now()}) \
        .eq('id', row['id']).eq('is_active', True).execute().data
    if not claimed:
        return {}
    value = economy.money(row.get('current_value'))
    sale = economy.money(value * (1 - SELLING_FEES))
    owed = economy.payoff_amount(loan) if loan else Decimal('0')
    surplus = max(sale - owed, Decimal('0'))
    if loan:
        supabase.table('liabilities').delete().eq('id', loan['id']).execute()
    name = (_listings([str(row['home_id'])]).get(str(row['home_id'])) or {}).get('name', 'your home')
    if surplus > 0:
        BalanceService.add_balance(user_id=uid, amount=surplus, reason=f"Repossessed {name}: what was left after the mortgage", category='home_sale')
    _recalc(uid)
    if summ is not None:
        summ.missed(Decimal('0'), f"Repossessed: {name}", f"🏚️ The bank repossessed {name}",
                    note=f"{MISSES_BEFORE_REPOSSESSION} missed mortgage payments in a row. It sold for ${sale:,.0f}"
                         f"{f', and ${surplus:,.0f} came back to you' if surplus > 0 else ' and the rest of the debt was written off'}.")
    return {'name': name, 'sale': float(sale), 'surplus': float(surplus)}


def clear_for_new_life(uid) -> None:
    supabase.table('player_homes').update({'is_active': False, 'lives_in': False}).eq('player_id', str(uid)).eq('is_active', True).execute()


def total_value(uid) -> Decimal:
    rows = supabase.table('player_homes').select('current_value').eq('player_id', str(uid)).eq('is_active', True).execute().data or []
    return sum((economy.money(r.get('current_value')) for r in rows), Decimal('0'))


def _recalc(uid):
    try:
        import uuid as _uuid
        from app.services.profile_service import ProfileService
        ProfileService.recalculate_net_worth(_uuid.UUID(str(uid)))
    except Exception:
        pass


# --- the month ---------------------------------------------------------------------------

def run_month(uid, summ, rng=random) -> None:
    """Upkeep on every home; rent from homes you let out; value growth on game months."""
    for h in owned(uid):
        listing = h.get('home') or {}
        name = listing.get('name') or 'Home'
        if not h.get('lives_in'):
            income, occupied = let_income(listing, rng)
            if income > 0:
                BalanceService.add_balance(user_id=uid, amount=income, reason=f"Tenant rent: {name}", category='rent_income')
                summ.credit(income, f"Tenant rent: {name}", note=f"{int(occupied * 100)}% occupied · agent takes {int(AGENT_CUT * 100)}%")
        costs = upkeep(listing)
        total = sum((a for _, a in costs), Decimal('0'))
        if total > 0:
            note = ' · '.join(f"{l} ${a:,.0f}" for l, a in costs)
            if BalanceService.get_current_balance(uid) >= total:
                BalanceService.subtract_balance(user_id=uid, amount=total, reason=f"Upkeep: {name}", category='home_upkeep')
                summ.debit(total, f"Upkeep: {name}", note=note)
            else:
                summ.missed(total, f"Missed upkeep: {name}", f"⚠️ Missed upkeep on {name} (${total:,.2f})", note=note)
        value, held = economy.appreciate({'value': h.get('current_value'), 'purchase_price': h.get('purchase_price'),
                                          'months_held': h.get('months_held')})
        supabase.table('player_homes').update({'current_value': float(value), 'months_held': held}).eq('id', h['id']).execute()
