from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.profile_service import ProfileService
from app.schemas.profile_schema import ProfileCreate, ProfileUpdate, ProfileResponse
import uuid

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

@profile_bp.route('/overview/', methods=['GET'])
@require_auth
def get_comprehensive_dashboard(current_user_id: str):
    """
    ULTIMATE CONSOLIDATION: Returns everything for the home/profile screen.
    Reduces up to 8 separate calls to 1.
    """
    try:
        from app.services.balance_service import BalanceService
        from app.routes.asset_routes import get_user_assets_internal
        from app.routes.rental_routes import get_active_rental_internal
        
        # Check if we're looking at another user's profile
        target_user_id = request.args.get('user_id', current_user_id)
        is_own_profile = (target_user_id == current_user_id)
        
        # 1. Profile
        profile = ProfileService.get_profile_by_user_id(uuid.UUID(target_user_id))
        if not profile:
             return jsonify({'success': False, 'error': 'Profile not found'}), 404
             
        # 2. Balance (Only shared if public or own)
        balance = BalanceService.get_current_balance(target_user_id)
        
        # 3. Assets
        assets = get_user_assets_internal(target_user_id)
        
        # 4. Liabilities
        liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').eq('player_id', target_user_id).eq('is_active', True).execute()
        liabilities = liabilities_res.data or []
        
        # 5. Jobs
        jobs_res = supabase.table('jobs').select('*').eq('user_id', target_user_id).eq('is_active', True).execute()
        jobs = jobs_res.data or []
        
        # 6. Rental
        rental = get_active_rental_internal(target_user_id)

        # 7. Social Stats (Followers/Following)
        followers_res = supabase.table('user_follows').select('id', count='exact').eq('following_id', target_user_id).execute()
        following_res = supabase.table('user_follows').select('id', count='exact').eq('follower_id', target_user_id).execute()
        
        # 8. Rank
        net_worth = profile.net_worth or 0
        rank_res = supabase.table('profiles').select('id', count='exact').gt('net_worth', net_worth).execute()
        rank = (rank_res.count or 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict() if profile else None,
                'balance': float(balance),
                'assets': assets,
                'liabilities': liabilities,
                'jobs': jobs,
                'rental': rental,
                'stats': {
                    'followers': followers_res.count or 0,
                    'following': following_res.count or 0,
                    'rank': rank
                }
            }
        }), 200
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict() if profile else None,
                'balance': float(balance),
                'assets': assets,
                'liabilities': liabilities,
                'jobs': jobs,
                'rental': rental
            }
        }), 200
    except Exception as e:
        print(f"[Dashboard Overview] Error: {str(e)}")
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
        from datetime import datetime
        
        user_uuid = uuid.UUID(current_user_id)
        
        # We execute a direct update query to avoid loading the whole model and locking
        Profile.query.filter_by(user_id=user_uuid).update({
            'last_active_at': datetime.utcnow()
        })
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Activity updated'}), 200
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@profile_bp.route('/<user_id>/', methods=['GET'])
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
def create_profile():
    """Create a new profile"""
    try:
        data = ProfileCreate(**request.json)
        user_uuid = uuid.UUID(data.user_id)
        
        profile = ProfileService.create_profile(user_uuid, data.username)
        response = ProfileResponse.model_validate(profile.to_dict())
        return jsonify(response.model_dump()), 201
    
    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@profile_bp.route('/<user_id>/', methods=['PUT'])
def update_profile(user_id: str):
    """Update user profile"""
    try:
        data = ProfileUpdate(**request.json)
        user_uuid = uuid.UUID(user_id)
        
        # Filter out None values
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        
        profile = ProfileService.update_profile(user_uuid, **update_data)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        response = ProfileResponse.model_validate(profile.to_dict())
        return jsonify(response.model_dump()), 200
    
    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': 'Invalid user ID format'}), 400
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500
