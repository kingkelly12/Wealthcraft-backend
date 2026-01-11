from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.profile_service import ProfileService
from app.schemas.profile_schema import ProfileCreate, ProfileUpdate, ProfileResponse
import uuid

profile_bp = Blueprint('profile', __name__)

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
