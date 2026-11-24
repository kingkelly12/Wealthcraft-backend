"""
Owning your home (see app/game/homes.py).

GET  /api/homes/                     homes for sale, homes you own, where you live
POST /api/homes/buy/                 {"home_id", "move_in": true, "finance": false}  (finance: 20% down, mortgage for the rest)
POST /api/homes/<id>/move-in/        live in a home you own (your lease ends: no more rent)
POST /api/homes/<id>/move-out/       stop living there (it gets let out)
POST /api/homes/<id>/sell/           sell it (5% fees)
"""
import logging

from flask import Blueprint, jsonify, request

from app import supabase
from app.game import homes
from app.game.homes import HomeError
from app.services.push_notification_service import ExpoPushService
from app.utils.jwt_helper import require_auth
from app.utils.mission_constraints import enforce_mission_constraints

homes_bp = Blueprint('homes', __name__)
logger = logging.getLogger(__name__)


def _tell_followers(uid, move_type, data, amount_key, profit_key=None):
    """A home is the biggest move in the game: put it on the player's timeline and tell their followers."""
    try:
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase, user_id=uid, move_type=move_type, item_name=data.get('name') or 'a home',
            amount=float(data[amount_key]) if data.get(amount_key) is not None else None,
            profit=float(data[profit_key]) if profit_key and data.get(profit_key) is not None else None)
    except Exception as e:
        logger.warning(f'Follower alert failed for {uid} ({move_type}): {e}')


def _run_and_tell(uid, move_type, amount_key, profit_key, fn, *args):
    res, status = _run(fn, *args)
    if status == 200:
        _tell_followers(uid, move_type, res.get_json()['data'], amount_key, profit_key)
    return res, status


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except HomeError as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message, 'data': e.data}), e.status
    except Exception as e:
        logger.exception('Home request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@homes_bp.route('/', methods=['GET'])
@require_auth
def overview(current_user_id: str):
    return _run(homes.overview, current_user_id)


@homes_bp.route('/buy/', methods=['POST'])
@require_auth
def buy(current_user_id: str):
    body = request.get_json(silent=True) or {}
    if not body.get('home_id'):
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Pick a home.'}), 400
    blocked = enforce_mission_constraints(current_user_id, 'buy_asset', {'category': 'real_estate', 'asset_type': 'property'})
    if blocked:
        return blocked
    finance = body.get('finance') is True
    if finance:
        blocked = enforce_mission_constraints(current_user_id, 'take_loan', {'loan_type': 'mortgage'})
        if blocked:
            return blocked
    return _run_and_tell(current_user_id, 'buy_home', 'purchase_price', None,
                         homes.buy, current_user_id, body['home_id'], body.get('move_in', True) is not False, finance)


@homes_bp.route('/<home_id>/move-in/', methods=['POST'])
@require_auth
def move_in(current_user_id: str, home_id: str):
    return _run(lambda: (homes.move_into(current_user_id, home_id), homes.overview(current_user_id))[1])


@homes_bp.route('/<home_id>/move-out/', methods=['POST'])
@require_auth
def move_out(current_user_id: str, home_id: str):
    return _run(lambda: (homes.move_out(current_user_id, home_id), homes.overview(current_user_id))[1])


@homes_bp.route('/<home_id>/sell/', methods=['POST'])
@require_auth
def sell(current_user_id: str, home_id: str):
    blocked = enforce_mission_constraints(current_user_id, 'sell_asset')
    if blocked:
        return blocked
    return _run_and_tell(current_user_id, 'sell_home', 'proceeds', 'gain', homes.sell, current_user_id, home_id)
