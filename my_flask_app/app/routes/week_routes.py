"""
This Week: turn-based play (see app/game/week_service.py).

GET  /api/week/                          clock + this week's deck
POST /api/week/cards/<card_id>/choose/   {"choice_id": "left"|"right"}
POST /api/week/complete/                 end the week (runs the month on payday weeks)
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import week_service
from app.game.week_service import WeekError
from app.utils.jwt_helper import require_auth

week_bp = Blueprint('week', __name__)
logger = logging.getLogger(__name__)


def _error(e: WeekError):
    body = {'success': False, 'error': e.code, 'message': e.message}
    if e.data:
        body['data'] = e.data
    return jsonify(body), e.status


@week_bp.route('/', methods=['GET'])
@require_auth
def get_this_week(current_user_id: str):
    try:
        return jsonify({'success': True, 'data': week_service.state(current_user_id)}), 200
    except WeekError as e:
        return _error(e)
    except Exception as e:
        logger.exception(f"This Week state failed for {current_user_id}")
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@week_bp.route('/cards/<card_id>/choose/', methods=['POST'])
@require_auth
def choose_card(current_user_id: str, card_id: str):
    choice_id = (request.get_json(silent=True) or {}).get('choice_id')
    if choice_id not in ('left', 'right'):
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'choice_id must be "left" or "right"'}), 400
    try:
        return jsonify({'success': True, 'data': week_service.choose(current_user_id, card_id, choice_id)}), 200
    except WeekError as e:
        return _error(e)
    except Exception as e:
        logger.exception(f"Card choice failed for {current_user_id}")
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@week_bp.route('/complete/', methods=['POST'])
@require_auth
def complete_week(current_user_id: str):
    try:
        return jsonify({'success': True, 'data': week_service.complete_week(current_user_id)}), 200
    except WeekError as e:
        return _error(e)
    except Exception as e:
        logger.exception(f"Week completion failed for {current_user_id}")
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500
