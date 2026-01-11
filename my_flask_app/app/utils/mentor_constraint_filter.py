"""
Constraint-aware mentor message filtering
Prevents mentors from advising actions blocked by active missions

This module filters mentor messages based on active mission constraints to ensure
mentors never advise actions that are currently blocked by the player's mission.
"""

def filter_mentor_messages_by_constraints(messages: list, active_mission_constraints: dict) -> list:
    """
    Filter mentor messages to exclude those advising blocked actions
    
    Args:
        messages: List of mentor messages from MentorService
        active_mission_constraints: Current mission constraints dict from player_mission_progress
        
    Returns:
        Filtered list of messages that don't conflict with constraints
    """
    if not active_mission_constraints:
        return messages  # No active mission, show all messages
    
    # Map message triggers to constraint checks
    # Returns True if message is SAFE to show, False if it should be filtered
    CONSTRAINT_CONFLICTS = {
        # === COACH CHEN MESSAGES (Strategic) ===
        # Messages that advise buying assets
        'high_cash_ratio': lambda c: c.get('can_buy_assets', True),
        'poor_diversification': lambda c: c.get('can_buy_assets', True),
        'strong_asset_growth': lambda c: c.get('can_buy_assets', True),  # Advises reinvestment
        'single_income_source': lambda c: c.get('can_buy_assets', True),  # Advises buying income assets
        
        # Messages that advise selling/managing liabilities
        'overextension': lambda c: c.get('can_sell_assets', True),  # Advises selling liabilities
        
        # Safe messages (informational/celebratory only)
        'net_worth_growth': lambda c: True,  # Just celebrates, no action
        'low_emergency_fund': lambda c: True,  # Advises saving cash (always allowed)
        'high_savings_rate': lambda c: True,  # Celebrates savings (no action)
        
        # === TASHA MESSAGES (Risk Analyst) ===
        # Messages that advise buying assets
        'low_passive_income': lambda c: c.get('can_buy_assets', True),  # Advises buying income assets
        'no_assets': lambda c: c.get('can_buy_assets', True),  # Advises buying first asset
        
        # Messages that advise taking loans
        'high_debt_to_income': lambda c: c.get('can_take_loans', True),  # May advise consolidation loan
        
        # Messages that advise changing expenses/rental
        'high_expense_ratio': lambda c: c.get('can_rent_property', True),  # Advises moving to cheaper place
        
        # Messages that advise job changes
        'stagnant_income': lambda c: c.get('can_change_job', True),  # Advises switching jobs
        
        # Safe messages
        'negative_cash_flow': lambda c: True,  # Emergency warning (always show)
        'poor_credit_score': lambda c: True,  # Credit advice (no blocked actions)
        'low_debt_ratio': lambda c: True,  # Celebrates good debt management
        
        # === PARENT MESSAGES (Emotional) ===
        # Messages that advise lifestyle changes
        'expensive_purchase': lambda c: c.get('can_buy_lifestyle_items', True),  # Warns about lifestyle spending
        
        # Safe messages (all emotional support)
        'milestone_10k': lambda c: True,  # Celebrates milestone
        'inactivity': lambda c: True,  # Encourages return
        'financial_stress': lambda c: True,  # Emotional support
        'first_asset': lambda c: True,  # Celebrates achievement
        'consistent_progress': lambda c: True,  # Celebrates discipline
        'debt_free': lambda c: True,  # Celebrates debt freedom
        'overworking': lambda c: True,  # Work-life balance concern
        
        # === REAL-TIME TRIGGERS (from check_real_time_triggers) ===
        'high_debt_taken': lambda c: True,  # Reactive warning (already happened)
        'panic_selling': lambda c: True,  # Reactive warning (already happened)
    }
    
    filtered_messages = []
    
    for message in messages:
        trigger_type = message.get('trigger_type')
        
        # If trigger type not in our map, include it (safe default)
        if trigger_type not in CONSTRAINT_CONFLICTS:
            print(f"⚠️  Unknown trigger type '{trigger_type}' - allowing by default")
            filtered_messages.append(message)
            continue
        
        # Check if this message type is allowed under current constraints
        constraint_check = CONSTRAINT_CONFLICTS[trigger_type]
        if constraint_check(active_mission_constraints):
            filtered_messages.append(message)
        else:
            # Log that we filtered this message (for debugging)
            print(f"🔒 Filtered mentor message '{trigger_type}' due to mission constraints")
    
    return filtered_messages


def get_constraint_safe_cta(cta_action: str, active_mission_constraints: dict) -> dict:
    """
    Modify CTA (Call-to-Action) based on mission constraints
    
    Args:
        cta_action: Original CTA action (e.g., 'navigate_to_marketplace')
        active_mission_constraints: Current mission constraints
        
    Returns:
        Dict with modified CTA if needed:
        {
            'action': str,  # Modified or original action
            'modified': bool,  # Whether it was changed
            'reason': str  # Why it was changed (if modified)
        }
    """
    if not active_mission_constraints:
        return {'action': cta_action, 'modified': False}
    
    # Map CTAs to required permissions
    CTA_CONSTRAINTS = {
        'navigate_to_marketplace': 'can_buy_assets',
        'navigate_to_liabilities': 'can_sell_assets',
        'navigate_to_jobs': 'can_change_job',
        'navigate_to_loans': 'can_take_loans',
    }
    
    required_permission = CTA_CONSTRAINTS.get(cta_action)
    
    if required_permission:
        if not active_mission_constraints.get(required_permission, True):
            # CTA is blocked, redirect to mission screen instead
            return {
                'action': 'navigate_to_missions',
                'modified': True,
                'reason': f'Action blocked by active mission (requires {required_permission})'
            }
    
    return {'action': cta_action, 'modified': False}


def get_safe_mentor_messages_for_mission(player_id, active_mission_data):
    """
    Complete workflow to get constraint-safe mentor messages
    
    Args:
        player_id: UUID of the player
        active_mission_data: Active mission data with constraints_applied
        
    Returns:
        List of safe mentor messages with modified CTAs
        
    Example usage in Flask route:
        from app.services.mentor_service import MentorService
        from app.utils.mentor_constraint_filter import get_safe_mentor_messages_for_mission
        
        @app.route('/api/mentors/messages')
        @require_auth
        def get_mentor_messages():
            player_id = g.current_user['id']
            
            # Get active mission
            active_mission = get_active_mission(player_id)
            
            # Get constraint-safe messages
            messages = get_safe_mentor_messages_for_mission(player_id, active_mission)
            
            return jsonify({'success': True, 'data': messages})
    """
    from app.services.mentor_service import MentorService
    
    # Get player metrics
    metrics = MentorService.analyze_player_finances(player_id)
    
    # Check which messages should trigger
    triggers = MentorService.check_triggers(player_id, metrics)
    
    # Generate messages
    profile = db.session.query(Profile).filter_by(user_id=player_id).first()
    username = profile.username if profile else "Player"
    
    messages = []
    for trigger in triggers:
        mentor_data = MentorService.generate_personalized_message(player_id, trigger, username)
        if mentor_data:
            messages.append({
                'trigger_type': trigger['type'],
                'mentor': mentor_data['mentor'].to_dict(),
                'message': mentor_data['personalized_message'],
                'cta_text': mentor_data['message_template'].cta_text,
                'cta_action': mentor_data['message_template'].cta_action,
                'priority': mentor_data['message_template'].priority,
                'points_reward': mentor_data['message_template'].points_reward
            })
    
    # Get constraints
    constraints = active_mission_data.get('constraints_applied') if active_mission_data else None
    
    # Filter by constraints
    safe_messages = filter_mentor_messages_by_constraints(messages, constraints)
    
    # Modify CTAs if needed
    for message in safe_messages:
        cta_result = get_constraint_safe_cta(message['cta_action'], constraints)
        if cta_result['modified']:
            message['cta_action'] = cta_result['action']
            message['cta_text'] = 'View Mission Details'
            message['cta_modified'] = True
            message['cta_modification_reason'] = cta_result['reason']
    
    return safe_messages


# Example integration in Flask route
"""
@app.route('/api/mentors/messages')
@require_auth
def get_mentor_messages():
    '''Get constraint-safe mentor messages for player'''
    from app.routes.mission_routes import get_active_mission
    from app.utils.mentor_constraint_filter import get_safe_mentor_messages_for_mission
    
    player_id = g.current_user['id']
    
    # Get active mission
    active_mission = get_active_mission(player_id)
    
    # Get safe messages
    messages = get_safe_mentor_messages_for_mission(player_id, active_mission)
    
    return jsonify({
        'success': True,
        'data': messages,
        'has_active_mission': active_mission is not None
    })
"""
