from flask import Blueprint, request, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.models.profile import Profile
from app import db
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from app.utils.db import fetch_one

sanity_bp = Blueprint('sanity', __name__)

RECOVERY_ACTIONS = {
    'touch_grass': {'cost': 0, 'sanity': 5, 'message': 'You touched grass. Nature heals a little.'},
    'therapy': {'cost': 150, 'sanity': 20, 'message': 'Therapy session complete. You feel heard.'},
    'vacation': {'cost': 1000, 'sanity': 50, 'message': 'You went to Bali. You forgot your password. Bliss.'}
}

@sanity_bp.route('/recover/', methods=['POST'])
@require_auth
def recover_sanity(current_user_id: str):
    try:
        data = request.get_json(silent=True) or {}
        action_key = data.get('action')
        
        if action_key not in RECOVERY_ACTIONS:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
            
        action = RECOVERY_ACTIONS[action_key]
        cost = Decimal(action['cost'])
        sanity_gain = action['sanity']
        
        profile_res = fetch_one(supabase.table('profiles').select('sanity').eq('user_id', current_user_id))
        if not profile_res.data:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
        if (profile_res.data.get('sanity') or 0) >= 100:
            return jsonify({'success': False, 'message': 'Your sanity is already full.'}), 400

        if cost > 0:
            # Atomic debit; raises "Insufficient funds" instead of overdrawing
            BalanceService.subtract_balance(
                user_id=current_user_id,
                amount=cost,
                reason=f"Sanity Recovery: {action_key.replace('_', ' ').title()}",
                category='sanity_recovery',
            )
        else:
            # Free action: once per 24h (it used to be unlimited, making sanity meaningless)
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
            claim = supabase.table('profiles').update({'last_free_recovery_at': datetime.now(timezone.utc).isoformat()}) \
                .eq('user_id', current_user_id) \
                .or_(f'last_free_recovery_at.is.null,last_free_recovery_at.lt.{cutoff}') \
                .execute()
            if not claim.data:
                return jsonify({'success': False, 'message': 'You already touched grass today. Come back tomorrow.'}), 429

        # 2. Update sanity atomically (clamped 0-100 in SQL)
        current_sanity = profile_res.data.get('sanity') or 0
        new_sanity = supabase.rpc('adjust_sanity', {'p_user_id': current_user_id, 'p_delta': sanity_gain}).execute().data
        new_sanity = int(new_sanity) if new_sanity is not None else min(100, current_sanity + sanity_gain)
        sanity_gain = new_sanity - current_sanity

        return jsonify({
            'success': True,
            'message': action['message'],
            'sanity_gained': sanity_gain,
            'new_sanity': new_sanity,
            'cost': float(cost)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
