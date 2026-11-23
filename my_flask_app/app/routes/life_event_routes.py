"""
Life event management routes
Handles life event choices with JWT authentication
"""
from flask import Blueprint, request, jsonify
from app.utils.jwt_helper import require_auth
from app.services.balance_service import BalanceService
from app import supabase
from app.services.push_notification_service import ExpoPushService
from app.utils.db import fetch_one
from app.game.life_events import AlreadyResolved, choice_effects, resolve
import logging

logger = logging.getLogger(__name__)

life_event_bp = Blueprint('life_event', __name__)


@life_event_bp.route('/make-choice/', methods=['POST'])
@require_auth
def make_life_event_choice(current_user_id: str):
    """
    Resolve a life event the player was dealt (calendar-time path; players on
    game time resolve events as cards in their weekly deck, with the same rules
    from app.game.life_events).
    """
    try:
        data = request.get_json(silent=True) or {}
        choice_id = data.get('choice_id')
        event_id = data.get('event_id')
        if not choice_id or not event_id:
            return jsonify({'success': False, 'error': 'VALIDATION_ERROR', 'message': 'event_id and choice_id are required'}), 400

        event_res = fetch_one(supabase.table('life_events').select('*').eq('id', str(event_id)))
        if not event_res.data:
            return jsonify({'success': False, 'error': 'EVENT_NOT_FOUND', 'message': f'Life event {event_id} not found'}), 404
        event = event_res.data

        # The choice must belong to this event (any choice from any event used
        # to be accepted, e.g. the most lucrative one).
        choices = supabase.table('life_event_choices').select('*').eq('life_event_id', str(event_id)).execute().data or []
        choice = next((c for c in choices if str(c['id']) == str(choice_id)), None)
        if not choice:
            return jsonify({'success': False, 'error': 'CHOICE_NOT_FOUND', 'message': 'That choice does not belong to this event'}), 404

        # The player's oldest unanswered copy of this event. (The old update
        # touched every pending row for the event at once.)
        pending = fetch_one(supabase.table('user_life_events').select('id')
                            .eq('user_id', current_user_id).eq('life_event_id', str(event_id))
                            .is_('choice_id', 'null').order('created_at'))
        if not pending.data:
            return jsonify({'success': False, 'error': 'ALREADY_RESOLVED',
                            'message': 'You have already made a choice for this event (or it is not assigned to you).'}), 400
        row_id = pending.data['id']

        try:
            fx = resolve(supabase, current_user_id, row_id, event, choice, choices)
        except LookupError:
            # Checked BEFORE claiming: previously the choice was recorded first,
            # the charge then failed, and the player kept the event "resolved"
            # without paying (free way out of any expensive event).
            cost = -choice_effects(choice)['cash']
            return jsonify({'success': False, 'error': 'INSUFFICIENT_FUNDS',
                            'message': f"You can't afford that (${cost:,.0f}). Pick the other option."}), 400
        except AlreadyResolved:
            return jsonify({'success': False, 'error': 'ALREADY_RESOLVED',
                            'message': 'You have already made a choice for this event.'}), 400
        cash, income, before, new_sanity, game_over = (
            fx['cash'], fx['income'], fx['sanity_before'], fx['new_sanity'], fx['game_over'])

        outcome_message = choice.get('outcome_description') or 'Choice made'
        if income:
            outcome_message = f"{outcome_message} (Permanent income change: {'+' if income > 0 else ''}${income:,.0f}/mo)"

        if cash or income:
            ExpoPushService.notify_followers_of_financial_move(
                supabase_client=supabase,
                user_id=current_user_id,
                move_type='life_event',
                item_name=choice.get('choice_label', 'Choice'),
                amount=float(abs(cash)) if cash else float(income),
            )

        return jsonify({
            'success': True,
            'message': 'Choice processed successfully',
            'outcome': outcome_message,
            'balance_change': float(cash),
            'new_balance': float(BalanceService.get_current_balance(current_user_id)),
            'sanity_change': new_sanity - before,   # what actually changed (clamped at 0/100)
            'new_sanity': new_sanity,
            'income_change': float(income),
            'burnout_triggered': game_over,
            'game_over': game_over,
        }), 200

    except Exception as e:
        logger.exception('make_life_event_choice failed')
        if 'Insufficient funds' in str(e):
            return jsonify({'success': False, 'error': 'INSUFFICIENT_FUNDS', 'message': "You can't afford that right now."}), 400
        return jsonify({'success': False, 'error': 'OPERATION_FAILED', 'message': str(e)}), 500


@life_event_bp.route('/<event_id>/', methods=['GET'])
@require_auth
def get_life_event_details(current_user_id: str, event_id: str):
    """
    Get details of a specific life event and its choices
    """
    try:
        # 1. Get life event details
        event_response = fetch_one(supabase.table('life_events').select('*').eq('id', event_id))
        
        if not event_response.data:
            return jsonify({
                'success': False,
                'error': 'EVENT_NOT_FOUND',
                'message': f'Life event {event_id} not found'
            }), 404
        
        event = event_response.data
        
        # 2. Get choices for this event
        choices_response = supabase.table('life_event_choices').select('*').eq('life_event_id', event_id).order('choice_order', desc=False).execute()
        choices = choices_response.data or []
        
        # 3. Check if user already made a choice
        rows = supabase.table('user_life_events').select('choice_id, created_at, was_auto_selected') \
            .eq('user_id', current_user_id).eq('life_event_id', event_id) \
            .order('created_at', desc=True).execute().data or []
        # An event can be dealt more than once: an unanswered copy wins over an
        # older answered one (rows came back unordered, so a repeat could show
        # as "already completed" and never be answerable).
        pending = any(r.get('choice_id') is None for r in rows)
        answered = next((r for r in rows if r.get('choice_id') is not None), None)

        return jsonify({
            'success': True,
            'data': {
                'event': event,
                'choices': choices,
                'user_choice': None if pending else (answered or {}).get('choice_id'),
                'is_completed': bool(answered) and not pending,
                'is_assigned': bool(rows),
                # True when the player ignored it past its time limit and the
                # daily job chose the "do nothing" option for them.
                'was_auto_selected': bool((answered or {}).get('was_auto_selected')) and not pending,
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
