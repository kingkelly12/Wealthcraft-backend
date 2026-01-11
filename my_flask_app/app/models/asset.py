from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import ARRAY

class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    price_change = db.Column(db.Numeric(12, 2), default=0)
    price_change_percent = db.Column(db.Numeric(5, 2), default=0)
    monthly_income = db.Column(db.Numeric(12, 2), default=0)
    description = db.Column(db.Text)
    risk_level = db.Column(db.String(20), default='medium')  # low, medium, high
    roi = db.Column(db.Numeric(5, 2), default=0)
    time_to_return = db.Column(db.String(50), default='unknown')
    availability = db.Column(db.Integer, default=0)
    total_supply = db.Column(db.Integer, default=0)
    mission_prerequisites = db.Column(ARRAY(db.Text), default=[])
    recommended_for_mission = db.Column(ARRAY(db.Text), default=[])
    risk_education = db.Column(db.Text)
    educational_tier = db.Column(db.String(50), default='beginner')
    mission_only = db.Column(db.Boolean, default=False)
    unlocks_on_purchase = db.Column(ARRAY(db.Text), default=[])
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': float(self.price) if self.price else 0,
            'price_change': float(self.price_change) if self.price_change else 0,
            'monthly_income': float(self.monthly_income) if self.monthly_income else 0,
            'description': self.description,
            'risk_level': self.risk_level,
            'availability': self.availability
        }
