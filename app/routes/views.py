"""
Endpoints de visualizações e impressões para o dashboard.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import require_role
from app.models.campaign import Campaign
from app.models.image import CampaignImage

router = APIRouter(tags=["views"])

def calculate_views(campaigns: List[Campaign], period_hours: int = 24) -> int:
    """
    Calcula visualizações estimadas baseado em:
    - Número de campanhas ativas
    - Número de imagens
    - Tempo de display
    - Período em horas
    """
    total_views = 0
    
    for campaign in campaigns:
        # Assumir que cada ciclo completo de imagens = 1 view
        # E que tablets fazem refresh a cada 2 minutos (cache)
        cycles_per_hour = 30  # 60min / 2min cache
        
        # Considerar prioridade (maior prioridade = mais views)
        priority_multiplier = 1 + (campaign.priority / 100)
        
        # Estimar baseado em número de estações
        stations_count = len(campaign.stations) if campaign.stations else 10  # assumir 10 estações se global
        
        views_per_hour = cycles_per_hour * stations_count * priority_multiplier
        total_views += int(views_per_hour * period_hours)
    
    return total_views

@router.get("/views", summary="Métricas de visualizações totais")
async def get_total_views(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas de visualizações totais e estimativas.
    """
    # Campanhas ativas
    active_campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False
    ).all()
    
    # Calcular diferentes períodos
    views_today = calculate_views(active_campaigns, 24)
    views_this_hour = calculate_views(active_campaigns, 1)
    views_last_7_days = calculate_views(active_campaigns, 168)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "views": {
            "total_today": views_today,
            "total_this_hour": views_this_hour,
            "total_last_7_days": views_last_7_days,
            "average_per_hour": views_today // 24,
            "active_campaigns": len(active_campaigns)
        }
    }

@router.get("/views/{period}", summary="Métricas de visualizações por período")
async def get_views_by_period(
    period: str = "today",  # today, week, month
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas de visualizações para um período específico.
    """
    # Definir período
    now = datetime.utcnow()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours = (now - start_date).total_seconds() / 3600
    elif period == "week":
        start_date = now - timedelta(days=7)
        hours = 168
    elif period == "month":
        start_date = now - timedelta(days=30)
        hours = 720
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours = 24
    
    # Campanhas ativas no período
    campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False,
        Campaign.start_date <= now,
        Campaign.end_date >= start_date
    ).all()
    
    total_views = calculate_views(campaigns, hours)
    
    # Distribuição por hora (para gráfico)
    hourly_distribution = []
    if period == "today":
        for hour in range(24):
            hour_campaigns = [c for c in campaigns if c.created_at.hour <= hour]
            hour_views = calculate_views(hour_campaigns, 1)
            hourly_distribution.append({
                "hour": f"{hour:02d}:00",
                "count": hour_views if hour <= now.hour else 0
            })
    
    # Por campanha
    by_campaign = []
    for campaign in campaigns[:10]:  # Top 10
        campaign_views = calculate_views([campaign], hours)
        by_campaign.append({
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
            "views": campaign_views
        })
    
    # Por estação (simulado)
    by_station = []
    station_ids = set()
    for campaign in campaigns:
        if campaign.stations:
            station_ids.update(campaign.stations)
    
    for station_id in list(station_ids)[:10]:  # Top 10 estações
        station_campaigns = [c for c in campaigns if not c.stations or station_id in c.stations]
        station_views = calculate_views(station_campaigns, hours)
        by_station.append({
            "station_id": station_id,
            "views": station_views
        })
    
    return {
        "timestamp": now.isoformat(),
        "period": period,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "views": {
            "total": total_views,
            "by_hour": hourly_distribution if period == "today" else [],
            "by_campaign": sorted(by_campaign, key=lambda x: x["views"], reverse=True),
            "by_station": sorted(by_station, key=lambda x: x["views"], reverse=True)
        }
    }