from flask import Blueprint, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.profile_service import ProfileService
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
import uuid

banking_bp = Blueprint('banking', __name__)

@banking_bp.route('/overview/', methods=['GET'])
@require_auth
def get_banking_overview(current_user_id: str):
    try:
        user_ids = resolve_user_ids(current_user_id)
        logger.info(f"Banking Overview: fetching data for user_ids {user_ids}")
        
        # 1. Profile & Balance
        # Try to find profile by any of the IDs
        profile = None
        for uid in user_ids:
            profile = ProfileService.get_profile_by_user_id(uuid.UUID(uid))
            if profile: break
            
        balance = BalanceService.get_current_balance(current_user_id)
        
        # 2. Portfolio Assets
        assets_res = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        assets = assets_res.data or []
        
        # 3. Active Liabilities (Joined)
        liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        liabilities = liabilities_res.data or []
        
        # 4. Current Jobs
        jobs_res = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_active', True).execute()
        jobs = jobs_res.data or []
        
        # 5. Recent Transactions
        transactions_res = supabase.table('transactions').select('*').in_('user_id', user_ids).order('created_at', desc=True).limit(20).execute()
        transactions = transactions_res.data or []
        
        # 6. Available Bank Loans (Templates)
        bank_loans_res = supabase.table('bank_loans').select('*').is_('borrower_id', 'null').execute()
        bank_loans = bank_loans_res.data or []
        
        # 7. Available P2P Loans
        p2p_loans_res = supabase.table('p2p_loans').select('*').eq('status', 'pending').neq('lender_id', current_user_id).execute()
        p2p_loans = p2p_loans_res.data or []
        
        return jsonify({
            'success': True,
            'data': {
                'profile': profile.to_dict() if profile else None,
                'account_balance': float(balance),
                'portfolio': assets,
                'liabilities': liabilities,
                'jobs': jobs,
                'transactions': transactions,
                'bank_offers': bank_loans,
                'p2p_offers': p2p_loans
            }
        }), 200
        
    except Exception as e:
        print(f"[Banking Overview] Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500
