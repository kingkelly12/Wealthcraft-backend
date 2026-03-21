from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.services.user_service import UserService
from app.services.google_auth_service import GoogleAuthService
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
        auth_response = UserService.create_user(user_data)
        user = auth_response.user
        session = auth_response.session
        
        response_data = {
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.user_metadata.get('username'),
                    'created_at': user.created_at
                }
            }
        }

        # Add session data if available (Supabase auto-login after sign-up)
        if session:
            response_data['data']['token'] = session.access_token
            response_data['data']['refresh_token'] = session.refresh_token

        return jsonify(response_data), 201

    except ValidationError as e:
        return jsonify(e.errors()), 400
    except ValueError as e:
        # Catch auth API errors (e.g. "User already registered")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"ERROR: {e}")
        # Check if it is a requests connection error (Supabase unreachable)
        return jsonify({'error': 'Internal Server Error'}), 500

@auth_bp.route('/google-signin', methods=['POST'])
def google_signin():
    """
    Handle Google OAuth sign-in from mobile app.
    
    Expects JSON:
    {
        "idToken": "...",
        "email": "user@example.com" (optional, used as fallback)
    }
    """
    try:
        data = request.get_json()
        id_token_str = data.get('idToken')
        email = data.get('email')

        if not id_token_str:
            return jsonify({
                'success': False,
                'error': 'Missing idToken'
            }), 400

        # Verify token and create/retrieve user
        user, access_token, refresh_token = GoogleAuthService.verify_and_create_user(
            id_token_str, 
            email
        )

        return jsonify({
            'success': True,
            'data': {
                'token': access_token,
                'refresh_token': refresh_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'profile_picture_url': user.profile_picture_url,
                }
            }
        }), 200

    except ValueError as e:
        print(f"Google Sign-In Validation Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401
    except Exception as e:
        print(f"Google Sign-In Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Authentication failed'
        }), 500

