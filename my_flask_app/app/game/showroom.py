"""
The Showroom: the swipeable feed of homes, businesses and luxury items (the app builds the deck).
The server keeps what has to persist or be trusted:

* Wishlist: items a player saved. When one becomes affordable at the end of a game week, the
  player gets one push ("You can afford the Lakehouse now"), once, until it slips out of reach.
* Seen: the game week a player first scrolled past each item, so the feed can say what it would
  have done since ("+$8,400 if you'd bought it in week 12", or "you dodged $41k of costs").
* Deals: a few discounts per two game weeks, bigger in seasonal sales. Only homes and luxury items:
  a discount is paid back after purchase and the item's value drops to what you really paid, so a
  deal can't be cashed out by reselling (businesses sell at the market price, so they never go on sale).
* Friends: recent purchases by people you follow.

Item keys match the app: kind is 'home', 'business' or 'item' (luxury), plus the catalog id.
"""
import logging
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app import supabase
from app.game import economy
from app.services.balance_service import BalanceService
from app.utils.perf import cached, parallel

logger = logging.getLogger(__name__)

KINDS = ('home', 'business', 'item')
DEAL_KINDS = ('home', 'item')
DEAL_WINDOW = 2                   # game weeks a deal lasts
PASSED_AFTER_WEEKS = 4            # a game month before "since you passed on it" means anything
FRIEND_DAYS = 14                  # how far back friends' purchases go (real days)
MAX_WISHLIST = 100

# Seasonal sales (real calendar, UTC): more deals and bigger discounts.
SEASONS = [
    ((11, 20), (12, 2), 'Black Friday', '🛍️'),
    ((12, 15), (12, 31), 'Holiday sale', '🎄'),
    ((1, 1), (1, 10), 'New Year sale', '🎆'),
    ((6, 20), (7, 10), 'Mid-year sale', '☀️'),
]
# (deals per window, discount range) for homes and for luxury items
NORMAL = {'count': 3, 'home': (0.04, 0.08), 'item': (0.10, 0.20)}
SEASONAL = {'count': 5, 'home': (0.08, 0.12), 'item': (0.15, 0.30)}


class ShowroomError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def season(today=None):
    d = today or datetime.now(timezone.utc).date()
    for (m1, d1), (m2, d2), label, emoji in SEASONS:
        if (m1, d1) <= (d.month, d.day) <= (m2, d2):
            return {'label': label, 'emoji': emoji}
    return None


# --- Catalog ---------------------------------------------------------------------------------

def _catalog():
    """{(kind, id): {'name', 'price', 'row'}} for everything in the Showroom (cached for a few minutes)."""
    def load():
        homes, businesses, items = parallel(
            lambda: supabase.table('home_listings').select('*').execute().data or [],
            lambda: supabase.table('assets').select('*').eq('category', 'business').execute().data or [],
            lambda: supabase.table('liability_items').select('*').execute().data or [],
        )
        out = {}
        for h in homes:
            out[('home', str(h['id']))] = {'name': h['name'], 'price': Decimal(str(h['price'])), 'row': h}
        for a in businesses:
            out[('business', str(a['id']))] = {'name': a['name'], 'price': Decimal(str(a['price'])), 'row': a}
        for i in items:
            out[('item', str(i['id']))] = {'name': i['name'], 'price': Decimal(str(i['base_price'])), 'row': i}
        return out
    return cached('showroom_catalog', load, client=supabase)


def _clock(uid):
    res = supabase.table('player_game_clock').select('week').eq('user_id', uid).limit(1).execute().data
    return int(res[0]['week']) if res else 1


def _life_number(uid):
    res = supabase.table('player_lives').select('life_number').eq('user_id', uid).eq('is_current', True).limit(1).execute().data
    return int(res[0]['life_number']) if res else 1


def _cash_needed(kind, entry):
    """Cash to buy it now: a home only needs the 20% down payment."""
    return entry['price'] * Decimal('0.2') if kind == 'home' else entry['price']


# --- Wishlist ----------------------------------------------------------------------------------

def wishlist(uid, catalog=None, balance=None):
    catalog = catalog if catalog is not None else _catalog()
    balance = balance if balance is not None else BalanceService.get_current_balance(uid)
    rows = supabase.table('showroom_wishlist').select('*').eq('user_id', uid).order('added_at', desc=True).execute().data or []
    out = []
    for r in rows:
        entry = catalog.get((r['kind'], str(r['item_id'])))
        if not entry:
            continue  # removed from the catalog
        need = _cash_needed(r['kind'], entry)
        out.append({'kind': r['kind'], 'item_id': str(r['item_id']), 'name': entry['name'], 'price': float(entry['price']),
                    'cash_needed': float(need), 'affordable': balance >= need,
                    'progress_pct': float(min(100, round(balance / need * 100, 1))) if need > 0 else 100.0,
                    'added_at': r.get('added_at')})
    return out


def _check_kind(kind):
    if kind not in KINDS:
        raise ShowroomError('VALIDATION_ERROR', f'kind must be one of {", ".join(KINDS)}.')


def wishlist_add(uid, kind, item_id):
    _check_kind(kind)
    catalog = _catalog()
    if (kind, str(item_id)) not in catalog:
        raise ShowroomError('NOT_FOUND', 'That item is no longer in the showroom.', 404)
    existing = supabase.table('showroom_wishlist').select('id').eq('user_id', uid).execute().data or []
    if len(existing) >= MAX_WISHLIST:
        raise ShowroomError('WISHLIST_FULL', f'Your wishlist holds {MAX_WISHLIST} things. Remove one first.', 409)
    already = supabase.table('showroom_wishlist').select('id').eq('user_id', uid).eq('kind', kind).eq('item_id', str(item_id)).limit(1).execute().data
    if not already:
        supabase.table('showroom_wishlist').insert({'user_id': uid, 'kind': kind, 'item_id': str(item_id)}).execute()
    return wishlist(uid, catalog)


def wishlist_remove(uid, kind, item_id):
    _check_kind(kind)
    supabase.table('showroom_wishlist').delete().eq('user_id', uid).eq('kind', kind).eq('item_id', str(item_id)).execute()
    return wishlist(uid)


def after_week(uid):
    """End of a game week: push once for wishlist items that just became affordable.
    An item that slips out of reach again can notify again later."""
    rows = supabase.table('showroom_wishlist').select('*').eq('user_id', uid).execute().data or []
    if not rows:
        return []
    catalog = _catalog()
    balance = BalanceService.get_current_balance(uid)
    newly = []
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        entry = catalog.get((r['kind'], str(r['item_id'])))
        if not entry:
            continue
        can = balance >= _cash_needed(r['kind'], entry)
        if can and not r.get('notified_at'):
            supabase.table('showroom_wishlist').update({'notified_at': now}).eq('id', r['id']).execute()
            newly.append({'kind': r['kind'], 'item_id': str(r['item_id']), 'name': entry['name'], 'home': r['kind'] == 'home'})
        elif not can and r.get('notified_at'):
            supabase.table('showroom_wishlist').update({'notified_at': None}).eq('id', r['id']).execute()
    if newly:
        first = newly[0]
        what = f"the {first['name']}" + (f" and {len(newly) - 1} more" if len(newly) > 1 else '')
        body = (f"You've saved the deposit for {what}. It's waiting in your showroom." if first['home'] and len(newly) == 1
                else f"You can afford {what} from your wishlist now. Still want it?")
        try:
            from app.services.push_notification_service import ExpoPushService
            ExpoPushService.send_notification_to_user(supabase, uid, '🎉 Wishlist unlocked', body,
                                                      notification_type='showroom_affordable', data={'type': 'showroom_affordable', 'screen': '/'})
        except Exception as e:
            logger.warning(f'Wishlist push failed for {uid}: {e}')
    return newly


# --- Seen and "since you passed on it" ------------------------------------------------------------

def mark_seen(uid, items):
    """Remember the game week each item was first scrolled past (in this life)."""
    keys = {(i.get('kind'), str(i.get('item_id'))) for i in (items or []) if i.get('kind') in KINDS and i.get('item_id')}
    if not keys:
        return 0
    life, week = _life_number(uid), _clock(uid)
    have = {(r['kind'], str(r['item_id'])) for r in
            supabase.table('showroom_seen').select('kind, item_id').eq('user_id', uid).eq('life_number', life).execute().data or []}
    catalog = _catalog()
    new = [{'user_id': uid, 'life_number': life, 'kind': k, 'item_id': i, 'first_seen_week': week, 'price': float(catalog[(k, i)]['price'])}
           for k, i in sorted(keys - have) if (k, i) in catalog]
    if new:
        try:
            supabase.table('showroom_seen').insert(new).execute()
        except Exception as e:  # a second phone racing this one: the first write wins
            logger.info(f'Seen insert skipped for {uid}: {e}')
    return len(new)


def _owned_keys(uid):
    owned = set()
    for h in supabase.table('player_homes').select('home_id').eq('player_id', uid).eq('is_active', True).execute().data or []:
        owned.add(('home', str(h['home_id'])))
    for a in supabase.table('user_assets').select('asset_id').eq('user_id', uid).execute().data or []:
        if a.get('asset_id'):
            owned.add(('business', str(a['asset_id'])))
    for li in supabase.table('player_liabilities').select('liability_id').eq('player_id', uid).eq('is_active', True).execute().data or []:
        owned.add(('item', str(li['liability_id'])))
    return owned


def _home_growth(price, months):
    """What a home bought `months` game months ago would be worth now (homes.py appreciation)."""
    first = min(months, 12)
    later = max(months - 12, 0)
    return price * (1 + economy.APPRECIATION_YEAR_1) ** first * (1 + economy.APPRECIATION_LATER) ** later


def what_if(kind, entry, months):
    """If you had bought it `months` game months ago: {'mode', 'amount', 'pct', 'detail'}."""
    price = entry['price']
    row = entry['row']
    if kind == 'home':
        worth = _home_growth(price, months)
        upkeep = sum((Decimal(str(u.get('monthly') or 0)) for u in (row.get('upkeep') or [])), Decimal('0')) * months
        gain = worth - price
        return {'mode': 'grew', 'amount': float(economy.money(gain)), 'pct': float(round(gain / price * 100, 1)),
                'detail': f'Upkeep over that time would have been about ${float(upkeep):,.0f}.'}
    if kind == 'business':
        earned = Decimal(str(row.get('monthly_income') or 0)) * months
        return {'mode': 'earned', 'amount': float(economy.money(earned)), 'pct': float(round(earned / price * 100, 1)) if price else 0,
                'detail': 'An average month. Real months swing up and down.'}
    econ = economy.item_economics(row)
    lost = price * Decimal(str(1 - (1 - econ['depreciation_rate']) ** (months / 12)))
    running = Decimal(str(econ['monthly_running'])) * months
    total = lost + running
    return {'mode': 'cost', 'amount': float(economy.money(total)), 'pct': float(round(total / price * 100, 1)),
            'detail': f'${float(lost):,.0f} of lost value plus ${float(running):,.0f} of running costs.'}


def passed(uid, catalog, owned, limit=3):
    """The items you scrolled past longest ago, with what they would have done since."""
    life, week = _life_number(uid), _clock(uid)
    rows = supabase.table('showroom_seen').select('*').eq('user_id', uid).eq('life_number', life).execute().data or []
    out = []
    for r in sorted(rows, key=lambda r: int(r['first_seen_week'])):
        key = (r['kind'], str(r['item_id']))
        weeks = week - int(r['first_seen_week'])
        if key in owned or key not in catalog or weeks < PASSED_AFTER_WEEKS:
            continue
        months = weeks // 4
        out.append({'kind': r['kind'], 'item_id': str(r['item_id']), 'name': catalog[key]['name'], 'price': float(catalog[key]['price']),
                    'first_seen_week': int(r['first_seen_week']), 'weeks_ago': weeks, **what_if(r['kind'], catalog[key], months)})
    # A mix: the biggest win and the biggest dodge first.
    out.sort(key=lambda p: -abs(p['pct']))
    return out[:limit]


# --- Deals -------------------------------------------------------------------------------------------

def _window(week):
    start = week - ((week - 1) % DEAL_WINDOW)
    return start, start + DEAL_WINDOW - 1


def deals(uid, catalog=None, balance=None, income=None, today=None):
    """This window's deals, made on first visit and then fixed until the window ends."""
    catalog = catalog if catalog is not None else _catalog()
    life, week = _life_number(uid), _clock(uid)
    start, end = _window(week)
    rows = supabase.table('showroom_deals').select('*').eq('user_id', uid).eq('life_number', life).eq('window_start_week', start).execute().data or []
    if not rows:
        rows = _make_deals(uid, life, start, end, catalog, balance, income, today)
    out = []
    for r in rows:
        entry = catalog.get((r['kind'], str(r['item_id'])))
        if not entry:
            continue
        pct = Decimal(str(r['discount_pct']))
        out.append({'kind': r['kind'], 'item_id': str(r['item_id']), 'name': entry['name'], 'price': float(entry['price']),
                    'discount_pct': float(pct * 100), 'saving': float(economy.money(entry['price'] * pct)),
                    'deal_price': float(economy.money(entry['price'] * (1 - pct))),
                    'ends_week': int(r['ends_week']), 'weeks_left': max(int(r['ends_week']) - week + 1, 0),
                    'label': r.get('label'), 'emoji': r.get('emoji'), 'redeemed': bool(r.get('redeemed_at'))})
    return out


def _make_deals(uid, life, start, end, catalog, balance, income, today):
    s = season(today)
    rules = SEASONAL if s else NORMAL
    balance = Decimal(str(balance if balance is not None else BalanceService.get_current_balance(uid)))
    if income is None:
        prof = supabase.table('profiles').select('monthly_income').eq('user_id', uid).limit(1).execute().data
        income = (prof[0] if prof else {}).get('monthly_income') or 0
    reach = balance + Decimal(str(income)) * Decimal('3.6')   # cash plus ~30% of a year's pay
    # Never the same item twice in a life.
    used = {(r['kind'], str(r['item_id'])) for r in
            supabase.table('showroom_deals').select('kind, item_id').eq('user_id', uid).eq('life_number', life).execute().data or []}
    pool = [(k, i) for (k, i), e in catalog.items() if k in DEAL_KINDS and (k, i) not in used]
    # Deals that matter: within about 4x of what you could reach, nearest first; then anything.
    near = sorted([key for key in pool if _cash_needed(key[0], catalog[key]) <= max(reach, Decimal('500')) * 4],
                  key=lambda key: catalog[key]['price'])
    rng = random.Random(f'{uid}:{life}:{start}')
    picks = rng.sample(near, min(len(near), rules['count']))
    if len(picks) < rules['count']:
        rest = [key for key in pool if key not in picks]
        picks += rng.sample(rest, min(len(rest), rules['count'] - len(picks)))
    rows = []
    for kind, item_id in picks:
        lo, hi = rules[kind]
        pct = round(rng.uniform(lo, hi), 2)
        rows.append({'user_id': uid, 'life_number': life, 'window_start_week': start, 'ends_week': end, 'kind': kind,
                     'item_id': item_id, 'discount_pct': pct,
                     'label': s['label'] if s else 'Deal', 'emoji': s['emoji'] if s else '🔥'})
    if rows:
        try:
            supabase.table('showroom_deals').insert(rows).execute()
        except Exception as e:  # another request made them first: use those
            logger.info(f'Deals insert raced for {uid}: {e}')
            return supabase.table('showroom_deals').select('*').eq('user_id', uid).eq('life_number', life).eq('window_start_week', start).execute().data or []
    return rows


def _bought_since(uid, kind, item_id, since_iso):
    """The newest active purchase of this item made since the deal appeared: (table, row) or None."""
    if kind == 'home':
        table, rows = 'player_homes', supabase.table('player_homes').select('*').eq('player_id', uid).eq('home_id', item_id).eq('is_active', True).execute().data or []
        when = 'purchased_at'
    else:
        table, rows = 'player_liabilities', supabase.table('player_liabilities').select('*').eq('player_id', uid).eq('liability_id', item_id).eq('is_active', True).execute().data or []
        when = 'purchase_date'
    fresh = [r for r in rows if str(r.get(when) or '') >= str(since_iso or '')]
    fresh.sort(key=lambda r: str(r.get(when) or ''), reverse=True)
    return (table, fresh[0]) if fresh else None


def redeem(uid, kind, item_id):
    """After buying a deal item: pay the discount back and lower the item's value to what was paid."""
    if kind not in DEAL_KINDS:
        raise ShowroomError('NO_DEAL', 'There is no deal on that.', 404)
    life, week = _life_number(uid), _clock(uid)
    start, _ = _window(week)
    deal = next((r for r in supabase.table('showroom_deals').select('*').eq('user_id', uid).eq('life_number', life)
                 .eq('window_start_week', start).eq('kind', kind).eq('item_id', str(item_id)).execute().data or []), None)
    if not deal or int(deal['ends_week']) < week:
        raise ShowroomError('NO_DEAL', 'That deal has ended.', 404)
    if deal.get('redeemed_at'):
        raise ShowroomError('ALREADY_REDEEMED', 'You already used this deal.', 409)
    found = _bought_since(uid, kind, str(item_id), deal.get('created_at'))
    if not found:
        raise ShowroomError('NOT_BOUGHT', 'Buy it first, then the deal is paid back.', 409)
    table, owned = found
    paid = Decimal(str(owned.get('purchase_price') or 0))
    saving = economy.money(paid * Decimal(str(deal['discount_pct'])))
    if saving <= 0:
        raise ShowroomError('NO_DEAL', 'Nothing to pay back on that.', 409)
    # Claim the deal first, so two taps can't pay it twice.
    claimed = supabase.table('showroom_deals').update({'redeemed_at': datetime.now(timezone.utc).isoformat(), 'saving': float(saving)}) \
        .eq('id', deal['id']).is_('redeemed_at', 'null').execute().data
    if not claimed:
        raise ShowroomError('ALREADY_REDEEMED', 'You already used this deal.', 409)
    value = Decimal(str(owned.get('current_value') if owned.get('current_value') is not None else paid))
    supabase.table(table).update({'purchase_price': float(paid - saving), 'current_value': float(max(value - saving, Decimal('0')))}) \
        .eq('id', owned['id']).execute()
    name = (_catalog().get((kind, str(item_id))) or {}).get('name', 'your purchase')
    BalanceService.add_balance(uid, saving, f'Showroom deal: {name}', category='showroom_deal')
    return {'saving': float(saving), 'name': name, 'balance': float(BalanceService.get_current_balance(uid))}


# --- Friends ------------------------------------------------------------------------------------------

def friends(uid, catalog, limit=6, now=None):
    """Recent purchases by people you follow."""
    following = [str(f['following_id']) for f in
                 supabase.table('user_follows').select('following_id').eq('follower_id', uid).limit(500).execute().data or []]
    if not following:
        return []
    since = ((now or datetime.now(timezone.utc)) - timedelta(days=FRIEND_DAYS)).isoformat()
    buys = []
    for h in supabase.table('player_homes').select('player_id, home_id, purchased_at').in_('player_id', following).gte('purchased_at', since).execute().data or []:
        buys.append((str(h['player_id']), 'home', str(h['home_id']), h['purchased_at']))
    for a in supabase.table('user_assets').select('user_id, asset_id, created_at').in_('user_id', following).gte('created_at', since).execute().data or []:
        if a.get('asset_id'):
            buys.append((str(a['user_id']), 'business', str(a['asset_id']), a['created_at']))
    for li in supabase.table('player_liabilities').select('player_id, liability_id, purchase_date').in_('player_id', following).gte('purchase_date', since).execute().data or []:
        buys.append((str(li['player_id']), 'item', str(li['liability_id']), li['purchase_date']))
    buys = [b for b in buys if (b[1], b[2]) in catalog]
    buys.sort(key=lambda b: str(b[3]), reverse=True)
    # One card per friend: their latest buy.
    seen, picked = set(), []
    for b in buys:
        if b[0] not in seen:
            seen.add(b[0]); picked.append(b)
        if len(picked) >= limit:
            break
    if not picked:
        return []
    profiles = {str(p['user_id']): p for p in
                supabase.table('profiles').select('user_id, username, profile_picture_url').in_('user_id', [b[0] for b in picked]).execute().data or []}
    return [{'user_id': b[0], 'username': (profiles.get(b[0]) or {}).get('username') or 'A friend',
             'avatar_url': (profiles.get(b[0]) or {}).get('profile_picture_url'),
             'kind': b[1], 'item_id': b[2], 'name': catalog[(b[1], b[2])]['name'], 'bought_at': b[3]} for b in picked]


# --- Everything the feed needs -------------------------------------------------------------------------

def state(uid):
    catalog, balance, prof, owned, week = parallel(
        _catalog,
        lambda: BalanceService.get_current_balance(uid),
        lambda: supabase.table('profiles').select('monthly_income, net_worth').eq('user_id', uid).limit(1).execute().data,
        lambda: _owned_keys(uid),
        lambda: _clock(uid),
    )
    prof = prof[0] if prof else {}
    wish, deal, gone, pals = parallel(
        lambda: wishlist(uid, catalog, balance),
        lambda: deals(uid, catalog, balance, prof.get('monthly_income') or 0),
        lambda: passed(uid, catalog, owned),
        lambda: friends(uid, catalog),
    )
    return {
        'week': week,
        'balance': float(balance),
        'net_worth': float(prof.get('net_worth') or 0),
        'season': season(),
        'wishlist': wish,
        'deals': deal,
        'passed': gone,
        'friends': pals,
    }


def clear_for_new_life(uid):
    """A new life restarts the clock at week 1: what you saw and the deals you had belong to the old one.
    The wishlist stays: it's what you want, not what you had."""
    supabase.table('showroom_seen').delete().eq('user_id', uid).execute()
    supabase.table('showroom_deals').delete().eq('user_id', uid).execute()
