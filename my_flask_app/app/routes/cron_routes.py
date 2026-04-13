"""
Cron job routes — called by Supabase pg_cron scheduler.

Separated from user-facing routes (Single Responsibility Principle).
All endpoints are protected by a shared CRON_SECRET to prevent
unauthorized external calls.
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps

from jobs.daily_mentor_analysis import run_daily_mentor_analysis
from jobs.market_fluctuation_monitor import simulate_market_fluctuation
from jobs.monthly_depreciation import run_monthly_depreciation
from jobs.monthly_apreciation import run_monthly_appreciation
from jobs.monthly_loan_deductions import process_monthly_deductions
from jobs.trigger_random_events import trigger_random_events
from jobs.inactive_users_monitor import run_inactive_users_monitor

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
        if token != cron_secret:
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


@cron_bp.route('/random-events/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_random_events():
    """Trigger random life events — Schedule: 0 9 * * * (9 AM daily)"""
    try:
        result = trigger_random_events()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Random events failed: {str(e)}\n{traceback.format_exc()}")
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


# ── Hourly Jobs ─────────────────────────────────────────────────

@cron_bp.route('/market-monitor/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_market_monitor():
    """Market fluctuation simulation — Schedule: 0 * * * * (every hour)"""
    try:
        simulate_market_fluctuation()
        return jsonify({'success': True, 'message': 'Market monitor executed'}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Market monitor failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


# ── Monthly Jobs ────────────────────────────────────────────────

@cron_bp.route('/depreciation/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_depreciation():
    """Monthly liability depreciation — Schedule: 0 2 1 * * (1st, 2 AM)"""
    try:
        result = run_monthly_depreciation()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Depreciation job failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


@cron_bp.route('/appreciation/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_appreciation():
    """Monthly asset appreciation — Schedule: 0 3 1 * * (1st, 3 AM)"""
    try:
        result = run_monthly_appreciation()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Appreciation job failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


@cron_bp.route('/loan-deductions/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_loan_deductions():
    """Monthly loan deductions — Schedule: 0 4 15 * * (15th, 4 AM)"""
    try:
        result = process_monthly_deductions()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        import traceback
        import logging
        error_logger = logging.getLogger(__name__)
        error_logger.error(f"Loan deductions failed: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False, 
            'error': str(e),
            'type': type(e).__name__
        }), 500


# ── Diagnostic Endpoint ─────────────────────────────────────────

@cron_bp.route('/health/', methods=['GET', 'POST'], strict_slashes=False)
@require_cron_secret
def cron_health():
    """Diagnostic endpoint to verify cron job infrastructure is operational"""
    from app import supabase
    import logging
    
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
            test_result = supabase.table('assets').select('id').limit(1).execute()
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
