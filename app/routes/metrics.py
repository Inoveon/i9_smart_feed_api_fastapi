"""
Endpoints de métricas e monitoramento.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import require_role
from app.routes.profile import get_current_user
from app.models.campaign import Campaign
from app.models.image import CampaignImage
from app.models.user import User


router = APIRouter(tags=["metrics"])


@router.get("/dashboard", summary="Métricas do dashboard")
async def dashboard_metrics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas gerais para o dashboard principal.
    
    Inclui:
    - Total de campanhas por status
    - Total de imagens
    - Campanhas criadas nos últimos 7/30 dias
    - Top campanhas por prioridade
    """
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    
    # Total de campanhas por status
    total_active = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False
    ).count()
    
    total_scheduled = db.query(Campaign).filter(
        Campaign.status == "scheduled",
        Campaign.is_deleted == False
    ).count()
    
    total_paused = db.query(Campaign).filter(
        Campaign.status == "paused",
        Campaign.is_deleted == False
    ).count()
    
    total_expired = db.query(Campaign).filter(
        Campaign.status == "expired",
        Campaign.is_deleted == False
    ).count()
    
    # Total de imagens
    total_images = db.query(CampaignImage).count()
    
    # Campanhas criadas recentemente
    recent_7days = db.query(Campaign).filter(
        Campaign.created_at >= seven_days_ago,
        Campaign.is_deleted == False
    ).count()
    
    recent_30days = db.query(Campaign).filter(
        Campaign.created_at >= thirty_days_ago,
        Campaign.is_deleted == False
    ).count()
    
    # Top 5 campanhas por prioridade
    top_campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False
    ).order_by(Campaign.priority.desc()).limit(5).all()
    
    # Total de usuários
    total_users = db.query(User).filter(User.is_active == True).count()
    
    # Campanhas globais vs específicas
    global_campaigns = db.query(Campaign).filter(
        Campaign.stations == [],
        Campaign.is_deleted == False
    ).count()
    
    specific_campaigns = db.query(Campaign).filter(
        Campaign.stations != [],
        Campaign.is_deleted == False
    ).count()
    
    return {
        "timestamp": now.isoformat(),
        "overview": {
            "total_campaigns": total_active + total_scheduled + total_paused,
            "total_active": total_active,
            "total_scheduled": total_scheduled,
            "total_paused": total_paused,
            "total_expired": total_expired,
            "total_images": total_images,
            "total_users": total_users
        },
        "campaigns_by_type": {
            "global": global_campaigns,
            "specific": specific_campaigns
        },
        "recent_activity": {
            "last_7_days": recent_7days,
            "last_30_days": recent_30days
        },
        "top_priority_campaigns": [
            {
                "id": str(c.id),
                "name": c.name,
                "priority": c.priority,
                "stations_count": len(c.stations) if c.stations else "global"
            }
            for c in top_campaigns
        ]
    }


@router.get("/campaigns/{campaign_id}", summary="Métricas de uma campanha")
async def campaign_metrics(
    campaign_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas detalhadas de uma campanha específica.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.is_deleted == False
    ).first()
    
    if not campaign:
        return {"error": "Campanha não encontrada"}
    
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
    
    return {
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "priority": campaign.priority,
            "type": "global" if not campaign.stations else "specific"
        },
        "duration": {
            "start_date": campaign.start_date.isoformat(),
            "end_date": campaign.end_date.isoformat(),
            "total_days": campaign_duration,
            "days_remaining": max(0, (campaign.end_date - datetime.utcnow()).days)
        },
        "content": {
            "total_images": images_count,
            "total_display_time_ms": total_display_time,
            "average_display_time_ms": total_display_time / images_count if images_count > 0 else 0
        },
        "reach": {
            "stations_count": len(campaign.stations) if campaign.stations else "all",
            "stations": campaign.stations[:10] if campaign.stations else []  # Limita a 10 para não sobrecarregar
        },
        "estimated_performance": {
            "views_per_day": round(estimated_views_per_day),
            "total_views": round(total_estimated_views),
            "note": "Estimativa baseada em exibição contínua"
        }
    }


@router.get("/stations", summary="Métricas por estação")
async def stations_metrics(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas de utilização por estação.
    """
    from app.utils.regions import REGIONS_MAPPING
    
    # Busca todas as campanhas ativas
    active_campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False
    ).all()
    
    # Conta campanhas por estação e região
    station_usage = {}
    global_campaigns_count = 0
    stations_by_region = {region: set() for region in REGIONS_MAPPING.keys()}
    
    for campaign in active_campaigns:
        if not campaign.stations:  # Campanha global
            global_campaigns_count += 1
        else:
            for station_id in campaign.stations:
                if station_id not in station_usage:
                    station_usage[station_id] = {
                        "station_id": station_id,
                        "campaigns_count": 0,
                        "campaigns": []
                    }
                station_usage[station_id]["campaigns_count"] += 1
                station_usage[station_id]["campaigns"].append({
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "priority": campaign.priority
                })
                
                # Identificar região pela UF do station_id
                # Assumindo formato: UF-CIDADE-XXX (ex: SP-CAMPINAS-001)
                if "-" in station_id:
                    uf = station_id.split("-")[0]
                    for region, ufs in REGIONS_MAPPING.items():
                        if uf in ufs:
                            stations_by_region[region].add(station_id)
                            break
    
    # Contar total de estações (simulado - em produção viria do DB)
    total_stations = 100  # Placeholder - deveria vir de uma tabela de stations
    active_stations = len(station_usage)
    
    # Calcular cobertura
    coverage_percentage = round((active_stations / total_stations * 100) if total_stations > 0 else 0, 2)
    
    # Contar estações por região
    stations_count_by_region = {
        region: len(stations) 
        for region, stations in stations_by_region.items()
    }
    
    # Ordena por uso
    sorted_stations = sorted(
        station_usage.values(),
        key=lambda x: x["campaigns_count"],
        reverse=True
    )
    
    # Top 10 estações mais usadas
    top_stations = sorted_stations[:10]
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "stations": {
            "active": active_stations,
            "total": total_stations,
            "with_campaigns": len(station_usage),
            "global_campaigns": global_campaigns_count,
            "by_region": stations_count_by_region
        },
        "coverage": {
            "percentage": coverage_percentage,
            "stations_with_campaigns": list(station_usage.keys())[:50],
            "note": "Campanhas globais aplicam-se a todas as estações"
        },
        "top_stations": [
            {
                "station_id": s["station_id"],
                "campaigns_count": s["campaigns_count"],
                "campaigns": s["campaigns"][:3]  # Top 3 campanhas
            }
            for s in top_stations
        ]
    }


@router.get("/activity", summary="Métricas de atividade")
async def activity_metrics(
    days: int = Query(7, ge=1, le=90, description="Número de dias para análise"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna métricas de atividade do sistema nos últimos N dias.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Campanhas criadas e atualizadas por dia
    campaigns_activity = db.execute(text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as created,
            0 as updated
        FROM campaigns
        WHERE created_at >= :start_date
            AND is_deleted = false
        GROUP BY DATE(created_at)
        
        UNION ALL
        
        SELECT 
            DATE(updated_at) as date,
            0 as created,
            COUNT(*) as updated
        FROM campaigns
        WHERE updated_at >= :start_date
            AND updated_at != created_at
            AND is_deleted = false
        GROUP BY DATE(updated_at)
    """), {"start_date": start_date}).fetchall()
    
    # Agrupar por data
    campaigns_by_date = {}
    for row in campaigns_activity:
        date_str = str(row[0])
        if date_str not in campaigns_by_date:
            campaigns_by_date[date_str] = {"date": date_str, "created": 0, "updated": 0}
        campaigns_by_date[date_str]["created"] += row[1]
        campaigns_by_date[date_str]["updated"] += row[2]
    
    # Imagens uploadadas por dia
    images_by_day = db.execute(text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM campaign_images
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """), {"start_date": start_date}).fetchall()
    
    # Status changes (simplificado - baseado em updated_at)
    status_changes = db.execute(text("""
        SELECT 
            status,
            COUNT(*) as count
        FROM campaigns
        WHERE updated_at >= :start_date
            AND is_deleted = false
        GROUP BY status
    """), {"start_date": start_date}).fetchall()
    
    # Formatar resposta conforme esperado pelo frontend
    return {
        "timestamp": now.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": now.isoformat(),
            "days": days
        },
        "campaigns_activity": {
            "daily": sorted(
                campaigns_by_date.values(),
                key=lambda x: x["date"],
                reverse=True
            )
        },
        "images_activity": {
            "daily": [
                {
                    "date": str(row[0]),
                    "uploaded": row[1]
                }
                for row in images_by_day
            ]
        },
        "status_distribution": {
            row[0]: row[1]
            for row in status_changes
        }
    }


@router.get("/system", summary="Métricas do sistema")
async def system_metrics() -> Dict[str, Any]:
    """
    Retorna métricas de performance do sistema.
    """
    import psutil
    import os
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Memória
    memory = psutil.virtual_memory()
    
    # Disco
    disk = psutil.disk_usage('/')
    
    # Processos Python
    current_process = psutil.Process(os.getpid())
    process_memory = current_process.memory_info()
    
    # Network (se disponível)
    net_io = psutil.net_io_counters()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "cpu": {
            "usage_percent": cpu_percent,
            "cores": cpu_count,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        },
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent
        },
        "process": {
            "memory_mb": round(process_memory.rss / (1024**2), 2),
            "cpu_percent": current_process.cpu_percent(),
            "threads": current_process.num_threads()
        },
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    }


@router.get("/activity/detailed", summary="Métricas de atividade detalhadas")
async def detailed_activity_metrics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retorna métricas de atividade detalhadas com informações de usuário e tipo.
    """
    from sqlalchemy import or_
    
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Buscar campanhas com detalhes
    campaigns = db.query(Campaign).filter(
        or_(
            Campaign.created_at >= start_date,
            Campaign.updated_at >= start_date
        ),
        Campaign.is_deleted == False
    ).all()
    
    campaigns_by_day = {}
    
    for campaign in campaigns:
        # Processar criação
        if campaign.created_at >= start_date:
            date_key = campaign.created_at.date().isoformat()
            if date_key not in campaigns_by_day:
                campaigns_by_day[date_key] = {
                    "date": date_key,
                    "campaigns_created": 0,
                    "campaigns_updated": 0,
                    "campaigns_deleted": 0,
                    "details": []
                }
            
            campaigns_by_day[date_key]["campaigns_created"] += 1
            campaigns_by_day[date_key]["details"].append({
                "type": "created",
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "user_id": str(current_user.id),
                "user_name": current_user.username,
                "timestamp": campaign.created_at.isoformat()
            })
        
        # Processar atualização
        if campaign.updated_at > campaign.created_at and campaign.updated_at >= start_date:
            date_key = campaign.updated_at.date().isoformat()
            if date_key not in campaigns_by_day:
                campaigns_by_day[date_key] = {
                    "date": date_key,
                    "campaigns_created": 0,
                    "campaigns_updated": 0,
                    "campaigns_deleted": 0,
                    "details": []
                }
            
            campaigns_by_day[date_key]["campaigns_updated"] += 1
            campaigns_by_day[date_key]["details"].append({
                "type": "updated",
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "user_id": str(current_user.id),
                "user_name": current_user.username,
                "timestamp": campaign.updated_at.isoformat()
            })
    
    # Converter para lista ordenada
    campaigns_activity = sorted(
        campaigns_by_day.values(),
        key=lambda x: x["date"],
        reverse=True
    )
    
    # Imagens por dia (mantém igual)
    images_by_day = db.execute(text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as count
        FROM campaign_images
        WHERE created_at >= :start_date
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """), {"start_date": start_date}).fetchall()
    
    return {
        "timestamp": now.isoformat(),
        "period": {
            "start": start_date.isoformat(),
            "end": now.isoformat(),
            "days": days
        },
        "campaigns_activity": campaigns_activity,
        "images_activity": [
            {
                "date": str(row[0]),
                "images_uploaded": row[1]
            }
            for row in images_by_day
        ]
    }