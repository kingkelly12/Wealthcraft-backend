from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class PlayerMentorInteraction(db.Model):
    __tablename__ = 'player_mentor_interactions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    mentor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('mentors.id'), nullable=False)
    message_id = db.Column(UUID(as_uuid=True), db.ForeignKey('mentor_messages.id'))
    message_content = db.Column(db.Text, nullable=False)  # Personalized message
    trigger_type = db.Column(db.String(50), nullable=False)
    player_data_snapshot = db.Column(JSONB, default={})  # Financial data at time of message
    sent_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime(timezone=True))
    action_taken = db.Column(db.Boolean, default=False)
    action_taken_at = db.Column(db.DateTime(timezone=True))
    points_earned = db.Column(db.Integer, default=0)
    relationship_score = db.Column(db.Integer, default=0)  # Running total with this mentor
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'mentor_id': str(self.mentor_id),
            'message_content': self.message_content,
            'trigger_type': self.trigger_type,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'action_taken': self.action_taken,
            'points_earned': self.points_earned,
            'relationship_score': self.relationship_score
        }
