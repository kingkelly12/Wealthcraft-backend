-- =============================================================================
-- Mission decision deadlines
-- =============================================================================
-- mission_decision_points already had is_required, auto_resolve_after_days and
-- auto_resolve_option_id, but nothing used them. Now (app/game/mission_decisions.py):
-- * a point with auto_resolve_after_days is decided for the player once it has
--   been due that many days (daily: /api/cron/mission-deadlines/);
-- * a required point still open when the mission month ends is decided at the
--   rollover;
-- * the game picks auto_resolve_option_id, else the cheapest ("do nothing") option.
--
-- "Due since" needs to know when the current mission month began, so progress
-- rows now record it. Safe to re-run.
-- =============================================================================

alter table public.player_mission_progress
  add column if not exists month_started_at timestamptz not null default now();

-- Missions already running: a mission still in month 1 counts from its start;
-- for later months the true start is unknown, so they count from now (the
-- column default) and nothing is decided early.
update public.player_mission_progress
   set month_started_at = started_at
 where month_started_at > started_at and current_month = 1;
