"""
Life event management routes
Handles life event choices with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.life_event_schema import LifeEventChoiceRequest, LifeEventChoiceResponse
from supabase import create_client
from decimal import Decimal
import os
from datetime import datetime

life_event_bp = Blueprint('life_event', __name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@life_event_bp.route('/make-choice', methods=['POST'])
@require_auth
def make_life_event_choice(current_user_id: str):
    """
    Process a life event choice
    
    This endpoint:
    1. Validates the request
    2. Gets choice details
    3. Updates user_life_event with choice
    4. Applies balance changes
    5. Logs transaction
    """
    try:
        # Validate request
        data = LifeEventChoiceRequest(**request.json)
        
        # 1. Get choice details
        choice_response = supabase.table('life_event_choices').select('*').eq('id', str(data.choice_id)).single().execute()
        
        if not choice_response.data:
            return jsonify({
                'success': False,
                'error': 'CHOICE_NOT_FOUND',
                'message': f'Choice {data.choice_id} not found'
            }), 404
        
        choice = choice_response.data
        
        # 2. Get life event details
        event_response = supabase.table('life_events').select('*').eq('id', str(data.event_id)).single().execute()
        
        if not event_response.data:
            return jsonify({
                'success': False,
                'error': 'EVENT_NOT_FOUND',
                'message': f'Life event {data.event_id} not found'
            }), 404
        
        event = event_response.data
        
        # 3. Update user_life_event with choice
        supabase.table('user_life_events').update({
            'choice_id': str(data.choice_id)
        }).eq('user_id', current_user_id).eq('life_event_id', str(data.event_id)).is_('choice_id', 'null').execute()
        
        # 4. Apply balance changes
        net_impact = Decimal(str(choice.get('benefit', 0))) - Decimal(str(choice.get('cost', 0)))
        
        if net_impact > 0:
            balance_result = BalanceService.add_balance(
                user_id=current_user_id,
                amount=net_impact,
                reason=f"{event['title']} - {choice['choice_label']}"
            )
        elif net_impact < 0:
            balance_result = BalanceService.subtract_balance(
                user_id=current_user_id,
                amount=abs(net_impact),
                reason=f"{event['title']} - {choice['choice_label']}"
            )
        else:
            # No balance change
            current_balance = BalanceService.get_current_balance(current_user_id)
            balance_result = {'new_balance': current_balance}
        
        return jsonify({
            'success': True,
            'message': 'Choice processed successfully',
            'outcome': choice.get('outcome_description', 'Choice made'),
            'balance_change': float(net_impact),
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        error_message = str(e)
        
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
