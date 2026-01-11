from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class MentorMessage(db.Model):
    __tablename__ = 'mentor_messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mentor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('mentors.id'), nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)  # high_cash, high_debt, milestone, etc.
    message_template = db.Column(db.Text, nullable=False)
    cta_text = db.Column(db.String(100))
    cta_action = db.Column(db.String(50))  # navigate_to, open_modal, etc.
    trigger_conditions = db.Column(JSONB, default={}, nullable=False)  # JSON conditions
    min_net_worth = db.Column(db.Numeric(15, 2))
    max_net_worth = db.Column(db.Numeric(15, 2))
    priority = db.Column(db.Integer, default=1)  # 1=low, 5=high
    points_reward = db.Column(db.Integer, default=10)  # Points for following advice
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'mentor_id': str(self.mentor_id),
            'trigger_type': self.trigger_type,
            'message_template': self.message_template,
            'cta_text': self.cta_text,
            'cta_action': self.cta_action,
            'points_reward': self.points_reward
        }
