from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionSuccessCriteria(db.Model):
    __tablename__ = 'mission_success_criteria'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), index=True)
    metric = db.Column(db.String(50), nullable=False)  # net_worth, monthly_income, debt_ratio, credit_score, etc.
    target = db.Column(db.Numeric(15, 2), nullable=False)
    comparison = db.Column(db.String(20), nullable=False)  # greater_than, less_than, equals, between
    target_min = db.Column(db.Numeric(15, 2))
    custom_metric_formula = db.Column(db.Text)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mission_id', 'metric', name='unique_mission_metric'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id) if self.mission_id else None,
            'metric': self.metric,
            'target': float(self.target) if self.target else 0,
            'comparison': self.comparison,
            'label': self.label
        }
