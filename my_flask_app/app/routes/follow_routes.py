"""
Follow management routes
Handles follow/unfollow operations with JWT authentication to prevent manipulation
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.schemas.follow_schema import FollowUserRequest, FollowUserResponse
from supabase import create_client
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

follow_bp = Blueprint('follow', __name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@follow_bp.route('/follow', methods=['POST'])
@require_auth
def follow_user(current_user_id: str):
    """
    Follow a user
    
    This endpoint:
    1. Validates the request
    2. Verifies follower_id matches JWT (prevents spoofing)
    3. Creates follow relationship with server-controlled follower_id
    4. Creates notification for followed user
    
    Security: follower_id is taken from JWT, not from request
    """
    try:
        # Validate request
        data = FollowUserRequest(**request.json)
        
        # Check if trying to follow self
        if str(data.target_user_id) == current_user_id:
            return jsonify({
                'success': False,
                'error': 'INVALID_TARGET',
                'message': 'You cannot follow yourself'
            }), 400
        
        # Verify target user exists
        target_check = supabase.table('profiles').select('id').eq('user_id', str(data.target_user_id)).execute()
        
        if not target_check.data:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'Target user not found'
            }), 404
        
        # Check if already following
        existing_follow = supabase.table('user_follows').select('id').eq('follower_id', current_user_id).eq('following_id', str(data.target_user_id)).execute()
        
        if existing_follow.data and len(existing_follow.data) > 0:
            return jsonify({
                'success': False,
                'error': 'ALREADY_FOLLOWING',
                'message': 'You are already following this user'
            }), 400
        
        # Create follow relationship (follower_id from JWT!)
        supabase.table('user_follows').insert({
            'follower_id': current_user_id,  # From JWT - cannot be spoofed!
            'following_id': str(data.target_user_id),
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        # Create notification for followed user
        supabase.table('notifications').insert({
            'user_id': str(data.target_user_id),
            'type': 'follow',
            'title': 'New Follower',
            'message': 'Someone started following you!',
            'related_user_id': current_user_id,
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=str(data.target_user_id),
                title='👥 New Follower',
                body='Someone started following you!',
                notification_type='follow',
                data={
                    'follower_id': current_user_id,
                    'navigate_to': f'/users/{current_user_id}'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Successfully followed user'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        error_message = str(e)
        
        # Handle unique constraint violation (duplicate follow)
        if '23505' in error_message or 'duplicate' in error_message.lower():
            return jsonify({
                'success': False,
                'error': 'ALREADY_FOLLOWING',
                'message': 'You are already following this user'
            }), 400
        
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': error_message
        }), 500


@follow_bp.route('/unfollow/<target_user_id>', methods=['POST'])
@require_auth
def unfollow_user(current_user_id: str, target_user_id: str):
    """
    Unfollow a user
    
    Security: follower_id is taken from JWT, not from request
    """
    try:
        # Delete follow relationship (follower_id from JWT!)
        result = supabase.table('user_follows').delete().eq('follower_id', current_user_id).eq('following_id', target_user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return jsonify({
                'success': False,
                'error': 'NOT_FOLLOWING',
                'message': 'You are not following this user'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Successfully unfollowed user'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
