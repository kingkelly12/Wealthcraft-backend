"""
JWT Helper utilities for verifying Supabase JWT tokens
"""
import jwt
import os
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Dict, Any

def get_supabase_secret():
    """
    Helper to get the secret from Flask config or Environment.
    This is safer than a top-level check.
    """
    # Priority: 1. Flask Config, 2. OS Environment
    secret = os.getenv('SUPABASE_JWT_SECRET')
    
    # If using current_app context (inside a request), check config too
    try:
        if not secret and current_app:
            secret = current_app.config.get('SUPABASE_JWT_SECRET')
    except RuntimeError:
        # Not in an application context
        pass
        
    return secret

def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a Supabase JWT token
    """
    secret = get_supabase_secret()
    if not secret:
        print("CRITICAL: SUPABASE_JWT_SECRET is not set. Cannot decode token.")
        return None

    try:
        # Verify and decode the token
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            audience='authenticated'
        )
        return payload
    except jwt.ExpiredSignatureError:
        print('Token has expired')
        return None
    except jwt.InvalidTokenError as e:
        print(f'Invalid token: {e}')
        return None



def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user_id from JWT token
    
    Args:
        token: The JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
    """
    payload = decode_jwt(token)
    if payload:
        return payload.get('sub')  # 'sub' claim contains the user ID
    return None


def extract_token_from_header() -> Optional[str]:
    """
    Extract JWT token from Authorization header
    
    Returns:
        Token string if present, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def require_auth(f):
    """
    Decorator to require authentication for a route
    
    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route(current_user_id):
            # current_user_id is automatically injected
            return jsonify({'user_id': current_user_id})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'UNAUTHORIZED',
                'message': 'Authorization token is required'
            }), 401
        
        user_id = get_user_id_from_token(token)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'INVALID_TOKEN',
                'message': 'Invalid or expired token'
            }), 401
        
        # Inject user_id as first argument to the route function
        return f(user_id, *args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin role for a route
    
    Usage:
        @app.route('/api/admin/users')
        @require_admin
        def admin_route(current_user_id):
            # Only admins can access this
            return jsonify({'message': 'Admin only'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'UNAUTHORIZED',
                'message': 'Authorization token is required'
            }), 401
        
        payload = decode_jwt(token)
        
        if not payload:
            return jsonify({
                'success': False,
                'error': 'INVALID_TOKEN',
                'message': 'Invalid or expired token'
            }), 401
        
        # Check for admin role in user metadata
        user_metadata = payload.get('user_metadata', {})
        role = user_metadata.get('role', 'user')
        
        if role != 'admin':
            return jsonify({
                'success': False,
                'error': 'FORBIDDEN',
                'message': 'Admin access required'
            }), 403
        
        user_id = payload.get('sub')
        return f(user_id, *args, **kwargs)
    
    return decorated_function
