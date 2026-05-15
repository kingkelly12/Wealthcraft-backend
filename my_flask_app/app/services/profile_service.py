from app import db
from app.models.profile import Profile
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid

class ProfileService:
    @staticmethod
    def get_profile_by_user_id(user_id: uuid.UUID) -> Optional[Profile]:
        """Get profile by user ID"""
        return Profile.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create_profile(user_id: uuid.UUID, username: str) -> Profile:
        """Create a new profile"""
        try:
            profile = Profile(
                user_id=user_id,
                username=username
            )
            db.session.add(profile)
            db.session.commit()
            return profile
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Profile already exists or username is taken")

    @staticmethod
    def update_profile(user_id: uuid.UUID, **kwargs) -> Optional[Profile]:
        """Update profile fields"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None

        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        db.session.commit()
        return profile

    @staticmethod
    def update_net_worth(user_id: uuid.UUID, net_worth: float) -> Optional[Profile]:
        """Update user's net worth"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.net_worth = net_worth
            db.session.commit()
        return profile

    @staticmethod
    def recalculate_net_worth(user_id: uuid.UUID) -> float:
        """
        Calculates and updates the cached net_worth core field in the profiles table.
        This ensures the leaderboard (which reads from profiles.net_worth) is accurate.
        """
        from app import supabase
        from app.services.balance_service import BalanceService
        import time
        
        try:
            # 1. Get Balance
            balance = float(BalanceService.get_current_balance(str(user_id)))
            
            # 2. Get Assets - only select 'value' column (current_value doesn't exist in schema)
            assets_res = supabase.table('user_assets').select('value').eq('user_id', str(user_id)).execute()
            assets_total = sum(float(a.get('value') or 0) for a in (assets_res.data or []))
            
            # 3. Get Liabilities - use 'current_value' column (how much liability is currently owed)
            liabilities_res = supabase.table('player_liabilities').select('current_value').eq('player_id', str(user_id)).eq('is_active', True).execute()
            liabilities_total = sum(float(l.get('current_value') or 0) for l in (liabilities_res.data or []))
            
            # 4. Final Calculation
            net_worth = balance + assets_total - liabilities_total
            
            # 5. Update Profile
            ProfileService.update_net_worth(user_id, net_worth)
            
            return net_worth
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to recalculate net worth for {user_id}: {e}", exc_info=True)
            return 0.0

    @staticmethod
    def update_sanity(user_id: uuid.UUID, amount: int) -> Optional[Profile]:
        """Update user's sanity with clamping between 0-100"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            new_sanity = max(0, min(100, profile.sanity + amount))
            profile.sanity = new_sanity
            db.session.commit()
        return profile

    @staticmethod
    def update_monthly_income(user_id: uuid.UUID, amount: float) -> Optional[Profile]:
        """Update user's base monthly income (permanent change from boosts)"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.base_monthly_income = float(profile.base_monthly_income or 0) + amount
            db.session.commit()
            # After updating base, recalculate total
            ProfileService.recalculate_monthly_income(user_id)
        return profile

    @staticmethod
    def recalculate_monthly_income(user_id: uuid.UUID) -> float:
        """
        Calculates and updates the cached monthly_income core field in the profiles table.
        This ensures the leaderboard and all screens show the true total income.
        """
        from app import supabase
        
        try:
            profile = Profile.query.filter_by(user_id=user_id).first()
            if not profile:
                return 0.0

            # 1. Get Base Income (salary boosts)
            base_income = float(profile.base_monthly_income or 0)
            
            # 2. Get Job Salaries (annual / 12)
            jobs_res = supabase.table('jobs').select('salary').eq('user_id', str(user_id)).eq('is_current', True).execute()
            job_income = sum((float(j.get('salary') or 0) / 12.0) for j in (jobs_res.data or []))
            
            # 3. Get Passive Income from Assets
            assets_res = supabase.table('user_assets').select('quantity, asset_type, name').eq('user_id', str(user_id)).execute()
            asset_income = 0.0
            
            if assets_res.data:
                # We need to map user_assets to the base assets to get their monthly_income
                asset_names = [a.get('name') for a in assets_res.data if a.get('name')]
                if asset_names:
                    base_assets_res = supabase.table('assets').select('name, monthly_income').in_('name', asset_names).execute()
                    base_assets_map = {a.get('name'): float(a.get('monthly_income') or 0) for a in (base_assets_res.data or [])}
                    
                    for ua in assets_res.data:
                        name = ua.get('name')
                        qty = float(ua.get('quantity') or 1)
                        monthly_yield = base_assets_map.get(name, 0.0)
                        asset_income += (monthly_yield * qty)

            # 4. Final Calculation
            total_income = base_income + job_income + asset_income
            
            # 5. Update Profile
            profile.monthly_income = total_income
            db.session.commit()
            
            return total_income
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to recalculate monthly income for {user_id}: {e}", exc_info=True)
            return 0.0

    @staticmethod
    def update_credit_score(user_id: uuid.UUID, credit_score: int) -> Optional[Profile]:
        """Update user's credit score"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.credit_score = max(300, min(850, credit_score))  # Clamp between 300-850
            db.session.commit()
        return profile

    @staticmethod
    def update_trading_profits(user_id: uuid.UUID, amount: float) -> Optional[Profile]:
        """Update user's total trading profits (permanent change)"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.trading_profits = float(profile.trading_profits or 0) + amount
            db.session.commit()
        return profile
