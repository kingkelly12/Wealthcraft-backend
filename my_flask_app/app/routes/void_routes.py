from flask import Blueprint, request, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
import os
import uuid

void_bp = Blueprint('void', __name__)

@void_bp.route('/scream', methods=['POST'])
@require_auth
def scream(current_user_id: str):
    try:
        data = request.json
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'Silence is not a scream.'}), 400
        
        if len(content) > 280:
            return jsonify({'success': False, 'message': 'Scream too long. Max 280 chars.'}), 400
            
        # Post to Supabase
        res = supabase.table('void_posts').insert({
            'user_id': current_user_id,
            'content': content
        }).execute()
        
        return jsonify({'success': True, 'message': 'Scream released into the void.'}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@void_bp.route('/feed', methods=['GET'])
@require_auth
def feed(current_user_id: str):
    try:
        # Fetch latest 50 posts
        posts_res = supabase.table('void_posts').select('*').order('created_at', desc=True).limit(50).execute()
        posts = posts_res.data
        
        # Fetch user's reactions to these posts to show "active" state
        post_ids = [p['id'] for p in posts]
        my_reactions = []
        if post_ids:
            reactions_res = supabase.table('void_reactions')\
                .select('post_id, reaction_type')\
                .eq('user_id', current_user_id)\
                .in_('post_id', post_ids)\
                .execute()
            my_reactions = reactions_res.data
            
        # Map reactions to posts
        reaction_map = {r['post_id']: r['reaction_type'] for r in my_reactions}
        
        feed_data = []
        for p in posts:
            feed_data.append({
                'id': p['id'],
                'content': p['content'],
                'oof_count': p['oof_count'],
                'same_count': p['same_count'],
                'created_at': p['created_at'],
                'my_reaction': reaction_map.get(p['id'], None),
                'is_mine': p['user_id'] == current_user_id
            })
            
        return jsonify({'success': True, 'data': feed_data}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@void_bp.route('/react', methods=['POST'])
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
                    _reward_sanity(post_res.data['user_id'], current_user_id)

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
            
            # SANITY REWARD CHECK
            if new_type == 'same':
                _reward_sanity(post_res.data['user_id'], current_user_id)
                
        # Apply updates to post
        if post_update:
            supabase.table('void_posts').update(post_update).eq('id', post_id).execute()
            
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def _reward_sanity(poster_id, reactor_id):
    """
    Give +1 Sanity to the poster if they receive a 'Same'.
    Prevent self-validation.
    """
    if poster_id == reactor_id:
        return # No ego boosting
        
    try:
        # Fetch poster's sanity
        res = supabase.table('profiles').select('sanity').eq('user_id', poster_id).single().execute()
        current = res.data.get('sanity', 100)
        
        # +1 Sanity, capped at 100
        if current < 100:
            new_val = current + 1
            supabase.table('profiles').update({'sanity': new_val}).eq('user_id', poster_id).execute()
    except:
        pass # Fail silently, don't block reaction


@void_bp.route('/scream/<post_id>', methods=['DELETE', 'PUT'])
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
