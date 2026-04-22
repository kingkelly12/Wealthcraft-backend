"""
AI Routes — Endpoints for AI-powered mentor chat.

POST /api/ai/mentor/chat       — Send a message to a mentor, get AI response
GET  /api/ai/mentor/<id>/greeting — Get contextual opening message
GET  /api/ai/mentor/<id>/history  — Get conversation history
"""

from flask import Blueprint, request, jsonify
from app.utils.jwt_helper import require_auth
from app.services.ai_service import AIService
from app.services.mentor_service import MentorService
from app.models.mentor import Mentor
from app.models.player_mentor_interaction import PlayerMentorInteraction
from app.models.profile import Profile
from app import db, supabase
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/mentor/chat/', methods=['POST'])
@require_auth
def mentor_chat(current_user_id: str):
    """
    Send a message to a mentor and receive an AI-generated response.

    Request Body:
        mentor_id: UUID of the mentor
        message: Player's message text

    Returns:
        The AI-generated mentor response with suggested actions.
    """
    try:
        data = request.json
        mentor_id = data.get('mentor_id')
        user_message = data.get('message', '').strip()

        if not mentor_id or not user_message:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': 'mentor_id and message are required'
            }), 400

        if len(user_message) > 500:
            return jsonify({
                'success': False,
                'error': 'MESSAGE_TOO_LONG',
                'message': 'Messages must be under 500 characters'
            }), 400

        # Validate mentor exists
        mentor = Mentor.query.get(uuid.UUID(mentor_id))
        if not mentor:
            return jsonify({
                'success': False,
                'error': 'MENTOR_NOT_FOUND',
                'message': 'Mentor not found'
            }), 404

        # Check rate limit
        rate_limit = AIService.check_rate_limit(current_user_id, mentor_id)
        if not rate_limit['allowed']:
            return jsonify({
                'success': False,
                'error': 'RATE_LIMITED',
                'message': f'{mentor.name} needs to rest. Come back tomorrow!',
                'data': {
                    'remaining': 0,
                    'resets_at': rate_limit['resets_at'],
                    'limit': rate_limit['limit'],
                }
            }), 429

        # Get player profile
        profile = Profile.query.filter_by(user_id=uuid.UUID(current_user_id)).first()
        if not profile:
            return jsonify({
                'success': False,
                'error': 'PROFILE_NOT_FOUND',
                'message': 'Player profile not found'
            }), 404

        # Get financial metrics
        metrics = MentorService.analyze_player_finances(uuid.UUID(current_user_id))
        if not metrics:
            metrics = {}

        # Add sanity to metrics
        metrics['sanity'] = profile.sanity if hasattr(profile, 'sanity') else 100

        # Get conversation history
        conversation_history = AIService.get_conversation_history(current_user_id, mentor_id)

        # 1. Save the player's message as an interaction
        player_interaction = PlayerMentorInteraction(
            player_id=uuid.UUID(current_user_id),
            mentor_id=uuid.UUID(mentor_id),
            message_content=user_message,
            trigger_type='player_chat',
            is_player_message=True,
            player_data_snapshot=metrics,
        )
        db.session.add(player_interaction)
        db.session.flush()  # Get the ID before commit

        # 2. Generate AI response
        ai_response = AIService.chat_with_mentor(
            player_id=current_user_id,
            mentor_id=mentor_id,
            user_message=user_message,
            mentor_role=mentor.role,
            mentor_name=mentor.name,
            username=profile.username,
            metrics=metrics,
            conversation_history=conversation_history,
        )

        if not ai_response:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'AI_UNAVAILABLE',
                'message': 'AI service is temporarily unavailable. Try again later.'
            }), 503

        # 3. Save the mentor's AI response as an interaction
        mentor_interaction = PlayerMentorInteraction(
            player_id=uuid.UUID(current_user_id),
            mentor_id=uuid.UUID(mentor_id),
            message_content=ai_response['message'],
            trigger_type='ai_chat_response',
            is_player_message=False,
            parent_interaction_id=player_interaction.id,
            player_data_snapshot=metrics,
            points_earned=ai_response.get('relationship_points', 5),
            relationship_score=ai_response.get('relationship_points', 5),
            ai_metadata={
                'tone': ai_response.get('tone'),
                'suggested_actions': ai_response.get('suggested_actions', []),
                'follow_up_question': ai_response.get('follow_up_question'),
                'model': AIService.MODEL_NAME,
            },
        )
        db.session.add(mentor_interaction)

        # Update profile XP
        if profile:
            points = ai_response.get('relationship_points', 5)
            profile.experience_points = (profile.experience_points or 0) + points

        db.session.commit()

        # 4. Updated rate limit info
        updated_rate = AIService.check_rate_limit(current_user_id, mentor_id)

        return jsonify({
            'success': True,
            'data': {
                'player_message': {
                    'id': str(player_interaction.id),
                    'content': user_message,
                    'sent_at': player_interaction.sent_at.isoformat(),
                    'is_player_message': True,
                },
                'mentor_response': {
                    'id': str(mentor_interaction.id),
                    'content': ai_response['message'],
                    'tone': ai_response.get('tone', 'neutral'),
                    'suggested_actions': ai_response.get('suggested_actions', []),
                    'follow_up_question': ai_response.get('follow_up_question'),
                    'points_earned': ai_response.get('relationship_points', 5),
                    'sent_at': mentor_interaction.sent_at.isoformat(),
                    'is_player_message': False,
                },
                'rate_limit': updated_rate,
            }
        }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'INVALID_ID',
            'message': 'Invalid ID format'
        }), 400
    except Exception as e:
        logger.error(f"Mentor chat error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'CHAT_FAILED',
            'message': str(e)
        }), 500


@ai_bp.route('/mentor/<mentor_id>/greeting/', methods=['GET'])
@require_auth
def mentor_greeting(current_user_id: str, mentor_id: str):
    """
    Get a contextual opening message for a mentor chat.
    This is displayed when the player first opens the chat screen.
    Cached for 6 hours.
    """
    try:
        mentor = Mentor.query.get(uuid.UUID(mentor_id))
        if not mentor:
            return jsonify({
                'success': False,
                'error': 'MENTOR_NOT_FOUND'
            }), 404

        profile = Profile.query.filter_by(user_id=uuid.UUID(current_user_id)).first()
        if not profile:
            return jsonify({
                'success': False,
                'error': 'PROFILE_NOT_FOUND'
            }), 404

        metrics = MentorService.analyze_player_finances(uuid.UUID(current_user_id))
        if not metrics:
            metrics = {}

        metrics['sanity'] = profile.sanity if hasattr(profile, 'sanity') else 100

        greeting = AIService.generate_greeting(
            mentor_role=mentor.role,
            mentor_name=mentor.name,
            username=profile.username,
            metrics=metrics,
        )

        # Get rate limit info
        rate_limit = AIService.check_rate_limit(current_user_id, mentor_id)

        return jsonify({
            'success': True,
            'data': {
                'greeting': greeting,
                'rate_limit': rate_limit,
            }
        }), 200

    except Exception as e:
        logger.error(f"Greeting error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'GREETING_FAILED',
            'message': str(e)
        }), 500


@ai_bp.route('/mentor/<mentor_id>/history/', methods=['GET'])
@require_auth
def mentor_history(current_user_id: str, mentor_id: str):
    """
    Get the AI conversation history for a specific mentor.
    Returns both player messages and AI responses in chronological order.
    """
    try:
        mentor = Mentor.query.get(uuid.UUID(mentor_id))
        if not mentor:
            return jsonify({
                'success': False,
                'error': 'MENTOR_NOT_FOUND'
            }), 404

        history = AIService.get_conversation_history(current_user_id, mentor_id)

        # Also get rate limit
        rate_limit = AIService.check_rate_limit(current_user_id, mentor_id)

        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'rate_limit': rate_limit,
                'mentor': mentor.to_dict(),
            }
        }), 200

    except Exception as e:
        logger.error(f"History fetch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'HISTORY_FAILED',
            'message': str(e)
        }), 500


@ai_bp.route('/void/analyze/', methods=['POST'])
@require_auth
def analyze_void_scream(current_user_id: str):
    """
    Analyze a player's 'scream' into the void and receive an AI response.
    
    Request Body:
        content: The text of the scream
        
    Returns:
        The AI-generated analysis (mood, message, challenge).
    """
    try:
        data = request.json
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': 'Scream content is required'
            }), 400

        # Get player profile
        profile = Profile.query.filter_by(user_id=uuid.UUID(current_user_id)).first()
        if not profile:
            return jsonify({
                'success': False,
                'error': 'PROFILE_NOT_FOUND',
                'message': 'Player profile not found'
            }), 404

        # Get financial metrics for context
        metrics = MentorService.analyze_player_finances(uuid.UUID(current_user_id))
        if not metrics:
            metrics = {}

        metrics['sanity'] = profile.sanity if hasattr(profile, 'sanity') else 100
        metrics['username'] = profile.username

        # Generate AI analysis
        analysis = AIService.analyze_void_scream(content, metrics)

        return jsonify({
            'success': True,
            'data': analysis
        }), 200

    except Exception as e:
        logger.error(f"Void analysis error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'ANALYSIS_FAILED',
            'message': str(e)
        }), 500

@ai_bp.route('/market/news', methods=['GET'])
@require_auth
def get_market_news(current_user_id: str):
    """Fetch the latest AI-generated market news headlines."""
    try:
        # Fetch the last 10 headlines
        res = supabase.table('market_news')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(10)\
            .execute()
            
        return jsonify({
            'success': True,
            'data': res.data or []
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
