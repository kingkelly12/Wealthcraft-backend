"""
Notification management routes
Handles push token registration and notification management with JWT authentication
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError, BaseModel, Field
from app.utils.jwt_helper import require_auth
from app.services.push_notification_service import ExpoPushService
from app import supabase
import os
import uuid
from datetime import datetime
from typing import Optional

notification_bp = Blueprint('notification', __name__)


# Pydantic schemas
class RegisterTokenRequest(BaseModel):
    push_token: str = Field(..., min_length=1)


class TestPushRequest(BaseModel):
    title: Optional[str] = "Test Notification"
    body: Optional[str] = "This is a test push notification from Adulting!"


@notification_bp.route('/register-token', methods=['POST'])
@require_auth
def register_push_token(current_user_id: str):
    """
    Register or update a user's push notification token
    
    This endpoint:
    1. Validates the push token format
    2. Updates the user's profile with the new token
    3. Records the timestamp of the update
    
    Security: user_id is taken from JWT, not from request
    """
    try:
        # Validate request
        data = RegisterTokenRequest(**request.json)
        
        # Validate push token format
        if not ExpoPushService.validate_push_token(data.push_token):
            return jsonify({
                'success': False,
                'error': 'INVALID_TOKEN_FORMAT',
                'message': 'Invalid Expo push token format'
            }), 400
        
        # Update user's push token in database
        result = supabase.table('profiles').update({
            'push_token': data.push_token,
            'push_token_updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', current_user_id).execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User profile not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Push token registered successfully'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@notification_bp.route('/update-token', methods=['PUT'])
@require_auth
def update_push_token(current_user_id: str):
    """
    Update an existing push token (alias for register-token)
    """
    return register_push_token(current_user_id)


@notification_bp.route('/unregister-token', methods=['DELETE'])
@require_auth
def unregister_push_token(current_user_id: str):
    """
    Remove a user's push token (e.g., on logout)
    
    This prevents notifications from being sent to devices
    where the user has logged out.
    """
    try:
        # Clear push token from database
        result = supabase.table('profiles').update({
            'push_token': None,
            'push_token_updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', current_user_id).execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': 'USER_NOT_FOUND',
                'message': 'User profile not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Push token unregistered successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@notification_bp.route('/test-push', methods=['POST'])
@require_auth
def test_push_notification(current_user_id: str):
    """
    Send a test push notification to the current user
    
    Useful for debugging and verifying push notifications are working
    """
    try:
        # Parse optional custom message
        data = request.json or {}
        test_data = TestPushRequest(**data)
        
        # Send test notification
        success = ExpoPushService.send_notification_to_user(
            supabase_client=supabase,
            user_id=current_user_id,
            title=test_data.title,
            body=test_data.body,
            notification_type='test',
            data={'test': True}
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test notification sent successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'SEND_FAILED',
                'message': 'Failed to send test notification. Check if push token is registered.'
            }), 400
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': e.errors()
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@notification_bp.route('/mark-read/<notification_id>', methods=['PUT'])
@require_auth
def mark_notification_read(current_user_id: str, notification_id: str):
    """
    Mark a notification as read
    
    This is handled client-side via Supabase, but provided as a
    backup endpoint for consistency
    """
    try:
        # Verify notification belongs to user and mark as read
        result = supabase.table('notifications').update({
            'read': True
        }).eq('id', notification_id).eq('user_id', current_user_id).execute()
        
        if not result.data:
            return jsonify({
                'success': False,
                'error': 'NOTIFICATION_NOT_FOUND',
                'message': 'Notification not found or does not belong to user'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Notification marked as read'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@notification_bp.route('/', methods=['GET'])
@require_auth
def get_all_notifications(current_user_id: str):
    """Get all notifications"""
    try:
        limit = request.args.get('limit', 20, type=int)
        response = supabase.table('notifications').select('*').eq('user_id', current_user_id).order('created_at', desc=True).limit(limit).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@notification_bp.route('/unread', methods=['GET'])
@require_auth
def get_unread_count(current_user_id: str):
    """Get count of unread notifications"""
    try:
        response = supabase.table('notifications').select('id', count='exact').eq('user_id', current_user_id).eq('read', False).execute()
        return jsonify({'success': True, 'data': response.count}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@notification_bp.route('/read-all', methods=['PUT'])
@require_auth
def mark_all_read(current_user_id: str):
    """Mark all notifications as read"""
    try:
        supabase.table('notifications').update({'read': True}).eq('user_id', current_user_id).eq('read', False).execute()
        return jsonify({'success': True, 'message': 'All marked as read'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
