from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

class IntegratedMission(db.Model):
    __tablename__ = 'integrated_missions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    short_description = db.Column(db.Text)
    icon = db.Column(db.String(10), default='🎯')
    category = db.Column(db.String(50), nullable=False)  # career_path, investment, debt_management, etc.
    difficulty = db.Column(db.String(50), default='beginner', nullable=False)
    duration_months = db.Column(db.Integer, default=12, nullable=False)
    learning_objectives = db.Column(ARRAY(db.Text), default=[])
    affects_main_game = db.Column(db.Boolean, default=True, nullable=False)
    income_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    expense_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    can_change_job = db.Column(db.Boolean, default=True, nullable=False)
    can_buy_assets = db.Column(db.Boolean, default=True, nullable=False)
    can_take_loans = db.Column(db.Boolean, default=True, nullable=False)
    can_rent_property = db.Column(db.Boolean, default=True, nullable=False)
    can_sell_assets = db.Column(db.Boolean, default=True, nullable=False)
    can_buy_lifestyle_items = db.Column(db.Boolean, default=True, nullable=False)
    allowed_asset_types = db.Column(ARRAY(db.Text))
    max_loan_amount = db.Column(db.Numeric(15, 2))
    allowed_loan_types = db.Column(ARRAY(db.Text))
    max_monthly_spending = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'duration_months': self.duration_months,
            'icon': self.icon
        }
