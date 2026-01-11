from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class IntegratedMissionEvent(db.Model):
    __tablename__ = 'integrated_mission_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), index=True)
    trigger_month = db.Column(db.Integer, nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)  # month, metric, probability
    trigger_condition = db.Column(db.Text)
    probability = db.Column(db.Float, default=1.0)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # market_event, personal_event, opportunity, crisis
    immediate_cash = db.Column(db.Numeric(15, 2), default=0)
    monthly_income_change = db.Column(db.Numeric(15, 2), default=0)
    asset_impact = db.Column(db.Numeric(15, 2), default=0)
    has_choices = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id) if self.mission_id else None,
            'trigger_month': self.trigger_month,
            'title': self.title,
            'event_type': self.event_type
        }
