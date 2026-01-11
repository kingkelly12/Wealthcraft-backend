from app import db
from app.models.player_liability import PlayerLiability
from app.models.monthly_deduction import MonthlyDeduction
from app.models.transaction import Transaction
from app.models.user_balance import UserBalance
from typing import Optional, List, Dict
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func

class LiabilityService:
    # Depreciation rates
    YEAR_1_MONTHLY_RATE = Decimal('0.0104')  # 12.5% annual / 12 months = ~1.04% monthly
    YEAR_2_PLUS_MONTHLY_RATE = Decimal('0.0025')  # 3% annual / 12 months = ~0.25% monthly
    MINIMUM_VALUE_PERCENTAGE = Decimal('0.05')  # 5% floor
    
    @staticmethod
    def calculate_depreciation(player_liability: PlayerLiability) -> Dict:
        """
        Calculate depreciation for a single liability.
        Returns dict with current_value, depreciation_amount, and rate_used.
        """
        if not player_liability.is_active:
            return {
                'current_value': float(player_liability.current_value or 0),
                'depreciation_amount': 0,
                'rate_used': 0
            }
        
        # Get current value or initialize to purchase price
        current_value = player_liability.current_value or player_liability.purchase_price
        current_value = Decimal(str(current_value))
        purchase_price = Decimal(str(player_liability.purchase_price))
        
        # Calculate minimum allowed value (5% of purchase price)
        minimum_value = purchase_price * LiabilityService.MINIMUM_VALUE_PERCENTAGE
        
        # If already at minimum, no further depreciation
        if current_value <= minimum_value:
            return {
                'current_value': float(current_value),
                'depreciation_amount': 0,
                'rate_used': 0
            }
        
        # Determine depreciation rate based on age
        months_owned = player_liability.months_owned or 0
        if months_owned < 12:
            # Year 1: Higher depreciation
            rate = LiabilityService.YEAR_1_MONTHLY_RATE
        else:
            # Year 2+: Lower depreciation
            rate = LiabilityService.YEAR_2_PLUS_MONTHLY_RATE
        
        # Calculate new value
        depreciation_amount = current_value * rate
        new_value = current_value - depreciation_amount
        
        # Enforce minimum floor
        if new_value < minimum_value:
            depreciation_amount = current_value - minimum_value
            new_value = minimum_value
        
        return {
            'current_value': float(new_value),
            'depreciation_amount': float(depreciation_amount),
            'rate_used': float(rate)
        }
    
    @staticmethod
    def apply_monthly_depreciation(player_id: Optional[uuid.UUID] = None) -> Dict:
        """
        Apply monthly depreciation to all active liabilities.
        If player_id is provided, only depreciate that player's liabilities.
        Returns count of updated liabilities and total depreciation amount.
        """
        query = PlayerLiability.query.filter_by(is_active=True)
        
        if player_id:
            query = query.filter_by(player_id=player_id)
        
        liabilities = query.all()
        updated_count = 0
        total_depreciation = Decimal('0')
        
        today = date.today()
        
        for liability in liabilities:
            # Initialize current_value if not set
            if liability.current_value is None:
                liability.current_value = liability.purchase_price
            
            # Calculate depreciation
            result = LiabilityService.calculate_depreciation(liability)
            
            if result['depreciation_amount'] > 0:
                # Update liability
                liability.current_value = Decimal(str(result['current_value']))
                liability.months_owned = (liability.months_owned or 0) + 1
                liability.last_depreciation_date = today
                
                total_depreciation += Decimal(str(result['depreciation_amount']))
                updated_count += 1
        
        db.session.commit()
        
        return {
            'updated_count': updated_count,
            'total_depreciation': float(total_depreciation),
            'date': today.isoformat()
        }
    
    @staticmethod
    def sell_liability(player_liability_id: uuid.UUID, player_id: uuid.UUID) -> Dict:
        """
        Sell a player's liability at current depreciated value.
        Returns sale details including amount received.
        """
        # Fetch and validate liability
        liability = PlayerLiability.query.filter_by(
            id=player_liability_id,
            player_id=player_id,
            is_active=True
        ).first()
        
        if not liability:
            raise ValueError("Liability not found or does not belong to player")
        
        # Get current value (or purchase price if not depreciated yet)
        sale_value = liability.current_value or liability.purchase_price
        sale_value = Decimal(str(sale_value))
        
        # Update player balance
        user_balance = UserBalance.query.filter_by(user_id=player_id).first()
        if user_balance:
            user_balance.current_balance = Decimal(str(user_balance.current_balance)) + sale_value
        else:
            # Create balance record if it doesn't exist (edge case)
            user_balance = UserBalance(user_id=player_id, current_balance=sale_value)
            db.session.add(user_balance)
        
        # Log transaction
        transaction = Transaction(
            user_id=player_id,
            type='income',
            category='liability_sale',
            amount=float(sale_value),
            description=f"Sold liability (ID: {str(liability.liability_id)[:8]}...)"
        )
        db.session.add(transaction)
        
        # Remove associated monthly deductions
        MonthlyDeduction.query.filter_by(
            reference_id=player_liability_id,
            deduction_type='liability_cost'
        ).delete()
        
        # Mark as inactive (preserve history)
        liability.is_active = False
        
        db.session.commit()
        
        return {
            'sale_value': float(sale_value),
            'liability_id': str(liability.id),
            'purchase_price': float(liability.purchase_price),
            'depreciation_loss': float(Decimal(str(liability.purchase_price)) - sale_value),
            'transaction_id': str(transaction.id)
        }
    
    @staticmethod
    def get_depreciation_preview(player_liability_id: uuid.UUID) -> Dict:
        """
        Get depreciation preview for a liability without applying it.
        Shows current stats and next month's estimated value.
        """
        liability = PlayerLiability.query.get(player_liability_id)
        
        if not liability:
            raise ValueError("Liability not found")
        
        current_value = liability.current_value or liability.purchase_price
        purchase_price = liability.purchase_price
        
        # Calculate current depreciation percentage
        current_depreciation_pct = (
            (Decimal(str(purchase_price)) - Decimal(str(current_value))) / 
            Decimal(str(purchase_price)) * 100
        ) if purchase_price > 0 else 0
        
        # Calculate next month's value
        next_month_calc = LiabilityService.calculate_depreciation(liability)
        
        return {
            'current_value': float(current_value),
            'purchase_price': float(purchase_price),
            'depreciation_percentage': float(current_depreciation_pct),
            'depreciation_amount': float(Decimal(str(purchase_price)) - Decimal(str(current_value))),
            'next_month_value': next_month_calc['current_value'],
            'next_month_depreciation': next_month_calc['depreciation_amount'],
            'months_owned': liability.months_owned or 0,
            'is_active': liability.is_active
        }
    
    @staticmethod
    def backfill_existing_liabilities() -> Dict:
        """
        One-time function to backfill existing liabilities with initial values.
        Sets current_value = purchase_price and calculates months_owned from purchase_date.
        """
        liabilities = PlayerLiability.query.filter(
            PlayerLiability.current_value.is_(None)
        ).all()
        
        updated_count = 0
        today = date.today()
        
        for liability in liabilities:
            # Set current_value to purchase_price
            liability.current_value = liability.purchase_price
            
            # Calculate months_owned from purchase_date
            if liability.purchase_date:
                purchase_date = liability.purchase_date.date() if hasattr(liability.purchase_date, 'date') else liability.purchase_date
                months_diff = (today.year - purchase_date.year) * 12 + (today.month - purchase_date.month)
                liability.months_owned = max(0, months_diff)
            else:
                liability.months_owned = 0
            
            liability.last_depreciation_date = today
            updated_count += 1
        
        db.session.commit()
        
        return {
            'backfilled_count': updated_count,
            'date': today.isoformat()
        }
