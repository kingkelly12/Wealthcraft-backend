from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class LifeEvent(db.Model):
    __tablename__ = 'life_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # opportunity, challenge, neutral, emergency, etc.
    impact_cash = db.Column(db.Numeric(15, 2), default=0)
    impact_income = db.Column(db.Numeric(15, 2), default=0)
    impact_expenses = db.Column(db.Numeric(15, 2), default=0)
    impact_sanity = db.Column(db.Integer, default=0)
    impact_assets = db.Column(db.Text)
    time_limit_seconds = db.Column(db.Integer, default=604800)  # 7 days default
    icon_name = db.Column(db.String(50), default='Zap')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'event_type': self.event_type,
            'impact_cash': float(self.impact_cash) if self.impact_cash else 0,
            'impact_sanity': self.impact_sanity,
            'icon_name': self.icon_name,
            'is_active': self.is_active
        }
