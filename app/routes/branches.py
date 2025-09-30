"""
Endpoints para gerenciamento de Filiais (Branches).
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.config.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.branch import Branch
from app.models.station import Station
from app.models.user import User
from app.schemas.branch import (
    BranchCreate,
    BranchUpdate,
    BranchResponse,
    BranchWithStations,
    PaginatedBranchResponse
)
from app.schemas.pagination import PaginatedResponse
from app.utils.regions import REGIONS, get_states_by_region


router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=PaginatedBranchResponse, summary="Listar filiais")
async def list_branches(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por código ou nome"),
    sort: Optional[str] = Query("name", description="Campo para ordenação (name, code, state, created_at)"),
    order: Optional[str] = Query("asc", description="Ordem: asc ou desc"),
    region: Optional[str] = Query(None, description="Filtrar por região"),
    state: Optional[str] = Query(None, description="Filtrar por estado (UF)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> PaginatedBranchResponse:
    """
    Lista todas as filiais com paginação e filtragem.
    
    Parâmetros de paginação:
    - page: Página atual (default: 1)
    - limit: Itens por página (default: 10, máx: 100)
    
    Filtros:
    - search: Busca por código ou nome
    - region: Filtrar por região (Norte, Sul, etc.)
    - state: Filtrar por estado (UF)
    - is_active: Filtrar por status
    
    Ordenação:
    - sort: Campo para ordenação (name, code, state, created_at)
    - order: Direção (asc ou desc)
    """
    # Query base
    query = db.query(Branch)
    
    # Aplicar busca
    if search:
        search_filter = or_(
            Branch.code.ilike(f"%{search}%"),
            Branch.name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Aplicar filtro de estado
    if state:
        query = query.filter(Branch.state == state.upper())
    
    # Aplicar filtro de região
    if region:
        if region not in REGIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Região inválida. Opções: {', '.join(REGIONS)}"
            )
        states = get_states_by_region(region)
        query = query.filter(Branch.state.in_(states))
    
    # Aplicar filtro de status
    if is_active is not None:
        query = query.filter(Branch.is_active == is_active)
    
    # Contar total antes de paginar
    total = query.count()
    
    # Aplicar ordenação
    sort_column = {
        "name": Branch.name,
        "code": Branch.code,
        "state": Branch.state,
        "created_at": Branch.created_at
    }.get(sort, Branch.name)
    
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)
    
    # Aplicar paginação
    offset = (page - 1) * limit
    branches = query.offset(offset).limit(limit).all()
    
    # Preparar resposta
    items = []
    for branch in branches:
        # Contar estações ativas
        stations_count = db.query(func.count(Station.id)).filter(
            Station.branch_id == branch.id,
            Station.is_active == True
        ).scalar()
        
        branch_dict = {
            'id': branch.id,
            'code': branch.code,
            'name': branch.name,
            'city': branch.city or "",
            'state': branch.state,
            'is_active': branch.is_active,
            'region': branch.region,
            'created_at': branch.created_at,
            'updated_at': branch.updated_at,
            'stations_count': stations_count
        }
        items.append(BranchResponse(**branch_dict))
    
    # Retornar resposta paginada
    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=limit,
        total=total
    )


@router.get("/regions", summary="Listar regiões e estados")
async def list_regions(
    user = Depends(get_current_user)
):
    """
    Lista todas as regiões e seus estados.
    """
    return {
        "regions": REGIONS,
        "states_by_region": {
            region: get_states_by_region(region)
            for region in REGIONS
        }
    }


@router.get("/active", response_model=List[BranchResponse], summary="Listar filiais ativas")
async def list_active_branches(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> List[BranchResponse]:
    """
    Lista apenas as filiais ativas.
    """
    branches = db.query(Branch).filter(Branch.is_active == True).all()
    
    result = []
    for branch in branches:
        # Criar dict manualmente
        branch_dict = {
            'id': branch.id,
            'code': branch.code,
            'name': branch.name,
            'city': branch.city or "",
            'state': branch.state,
            'is_active': branch.is_active,
            'region': branch.region,  # usar property
            'created_at': branch.created_at,
            'updated_at': branch.updated_at,
            'stations_count': db.query(func.count(Station.id)).filter(
                Station.branch_id == branch.id,
                Station.is_active == True
            ).scalar()
        }
        result.append(BranchResponse(**branch_dict))
    
    return result


@router.get("/by-code/{code}", response_model=BranchResponse, summary="Buscar filial por código")
async def get_branch_by_code(
    code: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> BranchResponse:
    """
    Busca uma filial pelo seu código.
    """
    branch = db.query(Branch).filter(Branch.code == code.upper()).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filial com código '{code}' não encontrada"
        )
    
    branch_dict = {
        'id': branch.id,
        'code': branch.code,
        'name': branch.name,
        'city': branch.city or "",
        'state': branch.state,
        'is_active': branch.is_active,
        'region': branch.region,
        'created_at': branch.created_at,
        'updated_at': branch.updated_at,
        'stations_count': db.query(func.count(Station.id)).filter(
            Station.branch_id == branch.id
        ).scalar()
    }
    
    return BranchResponse(**branch_dict)


@router.get("/{branch_id}", response_model=BranchWithStations, summary="Detalhes da filial")
async def get_branch(
    branch_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> BranchWithStations:
    """
    Obtém detalhes completos de uma filial, incluindo suas estações.
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    branch_dict = branch.__dict__.copy()
    branch_dict['stations'] = branch.stations
    branch_dict['stations_count'] = len(branch.stations)
    
    return BranchWithStations(**branch_dict)


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED, summary="Criar filial")
async def create_branch(
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
) -> BranchResponse:
    """
    Cria uma nova filial.
    
    Requer role: admin
    """
    # Verificar se o código já existe
    existing = db.query(Branch).filter(
        Branch.code == branch_data.code.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Filial com código '{branch_data.code}' já existe"
        )
    
    branch = Branch(**branch_data.dict())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    
    branch_dict = branch.__dict__.copy()
    branch_dict['stations_count'] = 0
    
    return BranchResponse(**branch_dict)


@router.put("/{branch_id}", response_model=BranchResponse, summary="Atualizar filial")
async def update_branch(
    branch_id: UUID,
    branch_data: BranchUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
) -> BranchResponse:
    """
    Atualiza uma filial existente.
    
    Requer role: admin
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    # Atualizar campos
    update_dict = branch_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(branch, field, value)
    
    db.commit()
    db.refresh(branch)
    
    branch_dict = branch.__dict__.copy()
    branch_dict['stations_count'] = db.query(func.count(Station.id)).filter(
        Station.branch_id == branch.id
    ).scalar()
    
    return BranchResponse(**branch_dict)


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar filial")
async def delete_branch(
    branch_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
):
    """
    Desativa uma filial (soft delete).
    
    Requer role: admin
    Nota: Não é possível deletar filiais com estações ativas.
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    # Verificar se há estações ativas
    active_stations = db.query(Station).filter(
        Station.branch_id == branch_id,
        Station.is_active == True
    ).count()
    
    if active_stations > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível desativar filial com {active_stations} estações ativas"
        )
    
    branch.is_active = False
    db.commit()


@router.get("/{branch_id}/statistics", summary="Estatísticas da filial")
async def get_branch_statistics(
    branch_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Obtém estatísticas de uma filial.
    """
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    # Contar estações
    total_stations = db.query(func.count(Station.id)).filter(
        Station.branch_id == branch_id
    ).scalar()
    
    active_stations = db.query(func.count(Station.id)).filter(
        Station.branch_id == branch_id,
        Station.is_active == True
    ).scalar()
    
    # TODO: Adicionar estatísticas de campanhas quando implementado
    
    return {
        "branch": {
            "id": str(branch.id),
            "code": branch.code,
            "name": branch.name,
            "state": branch.state,
            "region": branch.region
        },
        "stations": {
            "total": total_stations,
            "active": active_stations,
            "inactive": total_stations - active_stations
        },
        "campaigns": {
            "active": 0,  # TODO: Implementar
            "scheduled": 0,
            "total": 0
        }
    }