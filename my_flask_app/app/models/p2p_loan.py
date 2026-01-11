from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class P2PLoan(db.Model):
    __tablename__ = 'p2p_loans'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lender_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    borrower_id = db.Column(UUID(as_uuid=True), index=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending, active, completed, defaulted
    monthly_payment = db.Column(db.Numeric(15, 2))
    collateral_amount = db.Column(db.Numeric(10, 2))
    next_payment_date = db.Column(db.DateTime(timezone=True))
    remaining_balance = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    funded_at = db.Column(db.DateTime(timezone=True))
    due_date = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            'id': str(self.id),
            'lender_id': str(self.lender_id),
            'borrower_id': str(self.borrower_id) if self.borrower_id else None,
            'amount': float(self.amount) if self.amount else 0,
            'interest_rate': float(self.interest_rate) if self.interest_rate else 0,
            'term_months': self.term_months,
            'status': self.status,
            'monthly_payment': float(self.monthly_payment) if self.monthly_payment else None
        }
