"""
Pydantic schemas for loan operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from decimal import Decimal


class LoanApplicationRequest(BaseModel):
    """Request schema for applying for a loan"""
    loan_id: UUID4 = Field(description="ID of the loan product")
    
    class Config:
        json_schema_extra = {
            "example": {
                "loan_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class LoanApplicationResponse(BaseModel):
    """Response schema for loan application"""
    success: bool
    message: str
    liability_id: Optional[UUID4] = None
    new_balance: Optional[Decimal] = None
    loan_amount: Optional[Decimal] = None
    monthly_payment: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Loan approved! You received $10,000",
                "liability_id": "987e6543-e21b-12d3-a456-426614174000",
                "new_balance": 60000.00,
                "loan_amount": 10000.00,
                "monthly_payment": 500.00
            }
        }
