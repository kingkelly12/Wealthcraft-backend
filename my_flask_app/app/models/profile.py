from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Profile(db.Model):
    __tablename__ = 'profiles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    net_worth = db.Column(db.Numeric(15, 2), default=0)
    monthly_income = db.Column(db.Numeric(15, 2), default=0)
    credit_score = db.Column(db.Integer, default=650)
    wealth_level = db.Column(db.String(50), default='Beginner')
    experience_points = db.Column(db.Integer, default=0)
    profile_picture_url = db.Column(db.Text, default='https://example.com/default-profile.png')
    trading_profits = db.Column(db.Numeric(15, 2), default=0)
    push_token = db.Column(db.Text, nullable=True)
    push_token_updated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    income_sources_count = db.Column(db.Integer, default=1)
    monthly_savings = db.Column(db.Numeric(15, 2), default=0)
    engagement_days = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'username': self.username,
            'net_worth': float(self.net_worth) if self.net_worth else 0,
            'monthly_income': float(self.monthly_income) if self.monthly_income else 0,
            'credit_score': self.credit_score,
            'wealth_level': self.wealth_level,
            'experience_points': self.experience_points,
            'profile_picture_url': self.profile_picture_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
