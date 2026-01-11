"""
Pydantic schemas for rental operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from decimal import Decimal


class RentalRequest(BaseModel):
    """Request schema for renting a property"""
    property_id: UUID4 = Field(description="ID of the rental property")
    
    class Config:
        json_schema_extra = {
            "example": {
                "property_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class RentalResponse(BaseModel):
    """Response schema for renting a property"""
    success: bool
    message: str
    rental_id: Optional[UUID4] = None
    new_balance: Optional[Decimal] = None
    monthly_rent: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "You have successfully rented Luxury Apartment",
                "rental_id": "987e6543-e21b-12d3-a456-426614174000",
                "new_balance": 45000.00,
                "monthly_rent": 2000.00
            }
        }


class MoveOutResponse(BaseModel):
    """Response schema for moving out"""
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "You have moved out of Luxury Apartment"
            }
        }
