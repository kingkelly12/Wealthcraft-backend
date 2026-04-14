from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.liability_service import LiabilityService
from app.services.balance_service import BalanceService
from app.services.mentor_service import MentorService
from app.utils.jwt_helper import require_auth
from app.schemas.liability_schema import LiabilityPurchaseRequest, LiabilityPurchaseResponse, LiabilitySellResponse
import uuid
from datetime import datetime
from decimal import Decimal
from app.services.push_notification_service import ExpoPushService
from app import supabase
from app.services.profile_service import ProfileService
import logging

logger = logging.getLogger(__name__)

def resolve_user_ids(user_id):
    """
    Given a user_id (could be Auth UID or Profile ID),
    return a list of both possible IDs to ensure robust matching across tables.
    """
    try:
        uuid_obj = uuid.UUID(user_id)
        # Try finding profile by user_id First
        profile = ProfileService.get_profile_by_user_id(uuid_obj)
        if profile:
            return [str(profile.user_id), str(profile.id)]
        
        # If not found, try finding by profile ID
        from app.models.profile import Profile
        profile = Profile.query.filter_by(id=uuid_obj).first()
        if profile:
            return [str(profile.user_id), str(profile.id)]
            
        return [user_id]
    except:
        return [user_id]


liability_bp = Blueprint('liability', __name__)

def get_active_liabilities_internal(user_id):
    """Internal function to fetch active liabilities (luxury + loans)"""
    try:
        user_ids = resolve_user_ids(user_id)
        # 1. Fetch luxury items
        luxury_res = supabase.table('player_liabilities').select('*, liability_items(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        luxury_items = luxury_res.data or []
        
        # 2. Fetch loans
        loans_res = supabase.table('liabilities').select('*').in_('user_id', user_ids).execute()
        loans = loans_res.data or []
        
        # 3. Normalize luxury items
        normalized_luxury = []
        for li in luxury_items:
            item = li.get('liability_items')
            # Handle case where join returns a list
            if isinstance(item, list) and len(item) > 0:
                item = item[0]
            
            if item:
                normalized_luxury.append({
                    'id': li['id'],
                    'liability_id': li['liability_id'],
                    'name': item['name'],
                    'amount': li['current_value'] or li['purchase_price'],
                    'purchase_price': li['purchase_price'],
                    'current_value': li['current_value'],
                    'monthly_payment': li['monthly_cost'],
                    'image_url': item.get('image_url'),
                    'category': 'luxury',
                    'type': 'lifestyle'
                })
        
        # 4. Normalize liabilities from 'liabilities' table (Legacy Luxury + Loans)
        normalized_other = []
        for loan in loans:
            l_type = loan.get('liability_type', 'bank_loan')
            is_luxury = l_type == 'luxury'
            
            normalized_other.append({
                'id': loan['id'],
                'name': loan['name'] or ('P2P Loan' if l_type == 'p2p_loan' else 'Bank Loan'),
                'amount': loan.get('remaining_balance') or loan.get('remaining_amount') or loan['amount'],
                'monthly_payment': loan['monthly_payment'],
                'image_url': loan.get('image_url'), # Include image for both if exists
                'category': 'luxury' if is_luxury else 'loan',
                'type': 'lifestyle' if is_luxury else 'loan',
                'liability_type': l_type
            })
        
        return normalized_luxury + normalized_other
    except Exception as e:
        print(f"Error fetching active liabilities for user {user_id}: {str(e)}")
        raise e


@liability_bp.route('/purchase/', methods=['POST'])
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
        
        # Notify followers of liability purchase
        # (User gets immediate toast feedback from API response)
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='buy_liability',
            item_name=item['name'],
            amount=float(purchase_price)
        )

        try:
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='buy_liability',
                action_data={
                    'cost': purchase_price,
                    'item_name': item['name']
                }
            )
            
            if trigger:
                # Send mentor message to player (with push notification)
                MentorService.send_mentor_message(
                    player_id=current_user_id,
                    mentor_data=trigger,
                    metrics={},
                    supabase_client=supabase
                )
        except Exception as e:
            print(f"Failed to trigger mentor response: {str(e)}")
        
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


@liability_bp.route('/active/', methods=['GET'])
@require_auth
def get_all_active_liabilities(current_user_id: str):
    """Get all active liabilities (alias for luxury/active)"""
    try:
        liabilities = get_active_liabilities_internal(current_user_id)
        return jsonify({'success': True, 'data': liabilities}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/user/<user_id>/', methods=['GET'])
@require_auth
def get_user_liabilities(current_user_id: str, user_id: str):
    """Get specific user's active liabilities"""
    try:
        liabilities = get_active_liabilities_internal(user_id)
        return jsonify({'success': True, 'data': liabilities}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@liability_bp.route('/', methods=['GET'])
@require_auth
def get_all_liabilities(current_user_id: str):
    """Get all liabilities for user (loans + items)"""
    try:
        response = supabase.table('liabilities').select('*').eq('user_id', current_user_id).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/luxury/overview/', methods=['GET'])
@require_auth
def get_luxury_overview(current_user_id: str):
    """
    Consolidated endpoint for Upgrade Lifestyle screen.
    Returns both available luxury items and user's current luxury assets.
    """
    try:
        user_ids = resolve_user_ids(current_user_id)
        
        # 1. Fetch available items
        available_res = supabase.table('liability_items').select('*').execute()
        available_items = available_res.data or []
        
        # 2. Fetch active items (using internal helper)
        all_active = get_active_liabilities_internal(current_user_id)
        active_luxury = [li for li in all_active if li.get('category') == 'luxury']
        
        # 3. Get balance (already imported or using Service)
        balance = BalanceService.get_current_balance(current_user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'available': available_items,
                'active': active_luxury,
                'balance': float(balance)
            }
        }), 200
        
    except Exception as e:
        print(f"[Luxury Overview] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500


@liability_bp.route('/luxury/', methods=['GET'])
def get_luxury_items():
    """Get available luxury items"""
    try:
        # Query luxury items from liability_items table
        response = supabase.table('liability_items').select('*').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/luxury/purchase/', methods=['POST'])
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
        
        # Query from liability_items table (not luxury_items)
        item = supabase.table('liability_items').select('*').eq('id', item_id).single().execute()
        if not item.data: return jsonify({'error': 'Item not found'}), 404
        
        # Use base_price field (not cost)
        cost = item.data.get('base_price') or item.data.get('cost')
        monthly_cost = item.data.get('monthly_cost', 0)
        
        from app.services.balance_service import BalanceService
        
        BalanceService.subtract_balance(current_user_id, Decimal(str(cost)), f"Bought {item.data['name']}")
        
        supabase.table('player_liabilities').insert({
            'player_id': current_user_id,
            'liability_id': item_id,
            'purchase_price': float(cost),
            'monthly_cost': float(monthly_cost),
            'is_active': True,
            'purchase_date': datetime.utcnow().isoformat()
        }).execute()
        
        return jsonify({'success': True, 'message': f"Purchased {item.data['name']}"}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@liability_bp.route('/loan/', methods=['POST'])
@require_auth
def take_liability_loan(current_user_id: str):
    """Take a loan via liability service (Bank Loan Alias)"""
    # Redirect to loan blueprint logic if possible, or reimplement
    # Client uses this for 'takeLoan'.
    # I'll import the logic from loan_routes key function if I can, or just tell client to use /api/loans/apply?
    # Better to implement here to avoid client changes.
    from app.routes.loan_routes import apply_for_loan
    return apply_for_loan(current_user_id)

@liability_bp.route('/pay/', methods=['POST'])
@require_auth
def pay_liability_loan(current_user_id: str):
    """Pay a loan via liability service"""
    data = request.json
    liability_id = data.get('liability_id')
    from app.routes.loan_routes import repay_loan
    return repay_loan(current_user_id, liability_id)

@liability_bp.route('/luxury/active/', methods=['GET'])
@require_auth
def get_active_liabilities(current_user_id: str):
    """Get active luxury liabilities"""
    try:
        liabilities = get_active_liabilities_internal(current_user_id)
        return jsonify({'success': True, 'data': liabilities}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@liability_bp.route('/sell/<liability_id>/', methods=['POST'])
@require_auth
def sell_liability(current_user_id: str, liability_id: str):
    """Sell a player's liability"""
    try:
        user_uuid = uuid.UUID(current_user_id)
        liability_uuid = uuid.UUID(liability_id)
        
        result = LiabilityService.sell_liability(liability_uuid, user_uuid)
        
        # Notify followers about the sale
        try:
            item_name = result.get('name', 'liability') if isinstance(result, dict) else 'liability'
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='sell_liability',
                item_name=item_name
            )
        except Exception as e:
            logger.error(f"Failed to notify followers of liability sale: {str(e)}")
        
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

@liability_bp.route('/cron/monthly-depreciation', methods=['POST'])
def cron_monthly_depreciation():
    """
    Cron job endpoint for monthly depreciation
    Called by Supabase Edge Functions (monthly-depreciation)
    
    This endpoint:
    1. Backfills any liabilities missing initial values
    2. Applies monthly depreciation to all active liabilities
    3. Returns summary of updates
    """
    try:
        # 1. Backfill any liabilities missing initial values (safety check)
        backfill_result = LiabilityService.backfill_existing_liabilities()
        
        # 2. Apply monthly depreciation
        result = LiabilityService.apply_monthly_depreciation()
        
        return jsonify({
            'success': True,
            'backfilled': backfill_result.get('backfilled_count', 0),
            'updated': result.get('updated_count', 0),
            'total_depreciation': result.get('total_depreciation', 0),
            'date': result.get('date')
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500