from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse
from app.utils.jwt_helper import create_token, require_auth

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
             return jsonify({'error': 'Email and password are required'}), 400

        user = UserService.authenticate(email, password)
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
            
        token = create_token(user.id, user.email)
        
        # UserResponse.from_orm(user) converts SQLAlchemy model to Pydantic model
        user_response = UserResponse.from_orm(user)
        
        return jsonify({
            'success': True, 
            'data': {
                'token': token,
                'refresh_token': token, # Re-use access token as refresh token for simple JWT setup
                'user': user_response.dict()
            }
        }), 200

    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout(current_user_id):
    """
    Log out the user.
    Note: Since we use stateless JWTs, the client simply deletes the token.
    This endpoint serves as a confirmation and hook for any future server-side cleanup.
    """
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

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
