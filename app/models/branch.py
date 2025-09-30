"""
Modelo de Filial (Branch) com estado e região.
"""
from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.regions import get_region_by_state


class Branch(Base):
    """Modelo de filial."""
    __tablename__ = "branches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(10), unique=True, nullable=False, index=True)  # "SP", "RJ"
    name = Column(String(255), nullable=False)  # "São Paulo", "Rio de Janeiro"
    city = Column(String(100))
    state = Column(String(2), nullable=False, index=True)  # UF obrigatória
    # region é calculada dinamicamente baseada no state
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    stations = relationship("Station", back_populates="branch", cascade="all, delete-orphan")
    
    @property
    def region(self) -> str:
        """Retorna a região baseada no estado."""
        return get_region_by_state(self.state)
    
    def __repr__(self):
        return f"<Branch(code={self.code}, name={self.name}, state={self.state})>"