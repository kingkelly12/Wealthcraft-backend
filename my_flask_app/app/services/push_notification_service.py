"""
Push notifications via the Expo Push API.

Flow
----
1. The app registers its Expo push token through POST /api/notifications/register-token/
   (stored in profiles.expo_push_token; one device = one owner, see notification_routes).
2. send_notifications_to_users() looks the tokens up in ONE query and posts the
   messages in batches of up to 100 (Expo's limit), instead of one DB query and
   one HTTP call per player.
3. Expo answers each message with a *ticket*. A ticket of "ok" only means Expo
   accepted it; whether the phone actually got it is in a *receipt*, available a
   few minutes later. Accepted tickets are stored in push_tickets and
   check_receipts() (cron: /api/cron/push-receipts/) reads the receipts and
   clears tokens of uninstalled apps (DeviceNotRegistered). Without that step,
   dead tokens were never cleaned up on Android.

Set EXPO_ACCESS_TOKEN if "Enhanced push security" is enabled for the Expo project.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


class ExpoPushService:
    """Sends push notifications through Expo's Push API."""

    EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
    EXPO_RECEIPTS_URL = "https://exp.host/--/api/v2/push/getReceipts"
    MAX_MESSAGES_PER_REQUEST = 100   # Expo limit for /push/send
    MAX_RECEIPT_IDS_PER_REQUEST = 1000  # Expo limit for /push/getReceipts
    TOKEN_PREFIXES = ('ExponentPushToken[', 'ExpoPushToken[')  # Expo issues both forms

    # ------------------------------------------------------------------ helpers

    @classmethod
    def validate_push_token(cls, token: str) -> bool:
        """True for ExponentPushToken[...] and ExpoPushToken[...] tokens."""
        return (isinstance(token, str) and token.endswith(']')
                and token.startswith(cls.TOKEN_PREFIXES) and len(token) < 256)

    @staticmethod
    def _headers() -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }
        access_token = os.environ.get('EXPO_ACCESS_TOKEN')
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    @classmethod
    def _get_tokens(cls, supabase_client, user_ids: Iterable[str]) -> Dict[str, str]:
        """{user_id: token} for the given players, in one query per 200 ids."""
        ids = list(dict.fromkeys(str(u) for u in user_ids if u))
        tokens: Dict[str, str] = {}
        for i in range(0, len(ids), 200):
            try:
                rows = supabase_client.table('profiles').select('user_id, expo_push_token') \
                    .in_('user_id', ids[i:i + 200]).execute().data or []
            except Exception as e:
                logger.error(f"Error fetching Expo tokens: {e}")
                continue
            for row in rows:
                token = row.get('expo_push_token')
                if cls.validate_push_token(token):
                    tokens[str(row['user_id'])] = token
        return tokens

    @staticmethod
    def _build_message(token: str, title: str, body: str, notification_type: str, data: Optional[Dict]) -> Dict:
        payload_data = dict(data) if data else {}
        # The app routes taps on data.type when there's no data.screen; a type the
        # caller put in `data` wins over the generic notification_type.
        payload_data.setdefault('type', notification_type)
        payload_data['timestamp'] = datetime.now(timezone.utc).isoformat()
        return {
            "to": token,
            "title": (title or '')[:200],
            "body": (body or '')[:1000],
            "data": payload_data,
            "sound": "default",
            "priority": "high",
            "channelId": "default",   # created by the app on Android
        }

    @classmethod
    def _post_batch(cls, messages: List[Dict]) -> List[Dict]:
        """POST up to 100 messages; returns one ticket per message (error tickets on failure)."""
        try:
            response = requests.post(cls.EXPO_PUSH_URL, json=messages, headers=cls._headers(), timeout=15)
            result = response.json() if response.content else {}
            tickets = result.get('data')
            if isinstance(tickets, list) and len(tickets) == len(messages):
                return tickets
            message = (result.get('errors') or [{}])[0].get('message') or f'HTTP {response.status_code}'
        except Exception as e:
            message = str(e)
        logger.error(f"Expo push request failed: {message}")
        return [{'status': 'error', 'message': message, 'details': {}} for _ in messages]

    @staticmethod
    def _clear_dead_token(supabase_client, token: str) -> None:
        """
        Forget a token whose app was uninstalled. Matched on the token itself,
        so a player who re-registered a NEW token in the meantime keeps it.
        """
        try:
            supabase_client.table('profiles').update({'expo_push_token': None}) \
                .eq('expo_push_token', token).execute()
            logger.info("Cleared unregistered Expo token")
        except Exception as e:
            logger.warning(f"Failed to clear dead token: {e}")

    # -------------------------------------------------------------------- send

    @classmethod
    def send_notifications_to_users(
        cls,
        supabase_client,
        user_notifications: List[Dict],
        notification_type: str = 'system'
    ) -> Dict[str, int]:
        """
        Send many notifications. Each item: {'user_id', 'title', 'body', 'data'?}.
        Players without a registered token are counted as skipped.
        """
        if not user_notifications:
            return {'success': 0, 'failed': 0, 'skipped': 0}

        tokens = cls._get_tokens(supabase_client, (n.get('user_id') for n in user_notifications))
        outgoing: List[Tuple[str, str, Dict]] = []  # (user_id, token, message)
        skipped = 0
        for n in user_notifications:
            uid = str(n.get('user_id') or '')
            token = tokens.get(uid)
            if not token:
                skipped += 1
                continue
            outgoing.append((uid, token, cls._build_message(
                token, n.get('title', ''), n.get('body', ''), notification_type, n.get('data'))))

        success = failed = 0
        accepted = []
        for i in range(0, len(outgoing), cls.MAX_MESSAGES_PER_REQUEST):
            chunk = outgoing[i:i + cls.MAX_MESSAGES_PER_REQUEST]
            tickets = cls._post_batch([m for _, _, m in chunk])
            for (uid, token, _), ticket in zip(chunk, tickets):
                if ticket.get('status') == 'ok':
                    success += 1
                    if ticket.get('id'):
                        accepted.append({'ticket_id': ticket['id'], 'user_id': uid, 'token': token})
                    continue
                failed += 1
                error = (ticket.get('details') or {}).get('error', '')
                logger.warning(f"Expo push rejected for {uid}: {ticket.get('message')} ({error})")
                # Only a device-level error means this token is dead. Errors such
                # as InvalidCredentials or MessageRateExceeded are project or
                # rate problems; clearing tokens for those would wipe every
                # player's token after one misconfiguration.
                if error == 'DeviceNotRegistered':
                    cls._clear_dead_token(supabase_client, token)

        if accepted:
            try:
                supabase_client.table('push_tickets').insert(accepted).execute()
            except Exception as e:
                logger.warning(f"Could not store push tickets for receipt checks: {e}")

        logger.info(f"Expo push: {success} sent, {failed} failed, {skipped} without a token")
        return {'success': success, 'failed': failed, 'skipped': skipped}

    @classmethod
    def send_notification_to_user(
        cls,
        supabase_client,
        user_id: str,
        title: str,
        body: str,
        notification_type: str = 'system',
        data: Optional[Dict] = None
    ) -> bool:
        """Send one notification. False if the player has no token or Expo rejected it."""
        result = cls.send_notifications_to_users(
            supabase_client=supabase_client,
            user_notifications=[{'user_id': user_id, 'title': title, 'body': body, 'data': data}],
            notification_type=notification_type,
        )
        return result['success'] == 1

    # ---------------------------------------------------------------- receipts

    @classmethod
    def check_receipts(cls, supabase_client, min_age_minutes: int = 15) -> Dict[str, int]:
        """
        Read Expo receipts for tickets older than `min_age_minutes` (Expo needs a
        few minutes) and clear tokens of uninstalled apps. Processed tickets, and
        any older than a day (Expo forgets receipts after 24h), are deleted.
        """
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(minutes=min_age_minutes)).isoformat()
        tickets = supabase_client.table('push_tickets').select('ticket_id, token') \
            .lt('created_at', cutoff).order('created_at').limit(5000).execute().data or []

        checked = dead = errors = 0
        for i in range(0, len(tickets), cls.MAX_RECEIPT_IDS_PER_REQUEST):
            chunk = tickets[i:i + cls.MAX_RECEIPT_IDS_PER_REQUEST]
            ids = [t['ticket_id'] for t in chunk]
            try:
                r = requests.post(cls.EXPO_RECEIPTS_URL, json={'ids': ids}, headers=cls._headers(), timeout=15)
                receipts = (r.json() or {}).get('data') or {}
            except Exception as e:
                logger.error(f"Expo receipts request failed: {e}")
                continue  # keep the tickets; try again next run
            token_by_ticket = {t['ticket_id']: t['token'] for t in chunk}
            for ticket_id, receipt in receipts.items():
                if receipt.get('status') == 'error':
                    errors += 1
                    error = (receipt.get('details') or {}).get('error', '')
                    logger.warning(f"Expo receipt error: {receipt.get('message')} ({error})")
                    if error == 'DeviceNotRegistered':
                        dead += 1
                        cls._clear_dead_token(supabase_client, token_by_ticket[ticket_id])
            # Receipts not ready yet are omitted by Expo; keep those for next time
            # unless they're old enough that Expo has already forgotten them.
            done = [tid for tid in ids if tid in receipts]
            if done:
                supabase_client.table('push_tickets').delete().in_('ticket_id', done).execute()
            checked += len(done)

        supabase_client.table('push_tickets').delete() \
            .lt('created_at', (now - timedelta(hours=24)).isoformat()).execute()
        logger.info(f"Expo receipts: {checked} checked, {errors} errors, {dead} dead tokens cleared")
        return {'checked': checked, 'errors': errors, 'dead_tokens_cleared': dead}

    # ------------------------------------------------------- follower updates

    @classmethod
    def notify_followers_of_financial_move(
        cls,
        supabase_client,
        user_id: str,
        move_type: str,
        item_name: str,
        amount: Optional[float] = None,
        profit: Optional[float] = None
    ) -> None:
        """Record the move on the player's own profile, then tell everyone following them (push + in-app
        feed) in the background."""
        from app.utils.background_task import run_in_background

        cls.record_activity(supabase_client, user_id, move_type, item_name, amount, profit)

        def background_task():
            try:
                profile_res = supabase_client.table('profiles').select('username').eq('user_id', user_id).limit(1).execute()
                username = profile_res.data[0].get('username', 'A friend') if profile_res.data else 'A friend'

                followers_res = supabase_client.table('user_follows').select('follower_id').eq('following_id', user_id).execute()
                follower_ids = [f['follower_id'] for f in (followers_res.data or [])]
                if not follower_ids:
                    return

                title, body = cls._follower_copy(move_type, username, item_name, amount, profit)

                # The in-app feed is the history; the push is the alert. Both, always.
                supabase_client.table('notifications').insert([{
                    'user_id': fid, 'type': 'student_move', 'title': title, 'message': body,
                    'related_user_id': user_id, 'read': False,
                } for fid in follower_ids]).execute()

                cls.send_notifications_to_users(
                    supabase_client=supabase_client,
                    user_notifications=[{
                        'user_id': fid, 'title': title, 'body': body,
                        'data': {'type': 'student_move', 'student_id': user_id, 'screen': f'/profile?id={user_id}'},
                    } for fid in follower_ids],
                    notification_type='student_move',
                )
            except Exception as e:
                logger.error(f"Failed to notify followers of move: {e}")

        run_in_background(background_task)

    # The player's own timeline (their profile's Activity tab): (emoji, what they did).
    _ACTIVITY = {
        'buy_asset': ('📈', 'Invested in {item}'),
        'sell_asset': ('💰', 'Sold {item}'),
        'buy_liability': ('🛍️', 'Bought the {item}'),
        'sell_liability': ('🔄', 'Sold the {item}'),
        'buy_home': ('🔑', 'Bought the {item}'),
        'sell_home': ('🏡', 'Sold the {item}'),
        'take_loan': ('💳', 'Took out a {item} loan'),
        'repay_loan': ('📉', 'Paid down their {item}'),
        'post_p2p_offer': ('🤝', 'Offered a friend loan'),
        'rent_property': ('🏠', 'Moved into {item}'),
        'move_out': ('📦', 'Moved out of {item}'),
        'new_job': ('💼', 'Started as a {item}'),
        'quit_job': ('👋', 'Quit as a {item}'),
        'enroll_course': ('🎓', 'Started {item}'),
        'complete_course': ('📜', 'Completed {item}'),
        'life_event': ('🎲', 'Chose: {item}'),
    }

    @classmethod
    def record_activity(cls, supabase_client, user_id: str, move_type: str, item_name: str,
                        amount: Optional[float] = None, profit: Optional[float] = None) -> None:
        """One line on the player's public timeline. Never blocks the move it describes."""
        emoji, text = cls._ACTIVITY.get(move_type, ('💵', 'Made a move: {item}'))
        try:
            supabase_client.table('player_activity').insert({
                'user_id': user_id, 'kind': move_type, 'emoji': emoji, 'text': text.format(item=item_name),
                'item_name': item_name, 'amount': amount if isinstance(amount, (int, float)) else None,
                'profit': profit if isinstance(profit, (int, float)) else None,
            }).execute()
        except Exception as e:
            logger.warning(f"Activity not recorded for {user_id} ({move_type}): {e}")

    @staticmethod
    def _follower_copy(move_type: str, username: str, item_name: str,
                       amount: Optional[float], profit: Optional[float]) -> Tuple[str, str]:
        money = f"${amount:,.2f}" if isinstance(amount, (int, float)) else "some money"
        copy = {
            'buy_asset': ('📊 Friend Move', f'{username} just invested in {item_name}. Are you keeping up?'),
            'buy_liability': ('🚗 Friend Splurge', f'{username} just bought {item_name} for {money}. Will this ruin their budget?'),
            'sell_liability': ('🔄 Friend Downsized', f'{username} just sold their {item_name}. Smart move or forced cut?'),
            'take_loan': ('💳 Friend Took a Loan', f'{username} took out a {item_name} loan for {money}. Keep an eye on them.'),
            'repay_loan': ('📉 Debt Reduced', f'{username} just paid off {money} of their {item_name}. Building financial freedom.'),
            'post_p2p_offer': ('🤝 Friend Lending', f'{username} is offering {money} as a P2P loan. Playing the bank today?'),
            'rent_property': ('🏠 Friend Moved House', f'{username} just rented {item_name} at {money}/month. Watching their burn rate?'),
            'move_out': ('📦 Friend Relocated', f'{username} just moved out of {item_name}. Living situation changed.'),
            'new_job': ('💼 Friend Hired', f'{username} started as a {item_name}. Salary incoming!'),
            'quit_job': ('👋 Friend Resigned', f'{username} quit their job as {item_name}. Planning their next move?'),
            'enroll_course': ('🎓 Friend Enrolled', f'{username} started {item_name}. Investing in their future.'),
            'complete_course': ('📜 Friend Levelled Up', f'{username} completed {item_name}! Their earning potential just went up.'),
            'life_event': ('🎲 Friend Decision', f'{username} made a choice: "{item_name}". How will it impact them?'),
            'buy_home': ('🔑 Friend Bought a Home', f'{username} just bought the {item_name} for {money}. Homeowner era.'),
        }
        if move_type == 'sell_home':
            if isinstance(profit, (int, float)) and profit >= 0:
                return '🏡 Friend Sold a Home', f'{username} sold the {item_name} for a ${profit:,.0f} profit.'
            return '🏡 Friend Sold a Home', f'{username} sold the {item_name} at a loss. Ouch.'
        if move_type == 'sell_asset':
            if isinstance(profit, (int, float)) and profit >= 0:
                return '💰 Friend Win', f'{username} sold {item_name} for a ${profit:,.2f} profit. Impressive moves.'
            return '📉 Friend Alert', f'{username} sold {item_name} at a loss. Will they bounce back?'
        return copy.get(move_type, ('💵 Financial Move', f'{username} made a financial move involving {item_name}.'))
