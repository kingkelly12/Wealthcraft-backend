from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class PlayerMissionDecision(db.Model):
    __tablename__ = 'player_mission_decisions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_mission_id = db.Column(UUID(as_uuid=True), index=True)
    decision_point_id = db.Column(UUID(as_uuid=True), nullable=False)
    chosen_option_id = db.Column(UUID(as_uuid=True), nullable=False)
    month_made = db.Column(db.Integer, nullable=False)
    decision_data = db.Column(JSONB, default={})
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('player_mission_id', 'decision_point_id', name='unique_player_decision'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_mission_id': str(self.player_mission_id) if self.player_mission_id else None,
            'decision_point_id': str(self.decision_point_id),
            'chosen_option_id': str(self.chosen_option_id),
            'month_made': self.month_made
        }
