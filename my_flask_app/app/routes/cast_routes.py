"""
Texts from the cast and roommate co-op (see app/game/cast.py, roommates.py).

GET  /api/texts/                              threads (cast) + unread count
GET  /api/texts/<character>/                  one thread (marks it read)
POST /api/texts/messages/<id>/reply/          {"reply_id": "a"|"b"}

GET  /api/roommates/                          your arrangement and invites
POST /api/roommates/invite/                   {"user_id": ...}
POST /api/roommates/<id>/accept/
POST /api/roommates/<id>/decline/
POST /api/roommates/leave/
"""
import logging

from flask import Blueprint, jsonify, request

from app.game import cast, roommates
from app.game.cast import CastError
from app.game.roommates import RoommateError
from app.utils.jwt_helper import require_auth

texts_bp = Blueprint('texts', __name__)
roommates_bp = Blueprint('roommates', __name__)
logger = logging.getLogger(__name__)


def _run(fn, *args):
    try:
        return jsonify({'success': True, 'data': fn(*args)}), 200
    except (CastError, RoommateError) as e:
        return jsonify({'success': False, 'error': e.code, 'message': e.message}), e.status
    except Exception as e:
        logger.exception('Request failed')
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@texts_bp.route('/', methods=['GET'])
@require_auth
def list_threads(current_user_id: str):
    return _run(lambda uid: {'threads': cast.threads(uid), 'unread': cast.unread_count(uid)}, current_user_id)


@texts_bp.route('/<character>/', methods=['GET'])
@require_auth
def get_thread(current_user_id: str, character: str):
    return _run(cast.thread, current_user_id, character)


@texts_bp.route('/messages/<message_id>/reply/', methods=['POST'])
@require_auth
def reply(current_user_id: str, message_id: str):
    return _run(cast.reply, current_user_id, message_id, (request.get_json(silent=True) or {}).get('reply_id'))


@roommates_bp.route('/', methods=['GET'])
@require_auth
def get_roommates(current_user_id: str):
    return _run(roommates.state, current_user_id)


@roommates_bp.route('/invite/', methods=['POST'])
@require_auth
def invite(current_user_id: str):
    def go(uid, target):
        roommates.invite(uid, target)
        return roommates.state(uid)
    return _run(go, current_user_id, (request.get_json(silent=True) or {}).get('user_id'))


@roommates_bp.route('/<arr_id>/accept/', methods=['POST'])
@require_auth
def accept(current_user_id: str, arr_id: str):
    return _run(roommates.accept, current_user_id, arr_id)


@roommates_bp.route('/<arr_id>/decline/', methods=['POST'])
@require_auth
def decline(current_user_id: str, arr_id: str):
    return _run(roommates.decline, current_user_id, arr_id)


@roommates_bp.route('/leave/', methods=['POST'])
@require_auth
def leave(current_user_id: str):
    return _run(roommates.leave, current_user_id)
