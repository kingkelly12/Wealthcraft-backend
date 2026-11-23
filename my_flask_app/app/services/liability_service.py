from app import db
from app.models.player_liability import PlayerLiability
from typing import Dict
import uuid
from decimal import Decimal

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
    def sell_liability(player_liability_id: uuid.UUID, player_id: uuid.UUID) -> Dict:
        """
        Sell a player's liability at current depreciated value.
        Returns sale details including amount received.
        """
        # Atomically claim the item (only one concurrent sale can flip is_active)
        claimed = db.session.execute(
            PlayerLiability.__table__.update()
            .where(PlayerLiability.id == player_liability_id)
            .where(PlayerLiability.player_id == player_id)
            .where(PlayerLiability.is_active.is_(True))
            .values(is_active=False)
            .returning(PlayerLiability.id, PlayerLiability.liability_id,
                       PlayerLiability.purchase_price, PlayerLiability.current_value)
        ).first()
        db.session.commit()

        if not claimed:
            raise ValueError("Liability not found or does not belong to player")

        purchase_price = Decimal(str(claimed.purchase_price))
        sale_value = Decimal(str(claimed.current_value if claimed.current_value is not None else claimed.purchase_price))

        from app.services.balance_service import BalanceService
        balance_result = BalanceService.add_balance(
            user_id=str(player_id),
            amount=sale_value,
            reason="Sold lifestyle item",
            category='liability_sale',
        )

        return {
            'sale_value': float(sale_value),
            'liability_id': str(claimed.id),
            'purchase_price': float(purchase_price),
            'depreciation_loss': float(purchase_price - sale_value),
            'transaction_id': balance_result.get('transaction_id')
        }

    @staticmethod
    def get_depreciation_preview(player_liability_id: uuid.UUID, player_id: uuid.UUID) -> Dict:
        """
        Get depreciation preview for a liability without applying it.
        Shows current stats and next month's estimated value.
        """
        liability = PlayerLiability.query.filter_by(id=player_liability_id, player_id=player_id).first()
        
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
