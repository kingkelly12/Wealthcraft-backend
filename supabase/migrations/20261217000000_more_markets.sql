-- =============================================================================
-- More to invest in: the 50 largest listed companies, 7 more coins, 7 more currency pairs
-- Prices are a snapshot from 28 November 2026 (companiesmarketcap.com,
-- coinmarketcap.com, open.er-api.com). After that each player's market moves on
-- its own (app/game/market.py): these are not live prices.
-- Growth and swing figures are game settings by risk, not research.
-- Deploy the backend BEFORE running this (it writes market prices in one batch).
-- Safe to run more than once: a re-run leaves existing rows alone.
-- =============================================================================
begin;

insert into public.assets (name, category, price, monthly_income, annual_drift, annual_volatility, risk_level,
                           roi, time_to_return, availability, total_supply, description)
values
  ('Apple (AAPL)', 'stocks', 358.54, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Technology. One of the 50 largest companies in the world by market value.'),
  ('Microsoft (MSFT)', 'stocks', 492.85, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Technology. One of the 50 largest companies in the world by market value.'),
  ('NVIDIA (NVDA)', 'stocks', 150.49, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Alphabet (GOOG)', 'stocks', 272.44, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Technology. One of the 50 largest companies in the world by market value.'),
  ('Amazon (AMZN)', 'stocks', 254.12, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Technology and retail. One of the 50 largest companies in the world by market value.'),
  ('TSMC (TSM)', 'stocks', 353.34, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('SpaceX (SPCX)', 'stocks', 133.59, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Space. One of the 50 largest companies in the world by market value.'),
  ('Saudi Aramco (2222.SR)', 'stocks', 7.03, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Oil. One of the 50 largest companies in the world by market value.'),
  ('Meta Platforms (META)', 'stocks', 628.96, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Social media. One of the 50 largest companies in the world by market value.'),
  ('Tesla (TSLA)', 'stocks', 400.00, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Electric cars. One of the 50 largest companies in the world by market value.'),
  ('Broadcom (AVGO)', 'stocks', 312.34, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Eli Lilly (LLY)', 'stocks', 1392.00, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('Berkshire Hathaway (BRK-B)', 'stocks', 580.79, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Holding company. One of the 50 largest companies in the world by market value.'),
  ('Anthropic (ANT)', 'stocks', 91.88, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Artificial intelligence. One of the 50 largest companies in the world by market value.'),
  ('Walmart (WMT)', 'stocks', 133.13, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Retail. One of the 50 largest companies in the world by market value.'),
  ('Samsung (005930.KS)', 'stocks', 134.32, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Electronics. One of the 50 largest companies in the world by market value.'),
  ('JPMorgan Chase (JPM)', 'stocks', 322.96, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('Visa (V)', 'stocks', 429.56, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Payments. One of the 50 largest companies in the world by market value.'),
  ('Micron Technology (MU)', 'stocks', 646.95, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('AMD (AMD)', 'stocks', 424.54, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Johnson & Johnson (JNJ)', 'stocks', 275.51, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Healthcare. One of the 50 largest companies in the world by market value.'),
  ('Exxon Mobil (XOM)', 'stocks', 160.18, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Oil. One of the 50 largest companies in the world by market value.'),
  ('SK Hynix (000660.KS)', 'stocks', 832.45, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Mastercard (MA)', 'stocks', 666.96, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Payments. One of the 50 largest companies in the world by market value.'),
  ('AbbVie (ABBV)', 'stocks', 291.88, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('ASML (ASML)', 'stocks', 1326.00, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chip machines. One of the 50 largest companies in the world by market value.'),
  ('China Construction Bank (601939.SS)', 'stocks', 1.87, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('Costco (COST)', 'stocks', 1098.00, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Retail. One of the 50 largest companies in the world by market value.'),
  ('Coca-Cola (KO)', 'stocks', 97.40, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Drinks. One of the 50 largest companies in the world by market value.'),
  ('Palantir (PLTR)', 'stocks', 172.17, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Software. One of the 50 largest companies in the world by market value.'),
  ('Chevron (CVX)', 'stocks', 212.45, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Oil. One of the 50 largest companies in the world by market value.'),
  ('Agricultural Bank of China (601288.SS)', 'stocks', 1.18, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('Tencent (TCEHY)', 'stocks', 45.18, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Technology. One of the 50 largest companies in the world by market value.'),
  ('Procter & Gamble (PG)', 'stocks', 172.86, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Household goods. One of the 50 largest companies in the world by market value.'),
  ('CXMT (688825.SS)', 'stocks', 5.56, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Roche (RO.SW)', 'stocks', 493.63, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('Cisco (CSCO)', 'stocks', 97.04, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Networking. One of the 50 largest companies in the world by market value.'),
  ('Home Depot (HD)', 'stocks', 362.15, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Retail. One of the 50 largest companies in the world by market value.'),
  ('Bank of China (601988.SS)', 'stocks', 1.10, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('Merck (MRK)', 'stocks', 141.32, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('ICBC (1398.HK)', 'stocks', 0.97, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('Bank of America (BAC)', 'stocks', 49.07, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Banking. One of the 50 largest companies in the world by market value.'),
  ('General Electric (GE)', 'stocks', 323.94, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Engineering. One of the 50 largest companies in the world by market value.'),
  ('Oracle (ORCL)', 'stocks', 107.13, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Software. One of the 50 largest companies in the world by market value.'),
  ('UnitedHealth (UNH)', 'stocks', 351.41, 0, 0.08, 0.26, 'medium', 8.0, '5+ years', 100000, 100000, 'Health insurance. One of the 50 largest companies in the world by market value.'),
  ('Intel (INTC)', 'stocks', 57.40, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Chips. One of the 50 largest companies in the world by market value.'),
  ('Palo Alto Networks (PANW)', 'stocks', 366.76, 0, 0.09, 0.42, 'high', 9.0, '5+ years', 100000, 100000, 'Cyber security. One of the 50 largest companies in the world by market value.'),
  ('Philip Morris International (PM)', 'stocks', 187.80, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Tobacco. One of the 50 largest companies in the world by market value.'),
  ('Novartis (NVS)', 'stocks', 154.08, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('AstraZeneca (AZN)', 'stocks', 183.69, 0, 0.06, 0.18, 'low', 6.0, '5+ years', 100000, 100000, 'Medicines. One of the 50 largest companies in the world by market value.'),
  ('BNB', 'crypto', 548.91, 0, 0.12, 0.75, 'high', 12.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('XRP', 'crypto', 0.94, 0, 0.10, 0.90, 'high', 10.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('Solana', 'crypto', 70.73, 0, 0.12, 0.95, 'high', 12.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('Hyperliquid', 'crypto', 62.42, 0, 0.10, 1.10, 'very_high', 10.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('Zcash', 'crypto', 724.30, 0, 0.08, 1.00, 'very_high', 8.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('Monero', 'crypto', 429.50, 0, 0.08, 0.80, 'high', 8.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('Chainlink', 'crypto', 9.14, 0, 0.10, 0.95, 'high', 10.0, 'unknown', 100000, 100000, 'Cryptocurrency. Big swings, no yield.'),
  ('GBP/USD Position', 'forex', 1000.00, 0, 0.00, 0.09, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on GBP/USD, which was 1.3105 in late November 2026.'),
  ('USD/JPY Position', 'forex', 1000.00, 0, 0.00, 0.10, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on USD/JPY, which was 159.52 in late November 2026.'),
  ('USD/CHF Position', 'forex', 1000.00, 0, 0.00, 0.08, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on USD/CHF, which was 0.8359 in late November 2026.'),
  ('AUD/USD Position', 'forex', 1000.00, 0, 0.00, 0.11, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on AUD/USD, which was 0.6650 in late November 2026.'),
  ('USD/CAD Position', 'forex', 1000.00, 0, 0.00, 0.07, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on USD/CAD, which was 1.4244 in late November 2026.'),
  ('NZD/USD Position', 'forex', 1000.00, 0, 0.00, 0.11, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on NZD/USD, which was 0.5468 in late November 2026.'),
  ('EUR/GBP Position', 'forex', 1000.00, 0, 0.00, 0.06, 'high', 0.0, 'days', 100000, 100000, 'A $1,000 position on EUR/GBP, which was 0.8352 in late November 2026.')
on conflict (name) do nothing;

commit;
