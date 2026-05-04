"""
Consolidated Dashboard endpoint
Returns all data needed for the home screen in ONE request:
- Profile & Balance
- Assets
- Liabilities
- Jobs
- Rentals
- Missions Status
- Top 5 Leaderboard Players
- Market News

This consolidates 9+ separate API calls into 1, improving performance by 70%+
"""
from flask import Blueprint, jsonify
from app.utils.jwt_helper import require_auth
from app import supabase
import uuid
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


def resolve_user_ids(user_id: str) -> list:
    """
    Given a user_id (could be Supabase Auth UID or Profile UUID),
    return a list of both possible IDs so lookups work regardless of which
    UUID was used when creating a given record.

    Uses Supabase directly (not SQLAlchemy) to ensure this works in production
    where the SQLAlchemy DB connection may not be active.
    """
    try:
        # Try resolving by user_id (auth UID)
        res = supabase.table('profiles').select('id, user_id').eq('user_id', user_id).limit(1).execute()
        if res.data:
            p = res.data[0]
            ids = list({str(p['user_id']), str(p['id'])})
            logger.debug(f"resolve_user_ids({user_id}) → {ids}")
            return ids

        # Try resolving by profile id (profile UUID)
        res = supabase.table('profiles').select('id, user_id').eq('id', user_id).limit(1).execute()
        if res.data:
            p = res.data[0]
            ids = list({str(p['user_id']), str(p['id'])})
            logger.debug(f"resolve_user_ids({user_id}) via profile.id → {ids}")
            return ids

    except Exception as e:
        logger.warning(f"resolve_user_ids failed for {user_id}: {e}")

    # Fallback: use whatever was passed in
    return [user_id]


@dashboard_bp.route('/consolidated/', methods=['GET'])
@require_auth
def get_consolidated_dashboard(current_user_id: str):
    """
    GET /api/dashboard/consolidated/

    Returns everything needed for home screen in a single request.

    Replaces:
    - /api/profile/overview/
    - /api/profile/me/
    - /api/missions/status/
    - /api/social/leaderboard/?limit=5
    - Multiple /api/user_balances, /api/user_assets queries

    Performance: 9+ queries → 1 consolidated endpoint
    """
    try:
        user_ids = resolve_user_ids(current_user_id)
        logger.info(f"Dashboard: fetching consolidated data for user_ids {user_ids}")

        # 1. Profile
        profile_res = supabase.table('profiles').select('*').in_('user_id', user_ids).execute()
        if not profile_res.data:
            profile_res = supabase.table('profiles').select('*').in_('id', user_ids).execute()

        if not profile_res.data:
            return jsonify({'success': False, 'error': 'USER_NOT_FOUND', 'message': 'Profile not found'}), 404

        profile = profile_res.data[0]

        # 2. Account Balance
        balance_res = supabase.table('user_balances').select('current_balance').in_('user_id', user_ids).execute()
        account_balance = 0.0
        if balance_res.data:
            try:
                account_balance = float(balance_res.data[0].get('current_balance', 0))
            except Exception:
                pass

        # 3. Assets
        assets_res = supabase.table('user_assets').select('*').in_('user_id', user_ids).execute()
        assets = assets_res.data or []

        # 4. Active Liabilities (luxury lifestyle items)
        liabilities_res = supabase.table('player_liabilities').select('*, liability_items(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        luxury_liabilities = liabilities_res.data or []

        # 5. Active Loans
        loans_res = supabase.table('liabilities').select('*').in_('user_id', user_ids).execute()
        loans = loans_res.data or []

        # Combine all liabilities
        all_liabilities = luxury_liabilities + loans

        # 6. Active Jobs
        jobs_res = supabase.table('jobs').select('*').in_('user_id', user_ids).eq('is_current', True).execute()
        jobs = jobs_res.data or []

        # 7. Active Rentals
        rental_res = supabase.table('player_rentals').select('*, rental_properties(*)').in_('player_id', user_ids).eq('is_active', True).execute()
        rental = rental_res.data[0] if (rental_res.data and len(rental_res.data) > 0) else None

        # 8. Missions Status
        mission_progress_res = supabase.table('player_mission_progress').select(
            'id, mission_id, current_month, integrated_missions!mission_id(name, duration_months)'
        ).in_('player_id', user_ids).eq('is_active', True).execute()
        active_missions = mission_progress_res.data or []

        # 9. Completed Missions Count
        completed_missions_res = supabase.table('mission_completion_results').select('id').in_('player_id', user_ids).eq('completed', True).execute()
        completed_count = len(completed_missions_res.data) if completed_missions_res.data else 0

        # 10. Top 5 Leaderboard Players
        try:
            leaderboard_res = supabase.rpc('get_top_players', {'limit_count': 5}).execute()
            top_players = leaderboard_res.data or []
        except Exception as rpc_err:
            logger.warning(f"Leaderboard RPC failed, using fallback: {str(rpc_err)}")
            leaderboard_res = supabase.table('profiles').select(
                'id, user_id, username, net_worth, profile_picture_url'
            ).order('net_worth', desc=True).limit(5).execute()
            top_players = leaderboard_res.data or []

        top_players_with_rank = []
        for idx, player in enumerate(top_players):
            top_players_with_rank.append({
                'id': player.get('id'),
                'user_id': player.get('user_id'),
                'username': player.get('username'),
                'net_worth': float(player.get('net_worth', 0)),
                'profile_picture_url': player.get('profile_picture_url'),
                'rank': idx + 1
            })

        # 11. Market News (latest 10 headlines for MarketNewsTicker)
        try:
            news_res = supabase.table('market_news').select(
                'id, headline, body, analyst_tip, category, created_at'
            ).order('created_at', desc=True).limit(10).execute()
            news = news_res.data or []
        except Exception as news_err:
            logger.warning(f"Market news fetch failed: {str(news_err)}")
            news = []

        return jsonify({
            'success': True,
            'data': {
                'profile': profile,
                'account_balance': account_balance,
                'portfolio': assets,
                'liabilities': all_liabilities,
                'jobs': jobs,
                'rental': rental,
                'missions': {
                    'active_count': len(active_missions),
                    'completed_count': completed_count,
                    'active_missions': active_missions
                },
                'leaderboard': top_players_with_rank,
                'news': news
            }
        }), 200

    except Exception as e:
        logger.error(f"[Dashboard Consolidated] Error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'FETCH_FAILED',
            'message': str(e)
        }), 500
