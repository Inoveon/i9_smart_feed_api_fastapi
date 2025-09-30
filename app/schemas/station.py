"""
Schemas para Stations (Estações).
"""
from datetime import datetime
from typing import Optional, ForwardRef
from uuid import UUID
from pydantic import BaseModel, Field, validator


BranchResponse = ForwardRef("BranchResponse")


class StationBase(BaseModel):
    """Schema base para estação."""
    code: str = Field(..., min_length=1, max_length=10, description="Código da estação")
    name: str = Field(..., min_length=3, max_length=255, description="Nome da estação")
    branch_id: UUID = Field(..., description="ID da filial")
    address: Optional[str] = Field(None, description="Endereço")
    is_active: bool = Field(True, description="Status ativo/inativo")
    
    @validator('code')
    def validate_code(cls, v):
        """Valida e formata o código."""
        return v.strip()


class StationCreate(StationBase):
    """Schema para criar estação."""
    pass


class StationUpdate(BaseModel):
    """Schema para atualizar estação."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class StationResponse(StationBase):
    """Schema de resposta para estação."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StationWithBranch(StationResponse):
    """Schema de estação com informações da filial."""
    branch: "BranchResponse"
    
    class Config:
        from_attributes = True


# Resolver referência circular
from app.schemas.branch import BranchResponse
StationWithBranch.model_rebuild()


class BranchCompact(BaseModel):
    """Schema compacto de filial para uso em listagens de estações."""
    code: str
    name: str
    state: str
    
    class Config:
        from_attributes = True


class StationWithCompactBranch(StationBase):
    """Schema de estação com informações compactas da filial."""
    id: UUID
    branch: BranchCompact
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Paginação
from app.schemas.pagination import PaginatedResponse

class PaginatedStationResponse(PaginatedResponse[StationWithCompactBranch]):
    """Resposta paginada para listagem de estações."""
    pass