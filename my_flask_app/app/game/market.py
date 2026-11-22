"""
The market on game time.

Each player (each life) has their own market that moves one step every game
week they finish, not every few real hours. So whether you play ten weeks in
an evening or one a day, a year in the game is a year in the market.

* Every asset has a yearly drift (its average growth) and a yearly volatility
  (how far it swings). A week's move is drift/52 plus a random swing scaled
  by volatility/sqrt(52). An index fund grows ~7% a year and wobbles; Bitcoin
  grows more on average but can halve; a meme stock goes nowhere, violently.
* Now and then something big happens: a stock market crash or a bull run, a
  crypto winter or boom, a meme-stock squeeze or dump, a currency shock. Riskier
  assets take a bigger hit. Markets usually recover over time: that's the drift.
* The randomness is seeded by player, life and week, so a week's market is
  fixed once played, and different in every life (no tips from friends who are
  further ahead).

Property and businesses don't trade on this market: they grow on game months
(economy.appreciate). Prices live in player_market_prices; the big moments go
to player_market_events and show up in the receipt and the Stock Exchange news.
"""
import math
import random
from datetime import datetime, timezone
from decimal import Decimal

from app import supabase

TRADED = ('stocks', 'crypto', 'forex', 'investments')
WEEKS = 52
MAX_WEEKLY_MOVE = 0.60          # no single ordinary week moves more than this
PRICE_FLOOR = Decimal('0.01')

# Yearly (drift, volatility) when an asset doesn't set its own.
DEFAULTS = {
    'stocks': (0.07, 0.18),
    'crypto': (0.10, 0.70),
    'forex': (0.00, 0.08),
    'investments': (0.05, 0.10),
}

# A shock's headline size is what the benchmark takes: an index fund for
# stocks, Bitcoin for crypto. Swingier assets are hit harder (see _beta).
SHOCK_REFERENCE = {'stocks': 0.15, 'crypto': 0.65}

# Big moments: (key, category, chance a week, low %, high %, emoji, title, body)
# Shocks scale with an asset's riskiness (see _beta).
EVENTS = [
    ('stock_crash', 'stocks', 1 / 200, -30, -15, '📉', 'Stock market crash',
     'Stocks fell hard this week. Selling now locks in the loss; markets have always recovered, eventually.'),
    ('bull_run', 'stocks', 1 / 150, 8, 15, '📈', 'Bull run',
     'Good news everywhere: stocks jumped this week. Everyone at work is suddenly an investor.'),
    ('crypto_winter', 'crypto', 1 / 70, -60, -35, '🥶', 'Crypto winter',
     'Crypto collapsed this week. The group chat has gone very quiet.'),
    ('crypto_boom', 'crypto', 1 / 70, 30, 80, '🚀', 'Crypto boom',
     'Crypto went vertical. Your cousin is talking about buying a yacht. Again.'),
    ('meme_squeeze', 'meme', 1 / 50, 80, 300, '🦍', 'Meme stock squeeze',
     'The internet decided to buy the same stock at once. It rocketed. It will not stay up there.'),
    ('meme_dump', 'meme', 1 / 50, -70, -40, '🧻', 'Meme stock dump',
     'The forum moved on to a new favourite. The meme stock fell off a cliff.'),
    ('currency_shock', 'forex', 1 / 120, -12, 12, '💱', 'Currency shock',
     'A surprise interest rate decision sent currencies flying this week.'),
]


def _num(x, default=None):
    try:
        return float(x) if x is not None else default
    except (TypeError, ValueError):
        return default


def params(asset) -> tuple:
    """(yearly drift, yearly volatility) as fractions."""
    d_drift, d_vol = DEFAULTS.get((asset.get('category') or '').lower(), (0.05, 0.15))
    drift = _num(asset.get('annual_drift'), d_drift)
    vol = _num(asset.get('annual_volatility'), d_vol)
    return drift, max(0.0, vol)


def is_meme(asset) -> bool:
    return (asset.get('category') or '').lower() == 'stocks' and (asset.get('risk_level') or '').lower() == 'very_high'


def _beta(asset) -> float:
    """How much harder than an index fund a shock hits this asset."""
    _, vol = params(asset)
    ref = SHOCK_REFERENCE.get((asset.get('category') or '').lower(), 0.15)
    return max(0.7, min(2.5, math.sqrt(vol / ref)))


def weekly_return(asset, rng) -> float:
    """An ordinary week's move (fraction), from drift and volatility."""
    drift, vol = params(asset)
    log_r = (drift - vol * vol / 2) / WEEKS + vol / math.sqrt(WEEKS) * rng.gauss(0, 1)
    return max(-MAX_WEEKLY_MOVE, min(MAX_WEEKLY_MOVE, math.exp(log_r) - 1))


def roll_events(rng) -> list:
    """The big moments this week (at most one per category)."""
    out, seen = [], set()
    for key, cat, chance, lo, hi, emoji, title, body in EVENTS:
        if cat in seen or rng.random() >= chance:
            continue
        seen.add(cat)
        out.append({'key': key, 'category': cat, 'shock_pct': round(rng.uniform(lo, hi), 1),
                    'emoji': emoji, 'title': title, 'body': body})
    return out


def _applies(event, asset) -> bool:
    cat = (asset.get('category') or '').lower()
    if event['category'] == 'meme':
        return is_meme(asset)
    return event['category'] == cat           # crashes and bull runs hit meme stocks too


def shock_for(event, asset) -> float:
    pct = event['shock_pct']
    if event['category'] in ('stocks', 'crypto'):
        pct *= _beta(asset)
    return max(-75.0, pct) / 100


# --- state ---------------------------------------------------------------------------

def _life_seed(uid):
    try:
        res = supabase.table('player_lives').select('life_number').eq('user_id', uid).eq('is_current', True).limit(1).execute()
        return int(res.data[0]['life_number']) if res.data else 0
    except Exception:
        return 0


def traded_assets() -> list:
    return supabase.table('assets').select('*').in_('category', list(TRADED)).execute().data or []


def _rows(uid):
    rows = supabase.table('player_market_prices').select('*').eq('user_id', uid).execute().data or []
    return {str(r['asset_id']): r for r in rows}


def view(uid, assets=None) -> dict:
    """{asset_id: {'price', 'change_pct'}} for this player; untouched assets use the catalogue price."""
    uid = str(uid)
    rows = _rows(uid)
    out = {}
    for a in assets if assets is not None else traded_assets():
        if (a.get('category') or '').lower() not in TRADED:
            continue
        r = rows.get(str(a['id']))
        if r:
            price, prev = Decimal(str(r['price'])), Decimal(str(r.get('prev_price') or r['price']))
            change = float(round((price - prev) / prev * 100, 2)) if prev > 0 else 0.0
            out[str(a['id'])] = {'price': price, 'change_pct': change, 'change': float(price - prev)}
        else:
            out[str(a['id'])] = {'price': Decimal(str(a.get('price') or 0)), 'change_pct': 0.0, 'change': 0.0}
    return out


def price_of(uid, asset) -> Decimal:
    """What this player pays or gets for one unit right now."""
    if (asset.get('category') or '').lower() not in TRADED:
        return Decimal(str(asset.get('price') or 0))
    r = supabase.table('player_market_prices').select('price').eq('user_id', str(uid)).eq('asset_id', str(asset['id'])).limit(1).execute().data
    return Decimal(str(r[0]['price'])) if r else Decimal(str(asset.get('price') or 0))


def recent_events(uid, limit=5) -> list:
    rows = supabase.table('player_market_events').select('*').eq('user_id', str(uid)) \
        .order('week', desc=True).limit(limit).execute().data or []
    return rows


# --- the week ------------------------------------------------------------------------

def advance(uid, week) -> dict:
    """Move this player's market one game week. Returns the receipt's market section."""
    uid = str(uid)
    life = _life_seed(uid)
    assets = traded_assets()
    if not assets:
        return {'events': [], 'moves': [], 'portfolio_change': 0.0}
    rows = _rows(uid)
    events = roll_events(random.Random(f'{uid}:{life}:{week}:events'))
    now = datetime.now(timezone.utc).isoformat()

    new_prices = {}
    for a in sorted(assets, key=lambda a: str(a['id'])):
        aid = str(a['id'])
        rng = random.Random(f'{uid}:{life}:{week}:{aid}')
        old = Decimal(str(rows[aid]['price'])) if aid in rows else Decimal(str(a.get('price') or 0))
        if old <= 0:
            continue
        move = weekly_return(a, rng)
        for e in events:
            if _applies(e, a):
                move = (1 + move) * (1 + shock_for(e, a)) - 1
        new = max(PRICE_FLOOR, (old * Decimal(str(1 + move))).quantize(Decimal('0.01')))
        new_prices[aid] = (a, old, new)
        payload = {'price': float(new), 'prev_price': float(old), 'week': week, 'updated_at': now}
        if aid in rows:
            supabase.table('player_market_prices').update(payload).eq('user_id', uid).eq('asset_id', aid).execute()
        else:
            supabase.table('player_market_prices').insert({'user_id': uid, 'asset_id': aid, **payload}).execute()

    # Re-value what the player holds.
    by_name = {a['name']: aid for aid, (a, _, _) in new_prices.items()}
    holdings = supabase.table('user_assets').select('*').eq('user_id', uid).execute().data or []
    moves, change = [], Decimal('0')
    for h in holdings:
        aid = str(h.get('asset_id') or '') if str(h.get('asset_id') or '') in new_prices else by_name.get(h.get('name'))
        if not aid or aid not in new_prices:
            continue
        a, old, new = new_prices[aid]
        qty = Decimal(str(h.get('quantity') or 1))
        value = (new * qty).quantize(Decimal('0.01'))
        before = Decimal(str(h.get('value') or 0))
        supabase.table('user_assets').update({'value': float(value)}).eq('id', h['id']).execute()
        change += value - before
        moves.append({'name': a['name'], 'change_pct': float(round((new - old) / old * 100, 1)), 'value': float(value),
                      'value_change': float(value - before)})

    hit = []
    for e in events:
        names = [a['name'] for a, _, _ in new_prices.values() if _applies(e, a)]
        if not names:
            continue
        row = {'user_id': uid, 'week': week, 'kind': e['key'], 'emoji': e['emoji'], 'title': e['title'],
               'body': e['body'], 'shock_pct': e['shock_pct'], 'assets': names}
        try:
            supabase.table('player_market_events').insert(row).execute()
        except Exception:
            pass
        hit.append({k: row[k] for k in ('kind', 'emoji', 'title', 'body', 'shock_pct', 'assets')})

    moves.sort(key=lambda m: abs(m['value_change']), reverse=True)
    return {'events': hit, 'moves': moves, 'portfolio_change': float(change)}


def reset_for_new_life(uid) -> None:
    supabase.table('player_market_prices').delete().eq('user_id', str(uid)).execute()
    supabase.table('player_market_events').delete().eq('user_id', str(uid)).execute()
