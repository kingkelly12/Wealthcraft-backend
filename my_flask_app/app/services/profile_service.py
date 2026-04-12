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
        
        try:
            # 1. Get Balance
            balance = float(BalanceService.get_current_balance(str(user_id)))
            
            # 2. Get Assets
            assets_res = supabase.table('user_assets').select('value, current_value').eq('user_id', str(user_id)).execute()
            assets_total = sum(float(a.get('current_value') or a.get('value') or 0) for a in (assets_res.data or []))
            
            # 3. Get Liabilities
            liabilities_res = supabase.table('player_liabilities').select('amount, current_value').eq('player_id', str(user_id)).eq('is_active', True).execute()
            liabilities_total = sum(float(l.get('current_value') or l.get('amount') or 0) for l in (liabilities_res.data or []))
            
            # 4. Final Calculation
            net_worth = balance + assets_total - liabilities_total
            
            # 5. Update Profile
            ProfileService.update_net_worth(user_id, net_worth)
            
            return net_worth
        except Exception as e:
            print(f"Failed to recalculate net worth for {user_id}: {e}")
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
        """Update user's monthly income (permanent change)"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.monthly_income = float(profile.monthly_income) + amount
            db.session.commit()
        return profile

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
