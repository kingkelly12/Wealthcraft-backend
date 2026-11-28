"""
Land: buy a plot, pay its rates, and maybe one day someone wants it.

A plot earns nothing on its own. Its fate (whether a company ever comes, and
when) is rolled once, when you buy it, and stays on the server: the app never
sees it, and each plot can be bought once per life, so it can't be re-rolled.

An offer arrives on a payday and stands for OFFER_STANDS paydays: sell, lease,
negotiate once, or decline. Ignoring it never sells anything; it just lapses.
Some owners also get a fake developer asking for a fee up front.

The odds and payouts live here (not in the database) so players can't read them.
scripts/sim/land.py simulates them; rerun it after changing a number.

Table: player_land. Money moves through BalanceService.
"""
import logging
import random
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase
from app.game import economy
from app.services.balance_service import BalanceService

logger = logging.getLogger(__name__)

# key: price, rates a month, chance a company ever comes, what the lease pays a year
PLOTS = {
    'river_flats': {
        'name': 'River Flats', 'emoji': '🌾', 'location': 'The Valley', 'price': 30000, 'upkeep': 60,
        'clue': 'Floods a little. Everything grows.',
        'chance': 0.30, 'annual': 15000, 'company': 'Greenfield Agri Co.', 'use': 'a commercial farm',
    },
    'highway_corner': {
        'name': 'Highway Corner', 'emoji': '🛣️', 'location': 'Edge of town', 'price': 55000, 'upkeep': 110,
        'clue': 'A new interchange is rumoured.',
        'chance': 0.20, 'annual': 55000, 'company': 'Crossroads Developments', 'use': 'shops and housing',
    },
    'powerline_fields': {
        'name': 'Powerline Fields', 'emoji': '⚡', 'location': 'Out by the substation', 'price': 75000, 'upkeep': 150,
        'clue': 'Ugly pylons. Very cheap power.',
        'chance': 0.10, 'annual': 150000, 'company': 'Nimbus Grid', 'use': 'a data center',
    },
    'red_ridge': {
        'name': 'Red Ridge', 'emoji': '⛰️', 'location': 'The back country', 'price': 120000, 'upkeep': 240,
        'clue': 'Nothing grows. Odd-coloured rocks.',
        'chance': 0.05, 'annual': 480000, 'company': 'Aurum Ridge Mining',
        'use': 'a gold mine. The state owns the gold, so this is what they pay you for your land',
    },
}

OFFER_MONTHS = (3, 12)          # game months of ownership in which an offer can arrive
OFFER_STANDS = 2                # paydays an offer waits before it lapses
LEASE_YEARS = 3
PAYDAYS = economy.PAYDAYS_PER_YEAR
PULL_OUT_CHANCE = 0.15          # after each full year of a lease
SELL_YEARS = Decimal('2.5')     # a buyout is the land price plus this many years of lease
NEGOTIATE_FEE = Decimal('0.05')  # of a year's lease, to your own lawyer
NEGOTIATE_WINS = 0.85
NEGOTIATE_BOOST = Decimal('1.30')
COME_BACK_CHANCE = 0.25         # a declined offer returns once...
COME_BACK_AFTER = 3             # ...this many paydays later...
COME_BACK_BOOST = Decimal('1.20')  # ...and better
SELLING_FEES = Decimal('0.05')  # selling with no offer on the table

SCAM_CHANCE = 0.20              # of landowners, rolled with their first plot
SCAM_MONTHS = (1, 10)
SCAM = {'company': 'Apex Global Holdings', 'amount': 900000, 'fee': 2500}
LAWYER_CHECK = 300


class LandError(Exception):
    def __init__(self, code, message, status=400, data=None):
        super().__init__(message)
        self.code, self.message, self.status, self.data = code, message, status, data


def _now():
    return datetime.now(timezone.utc).isoformat()


# --- rules (pure: the simulation uses these too) -----------------------------------------

def draw_fate(plot, first_plot, rng) -> dict:
    return {
        'offer_month': rng.randint(*OFFER_MONTHS) if rng.random() < plot['chance'] else None,
        'scam_month': rng.randint(*SCAM_MONTHS) if first_plot and rng.random() < SCAM_CHANCE else None,
    }


def terms(plot, annual, month, negotiated=False, returned=False) -> dict:
    annual = economy.money(annual)
    return {
        'type': 'real', 'annual': float(annual), 'sell': float(economy.money(Decimal(plot['price']) + annual * SELL_YEARS)),
        'expires_month': month + OFFER_STANDS, 'negotiated': negotiated, 'returned': returned,
    }


def new_lease(annual) -> dict:
    return {'annual': float(economy.money(annual)), 'paydays_left': LEASE_YEARS * PAYDAYS, 'paid': 0}


def lease_payday(lease, rng):
    """(payment, the lease afterwards or None, 'ran out' | 'pulled out' | None)."""
    pay = economy.money(Decimal(str(lease['annual'])) / PAYDAYS)
    after = {**lease, 'paydays_left': lease['paydays_left'] - 1, 'paid': lease['paid'] + 1}
    if after['paydays_left'] <= 0:
        return pay, None, 'ran out'
    if after['paid'] % PAYDAYS == 0 and rng.random() < PULL_OUT_CHANCE:
        return pay, None, 'pulled out'
    return pay, after, None


def next_offer(row, month, rng=random):
    """The offer (or scam) arriving on this payday, or None. `row` already has no open offer."""
    if row.get('status') != 'owned':
        return None
    plot, fate = PLOTS[row['plot_key']], row.get('fate') or {}
    if fate.get('offer_month') == month:
        return terms(plot, plot['annual'], month)
    if fate.get('return_month') == month:
        return terms(plot, fate['return_annual'], month, returned=True)
    scam = fate.get('scam_month')
    if scam and not fate.get('scam_sent') and month >= scam:
        return {'type': 'scam', 'expires_month': month + OFFER_STANDS}
    return None


# --- reads -------------------------------------------------------------------------------

def owned(uid) -> list:
    return supabase.table('player_land').select('*').eq('player_id', str(uid)).eq('is_active', True).execute().data or []


def total_value(uid) -> Decimal:
    return sum((economy.money(r.get('current_value')) for r in owned(uid)), Decimal('0'))


def _offer_view(row):
    """What the player sees. A scam reads like a real offer until you look at what it asks for."""
    offer = row.get('offer')
    if not offer:
        return None
    plot = PLOTS[row['plot_key']]
    left = max(offer['expires_month'] - int(row.get('months_held') or 0), 0)
    if offer['type'] == 'scam':
        return {
            'headline': f"URGENT: We want your land at {plot['name']}!",
            'body': f"{SCAM['company']} offers ${SCAM['amount']:,.0f}. Just send the ${SCAM['fee']:,.0f} processing fee by Friday.",
            'paydays_left': left,
            'actions': [
                {'id': 'pay', 'label': f"Send the ${SCAM['fee']:,.0f} fee"},
                {'id': 'check', 'label': f"Have a lawyer check it · ${LAWYER_CHECK}"},
                {'id': 'ignore', 'label': 'Ignore it'},
            ],
        }
    annual, sell = Decimal(str(offer['annual'])), Decimal(str(offer['sell']))
    fee = economy.money(annual * NEGOTIATE_FEE)
    actions = [
        {'id': 'lease', 'label': f"Lease it · ${annual:,.0f} a year"},
        {'id': 'sell', 'label': f"Sell it · ${sell:,.0f} now"},
    ]
    if not offer.get('negotiated'):
        actions.append({'id': 'negotiate', 'label': f"Negotiate · ${fee:,.0f} to your lawyer"})
    actions.append({'id': 'decline', 'label': 'Decline'})
    intro = 'They are back, with more.' if offer.get('returned') else 'This could change everything.'
    return {
        'headline': f"{plot['company']} wants {plot['name']}",
        'body': f"{intro} They want it for {plot['use']}. Lease it for {LEASE_YEARS} years and keep the land, or sell it outright.",
        'paydays_left': left,
        'actions': actions,
    }


def _view(row):
    plot = PLOTS[row['plot_key']]
    value = economy.money(row.get('current_value'))
    lease = row.get('lease')
    return {
        'id': row['id'], 'plot_key': row['plot_key'], 'name': plot['name'], 'emoji': plot['emoji'],
        'location': plot['location'], 'clue': plot['clue'], 'upkeep_monthly': float(plot['upkeep']),
        'purchase_price': float(row.get('purchase_price') or 0), 'value': float(value),
        'sale_price': float(economy.money(value * (1 - SELLING_FEES))),
        'status': row.get('status'), 'months_held': int(row.get('months_held') or 0),
        'lease': ({'annual': lease['annual'], 'per_payday': float(economy.money(Decimal(str(lease['annual'])) / PAYDAYS)),
                   'paydays_left': lease['paydays_left']} if lease else None),
        'offer': _offer_view(row),
    }


def overview(uid) -> dict:
    rows = supabase.table('player_land').select('*').eq('player_id', str(uid)).execute().data or []
    had = {r['plot_key'] for r in rows}
    return {
        'plots': [{'key': k, 'name': p['name'], 'emoji': p['emoji'], 'location': p['location'], 'clue': p['clue'],
                   'price': float(p['price']), 'upkeep_monthly': float(p['upkeep']), 'taken': k in had}
                  for k, p in PLOTS.items()],
        'mine': [_view(r) for r in rows if r.get('is_active') and r['plot_key'] in PLOTS],
        'balance': float(BalanceService.get_current_balance(uid)),
    }


# --- actions -----------------------------------------------------------------------------

def buy(uid, plot_key, rng=None) -> dict:
    uid = str(uid)
    rng = rng or random.SystemRandom()
    plot = PLOTS.get(plot_key)
    if not plot:
        raise LandError('PLOT_NOT_FOUND', 'That plot is not for sale.', 404)
    rows = supabase.table('player_land').select('plot_key').eq('player_id', uid).execute().data or []
    if any(r['plot_key'] == plot_key for r in rows):
        raise LandError('ALREADY_BOUGHT', f"You can only buy {plot['name']} once.", 409)
    price = economy.money(plot['price'])
    _pay(uid, price, f"Bought land: {plot['name']}", 'land_purchase')
    try:
        row = supabase.table('player_land').insert({
            'player_id': uid, 'plot_key': plot_key, 'purchase_price': float(price), 'current_value': float(price),
            'months_held': 0, 'status': 'owned', 'fate': draw_fate(plot, not rows, rng), 'offer': None, 'lease': None,
            'version': 0, 'is_active': True,
        }).execute().data[0]
    except Exception:
        BalanceService.add_balance(user_id=uid, amount=price, reason=f"Refund: {plot['name']}", category='refund')
        raise
    _recalc(uid)
    return _view(row)


def _pay(uid, amount, reason, category):
    have = BalanceService.get_current_balance(uid)
    short = LandError('INSUFFICIENT_FUNDS', f"You're ${max(amount - have, Decimal('0')):,.0f} short.", 400,
                      data={'needed': float(amount), 'balance': float(have), 'short': float(max(amount - have, Decimal('0')))})
    if have < amount:
        raise short
    try:
        BalanceService.subtract_balance(user_id=uid, amount=amount, reason=reason, category=category)
    except Exception as e:
        if 'Insufficient funds' in str(e):
            raise short
        raise


def _mine_or_404(uid, land_id):
    rows = supabase.table('player_land').select('*').eq('id', str(land_id)).eq('player_id', str(uid)) \
        .eq('is_active', True).limit(1).execute().data
    if not rows:
        raise LandError('NOT_YOUR_LAND', "You don't own that plot.", 404)
    return rows[0]


def _claim(row, **changes):
    """Write only if nothing else changed the plot since it was read, so nothing pays out twice."""
    version = int(row.get('version') or 0)
    res = supabase.table('player_land').update({**changes, 'version': version + 1}) \
        .eq('id', row['id']).eq('version', version).eq('is_active', True).execute()
    if not res.data:
        raise LandError('CONFLICT', 'That offer was already answered.', 409)
    return res.data[0]


def sell(uid, land_id) -> dict:
    """Sell a plot on the open market, with no company involved."""
    uid = str(uid)
    row = _mine_or_404(uid, land_id)
    name = PLOTS[row['plot_key']]['name']
    if row.get('status') == 'leased':
        raise LandError('LEASED', f"{name} is leased. You can sell once the lease ends.", 400)
    proceeds = economy.money(economy.money(row.get('current_value')) * (1 - SELLING_FEES))
    _claim(row, is_active=False, status='sold', offer=None, sold_at=_now())
    BalanceService.add_balance(user_id=uid, amount=proceeds, reason=f"Sold land: {name}", category='land_sale')
    _recalc(uid)
    return {'name': name, 'proceeds': float(proceeds)}


def respond(uid, land_id, action, rng=None) -> dict:
    """Answer the open offer. Returns {'title', 'message', 'cash'}."""
    uid = str(uid)
    rng = rng or random.SystemRandom()
    row = _mine_or_404(uid, land_id)
    offer = row.get('offer')
    if not offer:
        raise LandError('NO_OFFER', 'That offer is no longer there.', 409)
    if action not in {a['id'] for a in _offer_view(row)['actions']}:
        raise LandError('BAD_ACTION', "That isn't one of the choices.", 400)
    plot = PLOTS[row['plot_key']]
    name, month = plot['name'], int(row.get('months_held') or 0)
    fate = row.get('fate') or {}

    def done(title, message, cash=Decimal('0')):
        _recalc(uid)
        return {'title': title, 'message': message, 'cash': float(cash)}

    def paid(amount, reason, **changes):
        """Claim the offer, then take the money; put the offer back if the money won't move."""
        if BalanceService.get_current_balance(uid) < amount:
            raise LandError('INSUFFICIENT_FUNDS', f"You need ${amount:,.0f} for that.", 400)
        claimed = _claim(row, **changes)
        try:
            _pay(uid, amount, reason, 'land_fee')
        except Exception:
            _claim(claimed, offer=offer)
            raise

    if offer['type'] == 'scam':
        if action == 'pay':
            fee = economy.money(SCAM['fee'])
            paid(fee, f"Processing fee to {SCAM['company']}", offer=None)
            return done('It was a scam 💸', f"{SCAM['company']} stopped replying. A real buyer never asks you to pay "
                                           f"before they pay you.", -fee)
        if action == 'check':
            fee = economy.money(LAWYER_CHECK)
            paid(fee, f"Lawyer: checking {SCAM['company']}", offer=None)
            return done('Good call 🕵️', f"Your lawyer found no company, no office and no money. ${LAWYER_CHECK} well spent.", -fee)
        _claim(row, offer=None)
        return done('Ignored', 'Nothing happens. Asking for money first was the giveaway.')

    annual = Decimal(str(offer['annual']))
    if action == 'sell':
        price = economy.money(offer['sell'])
        _claim(row, is_active=False, status='sold', offer=None, sold_at=_now())
        BalanceService.add_balance(user_id=uid, amount=price, reason=f"Sold {name} to {plot['company']}", category='land_sale')
        return done('Sold 🤝', f"${price:,.0f} is in your account.", price)
    if action == 'lease':
        lease = new_lease(annual)
        _claim(row, status='leased', offer=None, lease=lease)
        return done('Signed ✍️', f"{plot['company']} pays you ${economy.money(annual / PAYDAYS):,.0f} every payday. "
                                 f"The land stays yours.")
    if action == 'negotiate':
        fee = economy.money(annual * NEGOTIATE_FEE)
        if rng.random() < NEGOTIATE_WINS:
            better = {**terms(plot, annual * NEGOTIATE_BOOST, month, negotiated=True, returned=offer.get('returned', False)),
                      'expires_month': offer['expires_month']}
            paid(fee, f"Lawyer: negotiating for {name}", offer=better)
            return done('They agreed 💪', f"Now ${better['annual']:,.0f} a year, or ${better['sell']:,.0f} to buy it.", -fee)
        paid(fee, f"Lawyer: negotiating for {name}", offer=None)
        return done('They walked 🚪', f"{plot['company']} chose another site. The land is still yours.", -fee)
    # decline: it may come back once
    if not offer.get('returned') and rng.random() < COME_BACK_CHANCE:
        fate = {**fate, 'return_month': month + COME_BACK_AFTER,
                'return_annual': float(economy.money(annual * COME_BACK_BOOST))}
    _claim(row, offer=None, fate=fate)
    return done('Declined', 'The land is still yours.')


# --- the month ---------------------------------------------------------------------------

def run_month(uid, summ, rng=random) -> None:
    """Rates, lease payments, value growth, and offers arriving or lapsing."""
    for row in owned(uid):
        plot = PLOTS.get(row['plot_key'])
        if not plot:
            continue
        name = plot['name']
        value, month = economy.appreciate({'value': row.get('current_value'), 'purchase_price': row.get('purchase_price'),
                                           'months_held': row.get('months_held')})
        status, lease, offer, fate = row.get('status'), row.get('lease'), row.get('offer'), row.get('fate') or {}
        payment, ended, news = Decimal('0'), None, None
        if status == 'leased' and lease:
            payment, lease, ended = lease_payday(lease, rng)
            if lease is None:
                status = 'owned'
        if offer and month >= offer['expires_month']:
            offer, news = None, ('Offer lapsed', f"The offer for {name} ran out of time. Nothing was sold.")
        if not offer:
            offer = next_offer({**row, 'status': status}, month, rng)
            if offer:
                if offer['type'] == 'scam':
                    fate = {**fate, 'scam_sent': True}
                news = ('📨 Someone wants your land', f"{name}: see Investments › Land")
        try:
            _claim(row, current_value=float(value), months_held=month, status=status, lease=lease, offer=offer, fate=fate)
        except LandError:       # answered while the month ran: leave it for next payday
            logger.warning(f"Land {row['id']} changed during the month for {uid}")
            continue
        if payment > 0:
            BalanceService.add_balance(user_id=uid, amount=payment, reason=f"Land lease: {name}", category='land_lease')
            summ.credit(payment, f"Land lease: {name}")
        cost = economy.money(plot['upkeep'])
        if BalanceService.get_current_balance(uid) >= cost:
            BalanceService.subtract_balance(user_id=uid, amount=cost, reason=f"Land rates: {name}", category='land_upkeep')
            summ.debit(cost, f"Land rates: {name}")
        else:
            summ.missed(cost, f"Missed land rates: {name}", f"⚠️ Missed land rates on {name} (${cost:,.2f})")
        if ended:
            summ.note(f"Lease ended: {name}", 'The company pulled out early.' if ended == 'pulled out' else 'The full term is up. The land is yours.')
        if news:
            summ.note(*news)
            if offer:
                _alert(uid, *news)


def _alert(uid, title, body):
    try:
        from app.services.push_notification_service import ExpoPushService
        ExpoPushService.send_notification_to_user(supabase, uid, title, body, notification_type='land_offer',
                                                  data={'type': 'land_offer', 'screen': '/(tabs)/investments?category=land'})
    except Exception as e:
        logger.warning(f"Land offer alert failed for {uid}: {e}")


def clear_for_new_life(uid) -> None:
    """A new life starts with no land, and fresh luck."""
    supabase.table('player_land').delete().eq('player_id', str(uid)).execute()


def _recalc(uid):
    try:
        import uuid as _uuid
        from app.services.profile_service import ProfileService
        ProfileService.recalculate_net_worth(_uuid.UUID(str(uid)))
    except Exception:
        pass
