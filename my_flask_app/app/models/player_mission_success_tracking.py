from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PlayerMissionSuccessTracking(db.Model):
    __tablename__ = 'player_mission_success_tracking'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_mission_id = db.Column(UUID(as_uuid=True), index=True)
    criteria_id = db.Column(UUID(as_uuid=True), nullable=False)
    current_value = db.Column(db.Numeric(15, 2), default=0)
    is_met = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('player_mission_id', 'criteria_id', name='unique_player_criteria'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_mission_id': str(self.player_mission_id) if self.player_mission_id else None,
            'criteria_id': str(self.criteria_id),
            'current_value': float(self.current_value) if self.current_value else 0,
            'is_met': self.is_met
        }
