"""
Owning your home.

Buy a home and move in: your lease ends, so rent stops. You pay the home's
upkeep (rates, insurance, service charge, staff...) and its bills instead.
A home you own but don't live in is let out: tenants pay its market rent,
minus an agent's cut, on months it's occupied. Homes gain value on game
months (like property in the market) and count towards net worth. Selling
costs 5% in agent and legal fees.

Tables: home_listings (the catalogue) and player_homes (what players own).
Money moves through BalanceService, so the wallet is never overdrawn.
"""
import random
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase
from app.game import economy
from app.services.balance_service import BalanceService

SELLING_FEES = Decimal('0.05')         # agent + legal fees when you sell
AGENT_CUT = Decimal('0.10')            # of the rent, when you let a home out
OCCUPANCY = (0.75, 1.0)                # share of a month a let home is occupied


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


def owned(uid) -> list:
    """Active homes a player owns, each with its listing under 'home'."""
    rows = supabase.table('player_homes').select('*').eq('player_id', str(uid)).eq('is_active', True).execute().data or []
    listings = _listings({str(r['home_id']) for r in rows})
    for r in rows:
        r['home'] = listings.get(str(r['home_id']), {})
    return rows


def lived_in(uid):
    """The home the player owns and lives in, or None."""
    return next((h for h in owned(uid) if h.get('lives_in')), None)


def overview(uid) -> dict:
    uid = str(uid)
    listings = sorted(_listings().values(), key=lambda l: float(l.get('price') or 0))
    mine = owned(uid)
    rental = supabase.table('player_rentals').select('id, monthly_rent').eq('player_id', uid).eq('is_active', True).limit(1).execute().data
    return {
        'listings': [{**l, 'figures': figures(l), 'owned': sum(1 for h in mine if str(h['home_id']) == str(l['id']))} for l in listings],
        'mine': [_view(h) for h in mine],
        'living': ('own' if any(h.get('lives_in') for h in mine) else 'renting' if rental else 'parents'),
        'rent_now': float(rental[0]['monthly_rent']) if rental else 0.0,
        'balance': float(BalanceService.get_current_balance(uid)),
    }


def _view(h):
    listing = h.get('home') or {}
    value = economy.money(h.get('current_value'))
    paid = economy.money(h.get('purchase_price'))
    return {
        'id': h['id'], 'home_id': h['home_id'], 'name': listing.get('name'), 'home_type': listing.get('home_type'),
        'location': listing.get('location'), 'image_url': listing.get('image_url'),
        'value': float(value), 'purchase_price': float(paid), 'gain': float(value - paid),
        'lives_in': bool(h.get('lives_in')), 'months_held': int(h.get('months_held') or 0),
        'sale_price': float(economy.money(value * (1 - SELLING_FEES))),
        'figures': figures(listing),
    }


# --- actions -----------------------------------------------------------------------------

def buy(uid, home_id, move_in=True) -> dict:
    uid = str(uid)
    listing = _listings([str(home_id)]).get(str(home_id))
    if not listing:
        raise HomeError('HOME_NOT_FOUND', 'That home is no longer for sale.', 404)
    price = economy.money(listing['price'])
    have = BalanceService.get_current_balance(uid)
    if have < price:
        short = price - have
        raise HomeError('INSUFFICIENT_FUNDS',
                        f"You're ${short:,.0f} short. A mortgage from the bank can cover the gap.", 400,
                        data={'needed': float(price), 'balance': float(have), 'short': float(short)})
    BalanceService.subtract_balance(user_id=uid, amount=price, reason=f"Bought a home: {listing['name']}", category='home_purchase')
    try:
        row = supabase.table('player_homes').insert({
            'player_id': uid, 'home_id': str(listing['id']), 'purchase_price': float(price),
            'current_value': float(price), 'lives_in': False, 'months_held': 0, 'is_active': True,
        }).execute().data[0]
    except Exception:
        BalanceService.add_balance(user_id=uid, amount=price, reason=f"Refund: {listing['name']}", category='refund')
        raise
    if move_in:
        move_into(uid, row['id'])
        row['lives_in'] = True
    _recalc(uid)
    row['home'] = listing
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
    # Claim the sale first so it can't be paid twice.
    claimed = supabase.table('player_homes').update({'is_active': False, 'lives_in': False, 'sold_at': _now()}) \
        .eq('id', row['id']).eq('is_active', True).execute().data
    if not claimed:
        raise HomeError('ALREADY_SOLD', 'That home was already sold.', 409)
    value = economy.money(row.get('current_value'))
    proceeds = economy.money(value * (1 - SELLING_FEES))
    name = (_listings([str(row['home_id'])]).get(str(row['home_id'])) or {}).get('name', 'your home')
    BalanceService.add_balance(user_id=uid, amount=proceeds, reason=f"Sold {name}", category='home_sale')
    _recalc(uid)
    return {'name': name, 'proceeds': float(proceeds), 'fees': float(value - proceeds),
            'gain': float(proceeds - economy.money(row.get('purchase_price')))}


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

def run_month(uid, summ, game_time=True, rng=random) -> None:
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
        if game_time:
            value, held = economy.appreciate({'value': h.get('current_value'), 'purchase_price': h.get('purchase_price'),
                                              'months_held': h.get('months_held')})
            supabase.table('player_homes').update({'current_value': float(value), 'months_held': held}).eq('id', h['id']).execute()
