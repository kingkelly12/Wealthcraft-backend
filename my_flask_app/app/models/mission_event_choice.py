from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionEventChoice(db.Model):
    __tablename__ = 'mission_event_choices'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), index=True)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    financial_impact = db.Column(db.Numeric(15, 2), nullable=False)
    risk_level = db.Column(db.String(20))  # low, medium, high
    choice_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'event_id': str(self.event_id) if self.event_id else None,
            'label': self.label,
            'financial_impact': float(self.financial_impact) if self.financial_impact else 0,
            'risk_level': self.risk_level
        }
