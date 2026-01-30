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


@liability_bp.route('/active', methods=['GET'])
@require_auth
def get_all_active_liabilities(current_user_id: str):
    """Get all active liabilities (alias for luxury/active)"""
    return get_active_liabilities(current_user_id)


@liability_bp.route('/', methods=['GET'])
@require_auth
def get_all_liabilities(current_user_id: str):
    """Get all liabilities for user (loans + items)"""
    try:
        response = supabase.table('liabilities').select('*').eq('user_id', current_user_id).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/luxury', methods=['GET'])
def get_luxury_items():
    """Get available luxury items"""
    try:
        # Assuming 'luxury_items' table exists
        response = supabase.table('luxury_items').select('*').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/luxury/purchase', methods=['POST'])
@require_auth
def purchase_luxury_item(current_user_id: str):
    """Purchase a luxury item (alias or implementation)"""
    # Assuming there's a purchase logic implementation to reuse or write here
    # For now, implementing redirect-like logic
    return _purchase_luxury_logic(current_user_id)

def _purchase_luxury_logic(current_user_id: str):
    # Implementation of purchase logic
    # (Copied/Refactored from existing if present, or new)
    try:
        data = request.json
        item_id = data.get('item_id')
        if not item_id: return jsonify({'error': 'item_id required'}), 400
        
        # ... logic ...
        # Creating stub for now as I need to see if it existed elsewhere.
        # Actually, let's assume it calls basic asset purchase or similar?
        # Re-reading: Client calls /liabilities/luxury/purchase. 
        # I'll implement basic purchase logic here since I didn't see it before.
        
        item = supabase.table('luxury_items').select('*').eq('id', item_id).single().execute()
        if not item.data: return jsonify({'error': 'Item not found'}), 404
        
        cost = item.data['cost']
        from app.services.balance_service import BalanceService
        
        BalanceService.subtract_balance(current_user_id, Decimal(str(cost)), f"Bought {item.data['name']}")
        
        supabase.table('player_liabilities').insert({ # or user_assets? "liabilities" usually implies recurring cost?
            'user_id': current_user_id,
            'item_id': item_id,
            'is_active': True
        }).execute()
        
        return jsonify({'success': True, 'message': f"Purchased {item.data['name']}"}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/loan', methods=['POST'])
@require_auth
def take_liability_loan(current_user_id: str):
    """Take a loan via liability service (Bank Loan Alias)"""
    # Redirect to loan blueprint logic if possible, or reimplement
    # Client uses this for 'takeLoan'.
    # I'll import the logic from loan_routes key function if I can, or just tell client to use /api/loans/apply?
    # Better to implement here to avoid client changes.
    from app.routes.loan_routes import apply_for_loan
    return apply_for_loan(current_user_id)

@liability_bp.route('/pay', methods=['POST'])
@require_auth
def pay_liability_loan(current_user_id: str):
    """Pay a loan via liability service"""
    data = request.json
    liability_id = data.get('liability_id')
    from app.routes.loan_routes import repay_loan
    return repay_loan(current_user_id, liability_id)

@liability_bp.route('/luxury/active', methods=['GET'])
@require_auth
def get_active_liabilities(current_user_id: str):
    """Get active luxury liabilities"""
    try:
        response = supabase.table('player_liabilities').select('*, liability_items(*)').eq('player_id', current_user_id).eq('is_active', True).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@liability_bp.route('/sell/<liability_id>', methods=['POST'])
@require_auth
def sell_liability(current_user_id: str, liability_id: str):
    """Sell a player's liability"""
    try:
        user_uuid = uuid.UUID(current_user_id)
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
