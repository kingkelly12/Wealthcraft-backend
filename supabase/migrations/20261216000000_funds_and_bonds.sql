-- =============================================================================
-- Bonds, mutual funds, special funds, hedge funds and private capital
-- A year's return is split into income paid every payday (monthly_income per
-- unit = price x yield / 12) and price growth (annual_drift). Together they come
-- to the average of Kenyan and global figures, researched November 2026:
--   bonds            8.4%  = Kenya infrastructure/treasury ~12.4, global fund yield 4.46
--   mutual funds     9%    = Kenya balanced ~12, global balanced ~6.2
--   special funds   12%    = Kenya ~18.3, nearest global (funds of funds) 5.5
-- Hedge funds (13%) and private capital (15%) are game design, not averages:
-- they are set above the real figures (about 9%) so the big minimums are worth
-- reaching. Private capital is locked for 3 game years (asset_routes.LOCK_YEARS).
-- The price is the minimum you can put in. Fund names are made up.
-- Deploy the backend BEFORE running this: an older backend treats these as property.
-- Safe to run more than once.
-- =============================================================================
begin;

alter table public.user_assets add column if not exists locked_until_week integer;

insert into public.assets (name, category, price, monthly_income, annual_drift, annual_volatility, risk_level,
                           roi, time_to_return, availability, total_supply, description, risk_education)
values
  ('Government Bond', 'bonds', 500, 3.50, 0.00, 0.04, 'low', 8.4, '12 years', 100000, 100000,
   'You lend the government money and it pays you interest every month. The calmest thing on this screen.',
   'The price barely moves. Your return is the interest.'),
  ('Balanced Mutual Fund', 'mutual_funds', 500, 1.67, 0.05, 0.10, 'medium', 9.0, '8 years', 100000, 100000,
   'Everyone pools their money and a manager spreads it across shares and bonds.',
   'Falls in a market crash, though less than shares alone.'),
  ('Multi-Asset Special Fund', 'special_funds', 2000, 10.00, 0.06, 0.14, 'high', 12.0, '6 years', 50000, 50000,
   'A fund allowed to chase unusual things: currencies, commodities, private debt.',
   'The highest average here, and past good years are no promise.'),
  ('Summit Hedge Fund', 'hedge_funds', 100000, 333.33, 0.09, 0.08, 'medium', 13.0, '8 years', 1000, 1000,
   'For serious money. Managers bet both ways, trying to earn whatever the market does.',
   'Steadier than shares, with a very high entry ticket.'),
  ('Frontier Private Capital', 'private_capital', 250000, 625.00, 0.12, 0.15, 'high', 15.0, '3 years', 500, 500,
   'You buy into companies that are not on any stock exchange. Your money is locked in for 3 game years.',
   'Big minimum, uneven results, and you cannot sell for 3 game years.')
on conflict (name) do update set
  category = excluded.category, price = excluded.price, monthly_income = excluded.monthly_income,
  annual_drift = excluded.annual_drift, annual_volatility = excluded.annual_volatility,
  risk_level = excluded.risk_level, roi = excluded.roi, time_to_return = excluded.time_to_return,
  description = excluded.description, risk_education = excluded.risk_education;

commit;
