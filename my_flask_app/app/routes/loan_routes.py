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
import math
import uuid
from datetime import datetime, timedelta, timezone
from app.services.push_notification_service import ExpoPushService
from app.utils.db import fetch_one
from app.game import economy

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

        unaffordable = economy.affordability(current_user_id, monthly_payment)
        if unaffordable:
            return jsonify({'success': False, 'error': 'CANT_AFFORD', 'message': unaffordable}), 400

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
            'total_interest': float(total_interest),
            'remaining_balance': float(loan_amount + total_interest),
            'remaining_term': int(loan.get('term') or 0),
            'interest_rate': float(loan['interest_rate']) * 100,  # stored as percent
            'monthly_payment': float(monthly_payment),
            'bank_loan_id': user_loan_id,
        }).execute()

        # 4. Disburse; with no money paid out there must be no debt either.
        try:
            balance_result = BalanceService.add_balance(
                user_id=current_user_id,
                amount=loan_amount,
                reason=f"Loan received: {loan.get('type', 'Bank Loan')}",
                category='loan_disbursement',
            )
        except Exception:
            supabase.table('liabilities').delete().eq('id', liability_id).execute()
            supabase.table('bank_loans').delete().eq('id', user_loan_id).execute()
            raise

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


@loan_bp.route('/mine/', methods=['GET'])
@require_auth
def my_loans(current_user_id: str):
    """Every loan you owe (bank and friends) with what clearing each costs today, for the repay screen."""
    try:
        rows = supabase.table('liabilities').select('*').eq('user_id', current_user_id) \
            .in_('liability_type', ['bank_loan', 'p2p_loan']).gt('remaining_balance', 0).execute().data or []
        p2p_ids = [r['p2p_loan_id'] for r in rows if r.get('p2p_loan_id')]
        lenders = {}
        if p2p_ids:
            p2p = supabase.table('p2p_loans').select('id, lender_id').in_('id', p2p_ids).execute().data or []
            people = _usernames([p['lender_id'] for p in p2p])
            lenders = {str(p['id']): {'user_id': str(p['lender_id']), 'username': people.get(str(p['lender_id']), {}).get('username')} for p in p2p}
        loans = []
        for r in rows:
            remaining = economy.money(r['remaining_balance'])
            payoff = economy.payoff_amount(r)
            first_owed = economy.money(r.get('amount')) + economy.money(r.get('total_interest'))
            loans.append({
                'id': r['id'], 'name': r.get('name') or 'Loan',
                'kind': 'friend' if r.get('liability_type') == 'p2p_loan' else 'bank',
                'lender': lenders.get(str(r.get('p2p_loan_id'))),
                'amount': float(economy.money(r.get('amount'))), 'interest_rate': float(r.get('interest_rate') or 0),
                'remaining_balance': float(remaining), 'monthly_payment': float(economy.money(r.get('monthly_payment'))),
                'remaining_term': int(r.get('remaining_term') or 0),
                'is_mortgage': bool(r.get('player_home_id')), 'missed_streak': int(r.get('missed_streak') or 0),
                'payoff_amount': float(payoff), 'interest_saved': float(remaining - payoff),
                'paid_share': round(max(0.0, min(1.0, 1 - float(remaining / first_owed))), 3) if first_owed > 0 else 0.0,
            })
        # Friends get paid first on payday, so they come first here too.
        loans.sort(key=lambda l: (l['kind'] != 'friend', l['name']))
        return jsonify({'success': True, 'data': {'loans': loans, 'balance': float(BalanceService.get_current_balance(current_user_id))}}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


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
        
        # Cap payment at remaining balance. Clearing the whole loan costs less than the balance:
        # interest not yet earned is refunded (economy.payoff_amount).
        if payment_amount > remaining_balance:
            payment_amount = remaining_balance
        payoff = economy.payoff_amount(loan)
        paying_off = payment_amount >= payoff
        if paying_off:
            payment_amount = payoff
        
        # 2. Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)

        if current_balance < payment_amount:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f'Insufficient funds. You need ${payment_amount} but only have ${current_balance}'
            }), 400

        # 3. Claim the new balance first: a second request that read the same balance (double tap)
        #    finds it changed and is refused, instead of being charged for a payment that is only counted once.
        new_remaining_balance = Decimal('0') if paying_off else remaining_balance - payment_amount
        is_fully_paid = new_remaining_balance <= 0
        remaining_term = int(loan.get('remaining_term') or 0)
        # Term = instalments still to go at the monthly payment, so a $5 payment doesn't shorten it.
        new_term = 0 if is_fully_paid else (math.ceil(new_remaining_balance / monthly_payment) if monthly_payment > 0 else remaining_term)
        claim = supabase.table('liabilities').update({
            'remaining_balance': float(new_remaining_balance), 'remaining_term': new_term,
        }).eq('id', liability_id).eq('remaining_balance', float(remaining_balance)).execute()
        if not claim.data:
            return jsonify({'success': False, 'error': 'CONFLICT',
                            'message': 'This loan changed while you were paying. Check the balance and try again.'}), 409

        def release_claim():
            supabase.table('liabilities').update({
                'remaining_balance': float(remaining_balance), 'remaining_term': remaining_term,
            }).eq('id', liability_id).execute()

        try:
            balance_result = BalanceService.subtract_balance(
                user_id=current_user_id,
                amount=payment_amount,
                reason=f'Loan payment for {loan.get("name", "loan")}',
                category='loan_payment',
            )
        except Exception:
            release_claim()
            raise

        # ============ P2P REPAYMENT LOGIC ============
        # If this is a P2P loan, the lender is paid and the friend-loan record kept in step.
        if loan.get('liability_type') == 'p2p_loan' and loan.get('p2p_loan_id'):
            p2p_loan_id = loan['p2p_loan_id']
            p2p_res = fetch_one(supabase.table('p2p_loans').select('*').eq('id', p2p_loan_id))
            if p2p_res.data:
                lender_id = p2p_res.data['lender_id']
                try:
                    BalanceService.add_balance(user_id=lender_id, amount=payment_amount,
                                               reason="Friend loan repayment received", category='p2p_repayment')
                except Exception:
                    # The lender couldn't be paid: give the money back and leave the debt as it was.
                    BalanceService.add_balance(current_user_id, payment_amount, 'Refund: repayment failed', category='refund')
                    release_claim()
                    raise
                is_instalment = payment_amount >= min(monthly_payment, remaining_balance) or is_fully_paid
                supabase.table('p2p_loans').update({
                    'remaining_balance': float(max(Decimal('0'), new_remaining_balance)),
                    'status': 'completed' if is_fully_paid else 'active',
                    'payments_made': int(p2p_res.data.get('payments_made') or 0) + (1 if is_instalment else 0),
                }).eq('id', p2p_loan_id).execute()
                _push(lender_id, '💰 Friend loan payment received', f'You received ${payment_amount:,.2f} on a loan you made.')

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
            'interest_saved': float(remaining_balance - payment_amount) if is_fully_paid else 0.0,
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


def _err(code, message, status=400):
    return jsonify({'success': False, 'error': code, 'message': message}), status


def _usernames(ids):
    ids = [str(i) for i in ids if i]
    if not ids:
        return {}
    rows = supabase.table('profiles').select('user_id, username, profile_picture_url').in_('user_id', ids).execute().data or []
    return {str(r['user_id']): r for r in rows}


def _push(uid, title, body):
    try:
        ExpoPushService.send_notification_to_user(supabase_client=supabase, user_id=str(uid), title=title, body=body,
                                                  notification_type='social', data={'screen': '/banking'})
    except Exception:
        pass


def _parse_terms(data):
    """(amount, annual rate %, term months) or an error response."""
    try:
        amount = Decimal(str(data.get('amount')))
        rate = Decimal(str(data.get('interest_rate')))
        term = int(data.get('term_months', 12))
    except Exception:
        return None, _err('VALIDATION_ERROR', 'amount, interest_rate and term_months must be numbers')
    if not amount.is_finite() or amount <= 0:
        return None, _err('VALIDATION_ERROR', 'Amount must be positive')
    if amount > economy.P2P_MAX_AMOUNT:
        return None, _err('TOO_BIG', f'Friends lend up to ${economy.P2P_MAX_AMOUNT:,.0f}. For more, try the bank.')
    if not rate.is_finite() or not (0 <= rate <= economy.P2P_MAX_RATE):
        return None, _err('VALIDATION_ERROR', f'Interest must be between 0% and {economy.P2P_MAX_RATE}% a year')
    if not (1 <= term <= 60):
        return None, _err('VALIDATION_ERROR', 'Term must be between 1 and 60 months')
    return (amount, rate, term), None


def _qualify(borrower_id, monthly_payment):
    """None if the borrower qualifies, else an error response."""
    profile = supabase.table('profiles').select('credit_score, monthly_income').eq('user_id', str(borrower_id)).limit(1).execute().data
    if not profile:
        return _err('NOT_FOUND', 'User profile not found', 404)
    if (profile[0].get('credit_score') or 0) < 550:
        return _err('CREDIT_TOO_LOW', 'Friend loans need a credit score of 550 or more.')
    reason = economy.affordability(borrower_id, monthly_payment)
    return _err('CANT_AFFORD', reason) if reason else None


def _fund(loan, borrower_id, lender_paid_now):
    """
    Turn a claimed loan (status already 'active') into money and debt.
    lender_paid_now: the lender's money moves now (a request they approved);
    otherwise it was escrowed when they posted the offer.
    """
    terms = economy.loan_terms({**loan, 'rate_basis': loan.get('rate_basis') or 'annual'})
    amount = economy.money(loan['amount'])
    lender_charged = borrower_paid = False
    liability_id = str(uuid.uuid4())
    try:
        if lender_paid_now:
            BalanceService.subtract_balance(loan['lender_id'], amount, f"Friend loan to a friend: {loan.get('purpose')}", category='p2p_escrow')
            lender_charged = True
        BalanceService.add_balance(borrower_id, amount, "Friend loan received", category='loan_disbursement')
        borrower_paid = True
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': str(borrower_id),
            'name': f"Friend loan ({loan.get('purpose') or 'General'})",
            'liability_type': 'p2p_loan',
            'amount': float(amount),
            'total_interest': float(terms['interest']),
            'remaining_balance': float(terms['total']),
            'interest_rate': float(loan['interest_rate']),
            'monthly_payment': float(terms['monthly']),
            'remaining_term': int(loan['term_months']),
            'p2p_loan_id': loan['id'],
        }).execute()
        supabase.table('p2p_loans').update({
            'remaining_balance': float(terms['total']), 'monthly_payment': float(terms['monthly']),
        }).eq('id', loan['id']).execute()
    except Exception:
        # All or nothing: undo whatever moved, so nobody is left with money or debt but no loan.
        supabase.table('liabilities').delete().eq('id', liability_id).execute()
        if borrower_paid:
            BalanceService.subtract_balance(borrower_id, amount, "Reversed: friend loan failed", category='refund')
        if lender_charged:
            BalanceService.add_balance(loan['lender_id'], amount, "Refund: friend loan failed", category='refund')
        raise
    return liability_id, terms


def _public_loan(l, me, names, records):
    other = l.get('borrower_id') if str(l.get('lender_id')) == me else l.get('lender_id')
    terms = economy.loan_terms({**l, 'rate_basis': l.get('rate_basis') or 'annual'})
    return {
        'id': l['id'], 'status': l['status'], 'requested': bool(l.get('requested')),
        'role': 'lender' if str(l.get('lender_id')) == me else 'borrower',
        'with': ({'user_id': str(other), **{k: names.get(str(other), {}).get(k) for k in ('username', 'profile_picture_url')}} if other else None),
        'offered_to': str(l['offered_to']) if l.get('offered_to') else None,
        'amount': float(l['amount']), 'interest_rate': float(l['interest_rate']),
        'rate_basis': l.get('rate_basis') or 'annual', 'term_months': int(l['term_months']),
        'purpose': l.get('purpose'), 'monthly_payment': float(terms['monthly']),
        'total_interest': float(terms['interest']), 'total_repayment': float(terms['total']),
        'remaining_balance': float(l['remaining_balance']) if l.get('remaining_balance') is not None else None,
        'payments_made': int(l.get('payments_made') or 0), 'payments_missed': int(l.get('payments_missed') or 0),
        'borrower_record': records.get(str(l.get('borrower_id'))) if l.get('borrower_id') else None,
        'created_at': l.get('created_at'),
    }


@loan_bp.route('/p2p/available/', methods=['GET'])
@require_auth
def get_available_p2p_loans(current_user_id: str):
    """Open friend-loan offers: public ones and ones made just to you."""
    try:
        rows = supabase.table('p2p_loans').select('*').eq('status', 'pending').neq('lender_id', current_user_id) \
            .or_(f'offered_to.is.null,offered_to.eq.{current_user_id}').execute().data or []
        names = _usernames([r['lender_id'] for r in rows])
        return jsonify({'success': True, 'data': [_public_loan(r, current_user_id, names, {}) for r in rows]}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/mine/', methods=['GET'])
@require_auth
def my_p2p_loans(current_user_id: str):
    """
    Everything friend-loan for you: requests waiting on you, your requests,
    your offers, money you've lent and money you owe, plus each borrower's
    repayment record and how banks compare.
    """
    try:
        me = str(current_user_id)
        rows = supabase.table('p2p_loans').select('*').or_(f'lender_id.eq.{me},borrower_id.eq.{me}') \
            .in_('status', ['requested', 'pending', 'active', 'completed', 'defaulted']).execute().data or []
        people = {str(r.get('lender_id')) for r in rows} | {str(r.get('borrower_id')) for r in rows if r.get('borrower_id')}
        people.discard(me)
        names = _usernames(people)
        records = {uid: economy.repayment_record(uid) for uid in {str(r['borrower_id']) for r in rows if r.get('borrower_id')}}
        loans = [_public_loan(r, me, names, records) for r in rows]
        banks = supabase.table('bank_loans').select('interest_rate, amount').is_('borrower_id', 'null').execute().data or []
        rates = [float(b['interest_rate']) * 100 for b in banks]
        return jsonify({'success': True, 'data': {
            'requests_to_me': [l for l in loans if l['status'] == 'requested' and l['role'] == 'lender'],
            'my_requests': [l for l in loans if l['status'] == 'requested' and l['role'] == 'borrower'],
            'my_offers': [l for l in loans if l['status'] == 'pending' and l['role'] == 'lender'],
            'lent': [l for l in loans if l['status'] in ('active', 'completed', 'defaulted') and l['role'] == 'lender'],
            'borrowed': [l for l in loans if l['status'] in ('active', 'completed', 'defaulted') and l['role'] == 'borrower'],
            'my_record': economy.repayment_record(me),
            'limits': {'max_amount': float(economy.P2P_MAX_AMOUNT), 'max_rate': float(economy.P2P_MAX_RATE), 'max_term': 60},
            'bank_rates': {'min': min(rates) if rates else None, 'max': max(rates) if rates else None,
                           'max_amount': max((float(b['amount']) for b in banks), default=None)},
        }}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/offer/', methods=['POST'])
@require_auth
def post_p2p_offer(current_user_id: str):
    """
    Offer a friend loan: {"amount", "interest_rate" (% a year), "term_months",
    "purpose", "offered_to"?}. The money is set aside (escrow) until someone
    accepts or you cancel. With offered_to, only that friend can take it.
    """
    try:
        data = request.get_json(silent=True) or {}
        terms, error = _parse_terms(data)
        if error:
            return error
        amount, rate, term = terms
        purpose = (data.get('purpose') or 'General Loan')[:200]
        offered_to = data.get('offered_to')
        if offered_to and not economy.are_friends(current_user_id, offered_to):
            return _err('NOT_FRIENDS', 'You can only make private offers to friends, squadmates or your roommate.', 403)

        current_balance = BalanceService.get_current_balance(current_user_id)
        if current_balance < amount:
            return _err('INSUFFICIENT_FUNDS', f'You need ${amount:,.2f} to post this offer, but only have ${current_balance:,.2f}')
        BalanceService.subtract_balance(user_id=current_user_id, amount=amount, reason=f"Friend loan offer: {purpose}", category='p2p_escrow')

        loan_id = str(uuid.uuid4())
        try:
            supabase.table('p2p_loans').insert({
                'id': loan_id, 'lender_id': current_user_id, 'amount': float(amount),
                'interest_rate': float(rate), 'rate_basis': 'annual', 'term_months': term,
                'purpose': purpose, 'status': 'pending', 'offered_to': offered_to or None,
                'created_at': datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception:
            BalanceService.add_balance(current_user_id, amount, 'Refund: friend loan offer failed to post', category='p2p_escrow')
            raise

        me = _usernames([current_user_id]).get(str(current_user_id), {}).get('username', 'A friend')
        if offered_to:
            _push(offered_to, f'🤝 {me} offered you a loan',
                  f'${amount:,.0f} at {rate}% a year over {term} months. Open the Bank to accept.')
        else:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase, user_id=current_user_id, move_type='post_p2p_offer', item_name=purpose, amount=float(amount))
        return jsonify({'success': True, 'message': 'Loan offer posted.', 'loan_id': loan_id}), 201
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/accept/', methods=['POST'])
@require_auth
def accept_p2p_loan(current_user_id: str):
    """Take an offer. Repayments come straight out of your account every month."""
    try:
        loan_id = (request.get_json(silent=True) or {}).get('loan_id')
        if not loan_id:
            return _err('VALIDATION_ERROR', 'loan_id is required')
        rows = supabase.table('p2p_loans').select('*').eq('id', loan_id).eq('status', 'pending').limit(1).execute().data
        if not rows:
            return _err('NOT_FOUND', 'Loan offer not found or already taken', 404)
        loan = rows[0]
        if loan['lender_id'] == current_user_id:
            return _err('OWN_OFFER', 'You cannot accept your own loan offer')
        if loan.get('offered_to') and str(loan['offered_to']) != str(current_user_id):
            return _err('NOT_FOUND', 'Loan offer not found or already taken', 404)

        blocked = enforce_mission_constraints(current_user_id, 'take_loan', {'amount': float(loan['amount']), 'loan_type': 'p2p'})
        if blocked:
            return blocked
        terms = economy.loan_terms({**loan, 'rate_basis': loan.get('rate_basis') or 'annual'})
        refused = _qualify(current_user_id, terms['monthly'])
        if refused:
            return refused

        claim = supabase.table('p2p_loans').update({
            'borrower_id': current_user_id, 'status': 'active',
            'funded_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', loan_id).eq('status', 'pending').execute()
        if not claim.data:
            return _err('TAKEN', 'Someone else just accepted this offer', 409)
        try:
            liability_id, terms = _fund(loan, current_user_id, lender_paid_now=False)
        except Exception:
            supabase.table('p2p_loans').update({'borrower_id': None, 'status': 'pending', 'funded_at': None}) \
                .eq('id', loan_id).eq('status', 'active').execute()
            raise

        me = _usernames([current_user_id]).get(str(current_user_id), {}).get('username', 'Someone')
        _push(loan['lender_id'], '🤝 Your loan offer was accepted',
              f"{me} borrowed ${float(loan['amount']):,.0f}. You'll get ${terms['monthly']:,.2f} a month, straight from their account.")
        return jsonify({'success': True, 'message': 'Loan accepted.', 'liability_id': liability_id}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/request/', methods=['POST'])
@require_auth
def request_p2p_loan(current_user_id: str):
    """Ask a friend for a loan: {"lender_id", "amount", "interest_rate", "term_months", "purpose"}."""
    try:
        data = request.get_json(silent=True) or {}
        lender = str(data.get('lender_id') or '')
        if not lender or lender == str(current_user_id):
            return _err('VALIDATION_ERROR', 'Pick a friend to ask.')
        if not economy.are_friends(current_user_id, lender):
            return _err('NOT_FRIENDS', 'You can only ask friends, squadmates or your roommate.', 403)
        terms, error = _parse_terms(data)
        if error:
            return error
        amount, rate, term = terms
        refused = _qualify(current_user_id, economy.p2p_terms(amount, rate, term)['monthly'])
        if refused:
            return refused
        open_asks = supabase.table('p2p_loans').select('id').eq('borrower_id', current_user_id).eq('lender_id', lender) \
            .eq('status', 'requested').limit(1).execute().data
        if open_asks:
            return _err('ALREADY_ASKED', 'You already asked them. Wait for an answer.', 409)

        loan_id = str(uuid.uuid4())
        purpose = (data.get('purpose') or 'General Loan')[:200]
        supabase.table('p2p_loans').insert({
            'id': loan_id, 'lender_id': lender, 'borrower_id': current_user_id, 'amount': float(amount),
            'interest_rate': float(rate), 'rate_basis': 'annual', 'term_months': term, 'purpose': purpose,
            'status': 'requested', 'requested': True, 'created_at': datetime.now(timezone.utc).isoformat(),
        }).execute()
        me = _usernames([current_user_id]).get(str(current_user_id), {}).get('username', 'A friend')
        _push(lender, f'🙏 {me} asked to borrow ${amount:,.0f}',
              f'{rate}% a year over {term} months, for "{purpose}". Repayments come out of their account automatically.')
        return jsonify({'success': True, 'message': 'Request sent.', 'loan_id': loan_id}), 201
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/requests/<loan_id>/approve/', methods=['POST'])
@require_auth
def approve_p2p_request(current_user_id: str, loan_id: str):
    """Lend a friend the money they asked for."""
    try:
        rows = supabase.table('p2p_loans').select('*').eq('id', loan_id).eq('lender_id', current_user_id) \
            .eq('status', 'requested').limit(1).execute().data
        if not rows:
            return _err('NOT_FOUND', 'That request is gone.', 404)
        loan = rows[0]
        amount = economy.money(loan['amount'])
        if BalanceService.get_current_balance(current_user_id) < amount:
            return _err('INSUFFICIENT_FUNDS', f"You need ${amount:,.2f} in your account to lend this.")
        terms = economy.loan_terms({**loan, 'rate_basis': loan.get('rate_basis') or 'annual'})
        refused = _qualify(loan['borrower_id'], terms['monthly'])
        if refused:
            supabase.table('p2p_loans').update({'status': 'declined'}).eq('id', loan_id).eq('status', 'requested').execute()
            return refused
        claim = supabase.table('p2p_loans').update({'status': 'active', 'funded_at': datetime.now(timezone.utc).isoformat()}) \
            .eq('id', loan_id).eq('status', 'requested').execute()
        if not claim.data:
            return _err('NOT_FOUND', 'That request is gone.', 404)
        try:
            _fund(loan, loan['borrower_id'], lender_paid_now=True)
        except Exception:
            supabase.table('p2p_loans').update({'status': 'requested', 'funded_at': None}).eq('id', loan_id).eq('status', 'active').execute()
            raise
        me = _usernames([current_user_id]).get(str(current_user_id), {}).get('username', 'Your friend')
        _push(loan['borrower_id'], f'💸 {me} lent you ${amount:,.0f}',
              f"${terms['monthly']:,.2f} a month comes out of your account automatically. Don't make it weird.")
        return jsonify({'success': True, 'message': 'Loan sent.'}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


@loan_bp.route('/p2p/requests/<loan_id>/decline/', methods=['POST'])
@require_auth
def decline_p2p_request(current_user_id: str, loan_id: str):
    """The lender says no, or the borrower takes the request back."""
    try:
        me = str(current_user_id)
        res = supabase.table('p2p_loans').update({'status': 'declined'}).eq('id', loan_id).eq('status', 'requested') \
            .or_(f'lender_id.eq.{me},borrower_id.eq.{me}').execute()
        if not res.data:
            return _err('NOT_FOUND', 'That request is gone.', 404)
        loan = res.data[0]
        if str(loan['lender_id']) == me:
            who = _usernames([me]).get(me, {}).get('username', 'Your friend')
            _push(loan['borrower_id'], f'{who} passed on your loan request', 'No hard feelings. Try someone else, or the bank.')
        return jsonify({'success': True, 'message': 'Request closed.'}), 200
    except Exception as e:
        return _err('OPERATION_FAILED', str(e), 500)


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
