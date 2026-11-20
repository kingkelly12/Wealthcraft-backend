from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime

class ProfileCreate(BaseModel):
    user_id: str
    username: constr(min_length=3, max_length=50) # type: ignore

class ProfileUpdate(BaseModel):
    # Only cosmetic fields are client-editable. Game stats (net worth, income,
    # credit score, sanity) are computed server-side and must never be accepted
    # from the client; extra keys are ignored.
    username: Optional[constr(min_length=3, max_length=50, pattern=r'^[A-Za-z0-9_.]+$')] = None # type: ignore
    profile_picture_url: Optional[constr(max_length=1000)] = None # type: ignore
    has_completed_onboarding: Optional[bool] = None

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    username: str
    net_worth: float
    monthly_income: float
    credit_score: int
    wealth_level: str
    experience_points: int
    has_completed_onboarding: bool
    profile_picture_url: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
