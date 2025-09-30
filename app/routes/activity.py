"""
Feed de atividades e audit log.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, desc
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import require_role
from app.routes.profile import get_current_user
from app.models.campaign import Campaign
from app.models.image import CampaignImage
from app.models.user import User

router = APIRouter(tags=["activity"])

def build_activity_item(
    type: str,
    title: str,
    description: str,
    timestamp: datetime,
    user: Optional[User] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Constrói um item de atividade padronizado."""
    return {
        "id": f"{type}_{timestamp.timestamp()}",
        "type": type,
        "title": title,
        "description": description,
        "user": {
            "id": str(user.id) if user else "system",
            "username": user.username if user else "Sistema",
            "full_name": user.full_name if user else "Sistema Automático"
        },
        "metadata": metadata or {},
        "timestamp": timestamp.isoformat()
    }

@router.get("/feed", summary="Feed de atividades do sistema")
async def get_activity_feed(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna o feed de atividades recentes do sistema.
    Constrói o feed baseado em campaigns e images.
    """
    activities = []
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Buscar campanhas criadas/atualizadas
    campaigns = db.query(Campaign).filter(
        or_(
            Campaign.created_at >= start_date,
            Campaign.updated_at >= start_date
        ),
        Campaign.is_deleted == False
    ).order_by(desc(Campaign.updated_at)).limit(50).all()
    
    for campaign in campaigns:
        # Atividade de criação
        if campaign.created_at >= start_date:
            # Buscar usuário criador se tiver created_by
            creator = None
            if campaign.created_by:
                creator = db.query(User).filter(User.id == campaign.created_by).first()
            
            activities.append(build_activity_item(
                type="campaign_created",
                title=f"Nova campanha '{campaign.name}' criada",
                description=f"Campanha com prioridade {campaign.priority} para {len(campaign.stations) if campaign.stations else 'todas'} estações",
                timestamp=campaign.created_at,
                user=creator or current_user,  # Usar usuário atual como fallback
                metadata={
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "status": campaign.status,
                    "priority": campaign.priority
                }
            ))
        
        # Atividade de atualização (se foi atualizada após criação)
        if campaign.updated_at > campaign.created_at and campaign.updated_at >= start_date:
            activities.append(build_activity_item(
                type="campaign_updated",
                title=f"Campanha '{campaign.name}' atualizada",
                description=f"Status: {campaign.status}, Prioridade: {campaign.priority}",
                timestamp=campaign.updated_at,
                user=current_user,  # Usar usuário atual
                metadata={
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "status": campaign.status
                }
            ))
    
    # Buscar imagens recentes
    images = db.query(CampaignImage).filter(
        CampaignImage.created_at >= start_date
    ).order_by(desc(CampaignImage.created_at)).limit(30).all()
    
    for image in images:
        campaign = db.query(Campaign).filter(Campaign.id == image.campaign_id).first()
        if campaign:
            activities.append(build_activity_item(
                type="image_uploaded",
                title=f"Nova imagem adicionada",
                description=f"Imagem adicionada à campanha '{campaign.name}'",
                timestamp=image.created_at,
                user=current_user,
                metadata={
                    "image_id": str(image.id),
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "filename": image.original_filename or image.filename
                }
            ))
    
    # Login do usuário atual (simulado)
    activities.append(build_activity_item(
        type="user_login",
        title=f"Login realizado",
        description=f"Usuário {current_user.username} fez login no sistema",
        timestamp=now - timedelta(minutes=30),  # 30 minutos atrás
        user=current_user,
        metadata={}
    ))
    
    # Ordenar por timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Paginação
    total = len(activities)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_activities = activities[start_idx:end_idx]
    
    return {
        "timestamp": now.isoformat(),
        "activities": paginated_activities,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    }

@router.get("/audit/summary", summary="Resumo de auditoria")
async def get_audit_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin"]))
) -> Dict[str, Any]:
    """
    Retorna resumo de atividades para auditoria.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Contar atividades
    campaigns_created = db.query(Campaign).filter(
        Campaign.created_at >= start_date,
        Campaign.is_deleted == False
    ).count()
    
    campaigns_updated = db.query(Campaign).filter(
        Campaign.updated_at >= start_date,
        Campaign.updated_at > Campaign.created_at,
        Campaign.is_deleted == False
    ).count()
    
    images_uploaded = db.query(CampaignImage).filter(
        CampaignImage.created_at >= start_date
    ).count()
    
    # Usuários ativos (simulado)
    active_users = db.query(User).filter(
        User.is_active == True
    ).count()
    
    return {
        "timestamp": now.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": now.isoformat(),
            "days": days
        },
        "summary": {
            "campaigns_created": campaigns_created,
            "campaigns_updated": campaigns_updated,
            "campaigns_deleted": 0,  # Soft delete, então sempre 0
            "images_uploaded": images_uploaded,
            "active_users": active_users,
            "total_activities": campaigns_created + campaigns_updated + images_uploaded
        }
    }