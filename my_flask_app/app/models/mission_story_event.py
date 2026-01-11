from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionStoryEvent(db.Model):
    __tablename__ = 'mission_story_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), index=True)
    title = db.Column(db.String(255), nullable=False)
    emoji = db.Column(db.String(10), default='📖')
    narrative = db.Column(db.Text, nullable=False)
    financial_context = db.Column(db.Text)
    story_type = db.Column(db.String(50), nullable=False)  # emotional, milestone, decision_point, crisis, etc.
    trigger_type = db.Column(db.String(50), nullable=False)  # mission_start, month, threshold, decision, custom
    trigger_value = db.Column(db.Integer)
    trigger_condition = db.Column(db.Text)
    probability = db.Column(db.Float, default=1.0)
    audio_cue = db.Column(db.String(50))  # decision, success, crisis, neutral, milestone
    background_image = db.Column(db.Text)
    mood_color = db.Column(db.String(50))
    happiness_change = db.Column(db.Integer, default=0)
    stress_change = db.Column(db.Integer, default=0)
    motivation_change = db.Column(db.Integer, default=0)
    immediate_cash = db.Column(db.Numeric(15, 2), default=0)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mission_id', 'display_order', name='unique_mission_display_order'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id) if self.mission_id else None,
            'title': self.title,
            'narrative': self.narrative,
            'story_type': self.story_type
        }
