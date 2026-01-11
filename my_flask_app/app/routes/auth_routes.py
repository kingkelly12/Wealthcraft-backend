from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # Validate input using Pydantic
        user_data = UserCreate(**request.json)
        
        # Call Service Layer
        new_user = UserService.create_user(user_data)
        
        # Format response
        response = UserResponse.from_orm(new_user)
        return jsonify(response.dict()), 201

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
