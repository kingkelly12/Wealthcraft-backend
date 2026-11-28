-- =============================================================================
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
  ('%(AAPL)', 0.3, 0.137, 0.28),
  ('%(MSFT)', 0.8, 0.122, 0.23),
  ('%(NVDA)', 0.66, 0.140, 0.55),
  ('%(GOOG)', 0.32, 0.113, 0.30),
  ('%(AMZN)', 0, 0.111, 0.35),
  ('%(TSM)', 1.26, 0.134, 0.34),
  ('%(SPCX)', 0, 0.080, 0.45),
  ('%(2222.SR)', 5.15, 0.065, 0.18),
  ('%(META)', 0.33, 0.103, 0.53),
  ('%(TSLA)', 0, 0.140, 0.55),
  ('%(AVGO)', 0.83, 0.140, 0.30),
  ('%(LLY)', 0.5, 0.140, 0.18),
  ('%(BRK-B)', 0, 0.094, 0.18),
  ('%(ANT)', 0, 0.080, 0.45),
  ('%(WMT)', 0.74, 0.112, 0.18),
  ('%(005930.KS)', 2.99, 0.105, 0.43),
  ('%(JPM)', 2.04, 0.100, 0.19),
  ('%(V)', 0.73, 0.107, 0.18),
  ('%(MU)', 0.09, 0.140, 0.51),
  ('%(AMD)', 0, 0.140, 0.52),
  ('%(JNJ)', 1.95, 0.089, 0.18),
  ('%(XOM)', 2.67, 0.083, 0.29),
  ('%(000660.KS)', 0.97, 0.140, 0.52),
  ('%(MA)', 0.52, 0.112, 0.18),
  ('%(ABBV)', 2.49, 0.113, 0.18),
  ('%(ASML)', 0.6, 0.133, 0.31),
  ('%(601939.SS)', 3.13, 0.095, 0.20),
  ('%(COST)', 0.54, 0.119, 0.20),
  ('%(KO)', 2.18, 0.092, 0.18),
  ('%(PLTR)', 0, 0.140, 0.55),
  ('%(CVX)', 3.35, 0.084, 0.23),
  ('%(601288.SS)', 4.82, 0.100, 0.19),
  ('%(TCEHY)', 1.34, 0.075, 0.39),
  ('%(PG)', 2.52, 0.086, 0.18),
  ('%(688825.SS)', 0, 0.080, 0.45),
  ('%(RO.SW)', 2.61, 0.086, 0.18),
  ('%(CSCO)', 1.73, 0.098, 0.18),
  ('%(HD)', 2.57, 0.093, 0.21),
  ('%(601988.SS)', 3.08, 0.094, 0.18),
  ('%(MRK)', 2.49, 0.090, 0.18),
  ('%(1398.HK)', 4.93, 0.090, 0.18),
  ('%(BAC)', 2.61, 0.083, 0.25),
  ('%(GE)', 0.58, 0.078, 0.47),
  ('%(ORCL)', 1.87, 0.091, 0.28),
  ('%(UNH)', 2.64, 0.085, 0.21),
  ('%(INTC)', 0, 0.076, 0.48),
  ('%(PANW)', 0, 0.140, 0.29),
  ('%(PM)', 3.41, 0.091, 0.20),
  ('%(NVS)', 3.1, 0.092, 0.18),
  ('%(AZN)', 1.76, 0.097, 0.18)
) as v(pattern, yield_pct, growth, swing)
where a.category = 'stocks' and a.name like v.pattern;

update public.assets a set annual_drift = v.growth, annual_volatility = v.swing, roi = round((v.growth * 100)::numeric, 1)
from (values
  ('Bitcoin', 0.12, 0.65),
  ('Ethereum', 0.08, 0.80),
  ('DogeMoon', -0.15, 1.20),
  ('BNB', 0.08, 0.75),
  ('XRP', 0.04, 0.90),
  ('Solana', 0.05, 0.95),
  ('Hyperliquid', 0.02, 1.10),
  ('Zcash', 0.00, 1.00),
  ('Monero', 0.05, 0.80),
  ('Chainlink', 0.03, 0.95)
) as v(name, growth, swing)
where a.category = 'crypto' and a.name = v.name;

commit;
