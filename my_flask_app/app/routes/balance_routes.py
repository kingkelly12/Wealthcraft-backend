"""
Balance management routes
Handles adding and subtracting user balance with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth, require_admin
from app.services.balance_service import BalanceService
from app.schemas.balance_schema import BalanceAddRequest, BalanceSubtractRequest, BalanceResponse

balance_bp = Blueprint('balance', __name__)


@balance_bp.route('/add', methods=['POST'])
@require_admin  # Only admins can add balance (prevents cheating)
def add_balance(current_user_id: str):
    """
    Add balance to a user's account (Admin only)
    
    This endpoint is restricted to admins to prevent users from giving themselves free money.
    """
    try:
        # Validate request body
        data = BalanceAddRequest(**request.json)
        
        # Get target user_id from request (admins can add balance to any user)
        target_user_id = request.json.get('user_id', current_user_id)
        
        # Add balance
        result = BalanceService.add_balance(
            user_id=target_user_id,
            amount=data.amount,
            reason=data.reason
        )
        
        response = BalanceResponse(
            success=result['success'],
            new_balance=result['new_balance'],
            message=result['message'],
            transaction_id=result['transaction_id']
        )
        
        return jsonify(response.model_dump()), 200
        
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


@balance_bp.route('/subtract', methods=['POST'])
@require_auth  # Any authenticated user (used internally by purchase endpoints)
def subtract_balance(current_user_id: str):
    """
    Subtract balance from the authenticated user's account
    
    This is typically called internally by other endpoints (e.g., purchase item).
    Users can only subtract from their own balance.
    """
    try:
        # Validate request body
        data = BalanceSubtractRequest(**request.json)
        
        # Subtract balance (users can only subtract from their own balance)
        result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=data.amount,
            reason=data.reason
        )
        
        response = BalanceResponse(
            success=result['success'],
            new_balance=result['new_balance'],
            message=result['message'],
            transaction_id=result['transaction_id']
        )
        
        return jsonify(response.model_dump()), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        error_message = str(e)
        
        # Check if it's an insufficient funds error
        if 'Insufficient funds' in error_message:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': error_message
            }), 400
        
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': error_message
        }), 500


@balance_bp.route('/current', methods=['GET'])
@require_auth
def get_current_balance(current_user_id: str):
    """
    Get the current balance for the authenticated user
    """
    try:
        balance = BalanceService.get_current_balance(current_user_id)
        
        return jsonify({
            'success': True,
            'balance': float(balance)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
