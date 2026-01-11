from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionCourse(db.Model):
    __tablename__ = 'mission_courses'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    course_id = db.Column(UUID(as_uuid=True), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    recommendation_level = db.Column(db.String(50))  # recommended, optional, avoid
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mission_id', 'course_id', name='unique_mission_course'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id),
            'course_id': str(self.course_id),
            'is_required': self.is_required,
            'recommendation_level': self.recommendation_level
        }
