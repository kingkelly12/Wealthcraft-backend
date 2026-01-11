from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

class RentalProperty(db.Model):
    __tablename__ = 'rental_properties'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    property_type = db.Column(db.String(100), nullable=False)
    monthly_rent = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    amenities = db.Column(ARRAY(db.Text), default=[])
    image_url = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'property_type': self.property_type,
            'monthly_rent': self.monthly_rent,
            'location': self.location,
            'amenities': self.amenities,
            'image_url': self.image_url
        }
