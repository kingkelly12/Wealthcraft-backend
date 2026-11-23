-- =============================================================================
-- Squad goal rewards: remember the payout even after the squad is gone
-- =============================================================================
-- "Once a week per player, whatever squad" was tracked by squad_member_weeks.rewarded.
-- Postgres deletes a squad's member-week rows when the squad is deleted (ON DELETE
-- CASCADE), and a squad is deleted when its last member leaves, so
--   leave -> start a new squad -> play 3 weeks
-- paid the +5 sanity out a second time in the same week.
--
-- squad_rewards has its own primary key (player + week) and no foreign key to the
-- squad, so the claim is atomic and survives. Safe to re-run.
-- =============================================================================

create table if not exists public.squad_rewards (
  user_id    uuid not null references public.profiles(user_id) on delete cascade,
  week_start date not null,
  squad_id   uuid,                 -- informational only: no FK, the squad may be gone
  created_at timestamptz not null default now(),
  primary key (user_id, week_start)
);
alter table public.squad_rewards enable row level security;   -- backend (service role) only

-- Carry over payouts already made, then retire the old flag.
do $$
begin
  if exists (select 1 from information_schema.columns
              where table_schema = 'public' and table_name = 'squad_member_weeks' and column_name = 'rewarded') then
    insert into public.squad_rewards (user_id, week_start, squad_id)
    select user_id, week_start, squad_id from public.squad_member_weeks where rewarded
    on conflict do nothing;
    alter table public.squad_member_weeks drop column rewarded;
  end if;
end $$;

comment on column public.squad_member_weeks.end_net_worth is
  'Net worth when the member last finished a game week in that calendar week; the MVP is judged on this.';
