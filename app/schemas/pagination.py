"""
Schemas para paginação padronizada da API.
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field
from math import ceil

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Resposta paginada padrão para todos os endpoints que retornam listas.
    """
    items: List[T]
    page: int = Field(ge=1, description="Página atual")
    page_size: int = Field(ge=1, le=100, description="Itens por página")
    total: int = Field(ge=0, description="Total de itens")
    total_pages: int = Field(ge=0, description="Total de páginas")
    has_next: bool = Field(description="Tem próxima página")
    has_prev: bool = Field(description="Tem página anterior")
    
    @classmethod
    def create(cls, items: List[T], page: int, page_size: int, total: int):
        """
        Factory method para criar resposta paginada.
        """
        total_pages = ceil(total / page_size) if page_size > 0 else 0
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginationParams(BaseModel):
    """
    Parâmetros de paginação comuns.
    """
    page: int = Field(default=1, ge=1, description="Número da página")
    limit: int = Field(default=10, ge=1, le=100, description="Itens por página")
    search: Optional[str] = Field(default=None, description="Texto de busca")
    sort: Optional[str] = Field(default=None, description="Campo para ordenação")
    order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Ordem: asc ou desc")
    
    @property
    def offset(self) -> int:
        """Calcula o offset para a query do banco."""
        return (self.page - 1) * self.limit