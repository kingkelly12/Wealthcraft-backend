from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionDecisionPoint(db.Model):
    __tablename__ = 'mission_decision_points'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), index=True)
    month = db.Column(db.Integer, nullable=False)
    is_required = db.Column(db.Boolean, default=True)
    auto_resolve_after_days = db.Column(db.Integer)
    auto_resolve_option_id = db.Column(UUID(as_uuid=True))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    learning_lesson = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mission_id', 'month', name='unique_mission_month'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id) if self.mission_id else None,
            'month': self.month,
            'title': self.title,
            'description': self.description
        }
