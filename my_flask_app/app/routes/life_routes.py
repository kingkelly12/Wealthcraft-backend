"""
Lives: character, age, backgrounds, endings (see app/game/life.py).

GET   /api/life/           current life, backgrounds, past lives
POST  /api/life/begin/     {"background": key | "original", "avatar": {...}}
POST  /api/life/end/       end the current life -> summary with an ending
PUT   /api/life/avatar/    {"avatar": {...}}
GET   /api/life/avatars/?ids=a,b,c   other players' avatars (max 200)
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import life
from app.game.life import LifeError
from app.utils.jwt_helper import require_auth

life_bp = Blueprint('life', __name__)
logger = logging.getLogger(__name__)


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except LifeError as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message}), e.status
    except Exception as e:
        logger.exception('Life request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@life_bp.route('/', methods=['GET'])
@require_auth
def get_life(current_user_id: str):
    return _run(life.state, current_user_id)


@life_bp.route('/begin/', methods=['POST'])
@require_auth
def begin(current_user_id: str):
    body = request.get_json(silent=True) or {}
    return _run(life.begin_life, current_user_id, body.get('background'), body.get('avatar'))


@life_bp.route('/end/', methods=['POST'])
@require_auth
def end(current_user_id: str):
    return _run(life.end_life, current_user_id)


@life_bp.route('/avatar/', methods=['PUT'])
@require_auth
def avatar(current_user_id: str):
    return _run(life.update_avatar, current_user_id, (request.get_json(silent=True) or {}).get('avatar'))


@life_bp.route('/avatars/', methods=['GET'])
@require_auth
def avatars(current_user_id: str):
    ids = [i for i in (request.args.get('ids') or '').split(',') if i][:200]
    return _run(life.avatars_for, ids)


@life_bp.route('/legacy/', methods=['GET'])
@require_auth
def legacy_view(current_user_id: str):
    """The Hall of Lives: achievements, endings collected, unlocks and past lives."""
    from app.game import legacy
    return _run(legacy.view, current_user_id)
