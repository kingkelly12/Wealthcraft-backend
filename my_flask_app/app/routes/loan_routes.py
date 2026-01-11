"""
Loan management routes
Handles loan applications with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.loan_schema import LoanApplicationRequest, LoanApplicationResponse
from supabase import create_client
from decimal import Decimal
import os
import uuid
from datetime import datetime

loan_bp = Blueprint('loan', __name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@loan_bp.route('/apply', methods=['POST'])
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
        
        # 2. Add loan amount to balance
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=loan_amount,
            reason=f"Loan received: {loan['name']}"
        )
        
        # 3. Create liability record
        liability_id = str(uuid.uuid4())
        supabase.table('liabilities').insert({
            'id': liability_id,
            'user_id': current_user_id,
            'name': loan['name'],
            'type': 'bank_loan',
            'total_amount': float(loan_amount),
            'remaining_amount': float(loan_amount),
            'interest_rate': loan.get('interest_rate', 5.0),
            'monthly_payment': float(monthly_payment),
            'term_months': loan.get('term', 12),
            'remaining_term': loan.get('term', 12)
        }).execute()
        
        return jsonify({
            'success': True,
            'message': f'You have received ${loan_amount:,.2f}.',
            'liability_id': uuid.UUID(liability_id),
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


@loan_bp.route('/repay/<liability_id>', methods=['POST'])
@require_auth
def repay_loan(current_user_id: str, liability_id: str):
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
        "amount": 1000.00  // Optional - defaults to monthly_payment
    }
    """
    try:
        # 1. Get the loan and verify ownership
        loan_response = supabase.table('liabilities').select('*').eq('id', liability_id).eq('user_id', current_user_id).single().execute()
        
        if not loan_response.data:
            return jsonify({
                'success': False,
                'error': 'LOAN_NOT_FOUND',
                'message': 'Loan not found or does not belong to you'
            }), 404
        
        loan = loan_response.data
        remaining_amount = Decimal(str(loan.get('remaining_amount', loan.get('total_amount', 0))))
        monthly_payment = Decimal(str(loan.get('monthly_payment', 0)))
        
        # Get payment amount from request or use monthly payment
        request_data = request.get_json() or {}
        payment_amount = Decimal(str(request_data.get('amount', monthly_payment)))
        
        # Cap payment at remaining amount
        if payment_amount > remaining_amount:
            payment_amount = remaining_amount
        
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
        
        # 4. Update loan
        new_remaining_amount = remaining_amount - payment_amount
        is_fully_paid = new_remaining_amount <= 0
        
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
            # Update remaining amount and term
            remaining_term = loan.get('remaining_term', 1) - 1
            supabase.table('liabilities').update({
                'remaining_amount': float(new_remaining_amount),
                'remaining_term': max(0, remaining_term)
            }).eq('id', liability_id).execute()
            
            # Create notification for payment
            supabase.table('notifications').insert({
                'user_id': current_user_id,
                'type': 'financial_move',
                'title': 'Loan Payment Made',
                'message': f'You paid ${payment_amount:,.2f} towards your {loan.get("name", "loan")}. Remaining: ${new_remaining_amount:,.2f}',
                'read': False
            }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Loan fully paid off!' if is_fully_paid else f'Payment of ${payment_amount:,.2f} successful',
            'payment_amount': float(payment_amount),
            'remaining_amount': 0 if is_fully_paid else float(new_remaining_amount),
            'is_fully_paid': is_fully_paid,
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500

