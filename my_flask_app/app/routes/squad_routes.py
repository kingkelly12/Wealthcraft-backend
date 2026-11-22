"""
Squads (see app/game/squads.py).

GET    /api/squads/                          your squad (members, goal, race, feed) or null
POST   /api/squads/                          {"name", "emoji"} start a squad
PUT    /api/squads/                          {"name"?, "emoji"?} owner only (PATCH works too)
GET    /api/squads/preview/?code=XXXXXX      name, emoji and size of a squad before joining
POST   /api/squads/join/                     {"code"}
POST   /api/squads/leave/
POST   /api/squads/invite/                   {"user_id"} someone you follow
POST   /api/squads/members/<user_id>/remove/ owner only
POST   /api/squads/feed/<id>/react/          {"emoji"} (same emoji again removes it)
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import squads
from app.game.squads import SquadError
from app.utils.jwt_helper import require_auth

squads_bp = Blueprint('squads', __name__)
logger = logging.getLogger(__name__)


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except SquadError as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message}), e.status
    except Exception as e:
        logger.exception('Squad request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


def _body():
    return request.get_json(silent=True) or {}


@squads_bp.route('/', methods=['GET'])
@require_auth
def get_squad(current_user_id: str):
    return _run(squads.state, current_user_id)


@squads_bp.route('/', methods=['POST'])
@require_auth
def create_squad(current_user_id: str):
    b = _body()
    return _run(squads.create, current_user_id, b.get('name'), b.get('emoji'))


@squads_bp.route('/', methods=['PATCH', 'PUT'])
@require_auth
def update_squad(current_user_id: str):
    b = _body()
    return _run(squads.update, current_user_id, b.get('name'), b.get('emoji'))


@squads_bp.route('/preview/', methods=['GET'])
@require_auth
def preview(current_user_id: str):
    return _run(squads.preview, request.args.get('code'))


@squads_bp.route('/join/', methods=['POST'])
@require_auth
def join(current_user_id: str):
    return _run(squads.join, current_user_id, _body().get('code'))


@squads_bp.route('/leave/', methods=['POST'])
@require_auth
def leave(current_user_id: str):
    return _run(squads.leave, current_user_id)


@squads_bp.route('/invite/', methods=['POST'])
@require_auth
def invite(current_user_id: str):
    return _run(squads.invite, current_user_id, _body().get('user_id'))


@squads_bp.route('/members/<user_id>/remove/', methods=['POST'])
@require_auth
def remove_member(current_user_id: str, user_id: str):
    return _run(squads.remove_member, current_user_id, user_id)


@squads_bp.route('/feed/<feed_id>/react/', methods=['POST'])
@require_auth
def react(current_user_id: str, feed_id: str):
    return _run(squads.react, current_user_id, feed_id, _body().get('emoji'))
