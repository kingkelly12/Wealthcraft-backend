from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.mentor_service import MentorService
from app.schemas.asset_schema import AssetPurchase
from app import supabase
from app.utils.mission_constraints import enforce_mission_constraints
from decimal import Decimal
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


VOLATILE_TYPES = ('stocks', 'crypto', 'forex')


def _asset_type_for(category: str) -> str:
    return {
        'real_estate': 'property',
        'business': 'business',   # not market-priced: appreciates monthly like property
        'stocks': 'stocks',
        'investments': 'stocks',
        'crypto': 'crypto',
        'forex': 'forex',
    }.get(category or '', 'property')


@asset_bp.route('/purchase/', methods=['POST'])
@require_auth
def purchase_asset(current_user_id: str):
    """
    Purchase an asset. The wallet is debited atomically first (adjust_balance
    refuses to overdraw); if writing the holding then fails, the debit is refunded.
    """
    try:
        data = AssetPurchase(**(request.get_json(silent=True) or {}))
        quantity = Decimal(str(data.quantity))

        asset_response = supabase.table('assets').select('*').eq('id', data.asset_id).limit(1).execute()
        if not asset_response.data:
            return jsonify({
                'success': False,
                'error': 'ASSET_NOT_FOUND',
                'message': f'Asset {data.asset_id} not found'
            }), 404

        asset = asset_response.data[0]
        # Your market's price (it moves with your game weeks: app/game/market.py).
        from app.game import market as game_market
        unit_price = game_market.price_of(current_user_id, asset)
        total_price = (unit_price * quantity).quantize(Decimal('0.01'))
        if total_price <= 0:
            return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Quantity too small'}), 400

        asset_type = _asset_type_for(asset.get('category'))

        blocked = enforce_mission_constraints(current_user_id, 'buy_asset', {'category': asset.get('category'), 'asset_type': asset_type})
        if blocked:
            return blocked

        # 1. Debit first (atomic, cannot overdraw)
        balance_result = BalanceService.subtract_balance(
            user_id=current_user_id,
            amount=total_price,
            reason=f'Purchased {quantity} {asset["name"]}',
            category='asset_purchase',
        )

        # 2. Create or stack the holding; refund if this fails
        try:
            existing = None
            if asset_type in VOLATILE_TYPES:
                existing_response = supabase.table('user_assets').select('*') \
                    .eq('user_id', current_user_id).eq('name', asset['name']).limit(1).execute()
                existing = existing_response.data[0] if existing_response.data else None

            if existing:
                old_qty = Decimal(str(existing.get('quantity') or 0))
                old_basis = Decimal(str(existing.get('purchase_price') or 0)) * old_qty
                new_quantity = old_qty + quantity
                supabase.table('user_assets').update({
                    'quantity': float(new_quantity),
                    'value': float(new_quantity * unit_price),
                    # weighted-average cost basis per unit
                    'purchase_price': float(((old_basis + total_price) / new_quantity).quantize(Decimal('0.01'))),
                    'asset_id': asset['id'],
                }).eq('id', existing['id']).execute()
                result_asset_id = existing['id']
            else:
                new_quantity = quantity
                insert_response = supabase.table('user_assets').insert({
                    'user_id': current_user_id,
                    'asset_id': asset['id'],
                    'name': asset['name'],
                    'asset_type': asset_type,
                    'value': float(total_price),
                    'purchase_price': float(unit_price),
                    'quantity': float(quantity),
                }).execute()
                result_asset_id = insert_response.data[0]['id'] if insert_response.data else None
        except Exception:
            logger.exception('Asset write failed after debit; refunding %s', current_user_id)
            BalanceService.add_balance(current_user_id, total_price, f'Refund: failed purchase of {asset["name"]}', category='refund')
            raise

        ProfileService.recalculate_monthly_income(uuid.UUID(current_user_id))
        ProfileService.recalculate_net_worth(uuid.UUID(current_user_id))

        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='buy_asset',
            item_name=asset['name'],
            amount=float(total_price)
        )

        try:
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='buy_asset',
                action_data={'cost': float(total_price), 'asset_name': asset['name'], 'quantity': float(quantity)}
            )
            if trigger:
                MentorService.send_mentor_message(
                    player_id=current_user_id, mentor_data=trigger, metrics={}, supabase_client=supabase
                )
        except Exception as e:
            logger.warning(f"Failed to trigger mentor response: {e}")

        return jsonify({
            'success': True,
            'message': f'Successfully purchased {quantity} {asset["name"]}',
            'asset_id': result_asset_id,
            'new_balance': float(balance_result['new_balance']),
            'total_cost': float(total_price),
            'quantity': float(new_quantity)
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
            # Say how far short the player is, so the app can offer a loan for the gap.
            needed = locals().get('total_price')
            have = BalanceService.get_current_balance(current_user_id) if needed is not None else None
            short = max(Decimal('0'), needed - have) if needed is not None else None
            return jsonify({
                'success': False,
                'error': 'INSUFFICIENT_FUNDS',
                'message': (f"You're ${short:,.0f} short. Borrow from the bank or a friend and let it pay you back."
                            if short else 'Insufficient funds for this purchase'),
                'data': {'needed': float(needed), 'balance': float(have), 'short': float(short)} if short is not None else None,
            }), 400
        logger.exception('purchase_asset failed')
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
    from app.game import economy
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
        
        # Traded assets show your market's price and this week's move.
        from app.game import market as game_market
        mine = game_market.view(current_user_id, market_res.data or [])
        listings = []
        for a in market_res.data or []:
            p = mine.get(str(a['id']))
            if p:
                a = {**a, 'price': float(p['price']), 'price_change': p['change'], 'price_change_percent': p['change_pct']}
            if (a.get('category') or '').lower() in game_market.TRADED:
                drift, vol = game_market.params(a)
                a['expected_growth_pct'] = round(drift * 100, 1)
                a['volatility_pct'] = round(vol * 100)
            listings.append({**a, 'income': economy.income_figures(a.get('monthly_income'), 1, a.get('price'), a.get('category'), a.get('risk_level'))})
        events = [{'headline': f"{e['emoji']} {e['title']}", 'body': e['body'],
                   'analyst_tip': 'Big swings are normal. Selling in a panic is how most people lose money.',
                   'market_mood': 'Crash' if (e.get('shock_pct') or 0) < 0 else 'Boom',
                   'market_mood_emoji': e['emoji'], 'created_at': e.get('created_at')}
                  for e in game_market.recent_events(current_user_id, 3)]

        return jsonify({
            'success': True,
            'data': {
                'market': listings,
                'portfolio': portfolio or [],
                'profile': profile,
                'news': events + (news_res.data or [])
            }
        }), 200
    except Exception as e:
        logger.error(f"Overview error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def with_income_figures(holdings):
    """Add income per week / month / year, yield and expected growth to each holding."""
    from app.game import economy
    names = list({h.get('name') for h in holdings if h.get('name')})
    if not names:
        return holdings
    catalog = supabase.table('assets').select('name, monthly_income, category, risk_level').in_('name', names).execute().data or []
    by_name = {a['name']: a for a in catalog}
    for h in holdings:
        a = by_name.get(h.get('name'), {})
        h['income'] = economy.income_figures(a.get('monthly_income'), h.get('quantity') or 1,
                                             h.get('purchase_price'), a.get('category') or h.get('asset_type'), a.get('risk_level'))
    return holdings


def get_user_assets_internal(user_id):
    """Internal function to fetch user assets without require_auth injection"""
    try:
        user_ids = resolve_user_ids(user_id)
        response = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        return with_income_figures(response.data or [])
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

@asset_bp.route('/sell/', methods=['POST'])
@asset_bp.route('/sell/<asset_id>/', methods=['POST'])
@require_auth
def sell_asset(current_user_id: str, asset_id: str = None):
    """
    Sell all or part of a holding.

    Body (all optional when asset_id is in the URL):
        { "asset_id": "<user_assets.id>", "quantity": <number> }   # omit quantity = sell everything

    The holding is claimed atomically (conditional delete/update on the quantity
    we read) BEFORE money is credited, so two concurrent sell requests can't
    both get paid for the same shares.
    """
    try:
        body = request.get_json(silent=True) or {}
        asset_id = asset_id or body.get('asset_id')
        if not asset_id:
            return jsonify({'success': False, 'error': 'MISSING_ID', 'message': 'asset_id is required'}), 400

        blocked = enforce_mission_constraints(current_user_id, 'sell_asset')
        if blocked:
            return blocked

        user_ids = resolve_user_ids(current_user_id)
        asset_response = supabase.table('user_assets').select('*').eq('id', asset_id).in_('user_id', user_ids).execute()
        if not asset_response.data:
            return jsonify({
                'success': False,
                'error': 'ASSET_NOT_FOUND',
                'message': 'Asset not found or does not belong to you'
            }), 404

        asset = asset_response.data[0]
        held_qty = Decimal(str(asset.get('quantity') or 1))
        cost_basis_unit = Decimal(str(asset.get('purchase_price') or 0))

        sell_qty = held_qty
        if body.get('quantity') is not None:
            sell_qty = Decimal(str(body['quantity']))
            if sell_qty <= 0:
                return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Quantity must be positive'}), 400
            sell_qty = min(sell_qty, held_qty)

        # Unit sale price: live market price for volatile assets, appreciated value otherwise.
        if asset.get('asset_type') in VOLATILE_TYPES:
            from app.game import market as game_market
            listing = supabase.table('assets').select('*').eq('name', asset.get('name')).limit(1).execute()
            unit_price = game_market.price_of(current_user_id, listing.data[0]) if listing.data else cost_basis_unit
        else:
            unit_price = Decimal(str(asset.get('value') or 0)) / held_qty

        sale_value = (unit_price * sell_qty).quantize(Decimal('0.01'))
        profit = ((unit_price - cost_basis_unit) * sell_qty).quantize(Decimal('0.01'))

        # 1. Atomically claim the shares
        if sell_qty >= held_qty:
            claim = supabase.table('user_assets').delete() \
                .eq('id', asset_id).eq('quantity', float(held_qty)).execute()
        else:
            remaining = held_qty - sell_qty
            claim = supabase.table('user_assets').update({
                'quantity': float(remaining),
                'value': float((unit_price * remaining).quantize(Decimal('0.01'))),
            }).eq('id', asset_id).eq('quantity', float(held_qty)).execute()
        if not claim.data:
            return jsonify({
                'success': False,
                'error': 'CONFLICT',
                'message': 'This holding changed while you were selling. Refresh and try again.'
            }), 409

        # 2. Pay out
        balance_result = BalanceService.add_balance(
            user_id=current_user_id,
            amount=sale_value,
            reason=f'Sold {sell_qty} {asset.get("name", "asset")}',
            category='asset_sale',
        ) if sale_value > 0 else {'new_balance': BalanceService.get_current_balance(current_user_id)}

        try:
            user_uuid = uuid.UUID(current_user_id)
            ProfileService.update_trading_profits(user_uuid, float(profit))
            ProfileService.recalculate_monthly_income(user_uuid)
        except Exception as e:
            logger.error(f"Failed to update trading profits for user {current_user_id}: {e}")

        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase,
            user_id=current_user_id,
            move_type='sell_asset',
            item_name=asset.get('name', 'asset'),
            amount=float(sale_value),
            profit=float(profit)
        )

        try:
            trigger = MentorService.check_real_time_triggers(
                player_id=current_user_id,
                action='sell_assets',
                action_data={
                    'amount': float(sale_value),
                    'asset_name': asset.get('name'),
                    'profit': float(profit),
                    'percentage_sold': float(sell_qty / held_qty),
                }
            )
            if trigger:
                MentorService.send_mentor_message(
                    player_id=current_user_id, mentor_data=trigger, metrics={}, supabase_client=supabase
                )
        except Exception as e:
            logger.warning(f"Failed to trigger mentor response: {e}")

        return jsonify({
            'success': True,
            'message': f'Successfully sold {asset.get("name", "asset")}',
            'sale_value': float(sale_value),
            'profit': float(profit),
            'quantity_sold': float(sell_qty),
            'new_balance': float(balance_result['new_balance'])
        }), 200

    except Exception as e:
        logger.exception('sell_asset failed')
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
