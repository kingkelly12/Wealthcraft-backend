from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserBalance(db.Model):
    __tablename__ = 'user_balances'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    current_balance = db.Column(db.Numeric(15, 2), default=0, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'current_balance': float(self.current_balance) if self.current_balance else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
