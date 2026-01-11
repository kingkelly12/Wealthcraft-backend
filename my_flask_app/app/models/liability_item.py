from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class LiabilityItem(db.Model):
    __tablename__ = 'liability_items'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # car, motorbike, boat, yacht, helicopter, aircraft
    base_price = db.Column(db.Numeric(15, 2), nullable=False)
    monthly_cost = db.Column(db.Numeric(15, 2), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'category': self.category,
            'base_price': float(self.base_price) if self.base_price else 0,
            'monthly_cost': float(self.monthly_cost) if self.monthly_cost else 0,
            'description': self.description,
            'image_url': self.image_url
        }
