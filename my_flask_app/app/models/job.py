from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    salary = db.Column(db.Numeric(15, 2), default=0, nullable=False)
    level = db.Column(db.String(50), default='entry', nullable=False)
    experience_months = db.Column(db.Integer, default=0, nullable=False)
    promotion_progress = db.Column(db.Integer, default=0, nullable=False)
    is_current = db.Column(db.Boolean, default=True, nullable=False)
    work_hours_per_week = db.Column(db.Integer, default=40)  
    start_date = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'title': self.title,
            'company': self.company,
            'salary': float(self.salary) if self.salary else 0,
            'level': self.level,
            'is_current': self.is_current,
            'start_date': self.start_date.isoformat() if self.start_date else None
        }
