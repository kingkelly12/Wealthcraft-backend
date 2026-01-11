from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserAsset(db.Model):
    __tablename__ = 'user_assets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_type = db.Column(db.String(50), nullable=False)  # stocks, property, retirement, cash, bonds, crypto
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric(15, 2), default=0, nullable=False)
    quantity = db.Column(db.Numeric(15, 4), default=1)
    purchase_price = db.Column(db.Numeric(15, 2))
    purchase_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'asset_type': self.asset_type,
            'name': self.name,
            'value': float(self.value) if self.value else 0,
            'quantity': float(self.quantity) if self.quantity else 1,
            'purchase_price': float(self.purchase_price) if self.purchase_price else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None
        }
