"""
Loan management routes
Handles loan applications with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.mentor_service import MentorService
from app.schemas.loan_schema import LoanApplicationRequest
from app import supabase
from decimal import Decimal
import uuid
from datetime import datetime, timedelta
from app.services.push_notification_service import ExpoPushService

loan_bp = Blueprint('loan', __name__)


@loan_bp.route('/available/', methods=['GET'])
def get_available_loans():
    """
    Get available bank loan products
    Returns a list of loans where borrower_id is NULL (templates)
    """
    try:
        response = supabase.table('bank_loans').select('*').is_('borrower_id', 'null').execute()
        
        return jsonify({
            'success': True,
            'data': response.data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500



@loan_bp.route('/apply/', methods=['POST'])
@require_auth
def apply_for_loan(current_user_id: str):
    """
    Apply for a bank loan
    
    This endpoint:
    1. Validates the request
    2. Gets loan product details
    3. Adds loan amount to balance
    4. Creates liability record
    5. Logs transaction
    """
    try:
        # Validate request
        data = LoanApplicationRequest(**request.json)
        
        # 1. Get loan product details
        # Note: Assuming there's a loan_products table or we use the data from request
        # For now, we'll fetch from a hypothetical bank_loans table
        loan_response = supabase.table('bank_loans').select('*').eq('id', str(data.loan_id)).single().execute()
        
        if not loan_response.data:
            return jsonify({
                'success': False,
                'error': 'LOAN_NOT_FOUND',
                'message': f'Loan product {data.loan_id} not found'
            }), 404
        
        loan = loan_response.data
        loan_amount = Decimal(str(loan['amount']))
        monthly_payment = Decimal(str(loan.get('monthly_payment', loan_amount * Decimal('0.05'))))
        
        # 2. Create a specific bank_loan record for this user
        user_loan_id = str(uuid.uuid4())
        supabase.table('bank_loans').insert({
            'id': user_loan_id,
            'borrower_id': current_user_id,
            'type': loan['type'],
            'amount': float(loan_amount),
            'interest_rate': float(loan['interest_rate']),
            'term': loan['term'],
            'monthly_payment': float(monthly_payment),
            'total_interest': float(loan['total_interest']),
            'credit_required': loan['credit_required'],
            'status': 'active',
            'collateral': loan['collateral'],
            'funded_at': datetime.utcnow().isoformat(),
            'due_date': (datetime.utcnow() + timedelta(days=int(loan.get('term', 12)) * 30)).isoformat()
        }).execute()

        # 3. Add loan amount to balance
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=loan_amount,
            reason=f"Loan received: {loan.get('type', 'Bank Loan')}"
        )
        
        # 4. Create liability record (for unified view)
        liability_id = str(uuid.uuid4())
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': current_user_id,
            'name': loan.get('type', 'Bank Loan'),
            'liability_type': 'bank_loan',
            'amount': float(loan_amount),
            'remaining_balance': float(loan_amount), # Full amount initially
            'interest_rate': float(loan['interest_rate']) * 100, 
            'monthly_payment': float(monthly_payment),
            'p2p_loan_id': None # Not a P2P loan
        }).execute()
        
        # Notify followers about the loan (push to mentors/observers only)
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='take_loan',
            item_name=loan.get('type', 'Bank'),
            amount=float(loan_amount)
        )
        
        try:
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='take_loan',
                action_data={
                    'amount': float(loan_amount),
                    'interest_rate': float(loan['interest_rate']),
                    'monthly_payment': float(monthly_payment)
                }
            )
            
            if trigger:
                MentorService.send_mentor_message(
                    player_id=current_user_id,
                    mentor_data=trigger,
                    metrics={},
                    supabase_client=supabase
                )
        except Exception as e:
            print(f"Failed to trigger mentor response: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'You have received ${loan_amount:,.2f}.',
            'liability_id': liability_id,
            'bank_loan_id': user_loan_id,
            'new_balance': float(balance_result['new_balance']),
            'loan_amount': float(loan_amount),
            'monthly_payment': float(monthly_payment)
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500

@loan_bp.route('/active/', methods=['GET'])
@require_auth
def get_active_loans(current_user_id: str):
    """
    Get active bank loans for the current user
    """
    try:
        response = supabase.table('bank_loans').select('*').eq('borrower_id', current_user_id).eq('status', 'active').execute()
        
        return jsonify({
            'success': True,
            'data': response.data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@loan_bp.route('/repay/', methods=['POST'])
@loan_bp.route('/repay/<liability_id>/', methods=['POST'])
@require_auth
def repay_loan(current_user_id: str, liability_id: str = None):
    """
    Repay a loan (full or partial payment)
    
    This endpoint:
    1. Validates the loan belongs to the user
    2. Checks if user has sufficient funds
    3. Deducts payment amount from balance
    4. Updates loan remaining balance
    5. If fully paid, marks loan as completed
    6. Logs the transaction
    
    Request body:
    {
        "amount": 1000.00,  // Optional - defaults to monthly_payment
        "loan_id": "..."    // Optional if in URL
    }
    """
    try:
        # Support getting ID from body if not in URL
        if not liability_id:
            data = request.get_json() or {}
            liability_id = data.get('loan_id') or data.get('liability_id')
            
        if not liability_id:
            return jsonify({'success': False, 'error': 'MISSING_ID', 'message': 'Loan ID is required'}), 400

        # 1. Get the loan and verify ownership
        loan_response = supabase.table('liabilities').select('*').eq('id', liability_id).eq('user_id', current_user_id).single().execute()
        
        if not loan_response.data:
            return jsonify({
                'success': False,
                'error': 'LOAN_NOT_FOUND',
                'message': 'Loan not found or does not belong to you'
            }), 404
        
        loan = loan_response.data
        remaining_balance = Decimal(str(loan.get('remaining_balance', loan.get('remaining_amount', loan.get('total_amount', 0)))))
        monthly_payment = Decimal(str(loan.get('monthly_payment', 0)))
        
        # Get payment amount from request or use monthly payment
        request_data = request.get_json() or {}
        payment_amount = Decimal(str(request_data.get('amount', monthly_payment)))
        
        # Cap payment at remaining balance
        if payment_amount > remaining_balance:
            payment_amount = remaining_balance
        
        # 2. Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)
        
        if current_balance < payment_amount:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f'Insufficient funds. You need ${payment_amount} but only have ${current_balance}'
            }), 400
        
        # 3. Deduct payment from balance
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=payment_amount,
            reason=f'Loan payment for {loan.get("name", "loan")}'
        )

        # 4. Update loan status calculations
        new_remaining_balance = remaining_balance - payment_amount
        is_fully_paid = new_remaining_balance <= 0

        # ============ P2P REPAYMENT LOGIC ============
        # If this is a P2P loan, credit the lender
        if loan.get('liability_type') == 'p2p_loan' and loan.get('p2p_loan_id'):
            try:
                p2p_loan_id = loan['p2p_loan_id']
                p2p_res = supabase.table('p2p_loans').select('*').eq('id', p2p_loan_id).single().execute()
                
                if p2p_res.data:
                    lender_id = p2p_res.data['lender_id']
                    # Credit the lender
                    BalanceService.add_balance(
                        user_id=lender_id,
                        amount=payment_amount,
                        reason=f"Received P2P loan payment from user"
                    )
                    
                    # Update P2P loan sync
                    new_p2p_balance = Decimal(str(p2p_res.data.get('remaining_balance') or 0)) - payment_amount
                    p2p_status = 'active'
                    if new_p2p_balance <= 0 or is_fully_paid:
                        p2p_status = 'completed'
                        
                    supabase.table('p2p_loans').update({
                        'remaining_balance': float(max(0, new_p2p_balance)),
                        'status': p2p_status
                    }).eq('id', p2p_loan_id).execute()
                    
                    # Notify lender
                    if payment_amount > 0:
                        try:
                            ExpoPushService.send_notification_to_user(
                                supabase_client=supabase,
                                user_id=lender_id,
                                title='💰 P2P Payment Received',
                                body=f'You received a payment of ${payment_amount:,.2f} on your active loan offer.',
                                notification_type='p2p_payment_received',
                                data={'loan_id': p2p_loan_id, 'amount': float(payment_amount), 'screen': '/loans'}
                            )
                        except: pass
            except Exception as p2p_err:
                print(f"Error handling P2P lender credit: {str(p2p_err)}")
        
        # 4. Finalize Liability Record
        if is_fully_paid:
            # Mark loan as completed and delete it
            supabase.table('liabilities').delete().eq('id', liability_id).execute()
            
            # Create notification for loan completion
            supabase.table('notifications').insert({
                'user_id': current_user_id,
                'type': 'financial_move',
                'title': '🎉 Loan Paid Off!',
                'message': f'Congratulations! You have fully paid off your {loan.get("name", "loan")}.',
                'read': False
            }).execute()
        else:
            # Update remaining balance and term
            remaining_term = loan.get('remaining_term', 1) - 1
            supabase.table('liabilities').update({
                'remaining_balance': float(new_remaining_balance),
                'remaining_term': max(0, remaining_term)
            }).eq('id', liability_id).execute()
            
            # Create notification for payment
            supabase.table('notifications').insert({
                'user_id': current_user_id,
                'type': 'financial_move',
                'title': 'Loan Payment Made',
                'message': f'You paid ${payment_amount:,.2f} towards your {loan.get("name", "loan")}. Remaining: ${new_remaining_balance:,.2f}',
                'read': False
            }).execute()
        
        # Notify followers about the loan payment
        try:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='repay_loan',
                item_name=loan.get("name", "loan"),
                amount=float(payment_amount)
            )
        except Exception as e:
            print(f"Failed to notify followers of repayment: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Loan fully paid off!' if is_fully_paid else f'Payment of ${payment_amount:,.2f} successful',
            'payment_amount': float(payment_amount),
            'remaining_balance': 0 if is_fully_paid else float(new_remaining_balance),
            'is_fully_paid': is_fully_paid,
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@loan_bp.route('/p2p/available/', methods=['GET'])
@require_auth
def get_available_p2p_loans(current_user_id: str):
    """
    Get available P2P loan offers (excluding own)
    """
    try:
        # Fetch P2P loans that are pending and not posted by the current user
        response = supabase.table('p2p_loans').select('*').eq('status', 'pending').neq('lender_id', current_user_id).execute()
        
        return jsonify({
            'success': True,
            'data': response.data
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500

@loan_bp.route('/p2p/offer/', methods=['POST'])
@require_auth
def post_p2p_offer(current_user_id: str):
    """
    Post a P2P loan offer
    """
    try:
        data = request.json
        amount = Decimal(str(data.get('amount')))
        interest_rate = Decimal(str(data.get('interest_rate')))
        term_months = int(data.get('term_months', 12))
        purpose = data.get('purpose', 'General Loan')
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be positive'}), 400
            
        # 1. Check if user has sufficient funds to offer as a loan
        current_balance = BalanceService.get_current_balance(current_user_id)
        if current_balance < amount:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f'You need ${amount:,.2f} to post this offer, but only have ${current_balance:,.2f}'
            }), 400
            
        # 2. Subtract balance (escrow)
        BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=amount,
            reason=f"P2P Loan offer posted: {purpose}"
        )
        
        # 3. Create P2P loan record
        loan_id = str(uuid.uuid4())
        supabase.table('p2p_loans').insert({
            'id': loan_id,
            'lender_id': current_user_id,
            'amount': float(amount),
            'interest_rate': float(interest_rate),
            'term_months': term_months,
            'purpose': purpose,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Notify followers about the loan offer
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='post_p2p_offer',
            item_name=purpose,
            amount=float(amount)
        )
        
        return jsonify({
            'success': True,
            'message': 'P2P Loan offer posted successfully.',
            'loan_id': loan_id
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500

@loan_bp.route('/p2p/accept/', methods=['POST'])
@require_auth
def accept_p2p_loan(current_user_id: str):
    """
    Accept a P2P loan offer
    """
    try:
        data = request.json
        loan_id = data.get('loan_id')
        
        if not loan_id:
            return jsonify({'success': False, 'message': 'loan_id is required'}), 400
            
        # 1. Get loan details
        loan_response = supabase.table('p2p_loans').select('*').eq('id', loan_id).eq('status', 'pending').single().execute()
        
        if not loan_response.data:
            return jsonify({'success': False, 'message': 'Loan offer not found or already occupied'}), 404
            
        loan = loan_response.data
        if loan['lender_id'] == current_user_id:
            return jsonify({'success': False, 'message': 'You cannot accept your own loan offer'}), 400
            
        amount = Decimal(str(loan['amount']))
        
        # Calculate proposed monthly payment
        total_interest = amount * (Decimal(str(loan['interest_rate'])) / 100)
        total_repayment = amount + total_interest
        monthly_payment = total_repayment / int(loan['term_months'])
        
        # PRE-QUALIFICATION CHECKS
        profile_res = supabase.table('profiles').select('*').eq('user_id', current_user_id).single().execute()
        if not profile_res.data:
            return jsonify({'success': False, 'message': 'User profile not found'}), 404
            
        profile = profile_res.data
        # 1. Credit Score Check
        credit_score = profile.get('credit_score', 0)
        if credit_score < 600:
            return jsonify({'success': False, 'message': 'Pre-qualification failed: Credit score must be 600 or higher.'}), 400
            
        # 2. Monthly Income Check
        monthly_income = Decimal(str(profile.get('monthly_income', 0)))
        if monthly_income <= 0:
            return jsonify({'success': False, 'message': 'Pre-qualification failed: You must have a positive monthly income.'}), 400
            
        if monthly_income < (monthly_payment * 3):
             return jsonify({'success': False, 'message': 'Pre-qualification failed: Your monthly income is insufficient for this loan amount.'}), 400
             
        # 3. Debt-to-Income (DTI) Ratio Check
        # Fetch existing active liabilities
        existing_liabilities_resp = supabase.table('liabilities').select('monthly_payment').eq('user_id', current_user_id).gt('remaining_balance', 0).execute()
        
        total_existing_debt = Decimal('0')
        if existing_liabilities_resp.data:
            for liab in existing_liabilities_resp.data:
                total_existing_debt += Decimal(str(liab.get('monthly_payment', 0)))
                
        proposed_total_debt = total_existing_debt + monthly_payment
        dti_ratio = proposed_total_debt / monthly_income
        
        if dti_ratio > Decimal('0.43'):
            return jsonify({'success': False, 'message': f'Pre-qualification failed: Your Debt-to-Income ratio would be {(dti_ratio*100):.1f}% (max allowed is 43%).'}), 400
        
        # 2. Update P2P loan record
        supabase.table('p2p_loans').update({
            'borrower_id': current_user_id,
            'status': 'active',
            'funded_at': datetime.utcnow().isoformat()
        }).eq('id', loan_id).execute()
        
        # 3. Add amount to borrower's balance
        BalanceService.add_balance(
            user_id=current_user_id,
            amount=amount,
            reason=f"P2P Loan accepted from user"
        )
        
        # 4. Create liability record for borrower
        liability_id = str(uuid.uuid4())
        # Calc monthly payment (simple interest for simplicity in this sim)
        total_interest = amount * (Decimal(str(loan['interest_rate'])) / 100)
        total_repayment = amount + total_interest
        monthly_payment = total_repayment / int(loan['term_months'])
        
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': current_user_id,
            'name': f"P2P Loan ({loan['purpose']})",
            'liability_type': 'p2p_loan',
            'amount': float(amount),
            'remaining_balance': float(total_repayment),
            'interest_rate': float(loan['interest_rate']),
            'monthly_payment': float(monthly_payment),
            'p2p_loan_id': loan_id
        }).execute()

        # Update P2P loan synced balance
        supabase.table('p2p_loans').update({
            'remaining_balance': float(total_repayment)
        }).eq('id', loan_id).execute()
        
        # Notify lender
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=loan['lender_id'],
                title='🤝 P2P Loan Accepted',
                body=f'Your loan offer of ${amount:,.2f} has been accepted!',
                notification_type='p2p_loan_accepted',
                data={'loan_id': loan_id, 'screen': '/loans'}
            )
        except: pass
        
        # Send Mentorship Notification
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='take_loan',
            item_name='P2P ' + loan.get('purpose', ''),
            amount=float(amount)
        )
        
        return jsonify({
            'success': True,
            'message': 'P2P Loan accepted successfully.',
            'liability_id': liability_id
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
