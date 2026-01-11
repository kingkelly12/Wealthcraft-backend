from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    recipient_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='sent', nullable=False)  # sent, delivered, read
    type = db.Column(db.String(20), default='text', nullable=False)  # text, file, image
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'sender_id': str(self.sender_id),
            'recipient_id': str(self.recipient_id),
            'content': self.content,
            'status': self.status,
            'type': self.type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
