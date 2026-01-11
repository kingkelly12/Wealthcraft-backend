from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class MissionDecisionOption(db.Model):
    __tablename__ = 'mission_decision_options'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    decision_point_id = db.Column(UUID(as_uuid=True), index=True)
    label = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    game_action_type = db.Column(db.String(50))  # buy_asset, take_loan, change_job, sell_asset, custom, none
    game_action_data = db.Column(JSONB, default={})
    immediate_cash = db.Column(db.Numeric(15, 2), default=0)
    monthly_income_change = db.Column(db.Numeric(15, 2), default=0)
    monthly_expense_change = db.Column(db.Numeric(15, 2), default=0)
    asset_impact = db.Column(db.Numeric(15, 2), default=0)
    debt_impact = db.Column(db.Numeric(15, 2), default=0)
    happiness_change = db.Column(db.Integer, default=0)
    stress_change = db.Column(db.Integer, default=0)
    motivation_change = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(20), default='medium')
    success_probability = db.Column(db.Float)
    unlocks_decision_id = db.Column(UUID(as_uuid=True))
    blocks_decision_id = db.Column(UUID(as_uuid=True))
    affects_story = db.Column(db.Boolean, default=False)
    hidden = db.Column(db.Boolean, default=False)
    condition = db.Column(db.Text)
    option_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'decision_point_id': str(self.decision_point_id) if self.decision_point_id else None,
            'label': self.label,
            'description': self.description,
            'immediate_cash': float(self.immediate_cash) if self.immediate_cash else 0,
            'risk_level': self.risk_level
        }
