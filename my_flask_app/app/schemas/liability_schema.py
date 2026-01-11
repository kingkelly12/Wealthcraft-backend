"""
Pydantic schemas for liability operations
"""
from pydantic import BaseModel, Field, UUID4
from decimal import Decimal
from typing import Optional


class LiabilityPurchaseRequest(BaseModel):
    """Request schema for purchasing a liability item"""
    item_id: UUID4 = Field(description="ID of the liability item to purchase")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class LiabilityPurchaseResponse(BaseModel):
    """Response schema for liability purchase"""
    success: bool
    message: str
    liability_id: Optional[UUID4] = None
    new_balance: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully purchased Tesla Model 3",
                "liability_id": "987e6543-e21b-12d3-a456-426614174000",
                "new_balance": 45000.00,
                "purchase_price": 55000.00
            }
        }


class LiabilitySellResponse(BaseModel):
    """Response schema for selling a liability"""
    success: bool
    message: str
    sale_value: Optional[Decimal] = None
    new_balance: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully sold Tesla Model 3",
                "sale_value": 48000.00,
                "new_balance": 93000.00
            }
        }
