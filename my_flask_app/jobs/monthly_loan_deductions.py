from app import create_app, db
import os
from datetime import datetime, timedelta
from app.services.balance_service import BalanceService
from supabase import create_client
from decimal import Decimal
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_monthly_deductions():
    """
    Process monthly payments for all active bank loans.
    - Deducts monthly payment from user balance
    - Updates next_payment_date for tracking
    - Logs missed payments if user has insufficient funds
    - Sends notifications for payment issues
    """
    app = create_app()
    with app.app_context():
        logger.info(f"Starting monthly deduction job...")
        
        # Fetch all active loans
        try:
            loans = supabase.table('bank_loans').select('*').eq('status', 'active').execute()
        except Exception as e:
            logger.error(f"Error fetching loans: {e}")
            return

        successful_payments = 0
        missed_payments = 0
        errors = 0

        for loan in loans.data:
            user_id = loan['borrower_id']
            loan_id = loan['id']
            monthly_payment = Decimal(str(loan['monthly_payment']))
            
            try:
                # 1. Check if payment is due (check next_payment_date)
                next_payment_date = loan.get('next_payment_date')
                if next_payment_date:
                    next_payment = datetime.fromisoformat(next_payment_date)
                    if datetime.utcnow() < next_payment:
                        logger.info(f"Loan {loan_id} payment not yet due (due: {next_payment_date})")
                        continue
                
                # 2. Check Balance
                current_balance = BalanceService.get_current_balance(user_id)
                
                if current_balance >= monthly_payment:
                    # Payment successful
                    # 3. Deduct from balance
                    BalanceService.subtract_balance(
                        user_id=user_id, 
                        amount=monthly_payment, 
                        reason=f"Monthly Loan Payment: {loan['type']}"
                    )
                    
                    # 4. Update loan with new next_payment_date and total_paid
                    next_payment_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
                    total_paid = Decimal(str(loan.get('total_paid', 0))) + monthly_payment
                    
                    supabase.table('bank_loans').update({
                        'next_payment_date': next_payment_date,
                        'total_paid': float(total_paid),
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', loan_id).execute()
                    
                    logger.info(f"✅ Processed payment of ${monthly_payment} for user {user_id} on loan {loan_id}")
                    
                    # 5. Send success notification
                    try:
                        from app.services.push_notification_service import ExpoPushService
                        loan_type = loan.get('type', 'loan')
                        ExpoPushService.send_notification_to_user(
                            supabase_client=supabase,
                            user_id=user_id,
                            title='💳 Loan Payment Processed',
                            body=f'Monthly payment of ${monthly_payment} for {loan_type} processed successfully.',
                            notification_type='financial_move',
                            data={
                                'type': 'loan_payment',
                                'loan_id': loan_id,
                                'amount': float(monthly_payment),
                                'screen': '/loans'
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send payment notification: {e}")
                    
                    successful_payments += 1
                    
                else:
                    # Payment failed - insufficient funds
                    logger.warning(f"⚠️  User {user_id} insufficient funds for loan {loan_id}. Required: ${monthly_payment}, Available: ${current_balance}")
                    
                    # Log missed payment
                    supabase.table('missed_payments').insert({
                        'user_id': user_id,
                        'loan_id': loan_id,
                        'missed_amount': float(monthly_payment),
                        'required_balance': float(monthly_payment),
                        'current_balance': float(current_balance),
                        'date': datetime.utcnow().isoformat(),
                        'status': 'pending'
                    }).execute()
                    
                    # Apply late penalty (e.g., 5% of monthly payment)
                    penalty = monthly_payment * Decimal('0.05')
                    
                    # Update loan with penalty
                    new_penalty_total = Decimal(str(loan.get('total_interest', 0))) + penalty
                    supabase.table('bank_loans').update({
                        'total_interest': float(new_penalty_total),
                        'status': 'delinquent',
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', loan_id).execute()
                    
                    logger.warning(f"Applied ${penalty} penalty for missed payment")
                    
                    # Send alert notification
                    try:
                        from app.services.push_notification_service import ExpoPushService
                        loan_type = loan.get('type', 'loan')
                        ExpoPushService.send_notification_to_user(
                            supabase_client=supabase,
                            user_id=user_id,
                            title='⚠️ Loan Payment Failed',
                            body=f'Insufficient funds for {loan_type} payment. Penalty of ${penalty} applied. Current balance: ${current_balance}',
                            notification_type='financial_alert',
                            data={
                                'type': 'missed_payment',
                                'loan_id': loan_id,
                                'amount': float(monthly_payment),
                                'penalty': float(penalty),
                                'screen': '/loans'
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send missed payment notification: {e}")
                    
                    missed_payments += 1
                    
            except Exception as e:
                db.session.rollback()
                errors += 1
                logger.error(f"Error processing loan {loan_id}: {e}")
                continue

        logger.info(
            f"Monthly deduction job completed. "
            f"Successful: {successful_payments}, Missed: {missed_payments}, Errors: {errors}"
        )
        
        return {
            'successful_payments': successful_payments,
            'missed_payments': missed_payments,
            'errors': errors
        }

if __name__ == "__main__":
    process_monthly_deductions()
