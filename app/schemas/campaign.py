from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID

from app.utils.regions import is_valid_region


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = Field(default="scheduled")
    start_date: datetime
    end_date: datetime
    default_display_time: Optional[int] = 5000
    branches: List[str] = Field(default_factory=list, description="Códigos das filiais")
    regions: List[str] = Field(default_factory=list, description="Regiões (Norte, Sul, etc.)")
    stations: List[str] = Field(default_factory=list, description="Códigos das estações")
    priority: Optional[int] = 0
    
    @validator('regions')
    def validate_regions(cls, v):
        """Valida se as regiões são válidas."""
        for region in v:
            if not is_valid_region(region):
                raise ValueError(f"Região inválida: {region}")
        return v
    
    @validator('stations')
    def validate_stations_require_branches(cls, v, values):
        """Valida que estações requerem filiais."""
        if v and not values.get('branches'):
            raise ValueError('Não pode ter estações sem filiais')
        return v


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    default_display_time: Optional[int] = None
    branches: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    stations: Optional[List[str]] = None
    priority: Optional[int] = None
    
    @validator('regions')
    def validate_regions(cls, v):
        """Valida se as regiões são válidas."""
        if v is not None:
            for region in v:
                if not is_valid_region(region):
                    raise ValueError(f"Região inválida: {region}")
        return v
    
    @validator('stations')
    def validate_stations_require_branches(cls, v, values):
        """Valida que estações requerem filiais."""
        if v and values.get('branches') is not None and not values.get('branches'):
            raise ValueError('Não pode ter estações sem filiais')
        return v
    is_deleted: Optional[bool] = None


class CampaignResponse(CampaignBase):
    id: UUID
    is_deleted: bool = False
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
