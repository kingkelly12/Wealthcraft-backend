from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserResponse

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
             return jsonify({'error': 'Email and password are required'}), 400

        # Authenticate with Supabase
        auth_response = UserService.authenticate(email, password)
        session = auth_response.session
        user = auth_response.user

        return jsonify({
            'success': True, 
            'data': {
                'token': session.access_token,
                'refresh_token': session.refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.user_metadata.get('username')
                }
            }
        }), 200

    except ValueError as e:
        # Catch explicit auth errors (e.g. "Invalid login credentials")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        print(f"LOGIN ERROR: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Log out the user.
    Front-end handles token deletion.
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
        
        # Register with Supabase
        new_user = UserService.create_user(user_data)
        
        # UserResponse schema currently expects DB model, let's return dict directly for now
        return jsonify({
            'id': new_user.id,
            'email': new_user.email,
            'username': new_user.user_metadata.get('username'),
            'created_at': new_user.created_at
        }), 201

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        # Catch auth API errors (e.g. "User already registered")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"ERROR: {e}")
        # Check if it is a requests connection error (Supabase unreachable)
        return jsonify({'error': 'Internal Server Error'}), 500
