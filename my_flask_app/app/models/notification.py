from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # system, financial_move, wealth_milestone, achievement, follow
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    asset_id = db.Column(UUID(as_uuid=True))
    related_user_id = db.Column(UUID(as_uuid=True))
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
