"""
Writes supabase/migrations/20261218000000_dividends_and_growth.sql.

    python3 scripts/catalog/market_data.py

Dividend yields: stockanalysis.com and companiesmarketcap.com, read 28 Nov 2026.
Yearly price changes: companiesmarketcap.com/<company>/stock-price-history/,
2017 to 2026 so far. Growth and swing are worked out from them below.
"""
import math
import statistics

# ticker: (dividend yield %, yearly price change % for 2017..2026; None = not listed then)
STOCKS = {
    'AAPL': (0.30, '48.04,-7.05,88.74,78.24,38.06,-28.20,54.80,35.56,11.88,31.88'),
    'MSFT': (0.80, '39.74,20.22,58.26,39.94,55.79,-27.69,58.35,14.50,16.17,1.91'),
    'NVDA': (0.66, '90.43,-32.85,73.41,118.02,124.48,-51.44,246.10,178.87,34.88,-19.31'),
    'GOOG': (0.32, '33.11,-2.76,27.84,28.12,67.43,-38.84,57.11,36.95,65.00,-13.18'),
    'AMZN': (0, '55.17,26.32,20.06,71.60,4.64,-50.71,77.04,46.33,4.81,10.09'),
    'TSM': (1.26, '39.69,-6.73,66.60,86.44,9.43,-40.92,43.21,97.27,51.89,16.27'),
    'SPCX': (0, ''),
    '2222.SR': (5.15, '-,-,0.06,3.12,6.85,1.85,16.70,-11.55,-11.57,14.02'),
    'META': (0.33, '51.00,-27.74,51.28,30.21,25.07,-64.45,183.76,69.73,10.34,-4.72'),
    'TSLA': (0, '43.49,3.83,34.89,720.05,44.81,-69.20,129.86,62.56,18.57,-11.06'),
    'AVGO': (0.83, '46.88,-0.30,29.44,42.02,61.13,-13.00,106.27,116.48,50.00,-9.75'),
    'LLY': (0.50, '16.18,40.09,16.99,30.27,69.43,36.47,61.28,31.21,38.95,29.56'),
    'BRK-B': (0, '20.99,3.53,11.69,1.52,30.88,2.70,15.09,25.06,11.43,15.55'),
    'ANT': (0, ''),
    'WMT': (0.74, '47.54,-3.28,29.90,23.22,0.31,-0.44,11.46,72.20,24.72,19.50'),
    '005930.KS': (2.99, '61.38,-25.52,42.28,62.11,-11.97,-32.50,40.62,-40.03,132.88,60.39'),
    'JPM': (2.04, '25.39,-7.50,44.75,-6.67,28.96,-14.45,29.64,42.63,36.44,0.23'),
    'V': (0.73, '44.44,15.99,42.27,15.15,0.13,-5.46,26.53,23.02,12.12,22.48'),
    'MU': (0.09, '82.35,-27.34,64.21,35.73,26.10,-47.40,70.60,2.65,227.55,126.67'),
    'AMD': (0, '-10.06,68.12,143.55,86.78,55.90,-56.89,130.26,-12.84,77.53,98.23'),
    'JNJ': (1.95, '23.75,-4.80,17.40,10.75,12.06,5.68,-9.37,-6.73,47.16,33.13'),
    'XOM': (2.67, '-4.47,-16.48,4.92,-37.22,56.51,80.48,-2.93,8.67,15.25,33.11'),
    '000660.KS': (0.97, '90.12,-22.93,50.60,33.51,-3.56,-44.55,84.01,7.75,293.47,83.08'),
    'MA': (0.52, '44.69,24.86,58.24,18.28,2.73,-5.71,23.73,25.53,9.76,16.83'),
    'ABBV': (2.49, '60.61,-2.67,4.83,26.28,34.61,23.99,-0.71,15.25,30.84,27.74'),
    'ASML': (0.60, '58.94,-11.66,92.39,62.50,60.11,-30.64,39.10,-2.55,53.50,23.92'),
    '601939.SS': (3.13, '55.43,-19.05,18.80,-4.01,1.36,-7.53,19.50,37.11,17.90,40.32'),
    'COST': (0.54, '22.66,9.31,44.95,33.77,50.48,-18.91,50.06,41.65,-4.86,27.31'),
    'KO': (2.18, '13.45,7.57,21.68,3.14,15.76,10.44,-3.43,7.26,14.69,39.32'),
    'PLTR': (0, '-,-,-,147.89,-22.08,-65.35,168.70,356.15,136.40,-3.14'),
    'CVX': (3.35, '10.45,-11.44,13.29,-26.51,45.79,55.92,-10.90,1.07,7.50,39.39'),
    '601288.SS': (4.82, '36.99,-7.02,8.13,-5.41,2.06,-2.85,29.78,49.08,60.76,7.39'),
    'TCEHY': (1.34, '112.85,-27.42,21.85,44.51,-19.76,-25.18,-10.08,43.40,45.13,-40.98'),
    'PG': (2.52, '12.53,4.97,40.68,15.53,21.68,-4.65,-0.86,15.52,-11.99,20.62'),
    '688825.SS': (0, ''),             # no yield or history found
    'RO.SW': (2.61, '10.36,-3.18,30.75,13.36,30.43,-10.74,-18.17,-2.83,46.73,21.64'),
    'CSCO': (1.73, '29.89,14.89,14.82,-5.10,47.19,-22.20,8.61,21.02,32.90,25.98'),
    'HD': (2.57, '44.37,-6.56,30.11,23.78,60.53,-20.76,12.75,15.49,-9.79,5.25'),
    '601988.SS': (3.08, '27.24,-9.86,7.73,-3.74,4.79,0.84,30.10,39.86,16.33,34.23'),
    'MRK': (2.49, '-3.58,40.08,23.60,-8.30,2.81,48.97,0.84,-9.75,8.13,34.26'),
    '1398.HK': (4.93, '40.52,-9.36,16.71,-11.87,-3.66,-1.80,2.20,51.20,33.27,20.42'),
    'BAC': (2.61, '33.10,-16.08,44.32,-12.67,51.00,-26.61,3.61,32.95,26.40,-10.78'),
    'GE': (0.58, '-43.08,-56.70,44.76,-9.01,13.14,-12.56,92.97,67.02,83.32,5.17'),
    'ORCL': (1.87, '24.13,-1.62,19.16,22.02,38.91,-5.39,27.84,62.10,18.36,-45.04'),
    'UNH': (2.64, '38.61,14.16,22.78,21.86,45.69,6.91,3.04,-4.74,-33.82,6.45'),
    'INTC': (0, '29.69,2.69,30.30,-16.08,6.37,-48.36,92.38,-57.49,82.49,55.56'),
    'PANW': (0, '14.18,26.79,26.22,50.97,58.32,-23.08,112.99,25.96,1.91,99.11'),
    'PM': (3.41, '20.19,-32.49,33.92,3.57,22.69,11.45,-1.94,32.25,34.63,17.08'),
    'NVS': (3.10, '19.48,5.04,29.78,3.06,-3.59,7.57,14.26,0.03,47.21,11.76'),
    'AZN': (1.76, '25.85,11.26,42.39,3.80,16.50,20.44,0.59,0.04,33.91,0.55'),
}
YEARS = 9.9                  # nine full years and most of 2026
MARKET = 0.08                # what a large company does in a long run, roughly
KEPT = 0.25                  # how much of a company's own past carries forward
GROWTH_RANGE = (0.03, 0.14)
SWING_RANGE = (0.18, 0.55)     # one company swings more than an index fund (0.15)

# Coins: typical yearly growth and swing. Game settings, informed by past
# drawdowns of 75-95%: not forecasts.
CRYPTO = {
    'Bitcoin': (0.12, 0.65), 'Ethereum': (0.08, 0.80), 'DogeMoon': (-0.15, 1.20), 'BNB': (0.08, 0.75),
    'XRP': (0.04, 0.90), 'Solana': (0.05, 0.95), 'Hyperliquid': (0.02, 1.10), 'Zcash': (0.00, 1.00),
    'Monero': (0.05, 0.80), 'Chainlink': (0.03, 0.95),
}


def history(changes):
    return [float(x) / 100 for x in changes.split(',') if x not in ('', '-')]


def past_growth(changes):
    """Compound yearly price growth over the years there are, or None."""
    years = history(changes)
    if not years:
        return None
    span = len(years) - (10 - YEARS)          # the last year is partial
    return math.prod(1 + r for r in years) ** (1 / span) - 1


def figures(changes):
    """(growth, swing) the game uses."""
    past = past_growth(changes)
    if past is None:
        return MARKET, 0.45                   # newly listed: average growth, big swings
    growth = min(max(MARKET + KEPT * (past - MARKET), GROWTH_RANGE[0]), GROWTH_RANGE[1])
    swing = statistics.pstdev([math.log(1 + r) for r in history(changes)])
    return round(growth, 3), round(min(max(swing, SWING_RANGE[0]), SWING_RANGE[1]), 2)


def sql():
    stocks = []
    for ticker, (dividend, changes) in STOCKS.items():
        growth, swing = figures(changes)
        stocks.append(f"  ('%({ticker})', {dividend}, {growth:.3f}, {swing:.2f})")
    coins = [f"  ('{name}', {g:.2f}, {v:.2f})" for name, (g, v) in CRYPTO.items()]
    return """-- =============================================================================
-- Real dividend yields, and growth and swings for stocks and coins
-- Written by scripts/catalog/market_data.py: change numbers there, not here.
-- * Dividends: yields read 28 Nov 2026, paid on paydays (monthly_income).
-- * annual_drift is now the TYPICAL yearly growth (app/game/market.py).
--   Stocks: 8% plus a quarter of how far the company's own 2017-2026 price
--   growth was from 8%, kept between 3% and 14%. Swing: from the same years.
-- * Coins: game settings.
-- Run after 20261217000000_more_markets.sql. Safe to run more than once.
-- =============================================================================
begin;

-- A $1 share's monthly dividend is a fraction of a cent.
alter table public.assets alter column monthly_income type numeric(14,4);

update public.assets a set
  monthly_income = round(a.price * v.yield_pct / 100 / 12, 4),
  annual_drift = v.growth, annual_volatility = v.swing,
  roi = round((v.growth * 100 + v.yield_pct)::numeric, 1)
from (values
""" + ",\n".join(stocks) + """
) as v(pattern, yield_pct, growth, swing)
where a.category = 'stocks' and a.name like v.pattern;

update public.assets a set annual_drift = v.growth, annual_volatility = v.swing, roi = round((v.growth * 100)::numeric, 1)
from (values
""" + ",\n".join(coins) + """
) as v(name, growth, swing)
where a.category = 'crypto' and a.name = v.name;

commit;
"""


if __name__ == '__main__':
    with open('supabase/migrations/20261218000000_dividends_and_growth.sql', 'w') as f:
        f.write(sql())
    for ticker, (dividend, changes) in STOCKS.items():
        past = past_growth(changes)
        growth, swing = figures(changes)
        print(f"{ticker:<11} past {'-' if past is None else f'{past:.0%}':>5}  game {growth:.1%}  swing {swing:.0%}  yield {dividend}%")
