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
        return jsonify({'success': False, 'error': str(e)}), 500


@cron_bp.route('/random-events/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_random_events():
    """Trigger random life events — Schedule: 0 9 * * * (9 AM daily)"""
    try:
        trigger_random_events()
        return jsonify({'success': True, 'message': 'Random events triggered'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cron_bp.route('/inactive-users-monitor/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_inactive_users_monitor():
    """Inactive users monitor — Schedule: 0 10 * * * (10 AM daily)"""
    try:
        result = run_inactive_users_monitor()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Hourly Jobs ─────────────────────────────────────────────────

@cron_bp.route('/market-monitor/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_market_monitor():
    """Market fluctuation simulation — Schedule: 0 * * * * (every hour)"""
    try:
        simulate_market_fluctuation()
        return jsonify({'success': True, 'message': 'Market monitor executed'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Monthly Jobs ────────────────────────────────────────────────

@cron_bp.route('/depreciation/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_depreciation():
    """Monthly liability depreciation — Schedule: 0 2 1 * * (1st, 2 AM)"""
    try:
        result = run_monthly_depreciation()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cron_bp.route('/appreciation/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_appreciation():
    """Monthly asset appreciation — Schedule: 0 3 1 * * (1st, 3 AM)"""
    try:
        result = run_monthly_appreciation()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cron_bp.route('/loan-deductions/', methods=['POST'], strict_slashes=False)
@require_cron_secret
def cron_loan_deductions():
    """Monthly loan deductions — Schedule: 0 4 15 * * (15th, 4 AM)"""
    try:
        process_monthly_deductions()
        return jsonify({'success': True, 'message': 'Loan deductions processed'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
