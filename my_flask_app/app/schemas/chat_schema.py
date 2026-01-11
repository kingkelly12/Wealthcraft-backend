"""
Pydantic schemas for chat operations
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional


class SendMessageRequest(BaseModel):
    """Request schema for sending a chat message"""
    recipient_id: UUID4 = Field(description="ID of the message recipient")
    content: str = Field(min_length=1, max_length=1000, description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "recipient_id": "123e4567-e89b-12d3-a456-426614174000",
                "content": "Hey! How's your investment portfolio doing?"
            }
        }


class SendMessageResponse(BaseModel):
    """Response schema for sending a message"""
    success: bool
    message: str
    message_id: Optional[UUID4] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Message sent successfully",
                "message_id": "987e6543-e21b-12d3-a456-426614174000"
            }
        }
