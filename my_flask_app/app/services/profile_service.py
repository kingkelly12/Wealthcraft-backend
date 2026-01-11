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
    def update_credit_score(user_id: uuid.UUID, credit_score: int) -> Optional[Profile]:
        """Update user's credit score"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.credit_score = max(300, min(850, credit_score))  # Clamp between 300-850
            db.session.commit()
        return profile
