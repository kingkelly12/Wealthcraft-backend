from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserLifeEvent(db.Model):
    __tablename__ = 'user_life_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    life_event_id = db.Column(UUID(as_uuid=True), nullable=False)
    choice_id = db.Column(UUID(as_uuid=True))
    was_auto_selected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'life_event_id': str(self.life_event_id),
            'choice_id': str(self.choice_id) if self.choice_id else None,
            'was_auto_selected': self.was_auto_selected
        }
