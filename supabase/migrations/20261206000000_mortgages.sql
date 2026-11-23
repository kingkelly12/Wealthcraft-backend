-- Mortgages: a loan secured on a home you bought. Repossessed after 3 missed paydays in a row.
alter table public.player_homes add column if not exists repossessed_at timestamptz;
alter table public.liabilities add column if not exists player_home_id uuid references public.player_homes(id) on delete set null;
alter table public.liabilities add column if not exists missed_streak integer not null default 0;
-- Mortgages now come with buying a home (20% down); the loose $250k cash product is retired.
delete from public.bank_loans where type = 'Mortgage' and borrower_id is null;
