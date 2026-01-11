from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class JobMarket(db.Model):
    __tablename__ = 'job_market'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    salary = db.Column(db.Numeric(15, 2), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    experience_months = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'industry': self.industry,
            'company': self.company,
            'salary': float(self.salary) if self.salary else 0,
            'level': self.level,
            'experience_months': self.experience_months
        }
