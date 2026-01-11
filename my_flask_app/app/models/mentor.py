from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Mentor(db.Model):
    __tablename__ = 'mentors'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # strategic, risk_analyst, emotional
    personality = db.Column(db.Text, nullable=False)
    avatar_url = db.Column(db.Text)
    greeting_template = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'role': self.role,
            'personality': self.personality,
            'avatar_url': self.avatar_url,
            'greeting_template': self.greeting_template
        }
