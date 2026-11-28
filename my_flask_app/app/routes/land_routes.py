"""
Land (see app/game/land.py).

GET  /api/land/                  plots for sale, your plots and any open offers
POST /api/land/buy/              {"plot_key"}
POST /api/land/<id>/respond/     {"action"}  answer an offer
POST /api/land/<id>/sell/        sell on the open market (5% fees)
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import land
from app.game.land import LandError
from app.utils.jwt_helper import require_auth
from app.utils.mission_constraints import enforce_mission_constraints

land_bp = Blueprint('land', __name__)
logger = logging.getLogger(__name__)


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except LandError as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message, 'data': e.data}), e.status
    except Exception:
        logger.exception('Land request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': 'Something went wrong. Try again.'}), 500


@land_bp.route('/', methods=['GET'])
@require_auth
def overview(current_user_id: str):
    return _run(land.overview, current_user_id)


@land_bp.route('/buy/', methods=['POST'])
@require_auth
def buy(current_user_id: str):
    key = (request.get_json(silent=True) or {}).get('plot_key')
    if not key:
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Pick a plot.'}), 400
    blocked = enforce_mission_constraints(current_user_id, 'buy_asset', {'category': 'real_estate', 'asset_type': 'property'})
    if blocked:
        return blocked
    return _run(land.buy, current_user_id, key)


@land_bp.route('/<land_id>/respond/', methods=['POST'])
@require_auth
def respond(current_user_id: str, land_id: str):
    action = (request.get_json(silent=True) or {}).get('action')
    if action == 'sell':
        blocked = enforce_mission_constraints(current_user_id, 'sell_asset')
        if blocked:
            return blocked
    return _run(land.respond, current_user_id, land_id, action)


@land_bp.route('/<land_id>/sell/', methods=['POST'])
@require_auth
def sell(current_user_id: str, land_id: str):
    blocked = enforce_mission_constraints(current_user_id, 'sell_asset')
    if blocked:
        return blocked
    return _run(land.sell, current_user_id, land_id)
