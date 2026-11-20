"""
JWT helpers for verifying Supabase access tokens.

Supabase projects created since 2025 sign access tokens with asymmetric
"JWT signing keys" (ES256/RS256) published at
    <SUPABASE_URL>/auth/v1/.well-known/jwks.json
Older projects use the shared HS256 "legacy JWT secret". Both are supported:
the token header's `alg` decides which path is used.
"""
import logging
import os
from functools import wraps
from typing import Any, Dict, Optional

import jwt
from flask import jsonify, request

logger = logging.getLogger(__name__)

SUPABASE_URL = (os.getenv('SUPABASE_URL') or '').rstrip('/')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')  # only needed for legacy HS256 projects

if not SUPABASE_URL and not SUPABASE_JWT_SECRET:
    raise ValueError('SUPABASE_URL (for JWKS) or SUPABASE_JWT_SECRET (legacy HS256) is required')

_ASYMMETRIC_ALGS = ['ES256', 'RS256', 'EdDSA']
_jwks_client: Optional[jwt.PyJWKClient] = None


def _get_jwks_client() -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        # PyJWKClient caches keys and refetches when it sees an unknown `kid`.
        _jwks_client = jwt.PyJWKClient(f'{SUPABASE_URL}/auth/v1/.well-known/jwks.json', cache_keys=True)
    return _jwks_client


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Supabase access token and return its claims, or None if invalid."""
    try:
        alg = jwt.get_unverified_header(token).get('alg')
        if alg == 'HS256':
            if not SUPABASE_JWT_SECRET:
                logger.warning('HS256 token received but SUPABASE_JWT_SECRET is not set')
                return None
            key = SUPABASE_JWT_SECRET
            algorithms = ['HS256']
        elif alg in _ASYMMETRIC_ALGS:
            key = _get_jwks_client().get_signing_key_from_jwt(token).key
            algorithms = [alg]
        else:
            logger.warning('Rejected token with unsupported alg %s', alg)
            return None

        return jwt.decode(token, key, algorithms=algorithms, audience='authenticated')
    except jwt.ExpiredSignatureError:
        return None
    except (jwt.InvalidTokenError, jwt.PyJWKClientError) as e:
        logger.info('Invalid token: %s', e)
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    payload = decode_jwt(token)
    return payload.get('sub') if payload else None


def extract_token_from_header() -> Optional[str]:
    """Return the bearer token from the Authorization header, if present."""
    parts = (request.headers.get('Authorization') or '').split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    return parts[1]


def _unauthorized(error: str, message: str):
    return jsonify({'success': False, 'error': error, 'message': message}), 401


def require_auth(f):
    """Inject the authenticated user's id (auth.users.id) as the first argument."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        if not token:
            return _unauthorized('UNAUTHORIZED', 'Authorization token is required')

        user_id = get_user_id_from_token(token)
        if not user_id:
            return _unauthorized('INVALID_TOKEN', 'Invalid or expired token')

        return f(user_id, *args, **kwargs)
    return decorated_function


def require_admin(f):
    """
    Require an admin. The role is read from `app_metadata`, which only the
    service role can write. (`user_metadata` is editable by the user themselves
    via supabase.auth.updateUser, so it must never be trusted for authorization.)

    Grant admin with SQL:
        update auth.users
           set raw_app_meta_data = raw_app_meta_data || '{"role": "admin"}'
         where email = '...';
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = extract_token_from_header()
        if not token:
            return _unauthorized('UNAUTHORIZED', 'Authorization token is required')

        payload = decode_jwt(token)
        if not payload:
            return _unauthorized('INVALID_TOKEN', 'Invalid or expired token')

        if (payload.get('app_metadata') or {}).get('role') != 'admin':
            return jsonify({'success': False, 'error': 'FORBIDDEN', 'message': 'Admin access required'}), 403

        return f(payload.get('sub'), *args, **kwargs)
    return decorated_function
