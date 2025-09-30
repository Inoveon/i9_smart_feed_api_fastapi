import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import require_role, get_current_user
from app.dependencies.cache import invalidate, cache
from app.models.campaign import Campaign
from app.models.image import CampaignImage
from app.models.user import User
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from typing import Dict, Any


router = APIRouter()


@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    global_only: Optional[bool] = Query(None, description="Filtrar campanhas globais (True) ou específicas (False)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # Adicionar dependência de autenticação
):
    """
    Listar campanhas.
    
    **Parâmetros:**
    - `global_only=true`: Apenas campanhas globais (stations=[])
    - `global_only=false`: Apenas campanhas com estações específicas
    - Sem parâmetro: Todas as campanhas
    """
    try:
        query = db.query(Campaign).filter(Campaign.is_deleted == False)  # noqa: E712
        
        # Comentado temporariamente para debug
        # if global_only is not None:
        #     if global_only:
        #         # Campanhas globais: stations é vazio
        #         query = query.filter(Campaign.stations == [])
        #     else:
        #         # Campanhas específicas: stations não é vazio
        #         query = query.filter(Campaign.stations != [])
        
        items = query.order_by(Campaign.created_at.desc()).all()
        
        # Criar response manualmente para debug
        result = []
        for campaign in items:
            try:
                campaign_dict = {
                    'id': campaign.id,
                    'name': campaign.name,
                    'description': campaign.description,
                    'status': campaign.status,
                    'start_date': campaign.start_date,
                    'end_date': campaign.end_date,
                    'default_display_time': campaign.default_display_time or 5000,
                    'branches': campaign.branches or [],
                    'regions': campaign.regions or [],
                    'stations': campaign.stations or [],
                    'priority': campaign.priority or 0,
                    'is_deleted': campaign.is_deleted or False,
                    'created_by': campaign.created_by,
                    'created_at': campaign.created_at,
                    'updated_at': campaign.updated_at
                }
                result.append(CampaignResponse(**campaign_dict))
            except Exception as e:
                print(f"Erro ao criar CampaignResponse: {e}")
                print(f"Campaign data: {campaign.__dict__}")
                raise
        
        return result
    except Exception as e:
        print(f"Erro em list_campaigns: {e}")
        raise


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(["admin", "editor"]))])
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)):
    """
    Criar nova campanha.
    
    **Comportamento de Estações:**
    - `stations: []` ou não informado → Campanha global (todas as estações)
    - `stations: ["001", "002"]` → Campanha específica para essas estações
    
    Não é necessário campo adicional para indicar campanha global.
    """
    entity = Campaign(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        default_display_time=payload.default_display_time,
        branches=payload.branches,  # Códigos das filiais
        regions=payload.regions,    # Regiões (Norte, Sul, etc)
        stations=payload.stations,  # Se vazio = global
        priority=payload.priority,
        is_deleted=False,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    invalidate("active_by_station:*")
    return entity


@router.get("/active")
@cache(expire=120, key_prefix="active_all")
async def get_all_active(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    items = (
        db.query(Campaign)
        .filter(
            Campaign.is_deleted == False,  # noqa: E712
            Campaign.status == "active",
            Campaign.start_date <= now,
            Campaign.end_date >= now,
        )
        .order_by(Campaign.priority.desc(), Campaign.created_at.desc())
        .all()
    )
    return {
        "campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "default_display_time": c.default_display_time,
                "stations": c.stations,
                "priority": c.priority,
            }
            for c in items
        ],
        "total": len(items),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/active/{station_code}")
# @cache(expire=120, key_prefix="active_by_station")  # Temporariamente desabilitado para debug
async def active_by_station(station_code: str, db: Session = Depends(get_db)):
    """
    Retorna campanhas ativas para uma estação específica.
    
    Lógica de targeting hierárquico:
    1. Campanhas GLOBAIS (arrays vazias) - sempre incluídas
    2. Campanhas por REGIÃO - se a estação pertencer à região
    3. Campanhas por FILIAL - se a estação pertencer à filial  
    4. Campanhas por ESTAÇÃO - se a estação estiver na lista
    
    Args:
        station_code: Código da estação (ex: "001", "002", etc)
    """
    try:
        from app.models.station import Station
        from app.models.branch import Branch
        from sqlalchemy import func
        
        now = datetime.utcnow()
        
        # Buscar informações da estação
        station = db.query(Station).filter(
            Station.code == station_code,
            Station.is_active == True  # noqa: E712
        ).first()
        
        # Buscar todas as campanhas ativas
        all_campaigns = db.query(Campaign).filter(
            Campaign.is_deleted == False,  # noqa: E712
            Campaign.status == "active",
            Campaign.start_date <= now,
            Campaign.end_date >= now
        ).all()
        
        # Filtrar campanhas aplicáveis
        campaigns = []
        branch_code = None
        region = None
        
        if station:
            branch = station.branch
            branch_code = branch.code if branch else None
            region = branch.region if branch else None
        
        for campaign in all_campaigns:
            # 1. Campanha GLOBAL (todas arrays vazias ou None)
            branches = campaign.branches or []
            regions = campaign.regions or []
            stations = campaign.stations or []
            
            if not branches and not regions and not stations:
                campaigns.append(campaign)
                continue
            
            # Só continuar se temos estação válida
            if not station:
                continue
                
            # 2. Campanha REGIONAL
            if regions and not branches and not stations:
                if region in regions:
                    campaigns.append(campaign)
                continue
            
            # 3. Campanha por FILIAL (todas estações da filial)
            if branches and not stations:
                if branch_code in branches:
                    campaigns.append(campaign)
                continue
            
            # 4. Campanha por ESTAÇÃO específica
            if branches and stations:
                if branch_code in branches and station_code in stations:
                    campaigns.append(campaign)
        
        # Ordenar por prioridade e remover duplicatas
        seen = set()
        unique_campaigns = []
        for c in sorted(campaigns, key=lambda x: (-x.priority if x.priority else 0, x.created_at), reverse=True):
            if c.id not in seen:
                seen.add(c.id)
                unique_campaigns.append(c)
        campaigns = unique_campaigns
        
    except Exception as e:
        print(f"Erro em active_by_station: {e}")
        import traceback
        traceback.print_exc()
        campaigns = []
    
    return {
        "station_code": station_code,
        "branch_code": branch_code if station else None,
        "region": region if station else None,
        "campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "default_display_time": c.default_display_time,
                "priority": c.priority,
                "targeting_level": (
                    "global" if not c.branches and not c.regions and not c.stations else
                    "regional" if c.regions and not c.branches else
                    "branch" if c.branches and not c.stations else
                    "station"
                )
            }
            for c in campaigns
        ],
        "total": len(campaigns),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{id}", response_model=CampaignResponse)
def get_campaign(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Obter campanha específica por ID.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == id,
        Campaign.is_deleted == False  # noqa: E712
    ).first()
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Criar response manualmente
    campaign_dict = {
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'status': campaign.status,
        'start_date': campaign.start_date,
        'end_date': campaign.end_date,
        'default_display_time': campaign.default_display_time or 5000,
        'branches': campaign.branches or [],
        'regions': campaign.regions or [],
        'stations': campaign.stations or [],
        'priority': campaign.priority or 0,
        'is_deleted': campaign.is_deleted or False,
        'created_by': campaign.created_by,
        'created_at': campaign.created_at,
        'updated_at': campaign.updated_at
    }
    
    return CampaignResponse(**campaign_dict)


@router.put("/{campaign_id}", response_model=CampaignResponse,
            dependencies=[Depends(require_role(["admin", "editor"]))])
def update_campaign(campaign_id: str, payload: CampaignUpdate, db: Session = Depends(get_db)):
    entity = db.get(Campaign, campaign_id)
    if not entity or entity.is_deleted:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entity, field, value)
    db.commit()
    db.refresh(entity)
    invalidate("active_by_station:*")
    return entity


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(["admin"]))])
def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    entity = db.get(Campaign, campaign_id)
    if not entity or entity.is_deleted:
        return
    entity.is_deleted = True
    db.commit()
    invalidate("active_by_station:*")


@router.get("/{campaign_id}/metrics", summary="Métricas de uma campanha específica")
async def get_campaign_metrics(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna métricas detalhadas de uma campanha específica.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.is_deleted == False
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    
    # Total de imagens
    images_count = db.query(CampaignImage).filter(
        CampaignImage.campaign_id == campaign_id
    ).count()
    
    # Tempo total de exibição
    images = db.query(CampaignImage).filter(
        CampaignImage.campaign_id == campaign_id
    ).all()
    
    total_display_time = sum(
        img.display_time or campaign.default_display_time 
        for img in images
    )
    
    # Calcula duração da campanha
    campaign_duration = (campaign.end_date - campaign.start_date).days
    
    # Estima visualizações (simplificado - 1 ciclo a cada minuto)
    if total_display_time > 0:
        cycles_per_hour = 3600000 / total_display_time  # ms para hora
        estimated_views_per_day = cycles_per_hour * 24
        total_estimated_views = estimated_views_per_day * campaign_duration
    else:
        estimated_views_per_day = 0
        total_estimated_views = 0
    
    # Calcular status baseado em datas
    now = datetime.utcnow()
    if campaign.end_date < now:
        actual_status = "expired"
    elif campaign.start_date > now:
        actual_status = "scheduled"
    else:
        actual_status = campaign.status
    
    return {
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": actual_status,
            "priority": campaign.priority,
            "type": "global" if not campaign.stations else "specific",
            "created_by": str(campaign.created_by) if campaign.created_by else None
        },
        "duration": {
            "start_date": campaign.start_date.isoformat(),
            "end_date": campaign.end_date.isoformat(),
            "total_days": campaign_duration,
            "days_remaining": max(0, (campaign.end_date - now).days),
            "progress_percentage": min(100, round(((now - campaign.start_date).days / campaign_duration * 100) if campaign_duration > 0 else 0, 2))
        },
        "content": {
            "total_images": images_count,
            "total_display_time_ms": total_display_time,
            "average_display_time_ms": total_display_time / images_count if images_count > 0 else 0,
            "images_size_bytes": sum(img.size_bytes for img in images if img.size_bytes)
        },
        "reach": {
            "scope": "global" if not campaign.stations else "specific",
            "stations_count": len(campaign.stations) if campaign.stations else "all",
            "stations": campaign.stations[:10] if campaign.stations else [],
            "regions": campaign.regions if campaign.regions else [],
            "branches": campaign.branches if campaign.branches else []
        },
        "estimated_performance": {
            "views_per_day": round(estimated_views_per_day),
            "total_views": round(total_estimated_views),
            "cycles_per_hour": round(cycles_per_hour, 2) if total_display_time > 0 else 0,
            "note": "Estimativa baseada em exibição contínua"
        },
        "metadata": {
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat(),
            "last_activity": campaign.updated_at.isoformat()
        }
    }
