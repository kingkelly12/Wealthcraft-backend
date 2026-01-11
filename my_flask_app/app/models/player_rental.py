from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class PlayerRental(db.Model):
    __tablename__ = 'player_rentals'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    player_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    property_id = db.Column(UUID(as_uuid=True), nullable=False)
    monthly_rent = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    rented_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime(timezone=True))

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player_id),
            'property_id': str(self.property_id),
            'monthly_rent': self.monthly_rent,
            'is_active': self.is_active,
            'rented_at': self.rented_at.isoformat() if self.rented_at else None
        }
