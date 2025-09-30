"""
Modelo de Estação (Station).
"""
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class Station(Base):
    """Modelo de estação/posto."""
    __tablename__ = "stations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(10), nullable=False)  # "001", "002" - pode repetir entre filiais
    name = Column(String(255), nullable=False)  # "Posto Shell Centro"
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    branch = relationship("Branch", back_populates="stations")
    
    # Constraint: código único por filial
    __table_args__ = (
        UniqueConstraint('branch_id', 'code', name='_branch_station_uc'),
    )
    
    def __repr__(self):
        return f"<Station(code={self.code}, name={self.name}, branch_id={self.branch_id})>"