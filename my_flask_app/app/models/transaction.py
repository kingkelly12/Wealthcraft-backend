from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # income, expense, investment, loan_payment, loan_disbursement
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    transaction_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'category': self.category,
            'amount': float(self.amount) if self.amount else 0,
            'description': self.description,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
