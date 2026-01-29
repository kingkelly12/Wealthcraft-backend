
"""
Service layer for balance operations
Handles business logic for adding/subtracting user balance
"""
from decimal import Decimal
from typing import Dict, Any
import uuid
from datetime import datetime
from app import supabase


class BalanceService:
    """Service for managing user balances"""
    
    @staticmethod
    def get_current_balance(user_id: str) -> Decimal:
        """Get the current balance for a user"""
        try:
            response = supabase.table('user_balances').select('current_balance').eq('user_id', user_id).single().execute()
            if response.data:
                return Decimal(str(response.data['current_balance']))
            return Decimal('0')
        except Exception as e:
            print(f'Error getting balance: {e}')
            raise Exception('Failed to retrieve balance')
    
    @staticmethod
    def add_balance(user_id: str, amount: Decimal, reason: str) -> Dict[str, Any]:
        """
        Add money to user's balance
        
        Args:
            user_id: UUID of the user
            amount: Amount to add (must be positive)
            reason: Reason for adding balance
            
        Returns:
            Dict with success status, new balance, and transaction ID
        """
        try:
            # Get current balance
            current_balance = BalanceService.get_current_balance(user_id)
            new_balance = current_balance + amount
            
            # Update balance
            supabase.table('user_balances').update({
                'current_balance': float(new_balance),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            # Create transaction record
            transaction_id = str(uuid.uuid4())
            supabase.table('transactions').insert({
                'id': transaction_id,
                'user_id': user_id,
                'type': 'income',
                'category': 'balance_adjustment',
                'amount': float(amount),
                'description': reason,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return {
                'success': True,
                'new_balance': new_balance,
                'transaction_id': transaction_id,
                'message': f'Successfully added ${amount} to balance'
            }
        except Exception as e:
            print(f'Error adding balance: {e}')
            raise Exception(f'Failed to add balance: {str(e)}')
    
    @staticmethod
    def subtract_balance(user_id: str, amount: Decimal, reason: str) -> Dict[str, Any]:
        """
        Subtract money from user's balance
        
        Args:
            user_id: UUID of the user
            amount: Amount to subtract (must be positive)
            reason: Reason for subtracting balance
            
        Returns:
            Dict with success status, new balance, and transaction ID
            
        Raises:
            Exception: If insufficient funds or operation fails
        """
        try:
            # Get current balance
            current_balance = BalanceService.get_current_balance(user_id)
            
            # Check if user has sufficient funds
            if current_balance < amount:
                raise Exception(f'Insufficient funds. Current balance: ${current_balance}, Required: ${amount}')
            
            new_balance = current_balance - amount
            
            # Update balance
            supabase.table('user_balances').update({
                'current_balance': float(new_balance),
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            # Create transaction record
            transaction_id = str(uuid.uuid4())
            supabase.table('transactions').insert({
                'id': transaction_id,
                'user_id': user_id,
                'type': 'expense',
                'category': 'balance_adjustment',
                'amount': float(amount),
                'description': reason,
                'created_at': datetime.utcnow().isoformat()
            }).execute()
            
            return {
                'success': True,
                'new_balance': new_balance,
                'transaction_id': transaction_id,
                'message': f'Successfully subtracted ${amount} from balance'
            }
        except Exception as e:
            print(f'Error subtracting balance: {e}')
            raise Exception(f'Failed to subtract balance: {str(e)}')
