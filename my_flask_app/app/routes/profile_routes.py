from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.profile_service import ProfileService
from app.schemas.profile_schema import ProfileCreate, ProfileUpdate, ProfileResponse
import uuid

profile_bp = Blueprint('profile', __name__)

from app.utils.jwt_helper import require_auth

@profile_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_profile(current_user_id: str):
    """Get authenticated user's profile"""
    return get_profile(current_user_id)

@profile_bp.route('/dashboard', methods=['GET'])
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

@profile_bp.route('/income', methods=['GET'])
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

@profile_bp.route('/net-worth', methods=['GET'])
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

@profile_bp.route('/<user_id>', methods=['GET'])
def get_profile(user_id: str):
    """Get user profile by user ID"""
    try:
        user_uuid = uuid.UUID(user_id)
        profile = ProfileService.get_profile_by_user_id(user_uuid)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        response = ProfileResponse.model_validate(profile.to_dict())
        return jsonify(response.model_dump()), 200
    
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

@profile_bp.route('/<user_id>', methods=['PUT'])
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
