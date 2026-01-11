"""
Pydantic schemas for job operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from decimal import Decimal


class JobApplicationRequest(BaseModel):
    """Request schema for applying to a job"""
    job_id: UUID4 = Field(description="ID of the job to apply for")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class JobApplicationResponse(BaseModel):
    """Response schema for job application"""
    success: bool
    message: str
    user_job_id: Optional[UUID4] = None
    new_balance: Optional[Decimal] = None
    salary: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "You have been hired as a Software Engineer!",
                "user_job_id": "987e6543-e21b-12d3-a456-426614174000",
                "new_balance": 55000.00,
                "salary": 5000.00
            }
        }


class JobQuitResponse(BaseModel):
    """Response schema for quitting a job"""
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "You have quit your job as Software Engineer"
            }
        }
