"""
Life event management routes
Handles life event choices with JWT authentication
"""
from flask import Blueprint, request, jsonify
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app import supabase
import uuid
from decimal import Decimal
from app.services.push_notification_service import ExpoPushService

life_event_bp = Blueprint('life_event', __name__)


@life_event_bp.route('/make-choice/', methods=['POST'])
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
        data = request.json
        choice_id = data.get('choice_id')
        event_id = data.get('event_id')
        
        # 1. Get choice details
        choice_response = supabase.table('life_event_choices').select('*').eq('id', str(choice_id)).single().execute()
        
        if not choice_response.data:
            return jsonify({
                'success': False,
                'error': 'CHOICE_NOT_FOUND',
                'message': f'Choice {choice_id} not found'
            }), 404
        
        choice = choice_response.data
        
        # 2. Get life event details
        event_response = supabase.table('life_events').select('*').eq('id', str(event_id)).single().execute()
        
        if not event_response.data:
            return jsonify({
                'success': False,
                'error': 'EVENT_NOT_FOUND',
                'message': f'Life event {event_id} not found'
            }), 404
        
        event = event_response.data
        
        # 3. Update user_life_event with choice
        supabase.table('user_life_events').update({
            'choice_id': str(choice_id)
        }).eq('user_id', current_user_id).eq('life_event_id', str(event_id)).is_('choice_id', 'null').execute()
        
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

        # 5. Apply Sanity & Income Impact & Check Burnout
        from app.services.profile_service import ProfileService
        user_uuid = uuid.UUID(current_user_id)
        
        # Income Impact
        impact_income = choice.get('impact_income', 0)
        if impact_income == 0:
             impact_income = event.get('impact_income', 0)
             
        if impact_income != 0:
            ProfileService.update_monthly_income(user_uuid, float(impact_income))

        # Sanity Impact
        impact_sanity = choice.get('impact_sanity', None)
        if impact_sanity is None or impact_sanity == 0:
            impact_sanity = event.get('impact_sanity', 0)
        
        profile = ProfileService.update_sanity(user_uuid, impact_sanity)
        new_sanity = profile.sanity if profile else 0
        current_sanity = new_sanity - impact_sanity # Approximation of old sanity for the check below

        burnout_triggered = False
        game_over = False
        outcome_message = choice.get('outcome_description', 'Choice made')

        if new_sanity <= 0:
            # GAME OVER — sanity hits 0, stays at 0 (no auto-reset)
            if current_sanity > 0:
                burnout_triggered = True
                game_over = True
                burnout_cost = Decimal(500)
                BalanceService.subtract_balance(
                    user_id=current_user_id,
                    amount=burnout_cost,
                    reason="Medical Bill: Mental Breakdown"
                )
                outcome_message = f"GAME OVER! You've lost your mind. Hospital bill: $500. Use recovery actions to regain sanity. {outcome_message}"
        
        if impact_income != 0:
            outcome_message = f"{outcome_message} (Permanent Salary Change: {'+' if impact_income > 0 else ''}${impact_income}/mo)"

        # Notify followers about the life event choice if it had a financial impact
        if net_impact != 0 or impact_income != 0:
            try:
                ExpoPushService.notify_followers_of_financial_move(
                    supabase_client=supabase,
                    user_id=current_user_id,
                    move_type='life_event',
                    item_name=choice.get('choice_label', 'Choice'),
                    amount=float(abs(net_impact)) if net_impact != 0 else float(impact_income)
                )
            except Exception as e:
                print(f"Failed to notify followers of life event choice: {str(e)}")

        return jsonify({
            'success': True,
            'message': 'Choice processed successfully',
            'outcome': outcome_message,
            'balance_change': float(net_impact),
            'new_balance': float(balance_result['new_balance']),
            'sanity_change': impact_sanity,
            'new_sanity': new_sanity,
            'income_change': float(impact_income),
            'burnout_triggered': burnout_triggered,
            'game_over': game_over
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
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


@life_event_bp.route('/<event_id>/', methods=['GET'])
@require_auth
def get_life_event_details(current_user_id: str, event_id: str):
    """
    Get details of a specific life event and its choices
    """
    try:
        # 1. Get life event details
        event_response = supabase.table('life_events').select('*').eq('id', event_id).single().execute()
        
        if not event_response.data:
            return jsonify({
                'success': False,
                'error': 'EVENT_NOT_FOUND',
                'message': f'Life event {event_id} not found'
            }), 404
        
        event = event_response.data
        
        # 2. Get choices for this event
        choices_response = supabase.table('life_event_choices').select('*').eq('life_event_id', event_id).order('choice_order', desc=False).execute()
        choices = choices_response.data or []
        
        # 3. Check if user already made a choice
        user_event_response = supabase.table('user_life_events').select('*').eq('user_id', current_user_id).eq('life_event_id', event_id).execute()
        
        user_event = None
        if user_event_response.data and len(user_event_response.data) > 0:
            user_event = user_event_response.data[0]
        
        return jsonify({
            'success': True,
            'data': {
                'event': event,
                'choices': choices,
                'user_choice': user_event.get('choice_id') if user_event else None,
                'is_completed': user_event.get('choice_id') is not None if user_event else False
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
