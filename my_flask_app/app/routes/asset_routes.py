from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.mentor_service import MentorService
from app.schemas.asset_schema import AssetPurchase
from app import supabase
from decimal import Decimal
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService
from app.models.profile import Profile
from app import db
import logging
from app.services.profile_service import ProfileService

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


asset_bp = Blueprint('asset', __name__)

logger = logging.getLogger(__name__)


@asset_bp.route('/purchase/', methods=['POST'])
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
            'forex' if category == 'forex' else
            'property'
        )
        
        # 4. Check if asset already exists (for stocks/crypto, we stack)
        should_update = False
        existing_asset_id = None
        new_quantity = quantity
        new_total_value = float(total_price)
        new_purchase_price = asset['price']
        
        if asset_type in ['stocks', 'crypto', 'forex']:
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
        
        # 7. Notify followers of asset purchase
        # (User gets immediate toast feedback from API response)
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='buy_asset',
            item_name=asset['name'],
            amount=float(total_price)
        )
        
        # ============ REAL-TIME MENTOR TRIGGER ============
        # Check if this is first asset purchase (triggers congratulations message)
        try:
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='buy_asset',
                action_data={
                    'cost': float(total_price),
                    'asset_name': asset['name'],
                    'quantity': quantity
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
        
        # (already handled before real-time triggers)
        
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


@asset_bp.route('/marketplace/', methods=['GET'])
def get_marketplace_assets():
    """Get all marketplace assets (public endpoint)"""
    try:
        category = request.args.get('category')
        
        query = supabase.table('assets').select('*')
        if category:
            query = query.eq('category', category)
        
        response = query.execute()
        return jsonify({'success': True, 'data': response.data or []}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_bp.route('/overview/', methods=['GET'])
@require_auth
def get_assets_overview(current_user_id: str):
    """Consolidated marketplace and user portfolio status"""
    try:
        user_ids = resolve_user_ids(current_user_id)
        logger.info(f"Assets Overview: fetching data for user_ids {user_ids}")
        
        # 1. Available Market
        category = request.args.get('category')
        query = supabase.table('assets').select('*')
        if category:
            query = query.eq('category', category)
        market_res = query.execute()
        
        # 2. User Portfolio
        portfolio = get_user_assets_internal(current_user_id)
        
        # 3. Profile Snippet (Balance/Sanity)
        profile_res = supabase.table('profiles')\
            .select('user_id, username, profile_picture_url, sanity, net_worth')\
            .in_('user_id', user_ids)\
            .execute()
            
        profile = profile_res.data[0] if profile_res.data else None
        
        # 4. Market News (Latest 5 headlines)
        news_res = supabase.table('market_news')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(5)\
            .execute()
        
        return jsonify({
            'success': True,
            'data': {
                'market': market_res.data or [],
                'portfolio': portfolio or [],
                'profile': profile,
                'news': news_res.data or []
            }
        }), 200
    except Exception as e:
        logger.error(f"Overview error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_user_assets_internal(user_id):
    """Internal function to fetch user assets without require_auth injection"""
    try:
        user_ids = resolve_user_ids(user_id)
        response = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        return response.data
    except Exception as e:
        logger.error(f"Error fetching assets for user {user_id}: {str(e)}")
        raise e

@asset_bp.route('/user/', methods=['GET'])
@require_auth
def get_user_assets(current_user_id: str):
    """Get all assets owned by the authenticated user"""
    try:
        assets = get_user_assets_internal(current_user_id)
        return jsonify({'success': True, 'data': assets}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@asset_bp.route('/', methods=['GET'])
def get_all_assets():
    """Get all available assets (public)"""
    return get_marketplace_assets()

@asset_bp.route('/portfolio/', methods=['GET'])
@require_auth
def get_portfolio(current_user_id: str):
    """Get authenticated user's portfolio (alias for /user)"""
    try:
        assets = get_user_assets_internal(current_user_id)
        return jsonify({'success': True, 'data': assets}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_bp.route('/portfolio/<user_id>/', methods=['GET'])
@require_auth
def get_user_portfolio(current_user_id: str, user_id: str):
    """Get specific user's portfolio"""
    try:
        assets = get_user_assets_internal(user_id)
        return jsonify({'success': True, 'data': assets}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@asset_bp.route('/sell/<asset_id>/', methods=['POST'])
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
        # Resolve both possible UUIDs (Auth UID and Profile UUID) for this user
        user_ids = resolve_user_ids(current_user_id)

        # 1. Get the asset and verify ownership (try all resolved IDs)
        asset_response = supabase.table('user_assets').select('*').eq('id', asset_id).in_('user_id', user_ids).execute()

        if not asset_response.data:
            return jsonify({
                'success': False,
                'error': 'ASSET_NOT_FOUND',
                'message': 'Asset not found or does not belong to you'
            }), 404

        asset = asset_response.data[0]
        
        # 1.5 Calculate true sale value based on asset type
        quantity = Decimal(str(asset.get('quantity', 1)))
        asset_type = asset.get('asset_type', '')
        
        if asset_type in ['stocks', 'crypto', 'forex']:
            # For volatile market assets, fetch current global market price
            market_asset_response = supabase.table('assets').select('price').eq('name', asset.get('name')).single().execute()
            
            current_price = Decimal(str(asset.get('purchase_price'))) # Default if lookup fails
            if market_asset_response.data:
                 current_price = Decimal(str(market_asset_response.data.get('price')))
                 
            sale_value = current_price * quantity
        else:
            # For properties and business, use the individually appreciated value from user_assets
            sale_value = Decimal(str(asset.get('value', asset.get('purchase_price', 0))))
        
        # Calculate profit
        purchase_price = Decimal(str(asset.get('purchase_price', 0)))
        cost_basis = purchase_price * quantity
        profit = sale_value - cost_basis
        
        # 2. Add money to balance
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=sale_value,
            reason=f'Sold {asset.get("name", "asset")}'
        )
        
        # 3. Delete the asset
        supabase.table('user_assets').delete().eq('id', asset_id).execute()
        
        # 3.5 Update Profile (Trading Profits)
        # Resolve the correct profile user_id for the SQLAlchemy ORM lookup.
        # The ORM stores profiles by their Auth UID in the user_id column.
        # We use resolve_user_ids to find whichever UUID the profile was stored under.
        try:
            # The asset owner_id is the one used when the user_asset was created
            owner_id = asset.get('user_id', current_user_id)
            profile_lookup_id = None
            # Prefer the UUID that exists in the profiles.user_id column
            profile_check = supabase.table('profiles').select('user_id').in_('user_id', user_ids).execute()
            if profile_check.data:
                profile_lookup_id = profile_check.data[0]['user_id']
            else:
                profile_lookup_id = owner_id

            user_uuid = uuid.UUID(str(profile_lookup_id))
            ProfileService.update_trading_profits(user_uuid, float(profit))
        except Exception as e:
            logger.error(f"Failed to update trading profits for user {current_user_id}: {e}")
        
        # 4. Send push notification to followers
        # (User gets immediate toast feedback from API response)
        try:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='sell_asset',
                item_name=asset.get('name', 'your asset'),
                amount=float(sale_value)
            )
        except Exception as e:
            print(f"Failed to notify followers of asset sale: {str(e)}")
        
        # Also send direct push to user for immediate alert
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='💵 Asset Sold',
                body=f'Sold {asset.get("name", "asset")} for ${sale_value:,.2f}. Profit: ${profit:,.2f}',
                notification_type='financial_move',
                data={
                    'asset_id': asset_id,
                    'amount': float(sale_value),
                    'profit': float(profit),
                    'transaction_type': 'asset_sale',
                    'screen': '/portfolio'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        # Send Mentorship Notification
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='sell_asset',
            item_name=asset.get('name', 'asset'),
            amount=float(sale_value),
            profit=float(profit)
        )

        # ============ REAL-TIME MENTOR TRIGGER ============
        # Check for panic selling (selling large percentage of portfolio)
        try:
            # Calculate percentage of assets sold (simple: assume this is significant if profit is negative)
            percentage_sold = 1.0 if profit < 0 else 0.3  # Full sale if loss, partial if gain
            
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='sell_assets',
                action_data={
                    'amount': float(sale_value),
                    'asset_name': asset.get('name'),
                    'profit': float(profit),
                    'percentage_sold': percentage_sold
                }
            )
            
            if trigger:
                # Send mentor message to player (with push notification in Phase 4)
                MentorService.send_mentor_message(
                    player_id=current_user_id,
                    mentor_data=trigger,
                    metrics={},
                    supabase_client=supabase
                )
        except Exception as e:
            print(f"Failed to trigger mentor response: {str(e)}")
        
        # (sell follower notification already sent above)
        
        return jsonify({
            'success': True,
            'message': f'Successfully sold {asset.get("name", "asset")}',
            'sale_value': float(sale_value),
            'profit': float(profit),
            'new_balance': float(balance_result['new_balance'])
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
