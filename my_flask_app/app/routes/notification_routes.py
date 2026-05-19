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
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

notification_bp = Blueprint('notification', __name__)


# Pydantic schemas
class RegisterTokenRequest(BaseModel):
    push_token: str = Field(..., min_length=1)


class TestPushRequest(BaseModel):
    title: Optional[str] = "Test Notification"
    body: Optional[str] = "This is a test push notification from Adulting!"


@notification_bp.route('/register-token/', methods=['POST'])
@require_auth
def register_push_token(current_user_id: str):
    """
    Register or update a user's push notification token
    
    This endpoint:
    1. Validates the push token format (must be Expo format: ExponentPushToken[...])
    2. Saves the token to the user's profile in Supabase
    3. Records the timestamp of the update
    4. Returns success only if token is saved
    
    Security: user_id is taken from JWT, not from request
    """
    try:
        # Validate request
        data = RegisterTokenRequest(**request.json)
        
        # Validate token format - must be ExponentPushToken[...]
        if not ExpoPushService.validate_push_token(data.push_token):
            return jsonify({
                'success': False,
                'error': 'INVALID_TOKEN_FORMAT',
                'message': 'Invalid Expo push token format. Expected ExponentPushToken[...]'
            }), 400
        
        # Save token to database
        try:
            result = supabase.table('profiles') \
                .update({
                    'expo_push_token': data.push_token,
                    'push_token_updated_at': datetime.utcnow().isoformat()
                }) \
                .eq('user_id', current_user_id) \
                .execute()
            
            if not result.data:
                return jsonify({
                    'success': False,
                    'error': 'UPDATE_FAILED',
                    'message': 'Failed to save push token to profile'
                }), 500
            
            logger.info(f"Push token registered for user {current_user_id}")
            return jsonify({
                'success': True,
                'message': 'Push token registered successfully'
            }), 200
            
        except Exception as db_error:
            logger.error(f"Database error saving push token for user {current_user_id}: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': 'DATABASE_ERROR',
                'message': 'Failed to save push token to database'
            }), 500
        
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


@notification_bp.route('/update-token/', methods=['PUT'])
@require_auth
def update_push_token(current_user_id: str):
    """
    Update an existing push token (alias for register-token)
    """
    return register_push_token(current_user_id)


@notification_bp.route('/unregister-token/', methods=['DELETE'])
@require_auth
def unregister_push_token(current_user_id: str):
    """
    Remove a user's push token (e.g., on logout or app uninstall)
    
    This prevents notifications from being sent to devices
    where the user has logged out.
    """
    try:
        result = supabase.table('profiles') \
            .update({
                'expo_push_token': None,
                'push_token_updated_at': datetime.utcnow().isoformat()
            }) \
            .eq('user_id', current_user_id) \
            .execute()
        
        if result.data:
            logger.info(f"Push token unregistered for user {current_user_id}")
            return jsonify({
                'success': True,
                'message': 'Push token unregistered successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'UPDATE_FAILED',
                'message': 'Failed to unregister push token'
            }), 500
        
    except Exception as e:
        logger.error(f"Error unregistering push token for user {current_user_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@notification_bp.route('/test-push/', methods=['POST'])
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


@notification_bp.route('/mark-read/<notification_id>/', methods=['PUT'])
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


def resolve_user_ids(user_id: str) -> list:
    """Resolve both Auth UID and Profile UUID"""
    try:
        res = supabase.table('profiles').select('id, user_id').eq('user_id', user_id).limit(1).execute()
        if res.data:
            p = res.data[0]
            return list({str(p['user_id']), str(p['id'])})
        res = supabase.table('profiles').select('id, user_id').eq('id', user_id).limit(1).execute()
        if res.data:
            p = res.data[0]
            return list({str(p['user_id']), str(p['id'])})
    except:
        pass
    return [user_id]


@notification_bp.route('/', methods=['GET'])
@require_auth
def get_all_notifications(current_user_id: str):
    """Get all notifications"""
    try:
        user_ids = resolve_user_ids(current_user_id)
        limit = request.args.get('limit', 20, type=int)
        response = supabase.table('notifications').select('*').in_('user_id', user_ids).order('created_at', desc=True).limit(limit).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@notification_bp.route('/unread/', methods=['GET'])
@require_auth
def get_unread_count(current_user_id: str):
    """Get count of unread notifications"""
    try:
        user_ids = resolve_user_ids(current_user_id)
        response = supabase.table('notifications').select('id', count='exact').in_('user_id', user_ids).eq('read', False).execute()
        return jsonify({'success': True, 'data': response.count}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@notification_bp.route('/read-all/', methods=['PUT'])
@require_auth
def mark_all_read(current_user_id: str):
    """Mark all notifications as read"""
    try:
        supabase.table('notifications').update({'read': True}).eq('user_id', current_user_id).eq('read', False).execute()
        return jsonify({'success': True, 'message': 'All marked as read'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
