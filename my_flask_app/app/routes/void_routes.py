from flask import Blueprint, request, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.push_notification_service import ExpoPushService
from app.services.profile_service import ProfileService
import os
import uuid
import logging

logger = logging.getLogger(__name__)

def resolve_user_ids(user_id):
    """
    Given a user_id (could be Auth UID or Profile ID),
    return a list of both possible IDs to ensure robust matching across tables.
    """
    try:
        uuid_obj = uuid.UUID(user_id)
        # Try finding profile by user_id First
        profile = ProfileService.get_profile_by_user_id(uuid_obj)
        if profile:
            return [str(profile.user_id), str(profile.id)]
        
        # If not found, try finding by profile ID
        from app.models.profile import Profile
        profile = Profile.query.filter_by(id=uuid_obj).first()
        if profile:
            return [str(profile.user_id), str(profile.id)]
            
        return [user_id]
    except:
        return [user_id]

void_bp = Blueprint('void', __name__)

from app.services.ai_service import AIService
from app.services.mentor_service import MentorService

@void_bp.route('/scream/', methods=['POST'])
@require_auth
def scream(current_user_id: str):
    try:
        data = request.json
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Silence is not a scream.'}), 400
        
        if len(content) > 280:
            return jsonify({'success': False, 'message': 'Scream too long. Max 280 chars.'}), 400

        # AI Analysis
        player_uuid = uuid.UUID(current_user_id)
        profile = ProfileService.get_profile_by_user_id(player_uuid)
        
        # Build context
        metrics = MentorService.analyze_player_finances(player_uuid)
        metrics['sanity'] = profile.sanity if profile and hasattr(profile, 'sanity') else 100
        metrics['username'] = profile.username if profile else 'Player'
        
        ai_analysis = AIService.analyze_void_scream(content, metrics)
            
        # Post to Supabase
        res = supabase.table('void_posts').insert({
            'user_id': current_user_id,
            'content': content,
            'ai_analysis': ai_analysis
        }).execute()
        
        return jsonify({
            'success': True, 
            'message': 'Scream released into the void.',
            'data': {
                'ai_analysis': ai_analysis
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error in scream route: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def _get_feed_data_internal(current_user_id: str, cursor=None, limit=20):
    """Internal helper to fetch feed data without triggering route decorators."""
    try:
        user_ids = resolve_user_ids(current_user_id)
        limit = min(int(limit), 50)

        # 1. Fetch Posts with Author Profiles in ONE trip
        query = supabase.table('void_posts')\
            .select('*, author:profiles!user_id(username, profile_picture_url)')\
            .order('created_at', desc=True)
            
        if cursor:
            query = query.lt('created_at', cursor)
            
        posts_res = query.limit(limit + 1).execute()
        raw_posts = posts_res.data or []

        has_more = len(raw_posts) > limit
        posts = raw_posts[:limit]
        post_ids = [p['id'] for p in posts]

        next_cursor = posts[-1]['created_at'] if posts else None
        
        # 2. Fetch ALL Reactions for these posts (for preview & my_reaction) in ONE trip
        all_reactions = []
        if post_ids:
            all_reactions_res = supabase.table('void_reactions')\
                .select('post_id, user_id, reaction_type, created_at, profiles(username, profile_picture_url)')\
                .in_('post_id', post_ids)\
                .order('created_at', desc=True)\
                .execute()
            all_reactions = all_reactions_res.data or []
        
        # 3. Organize reactions by post
        reactions_by_post = {}
        my_reactions = {} # post_id -> reaction_type

        for r in all_reactions:
            pid = r['post_id']
            uid = r['user_id']
            rtype = r['reaction_type']
            
            # Map my reaction
            if uid == current_user_id:
                my_reactions[pid] = rtype
                
            # Add to preview (latest 5)
            if pid not in reactions_by_post:
                reactions_by_post[pid] = []
            
            if len(reactions_by_post[pid]) < 5:
                profile = r.get('profiles', {})
                reactions_by_post[pid].append({
                    'username': profile.get('username', 'Anonymous'),
                    'profile_picture_url': profile.get('profile_picture_url'),
                    'reaction_type': rtype
                })
        
        # 4. Map everything to feed data
        feed_data = []
        for p in posts:
            author = p.get('author') or {}
            feed_data.append({
                'id': p['id'],
                'content': p['content'],
                'oof_count': p['oof_count'],
                'same_count': p['same_count'],
                'created_at': p['created_at'],
                'my_reaction': my_reactions.get(p['id']),
                'is_mine': p['user_id'] in user_ids,
                'reactors': reactions_by_post.get(p['id'], []),
                'author': {
                    'user_id': p['user_id'],
                    'username': author.get('username', 'Anonymous'),
                    'avatar_url': author.get('profile_picture_url')
                }
            })
            
        return {
            'data': feed_data,
            'next_cursor': next_cursor,
            'has_more': has_more
        }
    except Exception as e:
        logger.error(f"Internal feed fetch error: {str(e)}")
        raise e

@void_bp.route('/feed/', methods=['GET'])
@require_auth
def feed(current_user_id: str):
    try:
        # --- Cursor-based pagination (The Bottomless Bowl) ---
        cursor = request.args.get('cursor')  # ISO timestamp of last post seen
        limit = min(int(request.args.get('limit', 20)), 50)

        result = _get_feed_data_internal(current_user_id, cursor, limit)
        return jsonify({
            'success': True,
            **result
        }), 200
        
    except Exception as e:
        logger.error(f"Feed error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@void_bp.route('/overview/', methods=['GET'])
@require_auth
def void_overview(current_user_id: str):
    """Consolidated endpoint for Void screen mount"""
    try:
        user_ids = resolve_user_ids(current_user_id)
        
        # 1. Fetch Profile info (small snippet)
        profile_res = supabase.table('profiles')\
            .select('username, profile_picture_url, sanity')\
            .in_('user_id', user_ids)\
            .execute()
            
        profile = profile_res.data[0] if profile_res.data else None
        
        # 2. Fetch first page of Feed (Reuse internal logic)
        feed_data = _get_feed_data_internal(current_user_id)
        
        return jsonify({
            'success': True,
            'profile': profile,
            'feed': feed_data
        }), 200
        
    except Exception as e:
        logger.error(f"Overview error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@void_bp.route('/react/', methods=['POST'])
@require_auth
def react(current_user_id: str):
    try:
        data = request.json
        post_id = data.get('post_id')
        new_type = data.get('type') # 'oof' or 'same'
        
        if new_type not in ['oof', 'same']:
            return jsonify({'success': False, 'message': 'Invalid reaction'}), 400
            
        # Check existing reaction
        existing_res = supabase.table('void_reactions')\
            .select('*')\
            .eq('user_id', current_user_id)\
            .eq('post_id', post_id)\
            .execute()
        
        existing = existing_res.data[0] if existing_res.data else None
        
        # Determine counter updates
        post_update = {}
        
        if existing:
            if existing['reaction_type'] == new_type:
                # Toggle OFF (Remove reaction)
                supabase.table('void_reactions').delete().eq('id', existing['id']).execute()
                # Decrement counter
                col = f"{new_type}_count"
                # Need atomic decrement, but for now fetching post to get current count roughly or just trusting client? 
                # Better: use RPC or just read-update-write for MVP.
                # Assuming low concurrency for MVP.
                post_res = supabase.table('void_posts').select(col).eq('id', post_id).single().execute()
                curr_count = post_res.data.get(col, 0)
                post_update[col] = max(0, curr_count - 1)
                
            else:
                # Switch reaction (e.g. oof -> same)
                supabase.table('void_reactions').update({'reaction_type': new_type}).eq('id', existing['id']).execute()
                # Decrement old, Increment new
                old_col = f"{existing['reaction_type']}_count"
                new_col = f"{new_type}_count"
                
                post_res = supabase.table('void_posts').select('*').eq('id', post_id).single().execute()
                post_update[old_col] = max(0, post_res.data.get(old_col, 0) - 1)
                post_update[new_col] = post_res.data.get(new_col, 0) + 1
                
                # SANITY REWARD CHECK (Switching TO 'same')
                if new_type == 'same':
                    # Recipient reward
                    _apply_sanity_impact(post_res.data['user_id'], +1)
                    # Reactor reward (Helper's High)
                    _apply_sanity_impact(current_user_id, +1)
                    _send_consolation_notification(post_res.data['user_id'], current_user_id, post_id)
                # SANITY PENALTY (Switching TO 'oof')
                elif new_type == 'oof':
                    # Recipient penalty
                    _apply_sanity_impact(post_res.data['user_id'], -1)
                    # Reactor penalty (the person being rough)
                    _apply_sanity_impact(current_user_id, -1)

        else:
            # New Reaction
            supabase.table('void_reactions').insert({
                'user_id': current_user_id,
                'post_id': post_id,
                'reaction_type': new_type
            }).execute()
            
            # Increment new
            col = f"{new_type}_count"
            post_res = supabase.table('void_posts').select(col, 'user_id').eq('id', post_id).single().execute()
            post_update[col] = post_res.data.get(col, 0) + 1
            
            # SANITY REWARD/PENALTY CHECK
            if new_type == 'same' and post_res.data['user_id'] != current_user_id:
                # Recipient reward
                _apply_sanity_impact(post_res.data['user_id'], +1)
                # Reactor reward (Helper's High)
                _apply_sanity_impact(current_user_id, +1)
                _send_consolation_notification(post_res.data['user_id'], current_user_id, post_id)
            elif new_type == 'oof' and post_res.data['user_id'] != current_user_id:
                # Recipient penalty
                _apply_sanity_impact(post_res.data['user_id'], -1)
                # Reactor penalty (the person being rough)
                _apply_sanity_impact(current_user_id, -1)
                
        # Apply updates to post
        if post_update:
            supabase.table('void_posts').update(post_update).eq('id', post_id).execute()
            
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def _apply_sanity_impact(user_id: str, delta: int):
    """
    Apply a sanity change (positive or negative) to a user.
    - Positive delta = gain (capped at 100).
    - Negative delta = loss (capped at 0).
    - Will not deduct below 0.
    """
    try:
        res = supabase.table('profiles').select('sanity').eq('user_id', user_id).single().execute()
        current = res.data.get('sanity', 100)
        
        if delta < 0 and current <= 0:
            return  # Already at 0, don't go below
        
        new_val = max(0, min(100, current + delta))
        supabase.table('profiles').update({'sanity': new_val}).eq('user_id', user_id).execute()
    except:
        pass  # Fail silently, don't block reaction


def _send_consolation_notification(poster_id, reactor_id, post_id):
    """
    Send a "Consolation" push notification to the poster when someone reacts 'Same'.
    
    Psychology:
    - The notification deliberately withholds WHO reacted.
    - The user must re-enter The Void to see the reactor's face.
    - Copy sells the FEELING ("You're not alone") not the feature.
    """
    if poster_id == reactor_id:
        return  # No self-notifications
    
    try:
        ExpoPushService.send_notification_to_user(
            supabase_client=supabase,
            user_id=poster_id,
            title="🫂 The Void Heard You",
            body="Someone just related to your scream. You're not alone. Your Sanity is rising.",
            notification_type='void_consolation',
            data={
                'type': 'void_consolation',
                'screen': '/(tabs)/void',
                'post_id': str(post_id)
            }
        )
        logger.info(f"Consolation notification sent to poster {poster_id} for post {post_id}")
    except Exception as e:
        logger.error(f"Failed to send consolation notification: {str(e)}")
        # Fail silently — never block the reaction flow


@void_bp.route('/scream/<post_id>/', methods=['DELETE', 'PUT'])
@require_auth
def manage_scream(current_user_id: str, post_id: str):
    try:
        # Check ownership
        post_res = supabase.table('void_posts').select('*').eq('id', post_id).single().execute()
        if not post_res.data:
             return jsonify({'success': False, 'message': 'Post not found'}), 404
             
        post = post_res.data
        if post['user_id'] != current_user_id:
             return jsonify({'success': False, 'message': 'Unauthorized'}), 403
             
        if request.method == 'DELETE':
            supabase.table('void_posts').delete().eq('id', post_id).execute()
            return jsonify({'success': True, 'message': 'Scream deleted'}), 200
            
        if request.method == 'PUT':
            data = request.json
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'success': False, 'message': 'Silence is not a scream.'}), 400
                
            if len(content) > 280:
                return jsonify({'success': False, 'message': 'Scream too long. Max 280 chars.'}), 400
                
            supabase.table('void_posts').update({'content': content}).eq('id', post_id).execute()
            return jsonify({'success': True, 'message': 'Scream updated'}), 200
            
    except Exception as e:
         return jsonify({'success': False, 'message': str(e)}), 500
