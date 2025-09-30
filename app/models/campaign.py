from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, ENUM as PGEnum
import uuid
import enum

from app.models.base import Base, TimestampMixin


class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    EXPIRED = "expired"


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    status = Column(PGEnum("active", "scheduled", "paused", "expired", name="campaignstatus", create_type=False), default="scheduled", index=True)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    default_display_time = Column(Integer, default=5000)
    branches = Column(ARRAY(String), default=list)  # Códigos das filiais
    regions = Column(ARRAY(String), default=list)  # Regiões (Norte, Sul, etc.)
    stations = Column(ARRAY(String), default=list)  # Códigos das estações
    priority = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True))
