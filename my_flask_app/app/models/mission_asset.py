from datetime import datetime
from app import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

class MissionAsset(db.Model):
    __tablename__ = 'mission_assets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = db.Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_id = db.Column(db.String(100), nullable=False)  # References assets.id (string)
    recommendation_level = db.Column(db.String(50))  # required, recommended, optional, avoid
    allocation_percentage = db.Column(db.Numeric(5, 2))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('mission_id', 'asset_id', name='unique_mission_asset'),
    )

    def to_dict(self):
        return {
            'id': str(self.id),
            'mission_id': str(self.mission_id),
            'asset_id': self.asset_id,
            'recommendation_level': self.recommendation_level,
            'allocation_percentage': float(self.allocation_percentage) if self.allocation_percentage else None
        }
