"""
Roommate co-op: a real friend moves into your rental.

* The leaseholder (who rents the place) invites someone they follow.
* The invitee accepts only if they don't rent a place of their own.
* On each of the roommate's game months, they pay rent_share of the rent to
  the leaseholder (monthly_loan_deductions._roommate_rent). The leaseholder
  still pays the landlord the full rent, so the split nets out to 50/50.
* Either side can leave; moving out or starting a new life ends it too.
"""
import logging
from datetime import datetime, timezone

from app import supabase

logger = logging.getLogger(__name__)


class RoommateError(Exception):
    def __init__(self, code, message, status=400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def _now():
    return datetime.now(timezone.utc).isoformat()


def _active_rental(uid):
    res = supabase.table('player_rentals').select('*, rental_properties(*)').eq('player_id', str(uid)).eq('is_active', True).limit(1).execute()
    return res.data[0] if res.data else None


def _usernames(ids):
    ids = [str(i) for i in ids if i]
    if not ids:
        return {}
    rows = supabase.table('profiles').select('user_id, username, profile_picture_url').in_('user_id', ids).execute().data or []
    return {r['user_id']: r for r in rows}


def active_for(uid):
    """The active arrangement this player is part of (either side), or None."""
    uid = str(uid)
    for col in ('leaseholder_id', 'roommate_id'):
        res = supabase.table('roommates').select('*').eq(col, uid).eq('status', 'active').limit(1).execute()
        if res.data:
            return res.data[0]
    return None


def roommate_name(uid):
    """Display name of your real roommate, for cards that mention them."""
    arr = active_for(uid)
    if not arr:
        return None
    other = arr['roommate_id'] if str(arr['leaseholder_id']) == str(uid) else arr['leaseholder_id']
    return _usernames([other]).get(str(other), {}).get('username')


def _rental_view(rental):
    if not rental:
        return None
    prop = rental.get('rental_properties') or {}
    return {'id': rental['id'], 'name': prop.get('name') or 'Your place', 'monthly_rent': float(rental.get('monthly_rent') or 0)}


def state(uid):
    from app.game.life import avatars_for
    uid = str(uid)
    arr = active_for(uid)
    pending = supabase.table('roommates').select('*').eq('status', 'pending').or_(f'leaseholder_id.eq.{uid},roommate_id.eq.{uid}').execute().data or []
    people_ids = {r['leaseholder_id'] for r in pending} | {r['roommate_id'] for r in pending}
    if arr:
        people_ids |= {arr['leaseholder_id'], arr['roommate_id']}
    people_ids.discard(uid)
    names = _usernames(people_ids)
    avatars = avatars_for(list(people_ids))

    def person(pid):
        p = names.get(str(pid), {})
        return {'user_id': str(pid), 'username': p.get('username', 'Someone'), 'profile_picture_url': p.get('profile_picture_url'),
                'avatar': (avatars.get(str(pid)) or {}).get('avatar')}

    active = None
    if arr:
        is_leaseholder = str(arr['leaseholder_id']) == uid
        other = arr['roommate_id'] if is_leaseholder else arr['leaseholder_id']
        rental = _active_rental(arr['leaseholder_id'])
        view = _rental_view(rental)
        active = {
            'id': arr['id'], 'role': 'leaseholder' if is_leaseholder else 'roommate', 'with': person(other),
            'rental': view, 'rent_share': float(arr['rent_share']),
            'share_amount': round((view or {}).get('monthly_rent', 0) * float(arr['rent_share']), 2),
        }
    return {
        'active': active,
        'invites_received': [{'id': r['id'], 'from': person(r['leaseholder_id'])} for r in pending if str(r['roommate_id']) == uid],
        'invites_sent': [{'id': r['id'], 'to': person(r['roommate_id'])} for r in pending if str(r['leaseholder_id']) == uid],
        'can_invite': bool(_active_rental(uid)) and not arr,
    }


def invite(uid, target):
    uid, target = str(uid), str(target or '')
    if not target or target == uid:
        raise RoommateError('INVALID_TARGET', 'Pick a friend to invite.', 400)
    if not _active_rental(uid):
        raise RoommateError('NO_RENTAL', 'Rent a place first. Then you can invite a roommate.', 409)
    if active_for(uid):
        raise RoommateError('ALREADY_ROOMMATES', 'You already have a roommate arrangement.', 409)
    follows = supabase.table('user_follows').select('id').eq('follower_id', uid).eq('following_id', target).limit(1).execute()
    if not follows.data:
        raise RoommateError('NOT_FOLLOWING', 'You can only invite people you follow.', 403)
    if active_for(target):
        raise RoommateError('TARGET_TAKEN', 'They already live with someone.', 409)
    existing = supabase.table('roommates').select('id').eq('leaseholder_id', uid).eq('roommate_id', target).eq('status', 'pending').limit(1).execute()
    if existing.data:
        raise RoommateError('ALREADY_INVITED', 'You already invited them.', 409)

    rental = _active_rental(uid)
    row = supabase.table('roommates').insert({
        'leaseholder_id': uid, 'roommate_id': target, 'rental_id': rental['id'], 'status': 'pending', 'rent_share': 0.5,
    }).execute().data[0]

    me = _usernames([uid]).get(uid, {}).get('username', 'A friend')
    place = _rental_view(rental)
    try:
        from app.services.push_notification_service import ExpoPushService
        ExpoPushService.send_notification_to_user(
            supabase, target, f'🏠 {me} wants you as a roommate',
            f"Move into {place['name']} and split the ${place['monthly_rent']:,.0f}/mo rent 50/50.",
            notification_type='social', data={'screen': '/(tabs)/squad'},
        )
    except Exception as e:
        logger.warning(f'Roommate invite push failed: {e}')
    supabase.table('notifications').insert({
        'user_id': target, 'type': 'social', 'title': f'🏠 {me} wants you as a roommate',
        'message': f"Move into {place['name']} and split the rent 50/50. Answer in Squad.", 'read': False,
    }).execute()
    return row


def _pending_for(arr_id, uid, side):
    res = supabase.table('roommates').select('*').eq('id', arr_id).eq(side, str(uid)).eq('status', 'pending').limit(1).execute()
    if not res.data:
        raise RoommateError('NOT_FOUND', 'That invite is gone.', 404)
    return res.data[0]


def accept(uid, arr_id):
    uid = str(uid)
    arr = _pending_for(arr_id, uid, 'roommate_id')
    if _active_rental(uid):
        raise RoommateError('MOVE_OUT_FIRST', 'You rent your own place. Move out first, then accept.', 409)
    if active_for(uid) or active_for(arr['leaseholder_id']):
        raise RoommateError('TAKEN', 'One of you already has a roommate.', 409)
    if not _active_rental(arr['leaseholder_id']):
        supabase.table('roommates').update({'status': 'ended', 'ended_at': _now()}).eq('id', arr_id).execute()
        raise RoommateError('PLACE_GONE', 'They moved out of that place.', 409)
    try:
        done = supabase.table('roommates').update({'status': 'active', 'accepted_at': _now()}) \
            .eq('id', arr_id).eq('status', 'pending').execute()
    except Exception as e:  # unique index: someone else got there first
        if '23505' in str(e) or 'duplicate' in str(e).lower():
            raise RoommateError('TAKEN', 'One of you already has a roommate.', 409)
        raise
    if not done.data:
        raise RoommateError('NOT_FOUND', 'That invite is gone.', 404)
    # Other pending invites to or from either of you no longer make sense.
    for col in ('leaseholder_id', 'roommate_id'):
        for person in (uid, arr['leaseholder_id']):
            supabase.table('roommates').update({'status': 'declined', 'ended_at': _now()}) \
                .eq(col, person).eq('status', 'pending').execute()
    return state(uid)


def decline(uid, arr_id):
    uid = str(uid)
    res = supabase.table('roommates').update({'status': 'declined', 'ended_at': _now()}) \
        .eq('id', arr_id).eq('status', 'pending').or_(f'leaseholder_id.eq.{uid},roommate_id.eq.{uid}').execute()
    if not res.data:
        raise RoommateError('NOT_FOUND', 'That invite is gone.', 404)
    return state(uid)


def leave(uid):
    uid = str(uid)
    arr = active_for(uid)
    if not arr:
        raise RoommateError('NOT_FOUND', "You don't have a roommate.", 404)
    end(arr['id'])
    return state(uid)


def end(arr_id):
    supabase.table('roommates').update({'status': 'ended', 'ended_at': _now()}).eq('id', arr_id).eq('status', 'active').execute()


def end_all_for(uid):
    """Used when starting a new life: every arrangement involving the player ends."""
    uid = str(uid)
    for col in ('leaseholder_id', 'roommate_id'):
        supabase.table('roommates').update({'status': 'ended', 'ended_at': _now()}).eq(col, uid).in_('status', ['active', 'pending']).execute()
