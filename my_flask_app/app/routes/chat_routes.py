"""
Chat management routes
Handles sending messages with JWT authentication to prevent impersonation
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.schemas.chat_schema import SendMessageRequest, SendMessageResponse
from app import supabase
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService


chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/send', methods=['POST'])
@require_auth
def send_message(current_user_id: str):
    """
    Send a chat message
    
    This endpoint:
    1. Validates the request
    2. Verifies sender_id matches JWT (prevents impersonation)
    3. Creates message with server-controlled sender_id
    4. Creates notification for recipient
    
    Security: sender_id is taken from JWT, not from request
    """
    try:
        # Validate request
        data = SendMessageRequest(**request.json)
        
        # Validate content
        content = data.content.strip()
        if not content:
            return jsonify({
                'success': False,
                'error': 'EMPTY_MESSAGE',
                'message': 'Message content cannot be empty'
            }), 400
        
        # Check if trying to message self
        if str(data.recipient_id) == current_user_id:
            return jsonify({
                'success': False,
                'error': 'INVALID_RECIPIENT',
                'message': 'You cannot send messages to yourself'
            }), 400
        
        # Verify recipient exists
        recipient_check = supabase.table('profiles').select('id').eq('user_id', str(data.recipient_id)).execute()
        
        if not recipient_check.data:
            return jsonify({
                'success': False,
                'error': 'RECIPIENT_NOT_FOUND',
                'message': 'Recipient user not found'
            }), 404
        
        # Create message (sender_id from JWT, not request!)
        message_id = str(uuid.uuid4())
        supabase.table('chat_messages').insert({
            'id': message_id,
            'sender_id': current_user_id,  # From JWT - cannot be spoofed!
            'recipient_id': str(data.recipient_id),
            'content': content,
            'status': 'sent',
            'type': 'text',
            'timestamp': datetime.utcnow().isoformat()
        }).execute()
        
        # Create notification for recipient
        supabase.table('notifications').insert({
            'user_id': str(data.recipient_id),
            'type': 'system',
            'title': 'New Message',
            'message': 'You have a new message',
            'related_user_id': current_user_id,
            'read': False
        }).execute()
        
        # Send push notification to recipient
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=str(data.recipient_id),
                title='💬 New Message',
                body='You have a new message',
                notification_type='chat',
                data={
                    'sender_id': current_user_id,
                    'message_id': message_id,
                    'navigate_to': f'/chat/{current_user_id}'
                }
            )
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully',
            'message_id': uuid.UUID(message_id)
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
