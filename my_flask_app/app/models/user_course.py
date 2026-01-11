from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class UserCourse(db.Model):
    __tablename__ = 'user_courses'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)  # percentage
    completed_at = db.Column(db.DateTime(timezone=True))
    started_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'course_id', name='unique_user_course'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'course_id': str(self.course_id),
            'progress': self.progress,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
