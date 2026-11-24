"""
Courses (see app/game/courses.py): industry courses on game time that count as experience and
pay a bonus while you work in that industry.

GET  /api/education/overview/   every course with your status, your experience, your current bonus
POST /api/education/enroll/     {"course_id"}        pay and start (finishes after its game weeks)
POST /api/education/complete/   {"user_course_id"}   finish one whose weeks are up (normally automatic)
"""
import logging

from flask import Blueprint, jsonify, request

from app import supabase
from app.game import courses
from app.game.courses import CourseError
from app.services.push_notification_service import ExpoPushService
from app.utils.jwt_helper import require_auth

education_bp = Blueprint('education', __name__)
logger = logging.getLogger(__name__)


def _error(e: CourseError):
    return jsonify({'success': False, 'error': e.code, 'message': e.message, **({'data': e.data} if e.data else {})}), e.status


def _failed(what):
    logger.exception(f'Course {what} failed')
    return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': f'Could not {what}. Try again.'}), 500


@education_bp.route('/overview/', methods=['GET'])
@require_auth
def overview(current_user_id: str):
    try:
        return jsonify({'success': True, 'data': courses.overview(current_user_id)}), 200
    except Exception:
        return _failed('load courses')


@education_bp.route('/enroll/', methods=['POST'])
@require_auth
def enroll(current_user_id: str):
    course_id = (request.get_json(silent=True) or {}).get('course_id')
    if not course_id:
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Pick a course.'}), 400
    try:
        course = courses.enroll(current_user_id, str(course_id))
    except CourseError as e:
        return _error(e)
    except Exception:
        return _failed('enroll')
    try:
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase, user_id=current_user_id, move_type='enroll_course',
            item_name=course.get('title', 'a course'), amount=float(course.get('cost') or 0))
    except Exception as e:
        logger.warning(f'Follower alert failed for {current_user_id}: {e}')
    return jsonify({'success': True, 'message': f"You started {course['title']}.", 'data': courses.overview(current_user_id)}), 200


@education_bp.route('/complete/', methods=['POST'])
@require_auth
def complete(current_user_id: str):
    user_course_id = (request.get_json(silent=True) or {}).get('user_course_id')
    if not user_course_id:
        return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'Pick a course.'}), 400
    try:
        course = courses.complete(current_user_id, str(user_course_id))
    except CourseError as e:
        return _error(e)
    except Exception:
        return _failed('finish the course')
    try:
        ExpoPushService.notify_followers_of_financial_move(
            supabase_client=supabase, user_id=current_user_id, move_type='complete_course', item_name=course.get('title', 'a course'))
    except Exception as e:
        logger.warning(f'Follower alert failed for {current_user_id}: {e}')
    try:  # the mentor's congratulations
        from app.services.mentor_service import MentorService
        trigger = MentorService.check_real_time_triggers(player_id=current_user_id, action='complete_course',
                                                         action_data={'course_name': course.get('title')})
        if trigger:
            MentorService.send_mentor_message(player_id=current_user_id, mentor_data=trigger, metrics={}, supabase_client=supabase)
    except Exception as e:
        logger.warning(f'Mentor response failed for {current_user_id}: {e}')
    return jsonify({'success': True, 'message': f"You finished {course['title']}.", 'data': courses.overview(current_user_id)}), 200
