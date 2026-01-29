from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.liability_service import LiabilityService
from app.services.balance_service import BalanceService
from app.utils.jwt_helper import require_auth
from app.schemas.liability_schema import LiabilityPurchaseRequest, LiabilityPurchaseResponse, LiabilitySellResponse
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

liability_bp = Blueprint('liability', __name__)


@liability_bp.route('/purchase', methods=['POST'])
@require_auth
def purchase_liability(current_user_id: str):
    """
    Purchase a lifestyle item (liability)
    
    This endpoint:
    1. Validates the request
    2. Checks if user has sufficient funds
    3. Deducts money from balance
    4. Creates the liability record
    5. Logs the transaction
    
    All operations are atomic - if any step fails, nothing is committed.
    """
    try:
        # Validate request
        data = LiabilityPurchaseRequest(**request.json)
        
        # Get liability item details from database
        from app import db
        from app import supabase
        
        # Fetch liability item
        item_response = supabase.table('liability_items').select('*').eq('id', str(data.item_id)).single().execute()
        
        if not item_response.data:
            return jsonify({
                'success': False,
                'error': 'ITEM_NOT_FOUND',
                'message': f'Liability item {data.item_id} not found'
            }), 404
        
        item = item_response.data
        purchase_price = item['base_price']
        monthly_cost = item['monthly_cost']
        
        # Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)
        
        if current_balance < purchase_price:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f'Insufficient funds. You need ${purchase_price} but only have ${current_balance}'
            }), 400
        
        # Deduct balance
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=purchase_price,
            reason=f'Purchased {item["name"]}'
        )
        
        # Create player liability
        liability_id = str(uuid.uuid4())
        supabase.table('player_liabilities').insert({
            'id': liability_id,
            'player_id': current_user_id,
            'liability_id': str(data.item_id),
            'purchase_price': purchase_price,
            'monthly_cost': monthly_cost,
            'current_value': purchase_price,  # Initial value equals purchase price
            'is_active': True,
            'purchase_date': datetime.utcnow().isoformat()
        }).execute()
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Lifestyle Purchase',
            'message': f'You purchased {item["name"]} for ${purchase_price:,.2f}',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='🚗 Lifestyle Purchase',
                body=f'You purchased {item["name"]} for ${purchase_price:,.2f}',
                notification_type='financial_move',
                data={
                    'liability_id': liability_id,
                    'amount': float(purchase_price),
                    'monthly_cost': float(monthly_cost),
                    'transaction_type': 'expense'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        response = LiabilityPurchaseResponse(
            success=True,
            message=f'Successfully purchased {item["name"]}',
            liability_id=uuid.UUID(liability_id),
            new_balance=balance_result['new_balance'],
            purchase_price=purchase_price
        )
        
        return jsonify(response.model_dump(mode='json')), 200
        
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


@liability_bp.route('/sell/<user_id>/<liability_id>', methods=['POST'])
def sell_liability(user_id: str, liability_id: str):
    """Sell a player's liability"""
    try:
        user_uuid = uuid.UUID(user_id)
        liability_uuid = uuid.UUID(liability_id)
        
        result = LiabilityService.sell_liability(liability_uuid, user_uuid)
        return jsonify({
            'message': 'Liability sold successfully',
            'data': result
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@liability_bp.route('/preview/<liability_id>', methods=['GET'])
def get_depreciation_preview(liability_id: str):
    """Get depreciation preview for a liability"""
    try:
        liability_uuid = uuid.UUID(liability_id)
        
        result = LiabilityService.get_depreciation_preview(liability_uuid)
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
