"""
Server-side enforcement of mission constraints.

While a player has an active mission, its `constraints_applied` snapshot
(can_buy_assets, can_take_loans, allowed_asset_types, max_loan_amount, ...)
limits what they may do. Previously only the mobile app checked these, so any
direct API call bypassed them.
"""
import hashlib
from typing import Dict, Optional

from flask import jsonify

from app import supabase


def active_mission_constraints(user_id: str) -> Optional[Dict]:
    res = supabase.table('player_mission_progress').select('constraints_applied') \
        .eq('player_id', str(user_id)).eq('is_active', True).limit(1).execute()
    if not res.data:
        return None
    return res.data[0].get('constraints_applied') or {}


def constraint_violation(constraints: Optional[Dict], action: str, data: Optional[Dict] = None) -> Optional[str]:
    """Reason string if `action` breaks the constraints, else None."""
    if not constraints:
        return None
    data = data or {}

    if action == 'buy_asset':
        if not constraints.get('can_buy_assets', True):
            return '🎯 Mission constraint: You cannot buy assets during this mission'
        allowed = constraints.get('allowed_asset_types')
        if allowed:
            kinds = {k for k in (data.get('asset_type'), data.get('category')) if k}
            if kinds and not kinds & set(allowed):
                return f'🎯 Mission constraint: You can only buy {", ".join(allowed)} during this mission'
    elif action == 'take_loan':
        if not constraints.get('can_take_loans', True):
            return '🎯 Mission constraint: You cannot take loans during this mission'
        max_amount = constraints.get('max_loan_amount')
        try:
            if max_amount and float(data.get('amount') or 0) > float(max_amount):
                return f'🎯 Mission constraint: Maximum loan amount is ${float(max_amount):,.2f}'
        except (TypeError, ValueError):
            pass
        allowed_types = constraints.get('allowed_loan_types')
        if allowed_types and data.get('loan_type') and data['loan_type'] not in allowed_types:
            return f'🎯 Mission constraint: Allowed loans: {", ".join(allowed_types)}'
    elif action == 'change_job':
        if not constraints.get('can_change_job', True):
            return '🎯 Mission constraint: You cannot change jobs during this mission'
    elif action == 'rent_property':
        if not constraints.get('can_rent_property', True):
            return '🎯 Mission constraint: You cannot change rental properties during this mission'
    elif action == 'sell_asset':
        if not constraints.get('can_sell_assets', True):
            return '🎯 Mission constraint: You cannot sell assets during this mission'
    elif action == 'buy_lifestyle_item':
        if not constraints.get('can_buy_lifestyle_items', True):
            return '🎯 Mission constraint: You cannot buy lifestyle items during this mission'
    return None


def enforce_mission_constraints(user_id: str, action: str, data: Optional[Dict] = None):
    """
    For use at the top of a route:
        blocked = enforce_mission_constraints(uid, 'buy_asset', {...})
        if blocked: return blocked
    Returns a (response, 403) tuple when blocked, else None.
    """
    reason = constraint_violation(active_mission_constraints(user_id), action, data)
    if reason:
        return jsonify({'success': False, 'error': 'MISSION_CONSTRAINT', 'message': reason}), 403
    return None


def story_roll(player_mission_id: str, event_id: str, month: int) -> float:
    """
    Deterministic 0..1 roll for probability-based story events. The pending
    list used random.random() on every fetch, so simply refreshing re-rolled
    until the event appeared; the same roll also lets acknowledge() verify it.
    """
    digest = hashlib.sha256(f'{player_mission_id}:{event_id}:{month}'.encode()).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def story_event_due(event: Dict, player_mission_id: str, current_month: int) -> bool:
    trigger = event.get('trigger_type')
    if trigger == 'mission_start':
        return current_month == 1
    if trigger == 'month':
        return current_month >= int(event.get('trigger_value') or 0)
    if trigger == 'custom':
        probability = event.get('probability')
        probability = 1.0 if probability is None else float(probability)  # 0.0 must mean "never"
        return story_roll(player_mission_id, event['id'], current_month) < probability
    return True


def emotion_sanity_delta(row: Dict) -> int:
    """
    Story events and decision options carry happiness / stress / motivation.
    They land on sanity, the game's single mental-health stat:
        sanity += happiness + motivation / 2 - stress
    Keep in sync with storySanityDelta() in the app's MissionStoryEventModal.
    """
    happiness = int(row.get('happiness_change') or 0)
    motivation = int(row.get('motivation_change') or 0)
    stress = int(row.get('stress_change') or 0)
    return happiness + int(motivation / 2) - stress


def earlier_runs(player_id: str, mission_id: str, current_run_id: str) -> list:
    """Ids of the player's previous (abandoned/failed) runs of the same mission."""
    rows = supabase.table('player_mission_progress').select('id') \
        .eq('player_id', str(player_id)).eq('mission_id', str(mission_id)).execute().data or []
    return [r['id'] for r in rows if str(r['id']) != str(current_run_id)]
