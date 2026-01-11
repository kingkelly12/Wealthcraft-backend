from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class LifeEventChoice(db.Model):
    __tablename__ = 'life_event_choices'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    life_event_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    choice_label = db.Column(db.String(255), nullable=False)
    outcome_description = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Numeric(15, 2), default=0)
    benefit = db.Column(db.Numeric(15, 2), default=0)
    choice_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'life_event_id': str(self.life_event_id),
            'choice_label': self.choice_label,
            'outcome_description': self.outcome_description,
            'cost': float(self.cost) if self.cost else 0,
            'benefit': float(self.benefit) if self.benefit else 0
        }
