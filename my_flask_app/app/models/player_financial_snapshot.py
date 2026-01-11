from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PlayerFinancialSnapshot(db.Model):
    __tablename__ = 'player_financial_snapshots'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    net_worth = db.Column(db.Numeric(15, 2), nullable=False)
    total_assets = db.Column(db.Numeric(15, 2), nullable=False)
    total_liabilities = db.Column(db.Numeric(15, 2), nullable=False)
    monthly_income = db.Column(db.Numeric(15, 2), nullable=False)
    cash_balance = db.Column(db.Numeric(15, 2), nullable=False)
    snapshot_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'net_worth': float(self.net_worth) if self.net_worth else 0,
            'total_assets': float(self.total_assets) if self.total_assets else 0,
            'total_liabilities': float(self.total_liabilities) if self.total_liabilities else 0,
            'monthly_income': float(self.monthly_income) if self.monthly_income else 0,
            'cash_balance': float(self.cash_balance) if self.cash_balance else 0,
            'snapshot_date': self.snapshot_date.isoformat() if self.snapshot_date else None
        }
