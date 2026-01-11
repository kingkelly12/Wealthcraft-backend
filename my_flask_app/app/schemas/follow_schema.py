"""
Pydantic schemas for follow operations
"""
from pydantic import BaseModel, Field, UUID4


class FollowUserRequest(BaseModel):
    """Request schema for following a user"""
    target_user_id: UUID4 = Field(description="ID of the user to follow")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_user_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class FollowUserResponse(BaseModel):
    """Response schema for follow/unfollow operations"""
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Successfully followed user"
            }
        }
