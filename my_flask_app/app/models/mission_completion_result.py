from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class MissionCompletionResult(db.Model):
    __tablename__ = 'mission_completion_results'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), nullable=False)
    player_mission_id = db.Column(UUID(as_uuid=True), nullable=False)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    completed = db.Column(db.Boolean, nullable=False)
    failed = db.Column(db.Boolean, nullable=False)
    abandoned = db.Column(db.Boolean, nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    net_worth_change = db.Column(db.Numeric(15, 2), nullable=False)
    income_change = db.Column(db.Numeric(15, 2), nullable=False)
    credit_score_change = db.Column(db.Integer, nullable=False)
    criteria_met = db.Column(db.Integer, nullable=False)
    criteria_total = db.Column(db.Integer, nullable=False)
    success_percentage = db.Column(db.Float, nullable=False)
    rewards_earned = db.Column(JSONB, default=[], nullable=False)
    total_cash_reward = db.Column(db.Numeric(15, 2), default=0, nullable=False)
    learning_score = db.Column(db.Integer)
    financial_iq_gain = db.Column(db.Integer)
    completion_message = db.Column(db.Text)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id),
            'player_id': str(self.player_id),
            'completed': self.completed,
            'success_percentage': self.success_percentage,
            'completion_message': self.completion_message
        }
