from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class VoidReaction(db.Model):
    __tablename__ = 'void_reactions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = db.Column(UUID(as_uuid=True), db.ForeignKey('void_posts.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('profiles.user_id', ondelete='CASCADE'), nullable=False)
    reaction_type = db.Column(db.String(10), nullable=False) # 'oof' or 'same'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Constraint to ensure one reaction per user per post handled via DB unique constraint, 
    # but good to document: UniqueConstraint(user_id, post_id)

    def to_dict(self):
        return {
            'id': str(self.id),
            'post_id': str(self.post_id),
            'user_id': str(self.user_id),
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat()
        }
