"""
Pydantic schemas for life event operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional


class LifeEventChoiceRequest(BaseModel):
    """Request schema for making a life event choice"""
    event_id: UUID4 = Field(description="ID of the life event")
    choice_id: UUID4 = Field(description="ID of the choice made")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "choice_id": "987e6543-e21b-12d3-a456-426614174000"
            }
        }


class LifeEventChoiceResponse(BaseModel):
    """Response schema for life event choice"""
    success: bool
    message: str
    outcome: Optional[str] = None
    balance_change: Optional[float] = None
    new_balance: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Choice processed successfully",
                "outcome": "You invested wisely and earned $5000!",
                "balance_change": 5000.00,
                "new_balance": 55000.00
            }
        }
