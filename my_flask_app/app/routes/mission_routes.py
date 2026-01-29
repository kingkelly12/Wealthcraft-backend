from flask import Blueprint, request, jsonify
from app.utils.jwt_helper import require_auth
from app import supabase
from decimal import Decimal
import os
import uuid
from datetime import datetime
from app.services.push_notification_service import ExpoPushService

mission_bp = Blueprint('mission', __name__)


@mission_bp.route('/available', methods=['GET'])
@require_auth
def get_available_missions(current_user_id: str):
    """
    Get all missions available to the current user.
    
    This endpoint:
    1. Fetches all missions from the database
    2. Checks prerequisites (net worth, completed missions, etc.)
    3. Returns filtered list of missions the player can start
    """
    try:
        # Get user profile to check prerequisites
        profile_response = supabase.table('profiles').select(
            'net_worth, monthly_income, credit_score'
        ).eq('user_id', current_user_id).single().execute()
        
        if not profile_response.data:
            return jsonify({
                'success': False,
                'error': 'PROFILE_NOT_FOUND',
                'message': 'User profile not found'
            }), 404
        
        profile = profile_response.data
        
        # Get all missions with their decision points and success criteria
        missions_response = supabase.table('integrated_missions').select(
            '*, mission_decision_points(*), mission_success_criteria(*)'
        ).execute()
        
        if not missions_response.data:
            return jsonify({
                'success': True,
                'data': []
            }), 200
        
        # Get completed missions for this user
        completed_response = supabase.table('mission_completion_results').select(
            'mission_id'
        ).eq('player_id', current_user_id).eq('completed', True).execute()
        
        completed_mission_ids = [m['mission_id'] for m in (completed_response.data or [])]
        
        # Get active mission (if any)
        active_response = supabase.table('player_mission_progress').select(
            'mission_id'
        ).eq('player_id', current_user_id).eq('is_active', True).execute()
        
        has_active_mission = bool(active_response.data)
        
        # Filter missions based on prerequisites
        available_missions = []
        for mission in missions_response.data:
            # Skip if already completed
            if mission['id'] in completed_mission_ids:
                continue
            
            # Skip if user already has an active mission
            if has_active_mission:
                continue
            
            # Check prerequisites (simplified - you can expand this)
            # For now, we'll allow all missions
            can_start = True
            prerequisite_reasons = []
            
            # Format constraints for response
            constraints = {
                'income_multiplier': float(mission.get('income_multiplier', 1.0)),
                'expense_multiplier': float(mission.get('expense_multiplier', 1.0)),
                'can_change_job': mission.get('can_change_job', True),
                'can_buy_assets': mission.get('can_buy_assets', True),
                'can_take_loans': mission.get('can_take_loans', True),
                'can_rent_property': mission.get('can_rent_property', True),
                'can_sell_assets': mission.get('can_sell_assets', True),
                'can_buy_lifestyle_items': mission.get('can_buy_lifestyle_items', True),
                'allowed_asset_types': mission.get('allowed_asset_types'),
                'max_loan_amount': float(mission.get('max_loan_amount')) if mission.get('max_loan_amount') else None,
                'allowed_loan_types': mission.get('allowed_loan_types'),
                'max_monthly_spending': float(mission.get('max_monthly_spending')) if mission.get('max_monthly_spending') else None,
            }
            
            available_missions.append({
                'id': mission['id'],
                'name': mission['name'],
                'description': mission['description'],
                'short_description': mission.get('short_description'),
                'icon': mission.get('icon', '🎯'),
                'category': mission['category'],
                'difficulty': mission['difficulty'],
                'duration_months': mission['duration_months'],
                'learning_objectives': mission.get('learning_objectives', []),
                'affects_main_game': mission.get('affects_main_game', True),
                'constraints': constraints,
                'decision_points': mission.get('mission_decision_points', []),
                'success_criteria': mission.get('mission_success_criteria', []),
                'can_start': can_start,
                'prerequisite_reasons': prerequisite_reasons
            })
        
        return jsonify({
            'success': True,
            'data': available_missions,
            'has_active_mission': has_active_mission
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/start', methods=['POST'])
@require_auth
def start_mission(current_user_id: str):
    """
    Start a mission for the current user.
    
    This endpoint:
    1. Validates the mission exists
    2. Checks if user already has an active mission
    3. Calls the database function to start the mission
    4. Returns the player mission progress
    """
    try:
        data = request.json
        mission_id = data.get('mission_id')
        
        if not mission_id:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'mission_id is required'
            }), 400
        
        # Check if mission exists
        mission_response = supabase.table('integrated_missions').select(
            '*'
        ).eq('id', mission_id).single().execute()
        
        if not mission_response.data:
            return jsonify({
                'success': False,
                'error': 'MISSION_NOT_FOUND',
                'message': 'Mission not found'
            }), 404
        
        mission = mission_response.data
        
        # Check if user already has an active mission
        active_response = supabase.table('player_mission_progress').select(
            '*'
        ).eq('player_id', current_user_id).eq('is_active', True).execute()
        
        if active_response.data:
            return jsonify({
                'success': False,
                'error': 'ACTIVE_MISSION_EXISTS',
                'message': 'You already have an active mission. Complete or abandon it first.'
            }), 400
        
        # Call the database function to start the mission
        try:
            result = supabase.rpc('start_integrated_mission', {
                'p_player_id': current_user_id,
                'p_mission_id': mission_id
            }).execute()
            
            player_mission_id = result.data
            
        except Exception as db_error:
            # If the function doesn't exist or fails, create manually
            # Get user profile for snapshot
            profile_response = supabase.table('profiles').select(
                'net_worth, monthly_income, credit_score'
            ).eq('user_id', current_user_id).single().execute()
            
            profile = profile_response.data
            
            # Create mission progress
            progress_response = supabase.table('player_mission_progress').insert({
                'player_id': current_user_id,
                'mission_id': mission_id,
                'is_active': True,
                'current_month': 1,
                'constraints_applied': {
                    'income_multiplier': mission.get('income_multiplier', 1.0),
                    'expense_multiplier': mission.get('expense_multiplier', 1.0),
                    'can_change_job': mission.get('can_change_job', True),
                    'can_buy_assets': mission.get('can_buy_assets', True),
                    'can_take_loans': mission.get('can_take_loans', True),
                    'can_rent_property': mission.get('can_rent_property', True),
                    'can_sell_assets': mission.get('can_sell_assets', True),
                    'can_buy_lifestyle_items': mission.get('can_buy_lifestyle_items', True),
                    'allowed_asset_types': mission.get('allowed_asset_types'),
                    'max_loan_amount': float(mission.get('max_loan_amount')) if mission.get('max_loan_amount') else None,
                    'allowed_loan_types': mission.get('allowed_loan_types'),
                    'max_monthly_spending': float(mission.get('max_monthly_spending')) if mission.get('max_monthly_spending') else None,
                },
                'game_state_snapshot': {
                    'net_worth': float(profile.get('net_worth', 0)),
                    'monthly_income': float(profile.get('monthly_income', 0)),
                    'credit_score': profile.get('credit_score', 650),
                    'started_at': datetime.utcnow().isoformat()
                }
            }).execute()
            
            player_mission_id = progress_response.data[0]['id'] if progress_response.data else None
            
            # Initialize success criteria tracking
            criteria_response = supabase.table('mission_success_criteria').select(
                '*'
            ).eq('mission_id', mission_id).execute()
            
            if criteria_response.data:
                for criteria in criteria_response.data:
                    # Calculate initial value based on metric
                    initial_value = 0
                    if criteria['metric'] == 'net_worth':
                        initial_value = float(profile.get('net_worth', 0))
                    elif criteria['metric'] == 'monthly_income':
                        initial_value = float(profile.get('monthly_income', 0))
                    elif criteria['metric'] == 'credit_score':
                        initial_value = profile.get('credit_score', 650)
                    
                    supabase.table('player_mission_success_tracking').insert({
                        'player_mission_id': player_mission_id,
                        'criteria_id': criteria['id'],
                        'current_value': initial_value,
                        'is_met': False
                    }).execute()
        
        # Get the created progress
        progress_response = supabase.table('player_mission_progress').select(
            '*, integrated_missions(*)'
        ).eq('id', player_mission_id).single().execute()
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'mission',
            'title': '🎯 Mission Started',
            'message': f'You started the mission: {mission["name"]}',
            'read': False
        }).execute()
        
        # Send push notification
        try:
            ExpoPushService.send_notification_to_user(
                supabase_client=supabase,
                user_id=current_user_id,
                title='🎯 Mission Started',
                body=f'You started: {mission["name"]}',
                notification_type='mission',
                data={
                    'mission_id': mission_id,
                    'player_mission_id': player_mission_id
                }
            )
        except Exception as e:
            print(f"Failed to send push notification: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Mission "{mission["name"]}" started successfully',
            'data': progress_response.data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/active', methods=['GET'])
@require_auth
def get_active_mission(current_user_id: str):
    """
    Get the current active mission for the user.
    
    Returns the mission progress, constraints, and current status.
    """
    try:
        # Get active mission with full details
        progress_response = supabase.table('player_mission_progress').select(
            '*, integrated_missions(*)'
        ).eq('player_id', current_user_id).eq('is_active', True).execute()
        
        if not progress_response.data:
            return jsonify({
                'success': True,
                'data': None,
                'message': 'No active mission'
            }), 200
        
        progress = progress_response.data[0]
        mission_id = progress['mission_id']
        
        # Get success criteria tracking
        tracking_response = supabase.table('player_mission_success_tracking').select(
            '*, mission_success_criteria(*)'
        ).eq('player_mission_id', progress['id']).execute()
        
        # Get decision points for this mission
        decisions_response = supabase.table('mission_decision_points').select(
            '*, mission_decision_options(*)'
        ).eq('mission_id', mission_id).execute()
        
        # Get player's decisions
        player_decisions_response = supabase.table('player_mission_decisions').select(
            '*'
        ).eq('player_mission_id', progress['id']).execute()
        
        player_decision_ids = [d['decision_point_id'] for d in (player_decisions_response.data or [])]
        
        # Find next decision point
        next_decision = None
        for decision in (decisions_response.data or []):
            if decision['month'] == progress['current_month'] and decision['id'] not in player_decision_ids:
                next_decision = decision
                break
        
        return jsonify({
            'success': True,
            'data': {
                'progress': progress,
                'success_criteria_tracking': tracking_response.data or [],
                'next_decision': next_decision,
                'decisions_made': player_decisions_response.data or []
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/decision', methods=['POST'])
@require_auth
def make_decision(current_user_id: str):
    """
    Make a decision in the current mission.
    
    This endpoint:
    1. Validates the decision point and option
    2. Records the decision
    3. Applies financial impacts
    4. Updates game state
    """
    try:
        data = request.json
        decision_point_id = data.get('decision_point_id')
        option_id = data.get('option_id')
        
        if not decision_point_id or not option_id:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'decision_point_id and option_id are required'
            }), 400
        
        # Get active mission
        progress_response = supabase.table('player_mission_progress').select(
            '*'
        ).eq('player_id', current_user_id).eq('is_active', True).single().execute()
        
        if not progress_response.data:
            return jsonify({
                'success': False,
                'error': 'NO_ACTIVE_MISSION',
                'message': 'No active mission found'
            }), 404
        
        progress = progress_response.data
        
        # Validate decision point belongs to this mission
        decision_response = supabase.table('mission_decision_points').select(
            '*'
        ).eq('id', decision_point_id).eq('mission_id', progress['mission_id']).single().execute()
        
        if not decision_response.data:
            return jsonify({
                'success': False,
                'error': 'INVALID_DECISION',
                'message': 'Decision point not found or does not belong to this mission'
            }), 404
        
        # Get the option
        option_response = supabase.table('mission_decision_options').select(
            '*'
        ).eq('id', option_id).eq('decision_point_id', decision_point_id).single().execute()
        
        if not option_response.data:
            return jsonify({
                'success': False,
                'error': 'INVALID_OPTION',
                'message': 'Option not found or does not belong to this decision point'
            }), 404
        
        option = option_response.data
        
        # Record the decision
        supabase.table('player_mission_decisions').insert({
            'player_mission_id': progress['id'],
            'decision_point_id': decision_point_id,
            'chosen_option_id': option_id,
            'month_made': progress['current_month'],
            'decision_data': {}
        }).execute()
        
        # Apply financial impacts
        immediate_cash = float(option.get('immediate_cash', 0))
        
        if immediate_cash != 0:
            from app.services.balance_service import BalanceService
            if immediate_cash > 0:
                BalanceService.add_balance(
                    user_id=current_user_id,
                    amount=Decimal(str(immediate_cash)),
                    reason=f'Mission decision: {option.get("label", "Decision reward")}'
                )
            else:
                BalanceService.subtract_balance(
                    user_id=current_user_id,
                    amount=Decimal(str(abs(immediate_cash))),
                    reason=f'Mission decision: {option.get("label", "Decision cost")}'
                )
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'mission',
            'title': '📖 Decision Made',
            'message': f'You chose: {option.get("label", "Option")}',
            'read': False
        }).execute()
        
        return jsonify({
            'success': True,
            'message': 'Decision recorded successfully',
            'data': {
                'option': option,
                'immediate_cash': immediate_cash
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/abandon', methods=['POST'])
@require_auth
def abandon_mission(current_user_id: str):
    """
    Abandon the current active mission.
    
    This endpoint:
    1. Finds the active mission
    2. Marks it as abandoned
    3. Removes constraints
    """
    try:
        # Get active mission
        progress_response = supabase.table('player_mission_progress').select(
            '*, integrated_missions(*)'
        ).eq('player_id', current_user_id).eq('is_active', True).single().execute()
        
        if not progress_response.data:
            return jsonify({
                'success': False,
                'error': 'NO_ACTIVE_MISSION',
                'message': 'No active mission to abandon'
            }), 404
        
        progress = progress_response.data
        mission_name = progress['integrated_missions']['name']
        
        # Update mission progress
        supabase.table('player_mission_progress').update({
            'is_active': False,
            'abandoned_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', progress['id']).execute()
        
        # Create notification
        supabase.table('notifications').insert({
            'user_id': current_user_id,
            'type': 'mission',
            'title': '❌ Mission Abandoned',
            'message': f'You abandoned the mission: {mission_name}',
            'read': False
        }).execute()
        
        return jsonify({
            'success': True,
            'message': f'Mission "{mission_name}" abandoned'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/history', methods=['GET'])
@require_auth
def get_mission_history(current_user_id: str):
    """
    Get the user's mission completion history.
    
    Returns all completed, failed, and abandoned missions.
    """
    try:
        # Get completion results
        results_response = supabase.table('mission_completion_results').select(
            '*, integrated_missions(*)'
        ).eq('player_id', current_user_id).order('completed_at', desc=True).execute()
        
        # Also get abandoned missions
        abandoned_response = supabase.table('player_mission_progress').select(
            '*, integrated_missions(*)'
        ).eq('player_id', current_user_id).not_.is_('abandoned_at', 'null').execute()
        
        return jsonify({
            'success': True,
            'data': {
                'completed': results_response.data or [],
                'abandoned': abandoned_response.data or []
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/check-constraints', methods=['POST'])
@require_auth
def check_constraints(current_user_id: str):
    """
    Check if an action is allowed under current mission constraints.
    
    This is a helper endpoint for the mobile app to validate actions
    before attempting them.
    """
    try:
        data = request.json
        action = data.get('action')  # e.g., 'buy_asset', 'take_loan', 'change_job'
        action_data = data.get('data', {})
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'VALIDATION_ERROR',
                'message': 'action is required'
            }), 400
        
        # Get active mission
        progress_response = supabase.table('player_mission_progress').select(
            'constraints_applied'
        ).eq('player_id', current_user_id).eq('is_active', True).execute()
        
        if not progress_response.data:
            # No active mission, all actions allowed
            return jsonify({
                'success': True,
                'allowed': True,
                'reason': None
            }), 200
        
        constraints = progress_response.data[0]['constraints_applied']
        
        # Check constraints based on action
        allowed = True
        reason = None
        
        if action == 'buy_asset':
            if not constraints.get('can_buy_assets', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot buy assets during this mission'
            elif constraints.get('allowed_asset_types'):
                asset_type = action_data.get('asset_type')
                if asset_type and asset_type not in constraints['allowed_asset_types']:
                    allowed = False
                    reason = f'🎯 Mission constraint: You can only buy {", ".join(constraints["allowed_asset_types"])} during this mission'
        
        elif action == 'take_loan':
            if not constraints.get('can_take_loans', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot take loans during this mission'
            elif constraints.get('max_loan_amount'):
                amount = action_data.get('amount', 0)
                if amount > constraints['max_loan_amount']:
                    allowed = False
                    reason = f'🎯 Mission constraint: Maximum loan amount is ${constraints["max_loan_amount"]:,.2f}'
        
        elif action == 'change_job':
            if not constraints.get('can_change_job', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot change jobs during this mission'
        
        elif action == 'rent_property':
            if not constraints.get('can_rent_property', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot change rental properties during this mission'
        
        elif action == 'sell_asset':
            if not constraints.get('can_sell_assets', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot sell assets during this mission'
        
        elif action == 'buy_lifestyle_item':
            if not constraints.get('can_buy_lifestyle_items', True):
                allowed = False
                reason = '🎯 Mission constraint: You cannot buy lifestyle items during this mission'
        
        return jsonify({
            'success': True,
            'allowed': allowed,
            'reason': reason,
            'constraints': constraints
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


# ============================================
# STORY EVENT ENDPOINTS
# ============================================

@mission_bp.route('/<mission_id>/story-events', methods=['GET'])
@require_auth
def get_mission_story_events(current_user_id: str, mission_id: str):
    """
    Get all story events for a specific mission.
    
    Returns story events ordered by display_order.
    """
    try:
        # Validate mission exists
        mission_response = supabase.table('integrated_missions').select(
            'id, name'
        ).eq('id', mission_id).single().execute()
        
        if not mission_response.data:
            return jsonify({
                'success': False,
                'error': 'MISSION_NOT_FOUND',
                'message': 'Mission not found'
            }), 404
        
        # Get all story events for this mission
        events_response = supabase.table('mission_story_events').select(
            '*'
        ).eq('mission_id', mission_id).eq('is_active', True).order('display_order').execute()
        
        return jsonify({
            'success': True,
            'data': events_response.data or []
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/active/pending-story-events', methods=['GET'])
@require_auth
def get_pending_story_events(current_user_id: str):
    """
    Get unviewed story events for the active mission.
    
    Returns events that should be shown based on:
    - Current mission month
    - Events not yet viewed
    - Trigger conditions met
    """
    try:
        # Get active mission
        progress_response = supabase.table('player_mission_progress').select(
            'id, mission_id, current_month, integrated_missions(name, duration_months)'
        ).eq('player_id', current_user_id).eq('is_active', True).single().execute()
        
        if not progress_response.data:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No active mission'
            }), 200
        
        progress = progress_response.data
        player_mission_id = progress['id']
        mission_id = progress['mission_id']
        current_month = progress['current_month']
        
        # Get all story events for this mission
        all_events_response = supabase.table('mission_story_events').select(
            '*'
        ).eq('mission_id', mission_id).eq('is_active', True).order('display_order').execute()
        
        if not all_events_response.data:
            return jsonify({
                'success': True,
                'data': []
            }), 200
        
        # Get already viewed events (check has_been_viewed flag)
        viewed_response = supabase.table('player_story_progress').select(
            'story_event_id'
        ).eq('player_mission_id', player_mission_id).eq('has_been_viewed', True).execute()
        
        viewed_event_ids = [v['story_event_id'] for v in (viewed_response.data or [])]
        
        # Filter events that should be shown
        pending_events = []
        for event in all_events_response.data:
            # Skip if already viewed
            if event['id'] in viewed_event_ids:
                continue
            
            # Check trigger conditions
            should_show = False
            
            if event['trigger_type'] == 'mission_start':
                # Show on month 1 only
                should_show = current_month == 1
            
            elif event['trigger_type'] == 'month':
                # Show when current month matches trigger_value
                trigger_month = event.get('trigger_value', 0)
                should_show = current_month >= trigger_month
            
            elif event['trigger_type'] == 'custom':
                # For custom triggers, show if probability check passes
                probability = event.get('probability', 1.0)
                import random
                should_show = random.random() <= probability
            
            else:
                # For other trigger types (threshold, decision), show them
                should_show = True
            
            if should_show:
                # Add mission context
                event['mission_month'] = current_month
                pending_events.append(event)
        
        return jsonify({
            'success': True,
            'data': pending_events,
            'mission_name': progress['integrated_missions']['name'],
            'current_month': current_month,
            'total_months': progress['integrated_missions']['duration_months']
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500


@mission_bp.route('/story-events/<event_id>/acknowledge', methods=['POST'])
@require_auth
def acknowledge_story_event(current_user_id: str, event_id: str):
    """
    Mark a story event as viewed and apply its impacts.
    
    This endpoint:
    1. Records the view in player_story_progress
    2. Applies happiness/stress/motivation changes
    3. Applies immediate cash impact
    """
    try:
        # Get active mission
        progress_response = supabase.table('player_mission_progress').select(
            'id, mission_id, current_month'
        ).eq('player_id', current_user_id).eq('is_active', True).single().execute()
        
        if not progress_response.data:
            return jsonify({
                'success': False,
                'error': 'NO_ACTIVE_MISSION',
                'message': 'No active mission found'
            }), 404
        
        progress = progress_response.data
        player_mission_id = progress['id']
        
        # Get the story event
        event_response = supabase.table('mission_story_events').select(
            '*'
        ).eq('id', event_id).eq('mission_id', progress['mission_id']).single().execute()
        
        if not event_response.data:
            return jsonify({
                'success': False,
                'error': 'EVENT_NOT_FOUND',
                'message': 'Story event not found or does not belong to active mission'
            }), 404
        
        event = event_response.data
        
        # Check if already viewed
        existing_response = supabase.table('player_story_progress').select(
            'id'
        ).eq('player_mission_id', player_mission_id).eq('story_event_id', event_id).execute()
        
        if existing_response.data:
            # Already viewed, just update flags
            supabase.table('player_story_progress').update({
                'has_been_viewed': True,
                'viewed_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', existing_response.data[0]['id']).execute()
        else:
            # Create new progress record
            supabase.table('player_story_progress').insert({
                'player_mission_id': player_mission_id,
                'story_event_id': event_id,
                'has_triggered': True,
                'has_been_viewed': True,
                'triggered_at': datetime.utcnow().isoformat(),
                'viewed_at': datetime.utcnow().isoformat(),
                'mission_month': progress['current_month']
            }).execute()
        
        # Apply impacts
        impacts_applied = {}
        
        # Apply immediate cash
        immediate_cash = float(event.get('immediate_cash', 0))
        if immediate_cash != 0:
            from app.services.balance_service import BalanceService
            if immediate_cash > 0:
                BalanceService.add_balance(
                    user_id=current_user_id,
                    amount=Decimal(str(immediate_cash)),
                    reason=f'Story event: {event.get("title", "Mission story")}'
                )
            else:
                BalanceService.subtract_balance(
                    user_id=current_user_id,
                    amount=Decimal(str(abs(immediate_cash))),
                    reason=f'Story event: {event.get("title", "Mission story")}'
                )
            impacts_applied['cash_change'] = immediate_cash
        
        # Note: Happiness, stress, and motivation changes would be applied
        # to a player_emotions table if it exists. For now, we just return them.
        if event.get('happiness_change'):
            impacts_applied['happiness_change'] = event['happiness_change']
        if event.get('stress_change'):
            impacts_applied['stress_change'] = event['stress_change']
        if event.get('motivation_change'):
            impacts_applied['motivation_change'] = event['motivation_change']
        
        return jsonify({
            'success': True,
            'message': 'Story event acknowledged',
            'data': {
                'event': event,
                'impacts_applied': impacts_applied
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'OPERATION_FAILED',
            'message': str(e)
        }), 500
