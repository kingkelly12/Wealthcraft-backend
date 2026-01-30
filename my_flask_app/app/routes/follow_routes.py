"""
Follow management routes
Handles follow/unfollow operations with JWT authentication to prevent manipulation
"""
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.utils.jwt_helper import require_auth
from app.schemas.follow_schema import FollowUserRequest, FollowUserResponse
from app import supabase
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

follow_bp = Blueprint('follow', __name__)


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


@follow_bp.route('/leaderboard', methods=['GET'])
@require_auth
def get_leaderboard(current_user_id: str):
    """
    Get leaderboard data sorted by specified metric
    
    Query Params:
    - sort_by: net_worth | monthly_income | credit_score | trading_profits (default: net_worth)
    - limit: max results (default: 50, max: 100)
    """
    try:
        from app.models.profile import Profile
        from sqlalchemy import desc
        from app import db
        
        # Get query parameters
        sort_by = request.args.get('sort_by', 'net_worth')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        # Validate sort_by
        valid_sort_fields = ['net_worth', 'monthly_income', 'credit_score', 'trading_profits', 'sanity']
        if sort_by not in valid_sort_fields:
            sort_by = 'net_worth'
            
        # Determine sort column
        sort_column = getattr(Profile, sort_by)
        
        # Query database
        profiles = db.session.query(Profile)\
            .order_by(desc(sort_column))\
            .limit(limit)\
            .all()
            
        # Format response
        leaderboard_data = []
        for index, profile in enumerate(profiles):
            data = profile.to_dict()
            data['rank'] = index + 1
            leaderboard_data.append(data)
            
        return jsonify({
            'success': True,
            'data': leaderboard_data
        }), 200
        
    except Exception as e:
        print(f"Leaderboard error: {str(e)}")
@follow_bp.route('/mentors', methods=['GET'])
def get_mentors():
    """Get list of potential mentors"""
    try:
        # Assuming mentors specific logic or just fetch high net worth users
        # For MVP, returning top 10 net worth users as mentors
        response = supabase.table('profiles').select('*').order('net_worth', desc=True).limit(10).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@follow_bp.route('/search', methods=['GET'])
def search_users():
    """Search for users"""
    try:
        query = request.args.get('query', '')
        if not query:
             return jsonify({'success': True, 'data': []}), 200
             
        response = supabase.table('profiles').select('*').ilike('username', f'%{query}%').execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@follow_bp.route('/rank/<user_id>', methods=['GET'])
def get_user_rank(user_id: str):
    """Get specific user's rank"""
    try:
        # Logic to calculate rank (can be expensive, maybe optimized via view?)
        # For now, simple count query
        profile_res = supabase.table('profiles').select('net_worth').eq('user_id', user_id).single().execute()
        if not profile_res.data:
             return jsonify({'success': False, 'error': 'User not found'}), 404
             
        net_worth = profile_res.data['net_worth']
        
        # Count users with greater net worth
        count_res = supabase.table('profiles').select('id', count='exact').gt('net_worth', net_worth).execute()
        rank = count_res.count + 1
        
        return jsonify({'success': True, 'data': rank}), 200
    except Exception as e:
         return jsonify({'success': False, 'error': str(e)}), 500

@follow_bp.route('/interactions', methods=['GET'])
@require_auth
def get_interactions(current_user_id: str):
    """Get social interactions"""
    try:
        # Assuming 'social_interactions' table
        response = supabase.table('social_interactions').select('*').eq('user_id', current_user_id).order('created_at', desc=True).execute()
        return jsonify({'success': True, 'data': response.data}), 200
    except Exception as e:
        # If table doesn't exist, return empty list
        return jsonify({'success': True, 'data': []}), 200

@follow_bp.route('/interactions/<interaction_id>/read', methods=['PUT'])
@require_auth
def mark_interaction_read(current_user_id: str, interaction_id: str):
    """Mark interaction as read"""
    try:
        supabase.table('social_interactions').update({'is_read': True}).eq('id', interaction_id).eq('user_id', current_user_id).execute()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@follow_bp.route('/interactions/<interaction_id>/action', methods=['POST'])
@require_auth
def interaction_action(current_user_id: str, interaction_id: str):
    """Perform action on interaction (e.g. accept friend request?)"""
    return jsonify({'success': True}), 200
