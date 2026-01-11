from datetime import datetime, date
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MonthlyDeduction(db.Model):
    __tablename__ = 'monthly_deductions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    deduction_type = db.Column(db.String(50), nullable=False)  # liability_cost, rent_payment
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reference_id = db.Column(UUID(as_uuid=True))  # player_liabilities.id or player_rentals.id
    deduction_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'deduction_type': self.deduction_type,
            'amount': float(self.amount) if self.amount else 0,
            'status': self.status,
            'deduction_date': self.deduction_date.isoformat() if self.deduction_date else None
        }
