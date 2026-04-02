"""
Mentor system routes - Handle mentor-player interactions
Provides endpoints for fetching mentors, viewing messages, marking as read, and following advice
"""
from flask import Blueprint, request, jsonify
from app.utils.jwt_helper import require_auth
from app.models.mentor import Mentor
from app.models.mentor_message import MentorMessage
from app.models.player_mentor_interaction import PlayerMentorInteraction
from app.models.profile import Profile
from app.services.mentor_service import MentorService
from app import db, supabase
from datetime import datetime
import uuid

mentor_bp = Blueprint('mentor', __name__)


@mentor_bp.route('/api/social/mentors/', methods=['GET'])
def get_all_mentors():
    """
    Get all available mentor NPCs
    
    Returns:
        List of all 3 mentors (Coach Chen, Tasha, Parent)
    """
    try:
        mentors = Mentor.query.all()
        
        mentor_data = []
        for mentor in mentors:
            mentor_data.append({
                'id': str(mentor.id),
                'name': mentor.name,
                'role': mentor.role,
                'personality': mentor.personality,
                'avatar_url': mentor.avatar_url,
                'greeting_template': mentor.greeting_template,
                'created_at': mentor.created_at.isoformat() if mentor.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': mentor_data
        }), 200
        
    except Exception as e:
        print(f"Error fetching mentors: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500


@mentor_bp.route('/api/social/interactions/', methods=['GET'])
@require_auth
def get_player_interactions(current_user_id: str):
    """
    Get all mentor interactions for the current player
    
    Returns:
        List of all mentor messages sent to this player, ordered by most recent
    """
    try:
        # Convert string to UUID
        player_uuid = uuid.UUID(current_user_id)
        
        # Query interactions with mentor details
        interactions = db.session.query(
            PlayerMentorInteraction,
            Mentor
        ).join(
            Mentor,
            PlayerMentorInteraction.mentor_id == Mentor.id
        ).filter(
            PlayerMentorInteraction.player_id == player_uuid
        ).order_by(
            PlayerMentorInteraction.sent_at.desc()
        ).all()
        
        interaction_data = []
        for interaction, mentor in interactions:
            interaction_data.append({
                'id': str(interaction.id),
                'player_id': str(interaction.player_id),
                'mentor_id': str(interaction.mentor_id),
                'mentor_name': mentor.name,
                'mentor_role': mentor.role,
                'mentor_avatar': mentor.avatar_url,
                'message_id': str(interaction.message_id) if interaction.message_id else None,
                'message_content': interaction.message_content,
                'trigger_type': interaction.trigger_type,
                'sent_at': interaction.sent_at.isoformat() if interaction.sent_at else None,
                'read_at': interaction.read_at.isoformat() if interaction.read_at else None,
                'action_taken': interaction.action_taken,
                'action_taken_at': interaction.action_taken_at.isoformat() if interaction.action_taken_at else None,
                'points_earned': interaction.points_earned or 0,
                'relationship_score': interaction.relationship_score or 0
            })
        
        return jsonify({
            'success': True,
            'data': interaction_data
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': 'INVALID_USER_ID',
            'message': 'Invalid user ID format'
        }), 400
    except Exception as e:
        print(f"Error fetching interactions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500


@mentor_bp.route('/api/social/interactions/<interaction_id>/read/', methods=['PUT'])
@require_auth
def mark_interaction_read(current_user_id: str, interaction_id: str):
    """
    Mark a mentor message as read
    
    Args:
        interaction_id: UUID of the interaction to mark as read
        
    Returns:
        Success status
        
    Security:
        Verifies the interaction belongs to the current user
    """
    try:
        # Convert IDs to UUIDs
        player_uuid = uuid.UUID(current_user_id)
        interaction_uuid = uuid.UUID(interaction_id)
        
        # Get interaction and verify ownership
        interaction = PlayerMentorInteraction.query.filter_by(
            id=interaction_uuid,
            player_id=player_uuid
        ).first()
        
        if not interaction:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Interaction not found or does not belong to you'
            }), 404
        
        # Mark as read if not already
        if not interaction.read_at:
            interaction.read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Interaction marked as read',
            'data': {
                'id': str(interaction.id),
                'read_at': interaction.read_at.isoformat()
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'INVALID_ID',
            'message': 'Invalid ID format'
        }), 400
    except Exception as e:
        print(f"Error marking interaction as read: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'UPDATE_FAILED',
            'message': str(e)
        }), 500


@mentor_bp.route('/api/social/interactions/<interaction_id>/action/', methods=['POST'])
@require_auth
def mark_advice_followed(current_user_id: str, interaction_id: str):
    """
    Mark that player followed mentor's advice and award points
    
    Args:
        interaction_id: UUID of the interaction
        
    Returns:
        Points earned, updated relationship score, and mentor details
        
    Security:
        Verifies the interaction belongs to the current user
    """
    try:
        # Convert IDs to UUIDs
        player_uuid = uuid.UUID(current_user_id)
        interaction_uuid = uuid.UUID(interaction_id)
        
        # Get interaction and verify ownership
        interaction = PlayerMentorInteraction.query.filter_by(
            id=interaction_uuid,
            player_id=player_uuid
        ).first()
        
        if not interaction:
            return jsonify({
                'success': False,
                'error': 'NOT_FOUND',
                'message': 'Interaction not found or does not belong to you'
            }), 404
        
        # Check if already followed
        if interaction.action_taken:
            return jsonify({
                'success': False,
                'error': 'ALREADY_FOLLOWED',
                'message': 'You already followed this advice'
            }), 400
        
        # Get message template to determine points
        message_template = None
        if interaction.message_id:
            message_template = MentorMessage.query.get(interaction.message_id)
        
        # Determine points based on priority
        points_to_award = 15  # Default
        if message_template:
            priority = message_template.priority or 3
            if priority == 5:
                points_to_award = 30  # High priority
            elif priority == 4:
                points_to_award = 25
            elif priority == 3:
                points_to_award = 15
            else:
                points_to_award = 10  # Low priority
        
        # Use service to mark as followed and award points
        updated_interaction = MentorService.mark_advice_followed(
            interaction_id=interaction_uuid,
            points=points_to_award
        )
        
        if not updated_interaction:
            return jsonify({
                'success': False,
                'error': 'UPDATE_FAILED',
                'message': 'Failed to update interaction'
            }), 500
        
        # Get mentor details
        mentor = Mentor.query.get(interaction.mentor_id)
        
        # Get total points for this player
        profile = Profile.query.filter_by(user_id=player_uuid).first()
        total_points = profile.experience_points if profile else points_to_award
        
        return jsonify({
            'success': True,
            'message': f'Great job! You earned {points_to_award} points',
            'data': {
                'points_earned': points_to_award,
                'mentor_id': str(mentor.id) if mentor else None,
                'mentor_name': mentor.name if mentor else 'Mentor',
                'new_relationship_score': updated_interaction.relationship_score,
                'total_points': total_points,
                'action_taken_at': updated_interaction.action_taken_at.isoformat()
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'INVALID_ID',
            'message': 'Invalid ID format'
        }), 400
    except Exception as e:
        print(f"Error marking advice as followed: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'UPDATE_FAILED',
            'message': str(e)
        }), 500


@mentor_bp.route('/api/mentors/<mentor_id>/interactions/', methods=['GET'])
@require_auth
def get_mentor_specific_interactions(current_user_id: str, mentor_id: str):
    """
    Get all interactions with a specific mentor
    
    Args:
        mentor_id: UUID of the mentor
        
    Returns:
        List of interactions with this specific mentor, ordered by most recent
        
    Used by: Individual mentor detail/chat screen
    """
    try:
        # Convert IDs to UUIDs
        player_uuid = uuid.UUID(current_user_id)
        mentor_uuid = uuid.UUID(mentor_id)
        
        # Verify mentor exists
        mentor = Mentor.query.get(mentor_uuid)
        if not mentor:
            return jsonify({
                'success': False,
                'error': 'MENTOR_NOT_FOUND',
                'message': 'Mentor not found'
            }), 404
        
        # Get interactions with this specific mentor
        interactions = PlayerMentorInteraction.query.filter_by(
            player_id=player_uuid,
            mentor_id=mentor_uuid
        ).order_by(
            PlayerMentorInteraction.sent_at.desc()
        ).all()
        
        interaction_data = []
        for interaction in interactions:
            interaction_data.append({
                'id': str(interaction.id),
                'message_content': interaction.message_content,
                'trigger_type': interaction.trigger_type,
                'sent_at': interaction.sent_at.isoformat() if interaction.sent_at else None,
                'read_at': interaction.read_at.isoformat() if interaction.read_at else None,
                'action_taken': interaction.action_taken,
                'action_taken_at': interaction.action_taken_at.isoformat() if interaction.action_taken_at else None,
                'points_earned': interaction.points_earned or 0,
                'relationship_score': interaction.relationship_score or 0
            })
        
        return jsonify({
            'success': True,
            'data': {
                'mentor': {
                    'id': str(mentor.id),
                    'name': mentor.name,
                    'role': mentor.role,
                    'personality': mentor.personality,
                    'avatar_url': mentor.avatar_url,
                    'greeting_template': mentor.greeting_template
                },
                'interactions': interaction_data,
                'total_interactions': len(interaction_data),
                'unread_count': len([i for i in interactions if not i.read_at]),
                'total_points': sum([i.points_earned or 0 for i in interactions]),
                'relationship_score': sum([i.relationship_score or 0 for i in interactions])
            }
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'INVALID_ID',
            'message': 'Invalid ID format'
        }), 400
    except Exception as e:
        print(f"Error fetching mentor interactions: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500


@mentor_bp.route('/api/mentors/stats/', methods=['GET'])
@require_auth
def get_mentor_stats(current_user_id: str):
    """
    Get player's overall mentor statistics
    
    Returns:
        Total messages, read count, advice followed, points earned, etc.
    """
    try:
        player_uuid = uuid.UUID(current_user_id)
        
        # Use service to calculate stats
        stats = MentorService.get_player_mentor_stats(player_uuid)
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'INVALID_USER_ID',
            'message': 'Invalid user ID format'
        }), 400
    except Exception as e:
        print(f"Error fetching mentor stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500
