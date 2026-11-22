"""
Pydantic schemas for loan operations
"""
from pydantic import BaseModel, Field, UUID4


class LoanApplicationRequest(BaseModel):
    """Request schema for applying for a loan"""
    loan_id: UUID4 = Field(description="ID of the loan product")
    
    class Config:
        json_schema_extra = {
            "example": {
                "loan_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
