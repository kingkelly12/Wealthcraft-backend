"""
Balance operations.

All money movement goes through the `adjust_balance` Postgres function
(supabase/schema.sql), which updates the wallet and writes the transactions
row in ONE atomic statement and refuses to overdraw. The old read-modify-write
implementation lost updates under concurrent requests (double-spend) and
accepted negative amounts.
"""
import logging
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from app import supabase

logger = logging.getLogger(__name__)


def _to_decimal(amount) -> Decimal:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f'Invalid amount: {amount!r}')
    if not value.is_finite():
        raise ValueError(f'Invalid amount: {amount!r}')
    return value


class BalanceService:
    """Service for managing user balances"""

    @staticmethod
    def get_current_balance(user_id: str) -> Decimal:
        """Current wallet balance (0 if the wallet row doesn't exist yet)."""
        response = supabase.table('user_balances').select('current_balance') \
            .eq('user_id', str(user_id)).limit(1).execute()
        if response.data:
            return Decimal(str(response.data[0]['current_balance']))
        return Decimal('0')

    @staticmethod
    def _adjust(user_id: str, signed_amount: Decimal, reason: str, category: str) -> Decimal:
        try:
            res = supabase.rpc('adjust_balance', {
                'p_user_id': str(user_id),
                'p_amount': str(signed_amount),
                'p_reason': reason,
                'p_category': category,
            }).execute()
        except Exception as e:
            if 'Insufficient funds' in str(e):
                raise Exception('Insufficient funds') from e
            raise
        new_balance = Decimal(str(res.data))

        # Keep the cached leaderboard net worth in sync.
        try:
            from app.services.profile_service import ProfileService
            ProfileService.recalculate_net_worth(uuid.UUID(str(user_id)))
        except Exception as sync_error:
            logger.warning(f'Failed to sync net worth for {user_id}: {sync_error}')

        return new_balance

    @staticmethod
    def add_balance(user_id: str, amount, reason: str, category: str = 'balance_adjustment') -> Dict[str, Any]:
        """Credit a positive amount."""
        amount = _to_decimal(amount)
        if amount <= 0:
            raise ValueError('Amount to add must be positive')
        new_balance = BalanceService._adjust(user_id, amount, reason, category)
        return {
            'success': True,
            'new_balance': new_balance,
            'transaction_id': None,
            'message': f'Successfully added ${amount} to balance',
        }

    @staticmethod
    def subtract_balance(user_id: str, amount, reason: str, category: str = 'balance_adjustment') -> Dict[str, Any]:
        """Debit a positive amount. Raises 'Insufficient funds' rather than overdrawing."""
        amount = _to_decimal(amount)
        if amount <= 0:
            raise ValueError('Amount to subtract must be positive')
        new_balance = BalanceService._adjust(user_id, -amount, reason, category)
        return {
            'success': True,
            'new_balance': new_balance,
            'transaction_id': None,
            'message': f'Successfully subtracted ${amount} from balance',
        }
