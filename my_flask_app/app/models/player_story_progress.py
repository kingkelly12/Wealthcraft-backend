from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class PlayerStoryProgress(db.Model):
    __tablename__ = 'player_story_progress'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_mission_id = db.Column(UUID(as_uuid=True), index=True)
    story_event_id = db.Column(UUID(as_uuid=True), index=True)
    has_triggered = db.Column(db.Boolean, default=False)
    has_been_viewed = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime(timezone=True))
    viewed_at = db.Column(db.DateTime(timezone=True))
    game_state_snapshot = db.Column(JSONB, default={})
    mission_month = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('player_mission_id', 'story_event_id', name='unique_player_story'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_mission_id': str(self.player_mission_id) if self.player_mission_id else None,
            'story_event_id': str(self.story_event_id) if self.story_event_id else None,
            'has_triggered': self.has_triggered,
            'has_been_viewed': self.has_been_viewed
        }
