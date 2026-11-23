-- Interest included in a loan's original balance. Paying a loan off early refunds the share not yet earned.
alter table public.liabilities add column if not exists total_interest numeric(15,2) not null default 0;
