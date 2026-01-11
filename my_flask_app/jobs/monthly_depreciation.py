"""
Monthly Liability Depreciation Job
Updates the value of all player liabilities based on age
Run this monthly via cron or task scheduler (e.g., 1st of every month)
"""

from app import create_app, db
from app.services.liability_service import LiabilityService
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_monthly_depreciation():
    """Run monthly depreciation update for all active player liabilities"""
    app = create_app()
    
    with app.app_context():
        logger.info("Starting monthly liability depreciation...")
        
        try:
            # 1. Backfill any liabilities missing initial values (safety check)
            backfill_result = LiabilityService.backfill_existing_liabilities()
            if backfill_result['backfilled_count'] > 0:
                logger.info(f"Backfilled {backfill_result['backfilled_count']} liabilities with initial values")
            
            # 2. Apply monthly depreciation
            result = LiabilityService.apply_monthly_depreciation()
            
            logger.info(
                f"Depreciation complete. "
                f"Updated: {result['updated_count']} liabilities. "
                f"Total value reduction: ${result['total_depreciation']:,.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running monthly depreciation: {str(e)}")
            return {'error': str(e)}

if __name__ == '__main__':
    run_monthly_depreciation()
