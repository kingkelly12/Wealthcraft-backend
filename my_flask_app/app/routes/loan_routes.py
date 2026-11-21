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
from app.utils.mission_constraints import enforce_mission_constraints
from decimal import Decimal
import uuid
from datetime import datetime, timedelta, timezone
from app.services.push_notification_service import ExpoPushService
from app.utils.db import fetch_one

loan_bp = Blueprint('loan', __name__)

MAX_ACTIVE_BANK_LOANS = 3


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
        loan_response = supabase.table('bank_loans').select('*') \
            .eq('id', str(data.loan_id)).is_('borrower_id', 'null').limit(1).execute()

        if not loan_response.data:
            return jsonify({
                'success': False,
                'error': 'LOAN_NOT_FOUND',
                'message': f'Loan product {data.loan_id} not found'
            }), 404

        loan = loan_response.data[0]
        loan_amount = Decimal(str(loan['amount']))
        monthly_payment = Decimal(str(loan.get('monthly_payment') or (loan_amount * Decimal('0.05'))))
        total_interest = Decimal(str(loan.get('total_interest') or 0))

        blocked = enforce_mission_constraints(current_user_id, 'take_loan', {'amount': float(loan_amount), 'loan_type': loan.get('type')})
        if blocked:
            return blocked


        # Underwriting: credit score requirement and a cap on concurrent loans
        profile_res = supabase.table('profiles').select('credit_score') \
            .eq('user_id', current_user_id).limit(1).execute()
        credit_score = (profile_res.data[0].get('credit_score') if profile_res.data else 0) or 0
        if credit_score < int(loan.get('credit_required') or 0):
            return jsonify({
                'success': False,
                'error': 'CREDIT_TOO_LOW',
                'message': f"This loan requires a credit score of {loan['credit_required']} (yours: {credit_score})."
            }), 400

        active = supabase.table('bank_loans').select('id', count='exact') \
            .eq('borrower_id', current_user_id).eq('status', 'active').execute()
        if (active.count or 0) >= MAX_ACTIVE_BANK_LOANS:
            return jsonify({
                'success': False,
                'error': 'LOAN_LIMIT_REACHED',
                'message': f'You can have at most {MAX_ACTIVE_BANK_LOANS} active bank loans.'
            }), 400

        # 2. Create the borrower's own bank_loan record
        user_loan_id = str(uuid.uuid4())
        supabase.table('bank_loans').insert({
            'id': user_loan_id,
            'borrower_id': current_user_id,
            'type': loan['type'],
            'amount': float(loan_amount),
            'interest_rate': float(loan['interest_rate']),
            'term': loan['term'],
            'monthly_payment': float(monthly_payment),
            'total_interest': float(total_interest),
            'credit_required': loan['credit_required'],
            'status': 'active',
            'collateral': loan['collateral'],
            'funded_at': datetime.now(timezone.utc).isoformat(),
            'due_date': (datetime.now(timezone.utc) + timedelta(days=int(loan.get('term', 12)) * 30)).isoformat()
        }).execute()

        # 3. Debt ledger entry. remaining_balance includes the interest: the old
        #    code only tracked principal, so bank loans were interest-free.
        liability_id = str(uuid.uuid4())
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': current_user_id,
            'name': loan.get('type', 'Bank Loan'),
            'liability_type': 'bank_loan',
            'amount': float(loan_amount),
            'remaining_balance': float(loan_amount + total_interest),
            'remaining_term': int(loan.get('term') or 0),
            'interest_rate': float(loan['interest_rate']) * 100,  # stored as percent
            'monthly_payment': float(monthly_payment),
            'bank_loan_id': user_loan_id,
        }).execute()

        # 4. Disburse
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=loan_amount,
            reason=f"Loan received: {loan.get('type', 'Bank Loan')}",
            category='loan_disbursement',
        )

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
        loan_response = supabase.table('liabilities').select('*').eq('id', liability_id).eq('user_id', current_user_id).limit(1).execute()
        
        if not loan_response.data:
            return jsonify({
                'success': False,
                'error': 'LOAN_NOT_FOUND',
                'message': 'Loan not found or does not belong to you'
            }), 404
        
        loan = loan_response.data[0]
        remaining_balance = Decimal(str(loan.get('remaining_balance') or 0))
        monthly_payment = Decimal(str(loan.get('monthly_payment', 0)))
        
        # Get payment amount from request or use monthly payment
        request_data = request.get_json() or {}
        try:
            payment_amount = Decimal(str(request_data.get('amount') or monthly_payment))
        except Exception:
            return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Invalid amount'}), 400

        # A negative "payment" used to INCREASE the player's cash (subtract of a
        # negative) and grow the lender's debt. Only positive payments are valid.
        if not payment_amount.is_finite() or payment_amount <= 0:
            return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Payment amount must be positive'}), 400
        if remaining_balance <= 0:
            return jsonify({'success': False, 'error': 'ALREADY_PAID', 'message': 'This loan is already paid off'}), 400
        
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
            reason=f'Loan payment for {loan.get("name", "loan")}',
            category='loan_payment',
        )

        # 4. Update loan status calculations
        new_remaining_balance = remaining_balance - payment_amount
        is_fully_paid = new_remaining_balance <= 0

        # ============ P2P REPAYMENT LOGIC ============
        # If this is a P2P loan, credit the lender
        if loan.get('liability_type') == 'p2p_loan' and loan.get('p2p_loan_id'):
            try:
                p2p_loan_id = loan['p2p_loan_id']
                p2p_res = fetch_one(supabase.table('p2p_loans').select('*').eq('id', p2p_loan_id))
                
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
                                data={'loan_id': p2p_loan_id, 'amount': float(payment_amount), 'screen': '/banking'}
                            )
                        except: pass
            except Exception as p2p_err:
                print(f"Error handling P2P lender credit: {str(p2p_err)}")
        
        # 4. Finalize Liability Record
        if is_fully_paid:
            # Remove the debt and close the underlying bank loan
            supabase.table('liabilities').delete().eq('id', liability_id).execute()
            if loan.get('bank_loan_id'):
                supabase.table('bank_loans').update({'status': 'completed'}).eq('id', loan['bank_loan_id']).execute()
            
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
            remaining_term = (loan.get('remaining_term') or 1) - 1
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
        data = request.get_json(silent=True) or {}
        try:
            amount = Decimal(str(data.get('amount')))
            interest_rate = Decimal(str(data.get('interest_rate')))
            term_months = int(data.get('term_months', 12))
        except Exception:
            return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'amount, interest_rate and term_months must be numbers'}), 400
        purpose = (data.get('purpose') or 'General Loan')[:200]
        
        if not amount.is_finite() or amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be positive'}), 400
        if not interest_rate.is_finite() or not (0 <= interest_rate <= 100):
            return jsonify({'success': False, 'message': 'Interest rate must be between 0 and 100%'}), 400
        if not (1 <= term_months <= 120):
            return jsonify({'success': False, 'message': 'Term must be between 1 and 120 months'}), 400
            
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
            reason=f"P2P Loan offer posted: {purpose}",
            category='p2p_escrow',
        )
        
        # 3. Create P2P loan record
        loan_id = str(uuid.uuid4())
        try:
            supabase.table('p2p_loans').insert({
                'id': loan_id,
                'lender_id': current_user_id,
                'amount': float(amount),
                'interest_rate': float(interest_rate),
                'term_months': term_months,
                'purpose': purpose,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
        except Exception:
            # escrow was already taken: give it back
            BalanceService.add_balance(current_user_id, amount, 'Refund: P2P offer failed to post', category='p2p_escrow')
            raise
        
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
        loan_response = supabase.table('p2p_loans').select('*').eq('id', loan_id).eq('status', 'pending').limit(1).execute()
        
        if not loan_response.data:
            return jsonify({'success': False, 'message': 'Loan offer not found or already occupied'}), 404
            
        loan = loan_response.data[0]
        if loan['lender_id'] == current_user_id:
            return jsonify({'success': False, 'message': 'You cannot accept your own loan offer'}), 400

        blocked = enforce_mission_constraints(current_user_id, 'take_loan', {'amount': float(loan['amount']), 'loan_type': 'p2p'})
        if blocked:
            return blocked

            
        amount = Decimal(str(loan['amount']))
        
        # Calculate proposed monthly payment
        total_interest = amount * (Decimal(str(loan['interest_rate'])) / 100)
        total_repayment = amount + total_interest
        monthly_payment = total_repayment / int(loan['term_months'])
        
        # PRE-QUALIFICATION CHECKS
        profile_res = supabase.table('profiles').select('*').eq('user_id', current_user_id).limit(1).execute()
        if not profile_res.data:
            return jsonify({'success': False, 'message': 'User profile not found'}), 404
            
        profile = profile_res.data[0]
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
        
        # 2. Claim the offer atomically: only one borrower can flip pending → active
        claim = supabase.table('p2p_loans').update({
            'borrower_id': current_user_id,
            'status': 'active',
            'funded_at': datetime.now(timezone.utc).isoformat(),
            'monthly_payment': float(round(monthly_payment, 2)),
        }).eq('id', loan_id).eq('status', 'pending').execute()
        if not claim.data:
            return jsonify({'success': False, 'message': 'Someone else just accepted this offer'}), 409
        
        # 3. Add amount to borrower's balance (it was escrowed from the lender at posting)
        BalanceService.add_balance(
            user_id=current_user_id,
            amount=amount,
            reason=f"P2P Loan accepted from user",
            category='loan_disbursement',
        )
        
        # 4. Create liability record for borrower
        liability_id = str(uuid.uuid4())
        
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': current_user_id,
            'name': f"P2P Loan ({loan['purpose']})",
            'liability_type': 'p2p_loan',
            'amount': float(amount),
            'remaining_balance': float(total_repayment),
            'interest_rate': float(loan['interest_rate']),
            'monthly_payment': float(round(monthly_payment, 2)),
            'remaining_term': int(loan['term_months']),
            'p2p_loan_id': loan_id
        }).execute()

        # Update P2P loan synced balance
        supabase.table('p2p_loans').update({
            'remaining_balance': float(total_repayment)
        }).eq('id', loan_id).execute()
        
        # Notify lender
        try:
            borrower_username = profile.get('username', 'Someone')
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=loan['lender_id'],
                title='🤝 P2P Loan Accepted',
                body=f'{borrower_username} has accepted your loan offer of ${amount:,.2f}!',
                notification_type='p2p_loan_accepted',
                data={'loan_id': loan_id, 'screen': f'/profile?id={current_user_id}'}
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


@loan_bp.route('/p2p/cancel/', methods=['POST'])
@require_auth
def cancel_p2p_offer(current_user_id: str):
    """Withdraw an un-accepted P2P offer and refund the escrowed amount."""
    try:
        loan_id = (request.get_json(silent=True) or {}).get('loan_id')
        if not loan_id:
            return jsonify({'success': False, 'message': 'loan_id is required'}), 400

        claim = supabase.table('p2p_loans').update({'status': 'cancelled'}) \
            .eq('id', loan_id).eq('lender_id', current_user_id).eq('status', 'pending').execute()
        if not claim.data:
            return jsonify({'success': False, 'message': 'Offer not found, not yours, or already accepted'}), 404

        amount = Decimal(str(claim.data[0]['amount']))
        result = BalanceService.add_balance(current_user_id, amount, 'P2P offer cancelled (escrow refund)', category='p2p_escrow')
        return jsonify({'success': True, 'message': 'Offer cancelled and funds returned',
                        'new_balance': float(result['new_balance'])}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500
