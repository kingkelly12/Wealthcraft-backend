"""
Monthly Asset Appreciation Job
Updates the value of all player assets based on age.
Run this monthly via cron or task scheduler (e.g., 1st of every month)

Mirrors monthly_depreciation.py but for assets:
  - Year 1:  +0.50% per month  (~6% annual growth)
  - Year 2+: +0.25% per month  (~3% annual growth)
  - Ceiling: 200% of purchase price (prevents runaway inflation)
"""

from app import db
from app.models.user_asset import UserAsset
from datetime import date
from decimal import Decimal
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Appreciation rates (mirrors depreciation tier structure)
YEAR_1_MONTHLY_RATE = Decimal('0.005')        # 0.50% monthly ≈ 6% annual
YEAR_2_PLUS_MONTHLY_RATE = Decimal('0.0025')  # 0.25% monthly ≈ 3% annual
MAXIMUM_VALUE_MULTIPLIER = Decimal('2.0')     # 200% ceiling of purchase price


def _calculate_months_owned(purchase_date, today):
    """Calculate months owned from purchase date (no DB column needed)."""
    if not purchase_date:
        return 0
    pd = purchase_date.date() if hasattr(purchase_date, 'date') else purchase_date
    return max(0, (today.year - pd.year) * 12 + (today.month - pd.month))


def _calculate_appreciation(asset, today):
    """
    Calculate appreciation for a single asset.
    Returns dict with new_value, appreciation_amount, and rate_used.
    """
    current_value = Decimal(str(asset.value or 0))
    purchase_price = Decimal(str(asset.purchase_price or 0))

    if purchase_price <= 0 or current_value <= 0:
        return {'new_value': float(current_value), 'appreciation_amount': 0, 'rate_used': 0}

    # Ceiling: asset value cannot exceed 200% of purchase price
    max_value = purchase_price * MAXIMUM_VALUE_MULTIPLIER
    if current_value >= max_value:
        return {'new_value': float(current_value), 'appreciation_amount': 0, 'rate_used': 0}

    # Determine rate based on age
    months_owned = _calculate_months_owned(asset.purchase_date, today)
    rate = YEAR_1_MONTHLY_RATE if months_owned < 12 else YEAR_2_PLUS_MONTHLY_RATE

    # Calculate new value
    appreciation_amount = current_value * rate
    new_value = current_value + appreciation_amount

    # Enforce ceiling
    if new_value > max_value:
        appreciation_amount = max_value - current_value
        new_value = max_value

    return {
        'new_value': float(new_value),
        'appreciation_amount': float(appreciation_amount),
        'rate_used': float(rate)
    }


def run_monthly_appreciation():
    """Run monthly appreciation update for all player assets."""
    logger.info("Starting monthly asset appreciation...")

    try:
        assets = UserAsset.query.all()
        today = date.today()

        updated_count = 0
        total_appreciation = Decimal('0')

        for asset in assets:
            result = _calculate_appreciation(asset, today)

            if result['appreciation_amount'] > 0:
                asset.value = Decimal(str(result['new_value']))
                total_appreciation += Decimal(str(result['appreciation_amount']))
                updated_count += 1

        db.session.commit()

        logger.info(
            f"Appreciation complete. "
            f"Updated: {updated_count} assets. "
            f"Total value increase: ${float(total_appreciation):,.2f}"
        )

        return {
            'updated_count': updated_count,
            'total_appreciation': float(total_appreciation),
            'date': today.isoformat()
        }

    except Exception as e:
        logger.error(f"Error running monthly appreciation: {str(e)}")
        return {'error': str(e)}


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        run_monthly_appreciation()
