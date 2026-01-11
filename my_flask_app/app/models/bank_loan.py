from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class BankLoan(db.Model):
    __tablename__ = 'bank_loans'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    borrower_id = db.Column(UUID(as_uuid=True), index=True)
    type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    term = db.Column(db.Integer, nullable=False)
    monthly_payment = db.Column(db.Numeric(15, 2), nullable=False)
    total_interest = db.Column(db.Numeric(15, 2), nullable=False)
    credit_required = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    collateral = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    funded_at = db.Column(db.DateTime(timezone=True))
    due_date = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            'id': str(self.id),
            'borrower_id': str(self.borrower_id) if self.borrower_id else None,
            'type': self.type,
            'amount': float(self.amount) if self.amount else 0,
            'interest_rate': float(self.interest_rate) if self.interest_rate else 0,
            'term': self.term,
            'monthly_payment': float(self.monthly_payment) if self.monthly_payment else 0,
            'credit_required': self.credit_required,
            'status': self.status
        }
