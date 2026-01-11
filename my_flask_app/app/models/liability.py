from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Liability(db.Model):
    __tablename__ = 'liabilities'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    liability_type = db.Column(db.String(100), nullable=False)  # credit_card, student_loan, mortgage, car_loan
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), default=0, nullable=False)
    monthly_payment = db.Column(db.Numeric(15, 2), default=0, nullable=False)
    due_date = db.Column(db.DateTime(timezone=True))
    p2p_loan_id = db.Column(UUID(as_uuid=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'liability_type': self.liability_type,
            'amount': float(self.amount) if self.amount else 0,
            'interest_rate': float(self.interest_rate) if self.interest_rate else 0,
            'monthly_payment': float(self.monthly_payment) if self.monthly_payment else 0
        }
