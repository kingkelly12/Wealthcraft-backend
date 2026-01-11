"""
Pydantic schemas for education operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional
from decimal import Decimal


class CourseEnrollmentRequest(BaseModel):
    """Request schema for enrolling in a course"""
    course_id: UUID4 = Field(description="ID of the course to enroll in")
    
    class Config:
        json_schema_extra = {
            "example": {
                "course_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class CourseCompletionRequest(BaseModel):
    """Request schema for completing a course"""
    user_course_id: UUID4 = Field(description="ID of the user's course enrollment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_course_id": "987e6543-e21b-12d3-a456-426614174000"
            }
        }


class CourseEnrollmentResponse(BaseModel):
    """Response schema for course enrollment"""
    success: bool
    message: str
    enrollment_id: Optional[UUID4] = None
    new_balance: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "You have successfully enrolled in Python Programming",
                "enrollment_id": "987e6543-e21b-12d3-a456-426614174000",
                "new_balance": 45000.00,
                "cost": 500.00
            }
        }


class CourseCompletionResponse(BaseModel):
    """Response schema for course completion"""
    success: bool
    message: str
    salary_boost: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    new_balance: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Course completed! Your salary increased by $1000/mo",
                "salary_boost": 1000.00,
                "bonus": 2000.00,
                "new_balance": 47000.00
            }
        }
