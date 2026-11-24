from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.profile_service import ProfileService
from app.schemas.profile_schema import ProfileCreate, ProfileUpdate, ProfileResponse
from app.routes.rental_routes import get_current_rental_internal
from app import supabase
import uuid
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

profile_bp = Blueprint('profile', __name__)

from app.utils.jwt_helper import require_auth

@profile_bp.route('/me/', methods=['GET'])
@require_auth
def get_current_user_profile(current_user_id: str):
    """Get authenticated user's profile"""
    return get_profile(current_user_id)

@profile_bp.route('/dashboard/', methods=['GET'])
@require_auth
def get_dashboard_data(current_user_id: str):
    """Get dashboard data (profile, balance, etc.)"""
    try:
        from app.services.balance_service import BalanceService
        
        # Get profile
        profile = ProfileService.get_profile_by_user_id(uuid.UUID(current_user_id))
        if not profile:
             return jsonify({'error': 'Profile not found'}), 404
             
        # Get balance
        balance = BalanceService.get_current_balance(current_user_id)
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict(),
                'balance': float(balance)
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _homes_for(uid):
    from app.game import homes
    try:
        return [homes._view(h) for h in homes.owned(uid)]
    except Exception as e:
        logger.warning(f"Homes for {uid} failed: {e}")
        return []


def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _owned_grid(assets, liabilities, homes_list):
    """What a player owns, as tiles for the profile grid: homes, flex items and businesses."""
    tiles = []
    for h in homes_list:
        tiles.append({'kind': 'home', 'id': h.get('id'), 'name': h.get('name'), 'image_url': h.get('image_url'),
                      'category': h.get('home_type'), 'value': _num(h.get('value')),
                      'note': 'Lives here' if h.get('lives_in') else 'Let out'})
    for li in liabilities:
        item = li.get('liability_items') or {}
        if isinstance(item, list):
            item = item[0] if item else {}
        tiles.append({'kind': 'item', 'id': li.get('id'), 'name': item.get('name') or li.get('name') or 'Item',
                      'image_url': item.get('image_url'), 'category': item.get('category'),
                      'value': _num(li.get('current_value') if li.get('current_value') is not None else li.get('purchase_price')),
                      'note': 'Leased out' if li.get('is_leased') else None})
    ids = [a['asset_id'] for a in assets if a.get('asset_id')]
    listings = {}
    if ids:
        try:
            listings = {str(r['id']): r for r in supabase.table('assets').select('id, name, category, image_url').in_('id', ids).execute().data or []}
        except Exception as e:
            logger.warning(f"Asset listings for the profile grid failed: {e}")
    for a in assets:
        row = listings.get(str(a.get('asset_id'))) or {}
        if (row.get('category') or a.get('asset_type') or '').lower() != 'business':
            continue
        tiles.append({'kind': 'business', 'id': a.get('id'), 'name': row.get('name') or a.get('name'), 'image_url': row.get('image_url'),
                      'category': 'business', 'value': _num(a.get('value')), 'note': None})
    tiles.sort(key=lambda t: -t['value'])
    return tiles


@profile_bp.route('/overview/', methods=['GET'])
@require_auth
def get_comprehensive_dashboard(current_user_id: str):
    """
    ULTIMATE CONSOLIDATION: Returns everything for the home/profile screen.
    Reduces up to 8 separate calls to 1.
    Optimized to avoid redundant resolve_user_ids calls.
    """
    from app.game import economy
    try:
        # Check if we're looking at another user's profile
        target_user_id = request.args.get('user_id', current_user_id)
        
        # Resolve user IDs ONCE at the start
        user_ids = resolve_user_ids(target_user_id)
        logger.info(f"Dashboard Overview: fetching data for user_ids {user_ids}")

        # 1. Profile
        profile = None
        for uid in user_ids:
            try:
                profile = ProfileService.get_profile_by_user_id(uuid.UUID(uid))
                if profile: break
            except: continue
            
        if not profile:
             # Fallback: try to fetch by profile ID directly if user_id lookup failed
             from app.models.profile import Profile
             profile = Profile.query.filter((Profile.user_id.in_(user_ids)) | (Profile.id.in_(user_ids))).first()

        # 2. Balance
        from app.services.balance_service import BalanceService
        balance = BalanceService.get_current_balance(target_user_id)
        
        # Standardize balance to float
        try:
            balance = float(balance)
        except:
            balance = 0.0

        # Batch Supabase calls together to reduce network roundtrips
        # 3. Assets
        assets_res = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        assets = assets_res.data or []
        
        # 4. Liabilities
        # Try to fetch with liability_items relationship
        try:
            liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        except:
            # Fallback: fetch without relationship
            liabilities_res = supabase.table('player_liabilities').select('*').in_('player_id', user_ids).eq('is_active', True).execute()
        liabilities = liabilities_res.data or []
        
        # 5. Jobs
        jobs_res = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        jobs = jobs_res.data or []
        
        # 6. Rental - Use resolved user_ids to avoid additional lookups
        rental = None
        try:
            rental_response = supabase.table('player_rentals')\
                .select('*, rental_properties(*)')\
                .in_('player_id', user_ids)\
                .eq('is_active', True)\
                .maybe_single()\
                .execute()
            rental = rental_response.data if rental_response else None
        except Exception as e:
            logger.warning(f"Error fetching rental for user {target_user_id}: {str(e)}")
            rental = None

        # 7. Social Stats (Followers/Following) - Parallel queries
        followers_res = supabase.table('user_follows').select('id', count='exact').in_('following_id', user_ids).execute()
        following_res = supabase.table('user_follows').select('id', count='exact').in_('follower_id', user_ids).execute()
        
        # 8. Rank
        net_worth = profile.net_worth if profile else 0
        rank_res = supabase.table('profiles').select('id', count='exact').gt('net_worth', net_worth).execute()
        rank = (rank_res.count or 0) + 1

        # 8b. You and them: do you follow them, do they follow you (not on your own profile)
        relationship = None
        if str(target_user_id) not in [str(current_user_id)]:
            try:
                is_following = bool(supabase.table('user_follows').select('id').eq('follower_id', current_user_id)
                                    .in_('following_id', user_ids).limit(1).execute().data)
                follows_you = bool(supabase.table('user_follows').select('id').in_('follower_id', user_ids)
                                   .eq('following_id', current_user_id).limit(1).execute().data)
                relationship = {'is_following': is_following, 'follows_you': follows_you}
            except Exception as e:
                logger.warning(f"Relationship lookup failed: {e}")

        # 8c. Their timeline: what they bought, sold, started and quit
        try:
            activity = supabase.table('player_activity').select('id, kind, emoji, text, amount, profit, created_at') \
                .in_('user_id', user_ids).order('created_at', desc=True).limit(30).execute().data or []
        except Exception as e:
            logger.warning(f"Activity lookup failed: {e}")
            activity = []

        # 8d. The balance sheet: what they own and what they owe
        homes_list = _homes_for(target_user_id)
        try:
            loans = supabase.table('liabilities').select('remaining_balance').in_('user_id', user_ids).execute().data or []
        except Exception as e:
            logger.warning(f"Debt lookup failed: {e}")
            loans = []
        owned = _owned_grid(assets, liabilities, homes_list)
        investments = sum(_num(a.get('value')) for a in assets) - sum(t['value'] for t in owned if t['kind'] == 'business')
        balance_sheet = {
            'cash': float(balance),
            'investments': round(max(investments, 0), 2),
            'businesses': round(sum(t['value'] for t in owned if t['kind'] == 'business'), 2),
            'homes': round(sum(t['value'] for t in owned if t['kind'] == 'home'), 2),
            'possessions': round(sum(t['value'] for t in owned if t['kind'] == 'item'), 2),
            'debt': round(sum(max(_num(l.get('remaining_balance')), 0) for l in loans), 2),
        }

        # 9. Education (Enrolled & Completed Courses)
        try:
            education_res = supabase.table('user_courses').select('*, courses(*)').in_('user_id', user_ids).execute()
            education = education_res.data or []
        except:
            education_res = supabase.table('user_courses').select('*').in_('user_id', user_ids).execute()
            education = education_res.data or []
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict() if profile else None,
                'balance': float(balance),
                'assets': assets,
                'liabilities': liabilities,
                # Cars, boats, aircraft and luxury pieces to show off.
                'showcase': economy.showcase(liabilities),
                # Homes they own (and whether they live in one).
                'homes': homes_list,
                # Tiles for the profile grid, their timeline, and what they own vs owe.
                'owned': owned,
                'activity': activity,
                'balance_sheet': balance_sheet,
                'relationship': relationship,
                'jobs': jobs,
                'rental': rental,
                'education': education,
                'stats': {
                    'followers': followers_res.count or 0,
                    'following': following_res.count or 0,
                    'rank': rank
                },
                'news': supabase.table('market_news')\
                    .select('*')\
                    .eq('category', 'profile')\
                    .order('created_at', desc=True)\
                    .limit(3)\
                    .execute().data or []
            }
        }), 200
    except Exception as e:
        logger.error(f"[Dashboard Overview] Error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/income/', methods=['GET'])
@require_auth
def get_income(current_user_id: str):
    """Get user's monthly income"""
    try:
        profile = ProfileService.get_profile_by_user_id(uuid.UUID(current_user_id))
        if not profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
        return jsonify({'success': True, 'data': float(profile.monthly_income)}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/net-worth/', methods=['GET'])
@require_auth
def get_net_worth(current_user_id: str):
    """Get user's net worth"""
    try:
        profile = ProfileService.get_profile_by_user_id(uuid.UUID(current_user_id))
        if not profile:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
            
        return jsonify({'success': True, 'data': float(profile.net_worth)}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/ping/', methods=['PUT'])
@require_auth
def ping_activity(current_user_id: str):
    """Lightweight endpoint specifically to update last_active_at"""
    try:
        from app import db
        from app.models.profile import Profile
        from datetime import datetime, timezone
        
        user_uuid = uuid.UUID(current_user_id)
        
        # We execute a direct update query to avoid loading the whole model and locking
        Profile.query.filter_by(user_id=user_uuid).update({
            'last_active_at': datetime.now(timezone.utc)
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Activity updated'}), 200
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/<user_id>/', methods=['GET'])
@require_auth
def get_user_profile(current_user_id: str, user_id: str):
    """Get any player's public profile"""
    return get_profile(user_id)


def get_profile(user_id: str):
    """Get user profile by user ID"""
    try:
        from app.services.balance_service import BalanceService
        user_uuid = uuid.UUID(user_id)
        profile = ProfileService.get_profile_by_user_id(user_uuid)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Fetch balance and inject into response
        balance = 0
        try:
            balance = float(BalanceService.get_current_balance(user_id))
        except Exception as e:
            print(f"Failed to fetch balance for profile: {e}")
            
        profile_dict = profile.to_dict()
        profile_dict['account_balance'] = balance
        
        return jsonify({
            'success': True,
            'data': profile_dict
        }), 200
    
    except ValueError as e:
        return jsonify({'error': 'Invalid user ID format'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/', methods=['POST'])
@require_auth
def create_profile(current_user_id: str):
    """
    Create the caller's profile if the signup trigger didn't.
    (Normally public.handle_new_user() creates it on sign-up.)
    """
    try:
        data = ProfileCreate(**{**(request.get_json(silent=True) or {}), 'user_id': current_user_id})
        profile = ProfileService.create_profile(uuid.UUID(current_user_id), data.username)
        response = ProfileResponse.model_validate(profile.to_dict())
        return jsonify(response.model_dump()), 201

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception('create_profile failed')
        return jsonify({'error': 'Internal Server Error'}), 500

@profile_bp.route('/<user_id>/', methods=['PUT'])
@require_auth
def update_profile(current_user_id: str, user_id: str):
    """Update the caller's own profile (cosmetic fields only)."""
    if user_id != current_user_id:
        return jsonify({'success': False, 'error': 'FORBIDDEN', 'message': 'You can only edit your own profile'}), 403
    try:
        data = ProfileUpdate(**(request.get_json(silent=True) or {}))
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}

        profile = ProfileService.update_profile(uuid.UUID(user_id), **update_data)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        response = ProfileResponse.model_validate(profile.to_dict())
        return jsonify(response.model_dump()), 200

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        # Username uniqueness violations surface here
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception('update_profile failed')
        return jsonify({'error': 'Internal Server Error'}), 500
