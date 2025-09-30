"""
Endpoints para gerenciamento de Estações (Stations).
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_

from app.config.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.branch import Branch
from app.models.station import Station
from app.models.user import User
from app.models.campaign import Campaign
from app.schemas.station import (
    StationCreate,
    StationUpdate,
    StationResponse,
    StationWithBranch,
    StationWithCompactBranch,
    BranchCompact,
    PaginatedStationResponse
)
from app.schemas.pagination import PaginatedResponse


router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=PaginatedStationResponse, summary="Listar estações")
async def list_stations(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Busca por código ou nome"),
    sort: Optional[str] = Query("name", description="Campo para ordenação (name, code, created_at)"),
    order: Optional[str] = Query("asc", description="Ordem: asc ou desc"),
    branch_id: Optional[UUID] = Query(None, description="Filtrar por ID da filial"),
    branch_code: Optional[str] = Query(None, description="Filtrar por código da filial"),
    state: Optional[str] = Query(None, description="Filtrar por estado (através da filial)"),
    is_active: Optional[bool] = Query(None, description="Filtrar por status"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> PaginatedStationResponse:
    """
    Lista todas as estações com paginação e filtragem.
    
    Parâmetros de paginação:
    - page: Página atual (default: 1)
    - limit: Itens por página (default: 10, máx: 100)
    
    Filtros:
    - search: Busca por código ou nome da estação
    - branch_id: Filtrar por ID da filial
    - branch_code: Filtrar por código da filial
    - state: Filtrar por estado (através da filial)
    - is_active: Filtrar por status
    
    Ordenação:
    - sort: Campo para ordenação (name, code, created_at)
    - order: Direção (asc ou desc)
    """
    # Query base com join para branch
    query = db.query(Station).options(joinedload(Station.branch))
    
    # Aplicar busca
    if search:
        search_filter = or_(
            Station.code.ilike(f"%{search}%"),
            Station.name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Aplicar filtro por branch_id
    if branch_id:
        query = query.filter(Station.branch_id == branch_id)
    
    # Aplicar filtro por branch_code
    if branch_code:
        query = query.join(Branch).filter(Branch.code == branch_code.upper())
    
    # Aplicar filtro por estado (através da filial)
    if state:
        if not branch_code:  # Só fazer join se ainda não foi feito
            query = query.join(Branch)
        query = query.filter(Branch.state == state.upper())
    
    # Aplicar filtro de status
    if is_active is not None:
        query = query.filter(Station.is_active == is_active)
    
    # Contar total antes de paginar
    total = query.count()
    
    # Aplicar ordenação
    sort_column = {
        "name": Station.name,
        "code": Station.code,
        "created_at": Station.created_at
    }.get(sort, Station.name)
    
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column)
    
    # Aplicar paginação
    offset = (page - 1) * limit
    stations = query.offset(offset).limit(limit).all()
    
    # Preparar resposta com branch compacto
    items = []
    for station in stations:
        branch_compact = BranchCompact(
            code=station.branch.code,
            name=station.branch.name,
            state=station.branch.state
        ) if station.branch else None
        
        station_dict = {
            'id': station.id,
            'code': station.code,
            'name': station.name,
            'branch_id': station.branch_id,
            'branch': branch_compact,
            'address': station.address,
            'is_active': station.is_active,
            'created_at': station.created_at,
            'updated_at': station.updated_at
        }
        items.append(StationWithCompactBranch(**station_dict))
    
    # Retornar resposta paginada
    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=limit,
        total=total
    )


@router.get("/active", response_model=List[StationWithBranch], summary="Listar estações ativas")
async def list_active_stations(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> List[StationWithBranch]:
    """
    Lista apenas as estações ativas.
    """
    stations = db.query(Station).filter(Station.is_active == True).all()
    
    result = []
    for station in stations:
        station_dict = station.__dict__.copy()
        station_dict['branch'] = station.branch
        result.append(StationWithBranch(**station_dict))
    
    return result


@router.get("/by-branch-and-code/{branch_code}/{station_code}", response_model=StationWithBranch, summary="Buscar por filial e código")
async def get_station_by_codes(
    branch_code: str,
    station_code: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> StationWithBranch:
    """
    Busca uma estação pelo código da filial e código da estação.
    """
    branch = db.query(Branch).filter(Branch.code == branch_code.upper()).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Filial com código '{branch_code}' não encontrada"
        )
    
    station = db.query(Station).filter(
        and_(
            Station.branch_id == branch.id,
            Station.code == station_code
        )
    ).first()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estação '{station_code}' não encontrada na filial '{branch_code}'"
        )
    
    station_dict = station.__dict__.copy()
    station_dict['branch'] = branch
    
    return StationWithBranch(**station_dict)


@router.get("/available", summary="Estrutura completa de filiais e estações")
async def get_available_locations(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Retorna a estrutura completa de filiais e suas estações ativas.
    Útil para preencher seletores no frontend.
    """
    branches = db.query(Branch).filter(Branch.is_active == True).all()
    
    result = {
        "regions": {},
        "branches": {}
    }
    
    for branch in branches:
        # Adicionar à região
        region = branch.region
        if region not in result["regions"]:
            result["regions"][region] = []
        
        result["regions"][region].append({
            "code": branch.code,
            "name": branch.name,
            "state": branch.state
        })
        
        # Adicionar estações da filial
        stations = db.query(Station).filter(
            Station.branch_id == branch.id,
            Station.is_active == True
        ).all()
        
        result["branches"][branch.code] = {
            "name": branch.name,
            "state": branch.state,
            "region": region,
            "stations": [
                {
                    "code": station.code,
                    "name": station.name
                }
                for station in stations
            ]
        }
    
    return result


@router.get("/{station_id}", response_model=StationWithBranch, summary="Detalhes da estação")
async def get_station(
    station_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> StationWithBranch:
    """
    Obtém detalhes completos de uma estação.
    """
    station = db.query(Station).filter(Station.id == station_id).first()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estação não encontrada"
        )
    
    station_dict = station.__dict__.copy()
    station_dict['branch'] = station.branch
    
    return StationWithBranch(**station_dict)


@router.post("", response_model=StationResponse, status_code=status.HTTP_201_CREATED, summary="Criar estação")
async def create_station(
    station_data: StationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
) -> StationResponse:
    """
    Cria uma nova estação.
    
    Requer role: admin
    """
    # Verificar se a filial existe
    branch = db.query(Branch).filter(Branch.id == station_data.branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    # Verificar se o código já existe na filial
    existing = db.query(Station).filter(
        and_(
            Station.branch_id == station_data.branch_id,
            Station.code == station_data.code
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Estação com código '{station_data.code}' já existe na filial '{branch.code}'"
        )
    
    station = Station(**station_data.dict())
    db.add(station)
    db.commit()
    db.refresh(station)
    
    return StationResponse(**station.__dict__)


@router.put("/{station_id}", response_model=StationResponse, summary="Atualizar estação")
async def update_station(
    station_id: UUID,
    station_data: StationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
) -> StationResponse:
    """
    Atualiza uma estação existente.
    
    Requer role: admin
    """
    station = db.query(Station).filter(Station.id == station_id).first()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estação não encontrada"
        )
    
    # Atualizar campos
    update_dict = station_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(station, field, value)
    
    db.commit()
    db.refresh(station)
    
    return StationResponse(**station.__dict__)


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar estação")
async def delete_station(
    station_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["admin"]))
):
    """
    Desativa uma estação (soft delete).
    
    Requer role: admin
    Nota: Verifica se a estação está referenciada em campanhas ativas.
    """
    station = db.query(Station).filter(Station.id == station_id).first()
    
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estação não encontrada"
        )
    
    # Verificar se há campanhas ativas usando esta estação
    # Precisaríamos buscar o código da estação nas campanhas
    branch = station.branch
    active_campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False,
        Campaign.branches.any(branch.code),
        Campaign.stations.any(station.code)
    ).count()
    
    if active_campaigns > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Não é possível desativar estação referenciada em {active_campaigns} campanhas ativas"
        )
    
    station.is_active = False
    db.commit()


@router.get("/branches/{branch_id}/stations", response_model=List[StationResponse], summary="Estações de uma filial")
async def get_branch_stations(
    branch_id: UUID,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
) -> List[StationResponse]:
    """
    Lista todas as estações de uma filial específica.
    """
    # Verificar se a filial existe
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filial não encontrada"
        )
    
    query = db.query(Station).filter(Station.branch_id == branch_id)
    
    if is_active is not None:
        query = query.filter(Station.is_active == is_active)
    
    stations = query.all()
    
    return [StationResponse(**station.__dict__) for station in stations]