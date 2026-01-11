from pydantic import BaseModel, Field, constr
from typing import Optional
from datetime import datetime

class ProfileCreate(BaseModel):
    user_id: str
    username: constr(min_length=3, max_length=50) # type: ignore

class ProfileUpdate(BaseModel):
    username: Optional[constr(min_length=3, max_length=50)] = None # type: ignore
    profile_picture_url: Optional[str] = None
    net_worth: Optional[float] = None
    monthly_income: Optional[float] = None
    credit_score: Optional[int] = Field(None, ge=300, le=850)

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    username: str
    net_worth: float
    monthly_income: float
    credit_score: int
    wealth_level: str
    experience_points: int
    profile_picture_url: str
    created_at: str

    class Config:
        from_attributes = True
