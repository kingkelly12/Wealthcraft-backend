from app import supabase
from datetime import datetime, timezone
from app.services.balance_service import BalanceService
from app.services.push_notification_service import ExpoPushService
from decimal import Decimal
import logging
from app.utils.db import fetch_one
from app.game import economy

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

    def credit(self, amount, label, detail=None, note=None):
        self.income += amount
        self.details.append(detail or f"+${amount:,.2f} {label}")
        self.lines.append({'label': label, 'amount': float(amount), 'missed': False, **({'note': note} if note else {})})

    def debit(self, amount, label, detail=None, note=None):
        self.expenses += amount
        self.details.append(detail or f"-${amount:,.2f} {label}")
        self.lines.append({'label': label, 'amount': float(-amount), 'missed': False, **({'note': note} if note else {})})

    def missed(self, amount, label, detail, note=None):
        self.details.append(detail)
        self.lines.append({'label': label, 'amount': float(-amount), 'missed': True, **({'note': note} if note else {})})

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
        ('lifestyle running costs', lambda: _charge_maintenance(scope, get_summary)),
        ('rent', lambda: _charge_rent(scope, get_summary)),
        ('homes you own', lambda: _run_homes(scope, get_summary)),
        ('roommate rent and bills', lambda: _roommate_rent(scope, get_summary, game_years)),
        ('household bills', lambda: _charge_living_costs(scope, profiles_map, get_summary, game_years)),
        ('asset income', lambda: _pay_asset_income(scope, get_summary)),
    )
    for name, step in steps:
        logger.info(f"Processing {name}...")
        try:
            step()
        except Exception as e:
            logger.error(f"Error processing {name}: {e}")
    return summary_by_user


def _mission_multipliers(scope):
    """
    {user_id: (income_multiplier, expense_multiplier)} for players on an active
    mission. The app shows these ("Income: 80%"); they were never applied.
    """
    rows = scope.filter(supabase.table('player_mission_progress').select('player_id, constraints_applied')
                        .eq('is_active', True), 'player_id').execute().data or []
    out = {}
    for r in rows:
        c = r.get('constraints_applied') or {}
        try:
            out[str(r['player_id'])] = (Decimal(str(c.get('income_multiplier') or 1)),
                                        Decimal(str(c.get('expense_multiplier') or 1)))
        except Exception:
            continue
    return out


def _pay_salaries(scope, profiles_map, get_summary):
    """
    Payday: main job salaries (annual / 12) + permanent income boosts.

    Gigs pay every game week (week_service.complete_week) for players on game
    time; players still on calendar time get their gigs' month here.
    """
    jobs_res = scope.filter(supabase.table('jobs').select('*').eq('is_current', True), 'user_id').execute()
    pay_by_user = {}
    for job in jobs_res.data or []:
        pay_by_user.setdefault(job['user_id'], []).append(job)
    multipliers = _mission_multipliers(scope)
    for uid, profile in profiles_map.items():
        jobs = pay_by_user.get(uid, [])
        salary = sum((Decimal(str(j.get('salary') or 0)) for j in jobs if j.get('kind', 'job') != 'gig'), Decimal('0')) / 12
        boosts = Decimal(str(profile.get('base_monthly_income') or 0))
        income_mult = multipliers.get(str(uid), (Decimal('1'), Decimal('1')))[0]
        pay = ((salary + boosts) * income_mult).quantize(Decimal('0.01'))
        if pay > 0:
            BalanceService.add_balance(user_id=uid, amount=pay, reason="Monthly salary", category='salary')
            get_summary(uid).credit(pay, 'Salary')
        # A month of experience on your main job (careers.py: it unlocks the next rung).
        mains = [j['id'] for j in jobs if j.get('kind', 'job') != 'gig']
        if mains:
            try:
                from app.game import careers
                careers.add_month(mains)
            except Exception as e:
                logger.error(f"Experience update failed for {uid}: {e}")
        if scope.only_user:
            continue
        for gig in (j for j in jobs if j.get('kind') == 'gig'):
            gig_pay = economy.weekly_to_monthly(gig.get('weekly_pay'))
            if gig_pay > 0:
                BalanceService.add_balance(user_id=uid, amount=gig_pay, reason=f"Gig: {gig.get('title')}", category='gig')
                get_summary(uid).credit(gig_pay, f"Gig: {gig.get('title')}")


def _charge_loans(scope, profiles_map, get_summary):
    """
    Loan instalments, taken straight from the borrower's account.

    Friend (P2P) loans are collected first, so a friend who lends you money is
    paid before the bank. If you're short, whatever you have goes towards the
    instalment; the rest is missed with a 5% late fee on the shortfall.
    """
    liabilities_data = scope.filter(supabase.table('liabilities').select('*').gt('remaining_balance', 0), 'user_id').execute()
    rows = sorted(liabilities_data.data or [], key=lambda l: 0 if l.get('liability_type') == 'p2p_loan' else 1)
    for liability in rows:
        user_id = liability['user_id']
        if not scope.includes(user_id):
            continue
        liability_id = liability['id']
        monthly_payment = Decimal(str(liability.get('monthly_payment', 0)))
        if monthly_payment <= 0:
            continue

        summ = get_summary(user_id)
        remaining = Decimal(str(liability['remaining_balance']))
        monthly_payment = min(monthly_payment, remaining)  # never overcharge the final instalment
        name = liability.get('name') or 'Loan'
        is_p2p = liability.get('liability_type') == 'p2p_loan' and liability.get('p2p_loan_id')

        available = max(Decimal('0'), BalanceService.get_current_balance(user_id))
        paid = min(available, monthly_payment).quantize(Decimal('0.01'))
        short = (monthly_payment - paid).quantize(Decimal('0.01'))

        if paid > 0:
            BalanceService.subtract_balance(
                user_id=user_id, amount=paid,
                reason=f"Monthly Loan Payment: {name}", category='loan_payment',
            )
            summ.debit(paid, name if short <= 0 else f"{name} (part)")
        penalty = Decimal('0')
        if short > 0:
            penalty = (short * Decimal('0.05')).quantize(Decimal('0.01'))
            _adjust_credit_score(profiles_map, user_id, CREDIT_MISSED_PAYMENT)
            logger.warning(f"User {user_id} was ${short} short on loan {liability_id}. Late fee ${penalty}.")
            summ.missed(
                short, f"Missed: {name} (+${penalty:,.2f} late fee)",
                f"⚠️ Missed ${short:,.2f} of {name} +${penalty:,.2f} late fee, credit score {CREDIT_MISSED_PAYMENT}",
            )
        else:
            _adjust_credit_score(profiles_map, user_id, CREDIT_ON_TIME_PAYMENT)

        new_bal = remaining - paid + penalty
        if new_bal <= 0:
            supabase.table('liabilities').delete().eq('id', liability_id).execute()
            if liability.get('bank_loan_id'):
                supabase.table('bank_loans').update({'status': 'completed'}).eq('id', liability['bank_loan_id']).execute()
        else:
            supabase.table('liabilities').update({
                'remaining_balance': float(new_bal),
                'remaining_term': max(0, (liability.get('remaining_term') or 1) - (1 if short <= 0 else 0)),
            }).eq('id', liability_id).execute()

        # P2P: the lender gets whatever was collected; keep the record in sync.
        if is_p2p:
            try:
                p2p_res = fetch_one(supabase.table('p2p_loans').select('*').eq('id', liability['p2p_loan_id']))
                if p2p_res.data:
                    loan = p2p_res.data
                    if paid > 0:
                        BalanceService.add_balance(
                            user_id=loan['lender_id'], amount=paid,
                            reason="Friend loan repayment received", category='p2p_repayment',
                        )
                        get_summary(loan['lender_id']).credit(paid, 'Friend loan repayment' if short <= 0 else 'Friend loan repayment (part)')
                    supabase.table('p2p_loans').update({
                        'remaining_balance': float(max(0, new_bal)),
                        'status': 'completed' if new_bal <= 0 else 'active',
                        'payments_made': int(loan.get('payments_made') or 0) + (1 if short <= 0 else 0),
                        'payments_missed': int(loan.get('payments_missed') or 0) + (1 if short > 0 else 0),
                    }).eq('id', loan['id']).execute()
                    if short > 0:
                        _tell_lender_short(loan, user_id, paid, short)
            except Exception as e:
                logger.error(f"Error handling P2P lender credit for loan {liability_id}: {e}")


def _tell_lender_short(loan, borrower_id, paid, short):
    try:
        who = supabase.table('profiles').select('username').eq('user_id', str(borrower_id)).limit(1).execute().data
        name = (who[0] if who else {}).get('username', 'Your borrower')
        ExpoPushService.send_notification_to_user(
            supabase_client=supabase, user_id=loan['lender_id'],
            title='💸 A friend loan came up short',
            body=f"{name} paid ${paid:,.2f} and missed ${short:,.2f}. A 5% late fee was added to what they owe you.",
            notification_type='social', data={'screen': '/banking'},
        )
    except Exception as e:
        logger.warning(f"Lender short-payment push failed: {e}")


def _charge_maintenance(scope, get_summary):
    """
    Lifestyle items: running costs (fuel, insurance, crew...), service bills,
    lease income for items rented out, and, on game time, a month of wear.
    """
    player_liabs = scope.filter(
        supabase.table('player_liabilities').select('*, liability_items(*)').eq('is_active', True), 'player_id'
    ).execute()
    for pliab in player_liabs.data or []:
        user_id = pliab['player_id']
        if not scope.includes(user_id):
            continue
        item = economy.item_of(pliab)
        name = item.get('name') or 'Luxury Item'
        summ = get_summary(user_id)
        months = int(pliab.get('months_owned') or 0) + (1 if scope.only_user else 0)

        # Lease income first: it helps pay this month's bills.
        income, booked = economy.lease_income(pliab)
        if income > 0:
            BalanceService.add_balance(user_id=user_id, amount=income, reason=f"Lease income: {name}", category='lease_income')
            summ.credit(income, f"{name} leased out", note=f"{int(booked * 100)}% booked")

        costs = economy.running_costs(pliab)
        service = economy.service_due(pliab, months)
        bills = costs + ([('Service', service)] if service > 0 else [])
        total = sum((c for _, c in bills), Decimal('0'))
        note = ' · '.join(f"{label} ${amt:,.0f}" for label, amt in bills)
        if total > 0:
            if BalanceService.get_current_balance(user_id) >= total:
                BalanceService.subtract_balance(user_id=user_id, amount=total, reason=f"Running costs: {name}", category='lifestyle')
                summ.debit(total, f"{name} running costs", note=note)
            else:
                logger.warning(f"User {user_id} missed running costs for {pliab['id']}.")
                summ.missed(total, f"Missed: {name} running costs", f"⚠️ Missed {name} running costs (${total:,.2f})", note=note)

        if scope.only_user:  # game time: a month of wear (calendar players get the monthly cron)
            supabase.table('player_liabilities').update({
                'current_value': float(economy.depreciate(pliab)), 'months_owned': months,
            }).eq('id', pliab['id']).execute()


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


def _run_homes(scope, get_summary):
    """Upkeep on homes players own, rent from homes they let out, and value growth."""
    from app.game import homes
    rows = scope.filter(supabase.table('player_homes').select('player_id').eq('is_active', True), 'player_id').execute().data or []
    for uid in sorted({str(r['player_id']) for r in rows}):
        if not scope.includes(uid):
            continue
        try:
            homes.run_month(uid, get_summary(uid))
        except Exception as e:
            logger.error(f"Homes month failed for {uid}: {e}")


def _roommate_rent(scope, get_summary, game_years=0.0):
    """
    On the roommate's month they pay the leaseholder their share of the rent
    and of the home bills (electricity, water, Wi-Fi).
    """
    arrangements = scope.filter(supabase.table('roommates').select('*').eq('status', 'active'), 'roommate_id').execute()
    for arr in arrangements.data or []:
        mate, holder = str(arr['roommate_id']), str(arr['leaseholder_id'])
        if not scope.includes(mate):
            continue
        rental = supabase.table('player_rentals').select('*, rental_properties(*)') \
            .eq('player_id', holder).eq('is_active', True).limit(1).execute().data
        if not rental:
            # The leaseholder moved out: the arrangement is over.
            supabase.table('roommates').update({'status': 'ended', 'ended_at': datetime.now(timezone.utc).isoformat()}) \
                .eq('id', arr['id']).execute()
            continue
        rental = rental[0]
        place = (rental.get('rental_properties') or {}).get('name') or 'the flat'
        part = Decimal(str(arr.get('rent_share') or 0.5))
        share = (Decimal(str(rental.get('monthly_rent') or 0)) * part).quantize(Decimal('0.01'))
        bills = economy.home_bills(rental, game_years)
        bill_share = (sum(bills.values(), Decimal('0')) * part).quantize(Decimal('0.01'))
        summ = get_summary(mate)
        for amount, label, holder_label, note in (
            (share, f"Rent share: {place}", "Roommate's rent share", None),
            (bill_share, f"Bills share: {place}", "Roommate's share of bills",
             ' · '.join(f"{k} ${(v * part):,.0f}" for k, v in bills.items())),
        ):
            if amount <= 0:
                continue
            if BalanceService.get_current_balance(mate) < amount:
                summ.missed(amount, f"Missed {label[0].lower()}{label[1:]}", f"⚠️ Missed {label} (${amount:,.2f})", note=note)
                continue
            BalanceService.subtract_balance(mate, amount, label, category='rent' if 'Rent' in label else 'bills')
            BalanceService.add_balance(holder, amount, holder_label, category='rent' if 'Rent' in label else 'bills')
            summ.debit(amount, label, note=note)
            get_summary(holder).credit(amount, holder_label)


def _years_since(created_at_str, now):
    if not created_at_str:
        return 0.0
    try:
        time_part = created_at_str.split('+')[0]
        created_dt = datetime.strptime(time_part[:19], "%Y-%m-%dT%H:%M:%S")
        return max(0.0, (now - created_dt).days / 365.25)
    except Exception:
        return 0.0


def _charge_living_costs(scope, profiles_map, get_summary, game_years):
    """
    Groceries, plus the bills for where you live:
    * renting: electricity, water and Wi-Fi for your home (a roommate pays you
      their share on their own month);
    * living in a home you own: that home's electricity, water and Wi-Fi;
    * a roommate: groceries only (bills go to the leaseholder);
    * living with your parents: groceries and a contribution at home.
    Roommates save 20% on groceries by cooking together. Prices rise 5% a game
    year (calendar years for players not on game time).
    """
    now = datetime.utcnow()
    uids = list(profiles_map)
    rentals = scope.filter(supabase.table('player_rentals').select('*, rental_properties(*)').eq('is_active', True), 'player_id').execute().data or []
    rental_of = {str(r['player_id']): r for r in rentals}
    arrangements = supabase.table('roommates').select('leaseholder_id, roommate_id').eq('status', 'active').execute().data or []
    holders = {str(a['leaseholder_id']) for a in arrangements}
    mates = {str(a['roommate_id']) for a in arrangements}
    from app.game import homes
    owned_rows = scope.filter(supabase.table('player_homes').select('player_id, home_id').eq('is_active', True).eq('lives_in', True), 'player_id').execute().data or []
    own_listing = homes._listings({str(r['home_id']) for r in owned_rows})
    owner_home = {str(r['player_id']): own_listing.get(str(r['home_id'])) for r in owned_rows if own_listing.get(str(r['home_id']))}
    multipliers = _mission_multipliers(scope)

    for user_id in uids:
        profile = profiles_map[user_id]
        uid = str(user_id)
        years = game_years if scope.only_user else _years_since(profile.get('created_at'), now)
        income = profile.get('monthly_income') or 0
        summ = get_summary(user_id)
        lines = []
        food = economy.groceries(income, years, shared=uid in holders or uid in mates)
        if food > 0:
            lines.append(('Groceries', food, 'Cooking with your roommate: 20% cheaper' if uid in holders or uid in mates else None))
        if uid in rental_of:
            bills = economy.home_bills(rental_of[uid], years)
            note = ' · '.join(f"{k} ${v:,.0f}" for k, v in bills.items())
            if uid in holders:
                note += ' (your roommate pays you half)'
            lines.append(('Electricity, water & Wi-Fi', sum(bills.values(), Decimal('0')), note))
        elif uid in owner_home:
            listing = owner_home[uid]
            bills = homes.bills(listing, years)
            note = ' · '.join(f"{k} ${v:,.0f}" for k, v in bills.items())
            lines.append(('Electricity, water & Wi-Fi', sum(bills.values(), Decimal('0')), f"{note} ({listing.get('name')}, your own place)"))
        elif uid not in mates:
            home = economy.parents_contribution(income, years)
            if home > 0:
                lines.append(('Chipping in at home', home, 'Living with your parents'))

        expense_mult = multipliers.get(uid, (Decimal('1'), Decimal('1')))[1]
        for label, cost, note in lines:
            if expense_mult != 1:
                cost = (cost * expense_mult).quantize(Decimal('0.01'))
                note = f"{note + ' · ' if note else ''}mission: {expense_mult * 100:.0f}% of usual"
            if cost <= 0:
                continue
            if BalanceService.get_current_balance(user_id) >= cost:
                BalanceService.subtract_balance(user_id=user_id, amount=cost, reason=label, category='living_costs')
                summ.debit(cost, label, note=note)
            else:
                logger.warning(f"User {user_id} missed {label}.")
                summ.missed(cost, f"Missed: {label.lower()}", f"⚠️ Missed {label} (${cost:,.2f})", note=note)


def _pay_asset_income(scope, get_summary):
    """Rent, dividends and profit share from owned assets; on game time, property and businesses grow."""
    assets_res = supabase.table('assets').select('name, monthly_income, category, risk_level').execute()
    catalog = {a['name']: a for a in assets_res.data or []}
    income_map = {n: Decimal(str(a.get('monthly_income') or 0)) for n, a in catalog.items()}

    user_assets = scope.filter(supabase.table('user_assets').select('*'), 'user_id').execute()
    for ua in user_assets.data or []:
        user_id = ua['user_id']
        if not scope.includes(user_id):
            continue
        name = ua['name']
        total_income = income_map.get(name, Decimal('0')) * Decimal(str(ua.get('quantity', 1)))
        listing = catalog.get(name) or {}
        note = None
        if total_income > 0 and economy.is_business(listing.get('category') or ua.get('asset_type')):
            # Businesses have good and bad months.
            swing = economy.profit_swing(listing.get('risk_level'))
            total_income = economy.money(total_income * swing)
            note = f"{economy.month_mood(swing)} · {int(swing * 100)}% of usual"
        if total_income > 0:
            BalanceService.add_balance(user_id=user_id, amount=total_income, reason=f"Monthly Asset Income: {name}", category='asset_income')
            label = f"{name} profit" if note else f"{name} yield"
            get_summary(user_id).credit(total_income, label, note=note)
        if scope.only_user and economy.appreciates(ua.get('asset_type')):
            value, held = economy.appreciate(ua)
            supabase.table('user_assets').update({'value': float(value), 'months_held': held}).eq('id', ua['id']).execute()


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


_KNOWN_METRICS = {'net_worth', 'monthly_income', 'credit_score', 'asset_value',
                  'business_value', 'passive_income', 'debt_ratio'}

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


def _mission_metrics(player_id, profile):
    """
    Every goal metric the schema allows, for one player. Previously only
    net_worth / monthly_income / credit_score were evaluated, so a mission
    with an asset_value, debt_ratio, passive_income or business_value goal
    could never be completed. 'custom' has no formula engine and stays unmet.
    """
    metrics = {k: profile.get(k) for k in ('net_worth', 'monthly_income', 'credit_score')}
    holdings = supabase.table('user_assets').select('name, asset_type, value, quantity') \
        .eq('user_id', player_id).execute().data or []
    metrics['asset_value'] = sum(Decimal(str(h.get('value') or 0)) for h in holdings)
    metrics['business_value'] = sum(Decimal(str(h.get('value') or 0)) for h in holdings
                                    if h.get('asset_type') == 'business')
    names = list({h['name'] for h in holdings if h.get('name')})
    yields = {}
    if names:
        yields = {a['name']: Decimal(str(a.get('monthly_income') or 0)) for a in
                  (supabase.table('assets').select('name, monthly_income').in_('name', names).execute().data or [])}
    metrics['passive_income'] = sum(yields.get(h.get('name'), Decimal('0')) * Decimal(str(h.get('quantity') or 1))
                                    for h in holdings)
    debts = supabase.table('liabilities').select('monthly_payment') \
        .eq('user_id', player_id).gt('remaining_balance', 0).execute().data or []
    income = Decimal(str(profile.get('monthly_income') or 0))
    payments = sum(Decimal(str(d.get('monthly_payment') or 0)) for d in debts)
    # debt-to-income; with no income any debt is "infinitely" bad, none is 0
    metrics['debt_ratio'] = (payments / income) if income > 0 else (Decimal('999') if payments else Decimal('0'))
    return metrics


def _criterion_met(criterion, profile):
    metric = criterion.get('metric')
    value = profile.get(metric) if metric in _KNOWN_METRICS else None
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

        player_id = pm['player_id']
        prof_res = supabase.table('profiles').select('net_worth, monthly_income, credit_score') \
            .eq('user_id', player_id).limit(1).execute()
        if not prof_res.data:
            continue
        profile = prof_res.data[0]
        metrics = _mission_metrics(player_id, profile)
        criteria = supabase.table('mission_success_criteria').select('*') \
            .eq('mission_id', pm['mission_id']).execute().data or []

        # Refresh the goal tracking EVERY month so the app's progress bars move
        # (it was only written when the mission ended).
        met = 0
        for c in criteria:
            ok, value = _criterion_met(c, metrics)
            met += int(ok)
            supabase.table('player_mission_success_tracking').update({
                'current_value': float(value or 0), 'is_met': ok,
            }).eq('player_mission_id', pm['id']).eq('criteria_id', c['id']).execute()

        if next_month <= duration:
            supabase.table('player_mission_progress').update({'current_month': next_month}) \
                .eq('id', pm['id']).eq('is_active', True).execute()
            continue

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
