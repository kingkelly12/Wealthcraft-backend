from datetime import datetime, date
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PlayerLiability(db.Model):
    __tablename__ = 'player_liabilities'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    liability_id = db.Column(UUID(as_uuid=True), nullable=False)
    purchase_price = db.Column(db.Numeric(15, 2), nullable=False)
    monthly_cost = db.Column(db.Numeric(15, 2), nullable=False)
    purchase_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Depreciation tracking columns
    current_value = db.Column(db.Numeric(15, 2))
    last_depreciation_date = db.Column(db.Date)
    months_owned = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'liability_id': str(self.liability_id),
            'purchase_price': float(self.purchase_price) if self.purchase_price else 0,
            'monthly_cost': float(self.monthly_cost) if self.monthly_cost else 0,
            'current_value': float(self.current_value) if self.current_value else float(self.purchase_price) if self.purchase_price else 0,
            'last_depreciation_date': self.last_depreciation_date.isoformat() if self.last_depreciation_date else None,
            'months_owned': self.months_owned if self.months_owned is not None else 0,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'is_active': self.is_active
        }
