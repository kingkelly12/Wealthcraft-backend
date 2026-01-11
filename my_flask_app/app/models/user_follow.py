from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserFollow(db.Model):
    __tablename__ = 'user_follows'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    follower_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    following_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'follower_id': str(self.follower_id),
            'following_id': str(self.following_id),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
