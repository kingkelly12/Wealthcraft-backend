from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class PlayerMissionProgress(db.Model):
    __tablename__ = 'player_mission_progress'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    mission_id = db.Column(UUID(as_uuid=True), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    is_completed = db.Column(db.Boolean, default=False)
    is_failed = db.Column(db.Boolean, default=False)
    current_month = db.Column(db.Integer, default=1)
    started_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    completed_at = db.Column(db.DateTime(timezone=True))
    failed_at = db.Column(db.DateTime(timezone=True))
    abandoned_at = db.Column(db.DateTime(timezone=True))
    constraints_applied = db.Column(JSONB, default={}, nullable=False)
    game_state_snapshot = db.Column(JSONB, default={}, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('player_id', 'mission_id', name='unique_player_mission'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'mission_id': str(self.mission_id),
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'current_month': self.current_month,
            'started_at': self.started_at.isoformat() if self.started_at else None
        }
