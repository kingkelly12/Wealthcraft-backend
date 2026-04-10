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

            if current_balance >= monthly_payment:
                # Deduct
                BalanceService.subtract_balance(
                    user_id=user_id,
                    amount=monthly_payment,
                    reason=f"Monthly Loan Payment: {liability.get('name')}"
                )
                
                new_bal = Decimal(str(liability['remaining_balance'])) - monthly_payment
                
                # Update liability
                supabase.table('liabilities').update({
                    'remaining_balance': float(max(0, new_bal)),
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', liability_id).execute()

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
                                reason=f"P2P Loan payment received"
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
                                'updated_at': datetime.utcnow().isoformat()
                            }).eq('id', p2p_loan_id).execute()
                    except Exception as e:
                        logger.error(f"Error handling P2P lender credit for loan {liability_id}: {e}")

                # Update Borrower Summary
                summ['expenses'] += monthly_payment
                summ['details'].append(f"-${monthly_payment:,.2f} {liability.get('name')}")
            else:
                # Provide a notification log for missing logic, applying penalty
                penalty = monthly_payment * Decimal('0.05')
                logger.warning(f"User {user_id} missed loan payment for {liability_id}. Applied penalty.")
                summ['expenses'] += Decimal('0')  # Missed, no deduct
                summ['details'].append(f"⚠️ Missed {liability.get('name')} (${monthly_payment:,.2f})")
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
                    reason=f"Maintenance Cost: {name}"
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
                    reason=f"Monthly Rent: {name}"
                )
                summ['expenses'] += rent
                summ['details'].append(f"-${rent:,.2f} {name}")
            else:
                logger.warning(f"User {user_id} missed rent for {rental['id']}.")
                summ['details'].append(f"⚠️ Missed {name} (${rent:,.2f})")
    except Exception as e:
        logger.error(f"Error processing rent: {e}")

    # --- 4. Process Asset Income (Rental / Dividend) ---
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
                    reason=f"Monthly Asset Income: {name}"
                )
                summ = get_summary(user_id)
                summ['income'] += total_income
                summ['details'].append(f"+${total_income:,.2f} {name} Yield")
    except Exception as e:
        logger.error(f"Error processing asset income: {e}")

    # --- 5. Batch Send Notifications ---
    logger.info(f"Queueing notifications for {len(summary_by_user)} users...")
    for uid, data in summary_by_user.items():
        if data['expenses'] == 0 and data['income'] == 0 and not data['details']:
            continue
            
        net_change = data['income'] - data['expenses']
        title = "💰 End of Month Summary"
        if net_change > 0:
            body = f"You gained a net +${net_change:,.2f} this month! \n" + "\n".join(data['details'])
        else:
            body = f"You had a net -${abs(net_change):,.2f} this month. \n" + "\n".join(data['details'])

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

    logger.info("End of Month Processing cycle complete.")
    return {'success': True}

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        process_monthly_deductions()
