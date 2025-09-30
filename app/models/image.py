from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base, TimestampMixin


class CampaignImage(Base, TimestampMixin):
    __tablename__ = "campaign_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    url = Column(String(500), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    display_time = Column(Integer)
    title = Column(String(255))
    description = Column(Text)
    active = Column(Boolean, default=True)
    size_bytes = Column(Integer)
    mime_type = Column(String(50))
    width = Column(Integer)
    height = Column(Integer)

    campaign = relationship("Campaign", backref="images")

