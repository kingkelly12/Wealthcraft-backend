from flask import Blueprint, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.profile_service import ProfileService
import uuid
import logging

logger = logging.getLogger(__name__)

banking_bp = Blueprint('banking', __name__)

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

@banking_bp.route('/overview/', methods=['GET'])
@require_auth
def get_banking_overview(current_user_id: str):
    try:
        user_ids = resolve_user_ids(current_user_id)
        logger.info(f"Banking Overview: fetching data for user_ids {user_ids}")
        
        # 1. Profile & Balance
        # Use simple select to find profile by user_id OR id
        profile_res = supabase.table('profiles').select('*, user_balances(current_balance)').in_('user_id', user_ids).execute()
        if not profile_res or not profile_res.data:
            profile_res = supabase.table('profiles').select('*, user_balances(current_balance)').in_('id', user_ids).execute()
            
        if not profile_res or not profile_res.data:
             # Last resort: try model query if Supabase failed
             from app.models.profile import Profile
             profile_obj = Profile.query.filter((Profile.user_id.in_(user_ids)) | (Profile.id.in_(user_ids))).first()
             if profile_obj:
                 profile = profile_obj.to_dict()
                 # Fetch balance separately if needed
                 balance = BalanceService.get_current_balance(current_user_id)
                 profile['user_balances'] = [{'current_balance': float(balance)}]
             else:
                 logger.error(f"Banking Overview: Profile not found for user_ids {user_ids}")
                 return jsonify({'success': False, 'error': 'USER_NOT_FOUND', 'message': f'Profile not found for {current_user_id}'}), 404
        else:
            profile = profile_res.data[0]

        # 2. Portfolio Assets
        assets_res = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        assets = assets_res.data or []
        
        # 3. Active Liabilities
        liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        liabilities = liabilities_res.data or []
        
        # 4. Active Jobs
        jobs_res = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        jobs = jobs_res.data or []
        
        # 5. Recent Transactions
        transactions_res = supabase.table('transactions').select('*').in_('user_id', user_ids).order('created_at', desc=True).limit(20).execute()
        transactions = transactions_res.data or []
        
        # 6. Available Bank Loans (Templates)
        bank_loans_res = supabase.table('bank_loans').select('*').is_('borrower_id', 'null').execute()
        bank_loans = bank_loans_res.data or []
        
        # 7. Available P2P Loans (with lender username)
        # Use full foreign key name to disambiguate between multiple relationships
        p2p_loans_res = supabase.table('p2p_loans').select('*, profiles!p2p_loans_lender_id_fkey(username)').eq('status', 'pending').neq('lender_id', current_user_id).execute()
        p2p_loans = p2p_loans_res.data or []
        
        # Account balance extraction
        account_balance = 0.0
        if profile.get('user_balances'):
             try:
                 account_balance = float(profile.get('user_balances', [{}])[0].get('current_balance', 0))
             except:
                 account_balance = 0.0

        return jsonify({
            'success': True,
            'data': {
                'profile': profile,
                'account_balance': account_balance,
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
