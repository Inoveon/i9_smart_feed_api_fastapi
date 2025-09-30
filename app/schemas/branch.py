"""
Schemas para Branches (Filiais).
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.utils.regions import is_valid_state, get_region_by_state


class BranchBase(BaseModel):
    """Schema base para filial."""
    code: str = Field(..., min_length=2, max_length=10, description="Código da filial")
    name: str = Field(..., min_length=3, max_length=255, description="Nome da filial")
    city: Optional[str] = Field(None, max_length=100, description="Cidade")
    state: str = Field(..., min_length=2, max_length=2, description="Estado (UF)")
    is_active: bool = Field(True, description="Status ativo/inativo")
    
    @validator('state')
    def validate_state(cls, v):
        """Valida se o estado é válido."""
        if not is_valid_state(v):
            raise ValueError(f"Estado inválido: {v}")
        return v.upper()
    
    @validator('code')
    def validate_code(cls, v):
        """Valida e formata o código."""
        return v.upper().strip()


class BranchCreate(BranchBase):
    """Schema para criar filial."""
    pass


class BranchUpdate(BaseModel):
    """Schema para atualizar filial."""
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    is_active: Optional[bool] = None
    
    @validator('state')
    def validate_state(cls, v):
        """Valida se o estado é válido."""
        if v is not None and not is_valid_state(v):
            raise ValueError(f"Estado inválido: {v}")
        return v.upper() if v else v


class BranchResponse(BranchBase):
    """Schema de resposta para filial."""
    id: UUID
    region: str = Field(description="Região calculada pelo estado")
    created_at: datetime
    updated_at: datetime
    stations_count: int = Field(0, description="Quantidade de estações")
    
    class Config:
        from_attributes = True
        
    @validator('region', pre=False, always=True)
    def set_region(cls, v, values):
        """Define a região baseada no estado."""
        # Temporariamente retornar "Sudeste" para debug
        return v or "Sudeste"


class BranchWithStations(BranchResponse):
    """Schema de filial com suas estações."""
    stations: List["StationResponse"] = []


# Import circular prevention
from app.schemas.station import StationResponse
BranchWithStations.model_rebuild()


# Paginação
from app.schemas.pagination import PaginatedResponse

class PaginatedBranchResponse(PaginatedResponse[BranchResponse]):
    """Resposta paginada para listagem de filiais."""
    pass