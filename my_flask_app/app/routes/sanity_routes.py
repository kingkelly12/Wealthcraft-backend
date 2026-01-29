from flask import Blueprint, request, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.models.profile import Profile
from app import db
from decimal import Decimal
import os

sanity_bp = Blueprint('sanity', __name__)

RECOVERY_ACTIONS = {
    'touch_grass': {'cost': 0, 'sanity': 5, 'message': 'You touched grass. Nature heals a little.'},
    'therapy': {'cost': 150, 'sanity': 20, 'message': 'Therapy session complete. You feel heard.'},
    'vacation': {'cost': 1000, 'sanity': 50, 'message': 'You went to Bali. You forgot your password. Bliss.'}
}

@sanity_bp.route('/recover', methods=['POST'])
@require_auth
def recover_sanity(current_user_id: str):
    try:
        data = request.json
        action_key = data.get('action')
        
        if action_key not in RECOVERY_ACTIONS:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
            
        action = RECOVERY_ACTIONS[action_key]
        cost = Decimal(action['cost'])
        sanity_gain = action['sanity']
        
        # 1. Check Balance
        if cost > 0:
            current_balance = BalanceService.get_current_balance(current_user_id)
            if current_balance < cost:
                 return jsonify({'success': False, 'message': 'Insufficient funds'}), 400
                 
            # Deduct cost
            BalanceService.subtract_balance(
                user_id=current_user_id,
                amount=cost,
                reason=f"Sanity Recovery: {action_key.replace('_', ' ').title()}"
            )
            
        # 2. Update Sanity
        profile_res = supabase.table('profiles').select('sanity').eq('user_id', current_user_id).single().execute()
        current_sanity = profile_res.data.get('sanity', 100)
        
        new_sanity = min(100, current_sanity + sanity_gain)
        
        supabase.table('profiles').update({'sanity': new_sanity}).eq('user_id', current_user_id).execute()
        
        return jsonify({
            'success': True,
            'message': action['message'],
            'sanity_gained': sanity_gain,
            'new_sanity': new_sanity,
            'cost': float(cost)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
