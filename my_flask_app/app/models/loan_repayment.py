from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class LoanRepayment(db.Model):
    __tablename__ = 'loan_repayments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = db.Column(UUID(as_uuid=True), index=True)
    amount = db.Column(db.Numeric(10, 2))
    due_date = db.Column(db.DateTime(timezone=True))
    payment_date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20))  # pending, paid, late, missed
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'loan_id': str(self.loan_id) if self.loan_id else None,
            'amount': float(self.amount) if self.amount else 0,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status
        }
