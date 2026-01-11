from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100), nullable=False)  # finance, career, investing
    difficulty = db.Column(db.String(50), default='beginner', nullable=False)
    duration_hours = db.Column(db.Integer, default=1, nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    salary_boost = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    mission_prerequisites = db.Column(ARRAY(db.Text), default=[])
    unlocks_assets = db.Column(ARRAY(db.Text), default=[])
    mission_only = db.Column(db.Boolean, default=False)
    difficulty_rating = db.Column(db.Integer, default=1)
    learning_path = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'difficulty': self.difficulty,
            'duration_hours': self.duration_hours,
            'cost': float(self.cost) if self.cost else 0,
            'salary_boost': float(self.salary_boost) if self.salary_boost else 0
        }
