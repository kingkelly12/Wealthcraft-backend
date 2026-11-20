from app import db, supabase
import os
from datetime import datetime, timedelta
from app.services.balance_service import BalanceService
from app.services.push_notification_service import ExpoPushService
from decimal import Decimal
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_monthly_deductions():
    """
    End of Month Processing Job.
    - Deducts monthly loan payments (Bank and P2P) from liabilities table
    - Credits P2P lenders
    - Deducts player liabilities maintenance (luxury items)
    - Deducts rent for user rentals
    - Credits asset monthly income for user assets
    - Sends a consolidated push notification with a summary of deductions and income
    """
    logger.info("Starting End of Month Processing cycle...")

    # Run at most once per calendar month, even if the scheduler retries or
    # someone calls the endpoint twice (double-charging rent/loans otherwise).
    from jobs.run_guard import claim_monthly_run
    period = claim_monthly_run('monthly_processing')
    if not period:
        logger.warning("Monthly processing already ran this month; skipping.")
        return {'success': True, 'skipped': True}

    notifications_to_send = []
    summary_by_user = {}

    def get_summary(uid):
        if uid not in summary_by_user:
            summary_by_user[uid] = {
                'expenses': Decimal('0'),
                'income': Decimal('0'),
                'details': []
            }
        return summary_by_user[uid]

    logger.info("Fetching profiles data for dynamic calculations...")
    try:
        profiles_res = supabase.table('profiles').select('user_id, username, monthly_income, base_monthly_income, credit_score, created_at, sanity').execute()
        profiles_map = {p['user_id']: p for p in profiles_res.data}
    except Exception as e:
        logger.error(f"Error fetching profiles: {e}")
        profiles_map = {}

    # --- 0. Payday: job salaries (annual / 12) + permanent income boosts ---
    # Nothing paid salaries before: players only ever got a lump sum on hire,
    # while living costs below were charged every month.
    logger.info("Paying salaries...")
    try:
        jobs_res = supabase.table('jobs').select('user_id, title, salary').eq('is_current', True).execute()
        pay_by_user = {}
        for job in jobs_res.data or []:
            pay_by_user.setdefault(job['user_id'], []).append(job)
        for uid, profile in profiles_map.items():
            user_jobs = pay_by_user.get(uid, [])
            salary = sum(Decimal(str(j.get('salary') or 0)) for j in user_jobs) / 12
            boosts = Decimal(str(profile.get('base_monthly_income') or 0))
            pay = (salary + boosts).quantize(Decimal('0.01'))
            if pay <= 0:
                continue
            BalanceService.add_balance(user_id=uid, amount=pay, reason="Monthly salary", category='salary')
            summ = get_summary(uid)
            summ['income'] += pay
            summ['details'].append(f"+${pay:,.2f} Salary")
    except Exception as e:
        logger.error(f"Error paying salaries: {e}")

    # --- 1. Process Liabilities (Loans) ---
    logger.info("Processing loans (Bank & P2P)...")
    try:
        # Fetch active liabilities (remaining_balance > 0)
        # Note: Some older records might use remaining_balance, others might be None
        liabilities_data = supabase.table('liabilities').select('*').gt('remaining_balance', 0).execute()
        for liability in liabilities_data.data:
            user_id = liability['user_id']
            liability_id = liability['id']
            monthly_payment = Decimal(str(liability.get('monthly_payment', 0)))
            if monthly_payment <= 0:
                continue

            current_balance = BalanceService.get_current_balance(user_id)
            summ = get_summary(user_id)

            remaining = Decimal(str(liability['remaining_balance']))
            monthly_payment = min(monthly_payment, remaining)  # never overcharge the final instalment

            if current_balance >= monthly_payment:
                # Deduct
                BalanceService.subtract_balance(
                    user_id=user_id,
                    amount=monthly_payment,
                    reason=f"Monthly Loan Payment: {liability.get('name')}",
                    category='loan_payment',
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

                # If P2P Loan, credit lender and update P2P table sync
                if liability.get('liability_type') == 'p2p_loan' and liability.get('p2p_loan_id'):
                    try:
                        p2p_loan_id = liability['p2p_loan_id']
                        p2p_res = supabase.table('p2p_loans').select('*').eq('id', p2p_loan_id).single().execute()
                        if p2p_res.data:
                            lender_id = p2p_res.data['lender_id']
                            # Credit lender
                            BalanceService.add_balance(
                                user_id=lender_id,
                                amount=monthly_payment,
                                reason=f"P2P Loan payment received",
                                category='p2p_repayment',
                            )
                            lender_summ = get_summary(lender_id)
                            lender_summ['income'] += monthly_payment
                            lender_summ['details'].append(f"+${monthly_payment:,.2f} P2P Repayment")

                            p2p_status = 'active'
                            if new_bal <= 0:
                                p2p_status = 'completed'
                            supabase.table('p2p_loans').update({
                                'remaining_balance': float(max(0, new_bal)),
                                'status': p2p_status,
                            }).eq('id', p2p_loan_id).execute()
                    except Exception as e:
                        logger.error(f"Error handling P2P lender credit for loan {liability_id}: {e}")

                # Update Borrower Summary
                summ['expenses'] += monthly_payment
                summ['details'].append(f"-${monthly_payment:,.2f} {liability.get('name')}")
            else:
                # Missed payment: 5% late fee added to the debt and a credit hit.
                # (Previously the penalty was computed and then thrown away, so
                # skipping payments had no consequence at all.)
                penalty = (monthly_payment * Decimal('0.05')).quantize(Decimal('0.01'))
                supabase.table('liabilities').update({
                    'remaining_balance': float(remaining + penalty),
                }).eq('id', liability_id).execute()
                _adjust_credit_score(profiles_map, user_id, CREDIT_MISSED_PAYMENT)
                logger.warning(f"User {user_id} missed loan payment for {liability_id}. Late fee ${penalty}.")
                summ['details'].append(f"⚠️ Missed {liability.get('name')} (${monthly_payment:,.2f}) +${penalty:,.2f} late fee, credit score {CREDIT_MISSED_PAYMENT}")
    except Exception as e:
        logger.error(f"Error processing liabilities: {e}")

    # --- 2. Process Player Liabilities Maintenance (Luxury Items) ---
    logger.info("Processing maintenance for luxury items...")
    try:
        player_liabs = supabase.table('player_liabilities').select('*, liability_items(*)').eq('is_active', True).execute()
        for pliab in player_liabs.data:
            user_id = pliab['player_id']
            cost = Decimal(str(pliab.get('monthly_cost', 0)))
            if cost <= 0:
                continue

            # Identify name
            item_data = pliab.get('liability_items')
            if isinstance(item_data, list) and len(item_data) > 0:
                item_data = item_data[0]
            name = item_data.get('name', 'Luxury Item') if item_data else 'Luxury Item'

            summ = get_summary(user_id)
            current_balance = BalanceService.get_current_balance(user_id)
            if current_balance >= cost:
                BalanceService.subtract_balance(
                    user_id=user_id,
                    amount=cost,
                    reason=f"Maintenance Cost: {name}",
                    category='lifestyle',
                )
                summ['expenses'] += cost
                summ['details'].append(f"-${cost:,.2f} {name} maintenance")
            else:
                logger.warning(f"User {user_id} missed maintenance for {pliab['id']}.")
                summ['details'].append(f"⚠️ Missed {name} maintenance (${cost:,.2f})")
    except Exception as e:
        logger.error(f"Error processing luxury maintenance: {e}")

    # --- 3. Process Rent Deductions ---
    logger.info("Processing rent deductions...")
    try:
        active_rentals = supabase.table('player_rentals').select('*, rental_properties(*)').eq('is_active', True).execute()
        for rental in active_rentals.data:
            user_id = rental['player_id']
            rent = Decimal(str(rental.get('monthly_rent', 0)))
            if rent <= 0:
                continue

            prop_data = rental.get('rental_properties')
            name = prop_data.get('name', 'Rent') if prop_data else 'Rent'

            summ = get_summary(user_id)
            current_balance = BalanceService.get_current_balance(user_id)
            if current_balance >= rent:
                BalanceService.subtract_balance(
                    user_id=user_id,
                    amount=rent,
                    reason=f"Monthly Rent: {name}",
                    category='rent',
                )
                summ['expenses'] += rent
                summ['details'].append(f"-${rent:,.2f} {name}")
            else:
                logger.warning(f"User {user_id} missed rent for {rental['id']}.")
                summ['details'].append(f"⚠️ Missed {name} (${rent:,.2f})")
    except Exception as e:
        logger.error(f"Error processing rent: {e}")

    # --- 4. Process Base Living Costs (Food, Utilities, WiFi) ---
    logger.info("Processing base living costs with inflation...")
    try:
        current_date_dt = datetime.utcnow()
        for user_id, profile in profiles_map.items():
            monthly_income = Decimal(str(profile.get('monthly_income') or 0))
            if monthly_income <= 0:
                continue
                
            base_cost = monthly_income * Decimal('0.20')
            
            created_at_str = profile.get('created_at')
            years_active = 0.0
            if created_at_str:
                try:
                    # Parse ISO string safely
                    time_part = created_at_str.split('+')[0]
                    if '.' in time_part:
                        created_dt = datetime.strptime(time_part[:19], "%Y-%m-%dT%H:%M:%S")
                    else:
                        created_dt = datetime.strptime(time_part, "%Y-%m-%dT%H:%M:%S")
                    days_active = (current_date_dt - created_dt).days
                    years_active = max(0.0, days_active / 365.25)
                except Exception:
                    pass
            
            # Cap years active reasonably
            years_active = min(float(years_active), 20.0)
            
            inflation_multiplier = Decimal(str((1.05) ** years_active))
            actual_living_cost = base_cost * inflation_multiplier
            
            summ = get_summary(user_id)
            current_balance = BalanceService.get_current_balance(user_id)
            
            if current_balance >= actual_living_cost:
                BalanceService.subtract_balance(
                    user_id=user_id,
                    amount=actual_living_cost,
                    reason="Living Costs (Food & WiFi)",
                    category='living_costs',
                )
                summ['expenses'] += actual_living_cost
                summ['details'].append(f"-${actual_living_cost:,.2f} Living Costs")
            else:
                logger.warning(f"User {user_id} missed living costs.")
                summ['details'].append(f"⚠️ Missed Living Costs (${actual_living_cost:,.2f})")
    except Exception as e:
        logger.error(f"Error processing living costs: {e}")

    # --- 5. Process Asset Income (Rental / Dividend) ---
    logger.info("Processing asset monthly incomes...")
    try:
        # Fetch base assets lookup map
        assets_res = supabase.table('assets').select('name, monthly_income').execute()
        income_map = {}
        for a in assets_res.data:
            income_map[a['name']] = Decimal(str(a.get('monthly_income', 0)))

        user_assets = supabase.table('user_assets').select('*').execute()
        for ua in user_assets.data:
            user_id = ua['user_id']
            name = ua['name']
            qty = Decimal(str(ua.get('quantity', 1)))
            base_income = income_map.get(name, Decimal('0'))
            
            total_income = base_income * qty
            if total_income > 0:
                BalanceService.add_balance(
                    user_id=user_id,
                    amount=total_income,
                    reason=f"Monthly Asset Income: {name}",
                    category='asset_income',
                )
                summ = get_summary(user_id)
                summ['income'] += total_income
                summ['details'].append(f"+${total_income:,.2f} {name} Yield")
    except Exception as e:
        logger.error(f"Error processing asset income: {e}")

    # --- 6. Batch Send Notifications & Evaluate Sanity Penalties ---
    from app.services.ai_service import AIService
    from app.services.mentor_service import MentorService
    import uuid

    logger.info(f"Checking financial stress and queueing notifications for {len(summary_by_user)} users...")
    for uid, data in summary_by_user.items():
        if data['expenses'] == 0 and data['income'] == 0 and not data['details']:
            continue
            
        profile = profiles_map.get(uid, {})
        monthly_income = Decimal(str(profile.get('monthly_income') or 0))
        current_sanity = int(profile.get('sanity', 100))
        
        is_stressed = False
        ai_stress_message = None
        
        if monthly_income > 0 and data['expenses'] > (monthly_income * Decimal('0.60')):
            is_stressed = True
            new_sanity = max(0, current_sanity - 10)
            
            # AI Analysis for Stress
            try:
                metrics = MentorService.analyze_player_finances(uuid.UUID(uid))
                metrics['sanity'] = current_sanity
                stress_analysis = AIService.analyze_financial_stress(profile.get('username', 'Player'), metrics)
                ai_stress_message = stress_analysis.get('message')
            except Exception as e:
                logger.error(f"Failed to generate AI stress message for {uid}: {e}")

            try:
                supabase.rpc('adjust_sanity', {'p_user_id': uid, 'p_delta': -10}).execute()
            except Exception as e:
                logger.error(f"Failed to deduct sanity for {uid}: {e}")
            
        net_change = data['income'] - data['expenses']
        
        if is_stressed:
            title = "🚨 Financial Stress!"
            body = f"{ai_stress_message or 'Expenses exceeded 60% of income. Sanity dropped (-10).'}\n\nNet: {'+' if net_change > 0 else '-'}${abs(net_change):,.2f}\n\n" + "\n".join(data['details'])
        else:
            title = "💰 End of Month Summary"
            if net_change > 0:
                body = f"You gained a net +${net_change:,.2f} this month! \n\n" + "\n".join(data['details'])
            else:
                body = f"You had a net -${abs(net_change):,.2f} this month. \n\n" + "\n".join(data['details'])

        # Truncate if too long
        if len(body) > 200:
            body = body[:197] + "..."

        notifications_to_send.append({
            'user_id': uid,
            'title': title,
            'body': body,
            'data': {
                'type': 'financial_move',
                'screen': '/banking'
            }
        })

    if notifications_to_send:
        # Batch in chunks of 50 just in case
        chunk_size = 50
        for i in range(0, len(notifications_to_send), chunk_size):
            chunk = notifications_to_send[i:i + chunk_size]
            ExpoPushService.send_notifications_to_users(
                supabase_client=supabase,
                user_notifications=chunk,
                notification_type='financial_move'
            )
        logger.info(f"Batched {len(notifications_to_send)} end of month notifications.")

    # --- 7. Advance missions one month; finish the ones that reached their end ---
    try:
        _advance_missions()
    except Exception as e:
        logger.error(f"Error advancing missions: {e}")

    logger.info("End of Month Processing cycle complete.")
    return {'success': True, 'period': period}


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


def _advance_missions():
    """
    Missions never progressed before: nothing advanced current_month or wrote
    mission_completion_results, so every mission stayed on month 1 forever.
    """
    active = supabase.table('player_mission_progress') \
        .select('*, integrated_missions!mission_id(name, duration_months, completion_reward)') \
        .eq('is_active', True).execute()

    for pm in active.data or []:
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
        now = datetime.utcnow().isoformat()
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

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        process_monthly_deductions()
