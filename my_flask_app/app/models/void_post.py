from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class VoidPost(db.Model):
    __tablename__ = 'void_posts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('profiles.user_id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    oof_count = db.Column(db.Integer, default=0)
    same_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('Profile', backref=db.backref('void_posts', lazy=True))
    reactions = db.relationship('VoidReaction', backref='post', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'content': self.content,
            'oof_count': self.oof_count,
            'same_count': self.same_count,
            'created_at': self.created_at.isoformat()
        }
