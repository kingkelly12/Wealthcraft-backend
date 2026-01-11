"""
Pydantic schemas for balance operations
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class BalanceAddRequest(BaseModel):
    """Request schema for adding balance"""
    amount: Decimal = Field(gt=0, description="Amount to add (must be positive)")
    reason: str = Field(min_length=3, max_length=200, description="Reason for adding balance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 1000.00,
                "reason": "Monthly salary payment"
            }
        }


class BalanceSubtractRequest(BaseModel):
    """Request schema for subtracting balance"""
    amount: Decimal = Field(gt=0, description="Amount to subtract (must be positive)")
    reason: str = Field(min_length=3, max_length=200, description="Reason for subtracting balance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 500.00,
                "reason": "Purchase of lifestyle item"
            }
        }


class BalanceResponse(BaseModel):
    """Response schema for balance operations"""
    success: bool
    new_balance: Decimal
    message: str
    transaction_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "new_balance": 5000.00,
                "message": "Balance updated successfully",
                "transaction_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
