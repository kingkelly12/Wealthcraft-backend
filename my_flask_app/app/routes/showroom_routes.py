"""
The Showroom feed's server side (see app/game/showroom.py).

GET    /api/showroom/                          wishlist, deals, "since you passed on it", friends' buys
POST   /api/showroom/seen/                     {"items": [{"kind", "item_id"}, ...]}  first time scrolled past
POST   /api/showroom/wishlist/                 {"kind", "item_id"}
DELETE /api/showroom/wishlist/<kind>/<item_id>/
POST   /api/showroom/deals/redeem/             {"kind", "item_id"}  after buying a deal item: the discount back
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import showroom
from app.game.showroom import ShowroomError
from app.utils.jwt_helper import require_auth

showroom_bp = Blueprint('showroom', __name__)
logger = logging.getLogger(__name__)


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except ShowroomError as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message}), e.status
    except Exception as e:
        logger.exception('Showroom request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


def _key(body):
    kind, item_id = body.get('kind'), body.get('item_id')
    if not kind or not item_id:
        raise ShowroomError('VALIDATION_ERROR', 'Send kind and item_id.')
    return str(kind), str(item_id)


@showroom_bp.route('/', methods=['GET'])
@require_auth
def state(current_user_id: str):
    return _run(showroom.state, current_user_id)


@showroom_bp.route('/seen/', methods=['POST'])
@require_auth
def seen(current_user_id: str):
    items = (request.get_json(silent=True) or {}).get('items') or []
    if not isinstance(items, list):
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'items must be a list.'}), 400
    return _run(lambda: {'recorded': showroom.mark_seen(current_user_id, items[:100])})


@showroom_bp.route('/wishlist/', methods=['POST'])
@require_auth
def wishlist_add(current_user_id: str):
    body = request.get_json(silent=True) or {}
    return _run(lambda: showroom.wishlist_add(current_user_id, *_key(body)))


@showroom_bp.route('/wishlist/<kind>/<item_id>/', methods=['DELETE'])
@require_auth
def wishlist_remove(current_user_id: str, kind: str, item_id: str):
    return _run(showroom.wishlist_remove, current_user_id, kind, item_id)


@showroom_bp.route('/deals/redeem/', methods=['POST'])
@require_auth
def redeem(current_user_id: str):
    body = request.get_json(silent=True) or {}
    return _run(lambda: showroom.redeem(current_user_id, *_key(body)))
