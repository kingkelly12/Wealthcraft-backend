from app import db, supabase
import os
from datetime import datetime, timedelta, timezone
from app.services.balance_service import BalanceService
from app.services.push_notification_service import ExpoPushService
from decimal import Decimal
import logging
from app.utils.db import fetch_one

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class _MonthSummary:
    """Income/expenses for one player's month, as push text and as receipt lines."""

    def __init__(self):
        self.income = Decimal('0')
        self.expenses = Decimal('0')
        self.details = []   # human strings, for the push notification
        self.lines = []     # structured, for the in-game receipt

    def credit(self, amount, label, detail=None):
        self.income += amount
        self.details.append(detail or f"+${amount:,.2f} {label}")
        self.lines.append({'label': label, 'amount': float(amount), 'missed': False})

    def debit(self, amount, label, detail=None):
        self.expenses += amount
        self.details.append(detail or f"-${amount:,.2f} {label}")
        self.lines.append({'label': label, 'amount': float(-amount), 'missed': False})

    def missed(self, amount, label, detail):
        self.details.append(detail)
        self.lines.append({'label': label, 'amount': float(-amount), 'missed': True})

    @property
    def empty(self):
        return self.expenses == 0 and self.income == 0 and not self.details

    def as_dict(self):
        return {
            'income': float(self.income),
            'expenses': float(self.expenses),
            'net': float(self.income - self.expenses),
            'lines': self.lines,
        }


class _Scope:
    """
    Which players a run covers.

    The calendar job covers everyone NOT on game time (no player_game_clock
    row); a game-clock month covers exactly one player.
    """

    def __init__(self, only_user=None, excluded=()):
        self.only_user = str(only_user) if only_user else None
        self.excluded = set(excluded)

    def includes(self, uid):
        uid = str(uid)
        return uid == self.only_user if self.only_user else uid not in self.excluded

    def filter(self, query, column):
        return query.eq(column, self.only_user) if self.only_user else query


def _clocked_user_ids():
    """Players on turn-based game time; the calendar job leaves them alone."""
    try:
        res = supabase.table('player_game_clock').select('user_id').execute()
        return {str(r['user_id']) for r in res.data or []}
    except Exception as e:
        # Table missing (migration not applied yet) means nobody is on game time.
        logger.warning(f"Could not read player_game_clock ({e}); treating everyone as calendar players")
        return set()


def process_monthly_deductions():
    """
    Calendar End-of-Month job (pg_cron, 1st of the month).

    Runs the month for every player still on calendar time. Players on game
    time (This Week) get their month from process_month_for_user() when their
    4th week ends, so they are skipped here.
    """
    logger.info("Starting End of Month Processing cycle...")

    # Run at most once per calendar month, even if the scheduler retries or
    # someone calls the endpoint twice (double-charging rent/loans otherwise).
    from jobs.run_guard import claim_monthly_run
    period = claim_monthly_run('monthly_processing')
    if not period:
        logger.warning("Monthly processing already ran this month; skipping.")
        return {'success': True, 'skipped': True}

    scope = _Scope(excluded=_clocked_user_ids())
    try:
        profiles_res = supabase.table('profiles').select(_PROFILE_COLS).execute()
        profiles_map = {p['user_id']: p for p in profiles_res.data if scope.includes(p['user_id'])}
    except Exception as e:
        logger.error(f"Error fetching profiles: {e}")
        profiles_map = {}

    summaries = _run_month(scope, profiles_map, game_years=None)
    _send_month_notifications(summaries, profiles_map)

    # Advance missions one month; finish the ones that reached their end.
    try:
        _advance_missions(scope=scope)
    except Exception as e:
        logger.error(f"Error advancing missions: {e}")

    logger.info("End of Month Processing cycle complete.")
    return {'success': True, 'period': period, 'players_on_game_time': len(scope.excluded)}


def process_month_for_user(user_id, game_years=0.0):
    """
    One player's month on game time (called when their 4th week ends).

    Same steps as the calendar job, scoped to this player. The caller has
    already claimed the week, so this runs once per game month. Returns the
    month's receipt: {'income', 'expenses', 'net', 'lines', 'sanity_change',
    'stressed', 'missions_finished'}.
    """
    uid = str(user_id)
    scope = _Scope(only_user=uid)
    prof = supabase.table('profiles').select(_PROFILE_COLS).eq('user_id', uid).limit(1).execute()
    profiles_map = {p['user_id']: p for p in prof.data or []}

    summaries = _run_month(scope, profiles_map, game_years=game_years)
    summ = summaries.get(uid) or _MonthSummary()
    result = summ.as_dict()

    stressed, sanity_change = _apply_stress(uid, summ, profiles_map.get(uid, {}))
    result['stressed'] = stressed
    result['sanity_change'] = sanity_change

    finished = []
    try:
        finished = _advance_missions(scope=scope)
    except Exception as e:
        logger.error(f"Error advancing missions for {uid}: {e}")
    result['missions_finished'] = finished
    return result


_PROFILE_COLS = 'user_id, username, monthly_income, base_monthly_income, credit_score, created_at, sanity'


def _run_month(scope, profiles_map, game_years):
    """Steps 0-5 of a month. Returns {user_id: _MonthSummary}."""
    summary_by_user = {}

    def get_summary(uid):
        return summary_by_user.setdefault(uid, _MonthSummary())

    steps = (
        ('salaries', lambda: _pay_salaries(scope, profiles_map, get_summary)),
        ('loans', lambda: _charge_loans(scope, profiles_map, get_summary)),
        ('luxury maintenance', lambda: _charge_maintenance(scope, get_summary)),
        ('rent', lambda: _charge_rent(scope, get_summary)),
        ('living costs', lambda: _charge_living_costs(profiles_map, get_summary, game_years)),
        ('asset income', lambda: _pay_asset_income(scope, get_summary)),
    )
    for name, step in steps:
        logger.info(f"Processing {name}...")
        try:
            step()
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
    return summary_by_user


def _pay_salaries(scope, profiles_map, get_summary):
    """Payday: job salaries (annual / 12) + permanent income boosts."""
    jobs_res = scope.filter(supabase.table('jobs').select('user_id, title, salary').eq('is_current', True), 'user_id').execute()
    pay_by_user = {}
    for job in jobs_res.data or []:
        pay_by_user.setdefault(job['user_id'], []).append(job)
    for uid, profile in profiles_map.items():
        salary = sum((Decimal(str(j.get('salary') or 0)) for j in pay_by_user.get(uid, [])), Decimal('0')) / 12
        boosts = Decimal(str(profile.get('base_monthly_income') or 0))
        pay = (salary + boosts).quantize(Decimal('0.01'))
        if pay <= 0:
            continue
        BalanceService.add_balance(user_id=uid, amount=pay, reason="Monthly salary", category='salary')
        get_summary(uid).credit(pay, 'Salary')


def _charge_loans(scope, profiles_map, get_summary):
    """Bank and P2P loan instalments (P2P lenders are credited)."""
    liabilities_data = scope.filter(supabase.table('liabilities').select('*').gt('remaining_balance', 0), 'user_id').execute()
    for liability in liabilities_data.data or []:
        user_id = liability['user_id']
        if not scope.includes(user_id):
            continue
        liability_id = liability['id']
        monthly_payment = Decimal(str(liability.get('monthly_payment', 0)))
        if monthly_payment <= 0:
            continue

        current_balance = BalanceService.get_current_balance(user_id)
        summ = get_summary(user_id)
        remaining = Decimal(str(liability['remaining_balance']))
        monthly_payment = min(monthly_payment, remaining)  # never overcharge the final instalment
        name = liability.get('name') or 'Loan'

        if current_balance < monthly_payment:
            # Missed payment: 5% late fee added to the debt and a credit hit.
            penalty = (monthly_payment * Decimal('0.05')).quantize(Decimal('0.01'))
            supabase.table('liabilities').update({
                'remaining_balance': float(remaining + penalty),
            }).eq('id', liability_id).execute()
            _adjust_credit_score(profiles_map, user_id, CREDIT_MISSED_PAYMENT)
            logger.warning(f"User {user_id} missed loan payment for {liability_id}. Late fee ${penalty}.")
            summ.missed(
                monthly_payment, f"Missed: {name} (+${penalty:,.2f} late fee)",
                f"⚠️ Missed {name} (${monthly_payment:,.2f}) +${penalty:,.2f} late fee, credit score {CREDIT_MISSED_PAYMENT}",
            )
            continue

        BalanceService.subtract_balance(
            user_id=user_id, amount=monthly_payment,
            reason=f"Monthly Loan Payment: {name}", category='loan_payment',
        )
        new_bal = remaining - monthly_payment
        if new_bal <= 0:
            supabase.table('liabilities').delete().eq('id', liability_id).execute()
            if liability.get('bank_loan_id'):
                supabase.table('bank_loans').update({'status': 'completed'}).eq('id', liability['bank_loan_id']).execute()
        else:
            supabase.table('liabilities').update({
                'remaining_balance': float(new_bal),
                'remaining_term': max(0, (liability.get('remaining_term') or 1) - 1),
            }).eq('id', liability_id).execute()
        _adjust_credit_score(profiles_map, user_id, CREDIT_ON_TIME_PAYMENT)

        # P2P: credit the lender and keep the p2p_loans row in sync.
        if liability.get('liability_type') == 'p2p_loan' and liability.get('p2p_loan_id'):
            try:
                p2p_loan_id = liability['p2p_loan_id']
                p2p_res = fetch_one(supabase.table('p2p_loans').select('*').eq('id', p2p_loan_id))
                if p2p_res.data:
                    lender_id = p2p_res.data['lender_id']
                    BalanceService.add_balance(
                        user_id=lender_id, amount=monthly_payment,
                        reason="P2P Loan payment received", category='p2p_repayment',
                    )
                    get_summary(lender_id).credit(monthly_payment, 'P2P repayment received')
                    supabase.table('p2p_loans').update({
                        'remaining_balance': float(max(0, new_bal)),
                        'status': 'completed' if new_bal <= 0 else 'active',
                    }).eq('id', p2p_loan_id).execute()
            except Exception as e:
                logger.error(f"Error handling P2P lender credit for loan {liability_id}: {e}")

        summ.debit(monthly_payment, name)


def _charge_maintenance(scope, get_summary):
    """Upkeep on lifestyle (luxury) items."""
    player_liabs = scope.filter(
        supabase.table('player_liabilities').select('*, liability_items(*)').eq('is_active', True), 'player_id'
    ).execute()
    for pliab in player_liabs.data or []:
        user_id = pliab['player_id']
        if not scope.includes(user_id):
            continue
        cost = Decimal(str(pliab.get('monthly_cost', 0)))
        if cost <= 0:
            continue
        item_data = pliab.get('liability_items')
        if isinstance(item_data, list) and len(item_data) > 0:
            item_data = item_data[0]
        name = item_data.get('name', 'Luxury Item') if item_data else 'Luxury Item'

        summ = get_summary(user_id)
        if BalanceService.get_current_balance(user_id) >= cost:
            BalanceService.subtract_balance(user_id=user_id, amount=cost, reason=f"Maintenance Cost: {name}", category='lifestyle')
            summ.debit(cost, f"{name} upkeep")
        else:
            logger.warning(f"User {user_id} missed maintenance for {pliab['id']}.")
            summ.missed(cost, f"Missed: {name} upkeep", f"⚠️ Missed {name} maintenance (${cost:,.2f})")


def _charge_rent(scope, get_summary):
    active_rentals = scope.filter(
        supabase.table('player_rentals').select('*, rental_properties(*)').eq('is_active', True), 'player_id'
    ).execute()
    for rental in active_rentals.data or []:
        user_id = rental['player_id']
        if not scope.includes(user_id):
            continue
        rent = Decimal(str(rental.get('monthly_rent', 0)))
        if rent <= 0:
            continue
        prop_data = rental.get('rental_properties')
        name = prop_data.get('name', 'Rent') if prop_data else 'Rent'

        summ = get_summary(user_id)
        if BalanceService.get_current_balance(user_id) >= rent:
            BalanceService.subtract_balance(user_id=user_id, amount=rent, reason=f"Monthly Rent: {name}", category='rent')
            summ.debit(rent, f"Rent: {name}")
        else:
            logger.warning(f"User {user_id} missed rent for {rental['id']}.")
            summ.missed(rent, f"Missed rent: {name}", f"⚠️ Missed {name} (${rent:,.2f})")


def _years_since(created_at_str, now):
    if not created_at_str:
        return 0.0
    try:
        time_part = created_at_str.split('+')[0]
        created_dt = datetime.strptime(time_part[:19], "%Y-%m-%dT%H:%M:%S")
        return max(0.0, (now - created_dt).days / 365.25)
    except Exception:
        return 0.0


def _charge_living_costs(profiles_map, get_summary, game_years):
    """
    Food, utilities, WiFi: 20% of income, inflated 5% a year. On game time the
    years are game years (weeks lived / 52), not calendar years.
    """
    now = datetime.utcnow()
    for user_id, profile in profiles_map.items():
        monthly_income = Decimal(str(profile.get('monthly_income') or 0))
        if monthly_income <= 0:
            continue
        years = game_years if game_years is not None else _years_since(profile.get('created_at'), now)
        years = min(float(years), 20.0)
        cost = (monthly_income * Decimal('0.20') * Decimal(str(1.05 ** years))).quantize(Decimal('0.01'))

        summ = get_summary(user_id)
        if BalanceService.get_current_balance(user_id) >= cost:
            BalanceService.subtract_balance(user_id=user_id, amount=cost, reason="Living Costs (Food & WiFi)", category='living_costs')
            summ.debit(cost, 'Food, bills & WiFi', f"-${cost:,.2f} Living Costs")
        else:
            logger.warning(f"User {user_id} missed living costs.")
            summ.missed(cost, 'Missed: food & bills', f"⚠️ Missed Living Costs (${cost:,.2f})")


def _pay_asset_income(scope, get_summary):
    """Rental / dividend income from owned assets."""
    assets_res = supabase.table('assets').select('name, monthly_income').execute()
    income_map = {a['name']: Decimal(str(a.get('monthly_income') or 0)) for a in assets_res.data or []}

    user_assets = scope.filter(supabase.table('user_assets').select('*'), 'user_id').execute()
    for ua in user_assets.data or []:
        user_id = ua['user_id']
        if not scope.includes(user_id):
            continue
        name = ua['name']
        total_income = income_map.get(name, Decimal('0')) * Decimal(str(ua.get('quantity', 1)))
        if total_income > 0:
            BalanceService.add_balance(user_id=user_id, amount=total_income, reason=f"Monthly Asset Income: {name}", category='asset_income')
            get_summary(user_id).credit(total_income, f"{name} yield")


STRESS_EXPENSE_RATIO = Decimal('0.60')
STRESS_SANITY_HIT = -10


def _is_stressed(summ, profile):
    monthly_income = Decimal(str(profile.get('monthly_income') or 0))
    return monthly_income > 0 and summ.expenses > monthly_income * STRESS_EXPENSE_RATIO


def _apply_stress(uid, summ, profile):
    """Spending over 60% of income costs sanity. Returns (stressed, sanity_change)."""
    if not _is_stressed(summ, profile):
        return False, 0
    try:
        supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': STRESS_SANITY_HIT}).execute()
    except Exception as e:
        logger.error(f"Failed to deduct sanity for {uid}: {e}")
        return True, 0
    return True, STRESS_SANITY_HIT


def _send_month_notifications(summary_by_user, profiles_map):
    """Calendar job only: stress check (with an AI line) and one push per player."""
    from app.services.ai_service import AIService
    from app.services.mentor_service import MentorService
    import uuid

    notifications_to_send = []
    logger.info(f"Checking financial stress and queueing notifications for {len(summary_by_user)} users...")
    for uid, summ in summary_by_user.items():
        if summ.empty:
            continue
        profile = profiles_map.get(uid, {})
        is_stressed, _ = _apply_stress(uid, summ, profile)

        ai_stress_message = None
        if is_stressed:
            try:
                metrics = MentorService.analyze_player_finances(uuid.UUID(uid))
                metrics['sanity'] = int(profile.get('sanity', 100))
                ai_stress_message = AIService.analyze_financial_stress(profile.get('username', 'Player'), metrics).get('message')
            except Exception as e:
                logger.error(f"Failed to generate AI stress message for {uid}: {e}")

        net_change = summ.income - summ.expenses
        if is_stressed:
            title = "🚨 Financial Stress!"
            body = f"{ai_stress_message or 'Expenses exceeded 60% of income. Sanity dropped (-10).'}\n\nNet: {'+' if net_change > 0 else '-'}${abs(net_change):,.2f}\n\n" + "\n".join(summ.details)
        else:
            title = "💰 End of Month Summary"
            if net_change > 0:
                body = f"You gained a net +${net_change:,.2f} this month! \n\n" + "\n".join(summ.details)
            else:
                body = f"You had a net -${abs(net_change):,.2f} this month. \n\n" + "\n".join(summ.details)
        if len(body) > 200:
            body = body[:197] + "..."

        notifications_to_send.append({
            'user_id': uid,
            'title': title,
            'body': body,
            'data': {'type': 'financial_move', 'screen': '/banking'},
        })

    for i in range(0, len(notifications_to_send), 50):
        ExpoPushService.send_notifications_to_users(
            supabase_client=supabase,
            user_notifications=notifications_to_send[i:i + 50],
            notification_type='financial_move',
        )
    if notifications_to_send:
        logger.info(f"Batched {len(notifications_to_send)} end of month notifications.")


CREDIT_ON_TIME_PAYMENT = 2
CREDIT_MISSED_PAYMENT = -25


def _adjust_credit_score(profiles_map, user_id, delta):
    """Nudge credit score, clamped to 300..850 (it never changed anywhere before)."""
    profile = profiles_map.get(user_id)
    if not profile:
        return
    current = int(profile.get('credit_score') or 650)
    new_score = max(300, min(850, current + delta))
    if new_score == current:
        return
    try:
        supabase.table('profiles').update({'credit_score': new_score}).eq('user_id', user_id).execute()
        profile['credit_score'] = new_score
    except Exception as e:
        logger.error(f"Failed to update credit score for {user_id}: {e}")


def _criterion_met(criterion, profile):
    metric = criterion.get('metric')
    value = {
        'net_worth': profile.get('net_worth'),
        'monthly_income': profile.get('monthly_income'),
        'credit_score': profile.get('credit_score'),
    }.get(metric)
    if value is None:
        logger.warning(f"Mission metric '{metric}' is not evaluated yet; counting as not met")
        return False, None
    value = Decimal(str(value))
    target = Decimal(str(criterion.get('target') or 0))
    comparison = criterion.get('comparison')
    if comparison == 'greater_than':
        ok = value > target
    elif comparison == 'less_than':
        ok = value < target
    elif comparison == 'equals':
        ok = value == target
    elif comparison == 'between':
        ok = Decimal(str(criterion.get('target_min') or 0)) <= value <= target
    else:
        ok = False
    return ok, value


def _advance_missions(scope=None):
    """
    Move each in-scope active mission one month on; close the ones that ran
    their course. Returns [{'mission_id', 'name', 'completed'}] for missions
    that finished in this run.
    """
    scope = scope or _Scope()
    query = supabase.table('player_mission_progress') \
        .select('*, integrated_missions!mission_id(name, duration_months, completion_reward)') \
        .eq('is_active', True)
    active = scope.filter(query, 'player_id').execute()

    finished = []
    for pm in active.data or []:
        if not scope.includes(pm['player_id']):
            continue
        mission = pm.get('integrated_missions') or {}
        duration = int(mission.get('duration_months') or 1)
        next_month = int(pm.get('current_month') or 1) + 1

        if next_month <= duration:
            supabase.table('player_mission_progress').update({'current_month': next_month}) \
                .eq('id', pm['id']).eq('is_active', True).execute()
            continue

        player_id = pm['player_id']
        prof_res = supabase.table('profiles').select('net_worth, monthly_income, credit_score') \
            .eq('user_id', player_id).limit(1).execute()
        if not prof_res.data:
            continue
        profile = prof_res.data[0]
        criteria = supabase.table('mission_success_criteria').select('*') \
            .eq('mission_id', pm['mission_id']).execute().data or []

        met = 0
        for c in criteria:
            ok, value = _criterion_met(c, profile)
            met += int(ok)
            supabase.table('player_mission_success_tracking').update({
                'current_value': float(value or 0), 'is_met': ok,
            }).eq('player_mission_id', pm['id']).eq('criteria_id', c['id']).execute()

        total = len(criteria)
        success = met == total
        now = datetime.now(timezone.utc).isoformat()
        closed = supabase.table('player_mission_progress').update({
            'is_active': False,
            'is_completed': success,
            'is_failed': not success,
            'completed_at' if success else 'failed_at': now,
        }).eq('id', pm['id']).eq('is_active', True).execute()
        if not closed.data:
            continue  # someone else closed it concurrently

        snapshot = pm.get('game_state_snapshot') or {}
        reward = Decimal(str(mission.get('completion_reward') or 0)) if success else Decimal('0')
        supabase.table('mission_completion_results').insert({
            'mission_id': pm['mission_id'],
            'player_mission_id': pm['id'],
            'player_id': player_id,
            'completed': success,
            'failed': not success,
            'abandoned': False,
            'duration_months': duration,
            'net_worth_change': float(Decimal(str(profile.get('net_worth') or 0)) - Decimal(str(snapshot.get('net_worth') or 0))),
            'income_change': float(Decimal(str(profile.get('monthly_income') or 0)) - Decimal(str(snapshot.get('monthly_income') or 0))),
            'credit_score_change': int(profile.get('credit_score') or 0) - int(snapshot.get('credit_score') or 0),
            'criteria_met': met,
            'criteria_total': total,
            'success_percentage': (100.0 * met / total) if total else 100.0,
            'total_cash_reward': float(reward),
            'completion_message': f"{'Completed' if success else 'Failed'}: {mission.get('name', 'Mission')}",
            'completed_at': now,
        }).execute()

        if reward > 0:
            BalanceService.add_balance(player_id, reward, f"Mission reward: {mission.get('name')}", category='mission_reward')

        supabase.table('notifications').insert({
            'user_id': player_id,
            'type': 'system',
            'title': '🏆 Mission Complete!' if success else '💀 Mission Failed',
            'message': f"{mission.get('name', 'Mission')}: {met}/{total} goals met."
                       + (f" Reward: ${reward:,.2f}" if reward > 0 else ''),
            'read': False,
        }).execute()
        finished.append({'mission_id': pm['mission_id'], 'name': mission.get('name', 'Mission'), 'completed': success})

    return finished


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        process_monthly_deductions()
