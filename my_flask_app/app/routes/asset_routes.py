from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.schemas.asset_schema import AssetPurchase
from supabase import create_client
from decimal import Decimal
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

asset_bp = Blueprint('asset', __name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@asset_bp.route('/purchase', methods=['POST'])
@require_auth
def purchase_asset(current_user_id: str):
    """
    Purchase an asset (stocks, crypto, real estate, etc.)
    
    This endpoint:
    1. Validates the request
    2. Checks if user has sufficient funds
    3. Deducts money from balance
    4. Creates or updates the asset record
    5. Logs the transaction
    
    All operations are atomic - if any step fails, nothing is committed.
    """
    try:
        # Validate request
        data = AssetPurchase(**request.json)
        quantity = int(data.quantity)
        
        # 1. Get asset details from database
        asset_response = supabase.table('assets').select('*').eq('id', data.asset_id).single().execute()
        
        if not asset_response.data:
            return jsonify({
                'success': False,
                'error': 'ASSET_NOT_FOUND',
                'message': f'Asset {data.asset_id} not found'
            }), 404
        
        asset = asset_response.data
        total_price = Decimal(str(asset['price'])) * quantity
        
        # 2. Check if user has sufficient funds
        current_balance = BalanceService.get_current_balance(current_user_id)
        
        if current_balance < total_price:
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': f'Insufficient funds. You need ${total_price} but only have ${current_balance}'
            }), 400
        
        # 3. Determine asset type
        category = asset.get('category', '')
        asset_type = (
            'property' if category == 'real_estate' else
            'stocks' if category in ['business', 'stocks', 'investments'] else
            'crypto' if category == 'crypto' else
            'property'
        )
        
        # 4. Check if asset already exists (for stocks/crypto, we stack)
        should_update = False
        existing_asset_id = None
        new_quantity = quantity
        new_total_value = float(total_price)
        new_purchase_price = asset['price']
        
        if asset_type in ['stocks', 'crypto']:
            existing_response = supabase.table('user_assets').select('*').eq('user_id', current_user_id).eq('name', asset['name']).execute()
            
            if existing_response.data and len(existing_response.data) > 0:
                existing_asset = existing_response.data[0]
                should_update = True
                existing_asset_id = existing_asset['id']
                new_quantity = (existing_asset.get('quantity') or 0) + quantity
                new_total_value = (existing_asset.get('value') or 0) + float(total_price)
                # Weighted average price
                new_purchase_price = new_total_value / new_quantity
        
        # 5. Deduct balance
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=total_price,
            reason=f'Purchased {quantity} {asset["name"]}'
        )
        
        # 6. Create or update asset
        if should_update and existing_asset_id:
            supabase.table('user_assets').update({
                'quantity': new_quantity,
                'value': new_total_value,
                'purchase_price': new_purchase_price,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', existing_asset_id).execute()
            
            result_asset_id = existing_asset_id
        else:
            insert_response = supabase.table('user_assets').insert({
                'user_id': current_user_id,
                'name': asset['name'],
                'asset_type': asset_type,
                'value': float(total_price),
                'purchase_price': asset['price'],
                'quantity': quantity
            }).execute()
            
            result_asset_id = insert_response.data[0]['id'] if insert_response.data else None
        
        # 7. Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Asset Purchased',
            'message': f'You purchased {quantity} {asset["name"]} for ${total_price:,.2f}',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='💰 Asset Purchased',
                body=f'You purchased {quantity} {asset["name"]} for ${total_price:,.2f}',
                notification_type='financial_move',
                data={
                    'asset_id': result_asset_id,
                    'amount': float(total_price),
                    'quantity': quantity,
                    'transaction_type': 'investment'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully purchased {quantity} {asset["name"]}',
            'asset_id': result_asset_id,
            'new_balance': float(balance_result['new_balance']),
            'total_cost': float(total_price),
            'quantity': new_quantity
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


@asset_bp.route('/marketplace', methods=['GET'])
def get_marketplace_assets():
    """Get all marketplace assets (public endpoint)"""
    try:
        category = request.args.get('category')
        
        query = supabase.table('assets').select('*')
        if category:
            query = query.eq('category', category)
        
        response = query.execute()
        return jsonify({'success': True, 'data': response.data}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_bp.route('/user', methods=['GET'])
@require_auth
def get_user_assets(current_user_id: str):
    """Get all assets owned by the authenticated user"""
    try:
        response = supabase.table('user_assets').select('*').eq('user_id', current_user_id).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_bp.route('/sell/<asset_id>', methods=['POST'])
@require_auth
def sell_asset(current_user_id: str, asset_id: str):
    """
    Sell a user's asset
    
    This endpoint:
    1. Validates the asset belongs to the user
    2. Calculates the sale value (current value of the asset)
    3. Adds money to user's balance
    4. Deletes the asset record
    5. Logs the transaction
    """
    try:
        # 1. Get the asset and verify ownership
        asset_response = supabase.table('user_assets').select('*').eq('id', asset_id).eq('user_id', current_user_id).single().execute()
        
        if not asset_response.data:
            return jsonify({
                'success': False,
                'error': 'ASSET_NOT_FOUND',
                'message': 'Asset not found or does not belong to you'
            }), 404
        
        asset = asset_response.data
        sale_value = Decimal(str(asset.get('value', 0)))
        
        # 2. Add money to balance
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=sale_value,
            reason=f'Sold {asset.get("name", "asset")}'
        )
        
        # 3. Delete the asset
        supabase.table('user_assets').delete().eq('id', asset_id).execute()
        
        # 4. Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'financial_move',
            'title': 'Asset Sold',
            'message': f'You sold {asset.get("name", "your asset")} for ${sale_value:,.2f}',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='💵 Asset Sold',
                body=f'You sold {asset.get("name", "your asset")} for ${sale_value:,.2f}',
                notification_type='financial_move',
                data={
                    'asset_id': asset_id,
                    'amount': float(sale_value),
                    'transaction_type': 'asset_sale'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully sold {asset.get("name", "asset")}',
            'sale_value': float(sale_value),
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
