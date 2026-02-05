"""
Pydantic schemas for mentor-related API requests/responses
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import datetime


class MentorResponse(BaseModel):
    """Mentor NPC data"""
    id: str
    name: str
    role: str
    personality: str
    avatar_url: Optional[str] = None
    greeting_template: str
    created_at: datetime


class MentorInteractionResponse(BaseModel):
    """Player-Mentor interaction data"""
    id: str
    player_id: str
    mentor_id: str
    message_id: Optional[str] = None
    message_content: str
    trigger_type: str
    player_data_snapshot: Optional[Dict[str, Any]] = None
    sent_at: datetime
    read_at: Optional[datetime] = None
    action_taken: bool = False
    action_taken_at: Optional[datetime] = None
    points_earned: int = 0
    relationship_score: int = 0


class MarkAdviceFollowedResponse(BaseModel):
    """Response when player follows mentor advice"""
    success: bool
    points_earned: int
    mentor_id: str
    mentor_name: str
    new_relationship_score: int
    total_points: int


class MentorStatsResponse(BaseModel):
    """Player's overall mentor statistics"""
    total_messages: int
    messages_read: int
    advice_followed: int
    total_points: int
    engagement_rate: float
    action_rate: float
    mentor_scores: Dict[str, int]
