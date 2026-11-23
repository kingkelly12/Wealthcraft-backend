"""
Mission decisions: making one, and deadlines.

One code path applies a decision, whether the player made it
(POST /api/missions/decision/) or the game made it for them:

* A decision point with `auto_resolve_after_days` is decided for the player
  once it has been due that many days (daily job: /api/cron/mission-deadlines/).
* A decision point with `is_required` that is still open when the mission month
  ends is decided at the rollover (jobs/monthly_loan_deductions._advance_missions),
  so a required decision always happens.
* Optional decisions without a deadline stay open and lapse at the mission's end.

The game picks `auto_resolve_option_id` if the point names one, otherwise the
"do nothing" option: the cheapest, and among equally cheap ones the one with
the worst sanity effect (ignoring a problem has a price).
"""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from app import supabase
from app.utils.mission_constraints import earlier_runs, emotion_sanity_delta

logger = logging.getLogger(__name__)


class DecisionError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _parse(ts) -> Optional[datetime]:
    if not ts:
        return None
    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def due_since(point: Dict, progress: Dict) -> Optional[datetime]:
    """When this decision point became available to the player."""
    if point['month'] > progress['current_month']:
        return None
    if point['month'] == progress['current_month']:
        return _parse(progress.get('month_started_at')) or _parse(progress.get('started_at'))
    # From an earlier mission month: due at least since the mission started.
    return _parse(progress.get('started_at'))


def deadline(point: Dict, progress: Dict) -> Optional[datetime]:
    """When the game will decide this point by itself (None: no day-based deadline)."""
    days = point.get('auto_resolve_after_days')
    since = due_since(point, progress)
    if not days or since is None:
        return None
    return since + timedelta(days=int(days))


def default_option(point: Dict, options: List[Dict]) -> Dict:
    named = point.get('auto_resolve_option_id')
    if named:
        match = next((o for o in options if str(o['id']) == str(named)), None)
        if match:
            return match
    return max(options, key=lambda o: (Decimal(str(o.get('immediate_cash') or 0)),
                                       -emotion_sanity_delta(o),
                                       -(o.get('option_order') or 0)))


def apply_decision(user_id: str, progress: Dict, point_id: str, option: Dict, options: List[Dict],
                   auto: bool = False) -> Dict:
    """
    Record one decision and apply its effects. Raises DecisionError.

    * once per decision point per mission run;
    * a restarted mission doesn't pay the same rewards again (costs still apply);
    * unaffordable with a free alternative -> refused (players) / the free one is
      picked by default_option anyway (auto); everything costs -> pay what you have;
    * recorded first so a duplicate can't pay twice, undone if the money fails.
    """
    from app.services.balance_service import BalanceService

    already = supabase.table('player_mission_decisions').select('id') \
        .eq('player_mission_id', progress['id']).eq('decision_point_id', point_id).limit(1).execute()
    if already.data:
        raise DecisionError('ALREADY_DECIDED', 'You already made this decision')

    cash = Decimal(str(option.get('immediate_cash') or 0))
    sanity_delta = emotion_sanity_delta(option)

    earlier = earlier_runs(user_id, progress['mission_id'], progress['id'])
    repeat = bool(earlier) and bool(
        supabase.table('player_mission_decisions').select('id')
        .in_('player_mission_id', earlier).eq('decision_point_id', point_id).limit(1).execute().data)
    if repeat:
        cash = min(cash, Decimal('0'))
        sanity_delta = min(sanity_delta, 0)

    if cash < 0:
        balance = BalanceService.get_current_balance(user_id)
        if -cash > balance:
            free_alternative = any(Decimal(str(o.get('immediate_cash') or 0)) >= 0
                                   for o in options if str(o['id']) != str(option['id']))
            if free_alternative and not auto:
                raise DecisionError('INSUFFICIENT_FUNDS',
                                    f"You can't afford that (${-cash:,.0f}). Pick another option.")
            cash = -balance

    try:
        recorded = supabase.table('player_mission_decisions').insert({
            'player_mission_id': progress['id'],
            'decision_point_id': point_id,
            'chosen_option_id': option['id'],
            'month_made': progress['current_month'],
            'decision_data': {'repeat_run': repeat, 'auto_resolved': auto},
        }).execute()
    except Exception as e:
        if '23505' in str(e) or 'duplicate' in str(e).lower():
            raise DecisionError('ALREADY_DECIDED', 'You already made this decision')
        raise

    reason = f"Mission decision: {option.get('label', 'Decision')}" + (' (decided for you)' if auto else '')
    try:
        if cash > 0:
            BalanceService.add_balance(user_id, cash, reason, category='mission')
        elif cash < 0:
            BalanceService.subtract_balance(user_id, -cash, reason, category='mission')
    except Exception:
        if recorded.data:
            supabase.table('player_mission_decisions').delete().eq('id', recorded.data[0]['id']).execute()
        raise

    sanity_change = 0
    if sanity_delta:
        row = supabase.table('profiles').select('sanity').eq('user_id', str(user_id)).limit(1).execute().data or []
        before = 100 if not row or row[0].get('sanity') is None else int(row[0]['sanity'])
        new = supabase.rpc('adjust_sanity', {'p_user_id': str(user_id), 'p_delta': sanity_delta}).execute().data
        sanity_change = (int(new) if new is not None else before) - before

    return {'immediate_cash': float(cash), 'sanity_change': sanity_change, 'repeat_run': repeat, 'auto_resolved': auto}


def _load(progress_rows: List[Dict]):
    """Decision points + options for the missions, and decisions already made."""
    mission_ids = list({p['mission_id'] for p in progress_rows})
    run_ids = [p['id'] for p in progress_rows]
    points = supabase.table('mission_decision_points').select('*').in_('mission_id', mission_ids).execute().data or []
    options = {}
    if points:
        for o in supabase.table('mission_decision_options').select('*') \
                .in_('decision_point_id', [p['id'] for p in points]).execute().data or []:
            options.setdefault(o['decision_point_id'], []).append(o)
    made = {(d['player_mission_id'], d['decision_point_id']) for d in
            (supabase.table('player_mission_decisions').select('player_mission_id, decision_point_id')
             .in_('player_mission_id', run_ids).execute().data or [])}
    by_mission = {}
    for p in points:
        by_mission.setdefault(p['mission_id'], []).append(p)
    return by_mission, options, made


def auto_decide(progress_rows: List[Dict], now: Optional[datetime] = None, month_end: bool = False) -> List[Dict]:
    """
    Decide, for the players, every open decision point that has reached its
    deadline (or, with month_end=True, every required one that's still open).
    Returns what was decided. Notifies each player.
    """
    from app.services.push_notification_service import ExpoPushService

    now = now or datetime.now(timezone.utc)
    if not progress_rows:
        return []
    by_mission, options, made = _load(progress_rows)

    decided, pushes = [], []
    for progress in progress_rows:
        for point in sorted(by_mission.get(progress['mission_id'], []), key=lambda p: p['month']):
            if (progress['id'], point['id']) in made or point['month'] > progress['current_month']:
                continue
            opts = options.get(point['id']) or []
            if not opts:
                continue
            due = deadline(point, progress)
            expired = due is not None and now >= due
            if not (expired or (month_end and point.get('is_required'))):
                continue
            option = default_option(point, opts)
            try:
                fx = apply_decision(str(progress['player_id']), progress, point['id'], option, opts, auto=True)
            except DecisionError:
                continue  # decided in the meantime
            except Exception as e:
                logger.error(f"Auto-decide failed for {progress['id']}/{point['id']}: {e}")
                continue

            title = f"⌛ Decided for you: {point.get('title', 'Mission decision')}"
            body = f"You let it slide, so: {option.get('label', 'the default option')}."
            if fx['immediate_cash']:
                body += f" ({'+' if fx['immediate_cash'] > 0 else '-'}${abs(fx['immediate_cash']):,.0f})"
            try:
                supabase.table('notifications').insert({
                    'user_id': progress['player_id'], 'type': 'mission', 'title': title, 'message': body, 'read': False,
                }).execute()
            except Exception as e:
                logger.warning(f"Could not record auto-decision notification: {e}")
            pushes.append({'user_id': str(progress['player_id']), 'title': title, 'body': body,
                           'data': {'type': 'mission', 'screen': '/missions', 'decision_point_id': point['id']}})
            decided.append({'player_mission_id': progress['id'], 'decision_point_id': point['id'],
                            'option_id': option['id'], **fx})

    if pushes:
        ExpoPushService.send_notifications_to_users(supabase_client=supabase, user_notifications=pushes,
                                                    notification_type='mission')
    return decided


def run_mission_deadlines(now: Optional[datetime] = None) -> Dict:
    """Daily job: decide every expired decision across all active missions."""
    rows = supabase.table('player_mission_progress').select('*').eq('is_active', True).execute().data or []
    decided = auto_decide(rows, now=now)
    logger.info(f"Mission deadlines: {len(decided)} decisions made for players")
    return {'active_missions': len(rows), 'auto_decided': len(decided)}
