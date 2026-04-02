from flask import Blueprint, jsonify
from app import supabase
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app.services.profile_service import ProfileService
from app.services.job_service import JobService
import uuid

banking_bp = Blueprint('banking', __name__)

@banking_bp.route('/overview/', methods=['GET'])
@require_auth
def get_banking_overview(current_user_id: str):
    """
    Consolidated endpoint for banking screen initial data.
    Provides profile, assets, liabilities, jobs, transactions, and available loans.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        # 1. Profile & Balance
        profile = ProfileService.get_profile_by_user_id(user_uuid)
        balance = BalanceService.get_current_balance(current_user_id)
        
        # 2. Portfolio Assets
        assets_res = supabase.table('user_assets').select('*').eq('user_id', current_user_id).execute()
        assets = assets_res.data or []
        
        # 3. Active Liabilities (Joined)
        liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').eq('player_id', current_user_id).eq('is_active', True).execute()
        liabilities = liabilities_res.data or []
        
        # 4. Current Jobs
        jobs_res = supabase.table('jobs').select('*').eq('user_id', current_user_id).eq('is_active', True).execute()
        jobs = jobs_res.data or []
        
        # 5. Recent Transactions
        # Matching client's api.balance.history(20)
        transactions_res = supabase.table('transactions').select('*').eq('user_id', current_user_id).order('created_at', desc=True).limit(20).execute()
        transactions = transactions_res.data or []
        
        # 6. Available Bank Loans (Templates)
        bank_loans_res = supabase.table('bank_loans').select('*').is_('borrower_id', 'null').execute()
        bank_loans = bank_loans_res.data or []
        
        # 7. Available P2P Loans
        # Matching client's api.loans.getP2P()
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
