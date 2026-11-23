"""
Cron job routes — called by Supabase pg_cron scheduler.

Separated from user-facing routes (Single Responsibility Principle).
All endpoints are protected by a shared CRON_SECRET to prevent
unauthorized external calls.
"""

from flask import Blueprint, request, jsonify, current_app
import hmac
from functools import wraps

from jobs.daily_mentor_analysis import run_daily_mentor_analysis
from jobs.event_deadlines import run_event_deadlines
from jobs.inactive_users_monitor import run_inactive_users_monitor
from jobs.week_ready_nudge import run_week_ready_nudge

cron_bp = Blueprint('cron', __name__)


# ── Auth decorator ──────────────────────────────────────────────
def require_cron_secret(f):
    """Verify the request carries the correct CRON_SECRET bearer token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        cron_secret = current_app.config.get('CRON_SECRET')
        if not cron_secret:
            # If no secret is configured, reject all cron calls
            return jsonify({'success': False, 'error': 'CRON_SECRET not configured'}), 500

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Missing or invalid Authorization header'}), 401

        token = auth_header.split('Bearer ', 1)[1]
        if not hmac.compare_digest(token.encode(), cron_secret.encode()):
            return jsonify({'success': False, 'error': 'Invalid cron secret'}), 401

        return f(*args, **kwargs)
    return decorated


# ── Daily Jobs ──────────────────────────────────────────────────

@cron_bp.route('/mentor-analysis/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_mentor_analysis():
    """Daily mentor analysis — Schedule: 0 6 * * * (6 AM daily)"""
    try:
        result = run_daily_mentor_analysis()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Mentor analysis failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


@cron_bp.route('/event-deadlines/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_event_deadlines():
    """Answer life events left unanswered past their time limit — Schedule: 0 9 * * * (9 AM daily)"""
    try:
        result = run_event_deadlines()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Event deadlines failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500

@cron_bp.route('/inactive-users-monitor/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_inactive_users_monitor():
    """Inactive users monitor — Schedule: 0 10 * * * (10 AM daily)"""
    try:
        result = run_inactive_users_monitor()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Inactive users monitor failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


# ── Monthly Jobs ────────────────────────────────────────────────

@cron_bp.route('/week-ready/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_week_ready():
    """'Your week is ready' push from a cast member, max one a day — Schedule: 0 16 * * *"""
    try:
        return jsonify({'success': True, 'data': run_week_ready_nudge()}), 200
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('Week-ready nudge failed')
        return jsonify({'success': False, 'error': str(e), 'type': type(e).__name__}), 500


# ── Diagnostic Endpoint ─────────────────────────────────────────

@cron_bp.route('/mission-deadlines/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_mission_deadlines():
    """Decide mission decisions left past their deadline — Schedule: daily"""
    from app.game.mission_decisions import run_mission_deadlines
    try:
        return jsonify({'success': True, 'data': run_mission_deadlines()}), 200
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception('Mission deadlines failed')
        return jsonify({'success': False, 'error': str(e), 'type': type(e).__name__}), 500


@cron_bp.route('/push-receipts/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_push_receipts():
    """Read Expo push receipts and clear tokens of uninstalled apps — Schedule: hourly"""
    from app import supabase
    from app.services.push_notification_service import ExpoPushService
    try:
        result = ExpoPushService.check_receipts(supabase)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Push receipts failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e), 'type': type(e).__name__}), 500


@cron_bp.route('/health/', methods=['GET', 'POST'], strict_slashes=False)
@require_cron_secret
def cron_health():
    """Diagnostic endpoint to verify cron job infrastructure is operational"""
    from app import supabase
    
    diagnostics = {
        'supabase_client_initialized': supabase is not None,
        'cron_secret_configured': bool(current_app.config.get('CRON_SECRET')),
        'supabase_url_set': bool(current_app.config.get('SUPABASE_URL')),
        'service_role_key_set': bool(current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')),
        'regular_key_set': bool(current_app.config.get('SUPABASE_KEY')),
    }
    
    # Test database connection
    try:
        if supabase:
            supabase.table('assets').select('id').limit(1).execute()
            diagnostics['database_accessible'] = True
        else:
            diagnostics['database_accessible'] = False
            diagnostics['error'] = 'Supabase client is None'
    except Exception as e:
        diagnostics['database_accessible'] = False
        diagnostics['error'] = str(e)
    
    return jsonify({
        'success': all([
            diagnostics.get('supabase_client_initialized'),
            diagnostics.get('cron_secret_configured'),
            diagnostics.get('database_accessible')
        ]),
        'diagnostics': diagnostics
    }), 200
