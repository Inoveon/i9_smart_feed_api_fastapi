"""
Endpoints de analytics e dashboards.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, func, and_
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.dependencies.auth import require_role
from app.models.campaign import Campaign
from app.models.image import CampaignImage
from app.models.user import User

router = APIRouter(tags=["analytics"])


@router.get("", summary="Dashboard de analytics geral")
async def analytics_dashboard(
    period: int = Query(30, description="Período em dias para análise"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna dashboard completo de analytics com KPIs, tendências e comparações.
    """
    now = datetime.utcnow()
    current_period_start = now - timedelta(days=period)
    previous_period_start = current_period_start - timedelta(days=period)
    
    # KPIs principais
    total_campaigns = db.query(Campaign).filter(
        Campaign.is_deleted == False
    ).count()
    
    active_campaigns = db.query(Campaign).filter(
        Campaign.status == "active",
        Campaign.is_deleted == False
    ).count()
    
    total_images = db.query(CampaignImage).count()
    
    # Taxa de ativação (campanhas ativas / total)
    activation_rate = round((active_campaigns / total_campaigns * 100) if total_campaigns > 0 else 0, 2)
    
    # Campanhas criadas no período atual vs anterior
    current_period_campaigns = db.query(Campaign).filter(
        Campaign.created_at >= current_period_start,
        Campaign.is_deleted == False
    ).count()
    
    previous_period_campaigns = db.query(Campaign).filter(
        and_(
            Campaign.created_at >= previous_period_start,
            Campaign.created_at < current_period_start
        ),
        Campaign.is_deleted == False
    ).count()
    
    # Calcular variação percentual
    if previous_period_campaigns > 0:
        growth_rate = round(
            ((current_period_campaigns - previous_period_campaigns) / previous_period_campaigns) * 100, 
            2
        )
    else:
        growth_rate = 100.0 if current_period_campaigns > 0 else 0.0
    
    # Tendências diárias
    daily_trend = db.execute(text("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as campaigns,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active
        FROM campaigns
        WHERE created_at >= :start_date
            AND is_deleted = false
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    """), {"start_date": current_period_start}).fetchall()
    
    # Performance por tipo de campanha
    campaign_performance = db.execute(text("""
        SELECT 
            CASE 
                WHEN stations IS NULL OR CARDINALITY(stations) = 0 THEN 'global'
                ELSE 'specific'
            END as type,
            COUNT(*) as count,
            AVG(priority) as avg_priority
        FROM campaigns
        WHERE is_deleted = false
        GROUP BY CASE 
            WHEN stations IS NULL OR CARDINALITY(stations) = 0 THEN 'global'
            ELSE 'specific'
        END
    """)).fetchall()
    
    # Top usuários criadores
    top_creators = db.execute(text("""
        SELECT 
            u.username,
            u.email,
            COUNT(c.id) as campaigns_created
        FROM users u
        JOIN campaigns c ON c.created_by = u.id
        WHERE c.is_deleted = false
            AND c.created_at >= :start_date
        GROUP BY u.id, u.username, u.email
        ORDER BY campaigns_created DESC
        LIMIT 5
    """), {"start_date": current_period_start}).fetchall()
    
    # Distribuição por status
    status_distribution = db.execute(text("""
        SELECT 
            status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
        FROM campaigns
        WHERE is_deleted = false
        GROUP BY status
    """)).fetchall()
    
    # Média de imagens por campanha
    avg_images = db.execute(text("""
        SELECT 
            AVG(image_count) as average,
            MIN(image_count) as minimum,
            MAX(image_count) as maximum
        FROM (
            SELECT 
                campaign_id,
                COUNT(*) as image_count
            FROM campaign_images
            GROUP BY campaign_id
        ) as counts
    """)).fetchone()
    
    return {
        "timestamp": now.isoformat(),
        "period": {
            "days": period,
            "start": current_period_start.isoformat(),
            "end": now.isoformat()
        },
        "kpis": {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_images": total_images,
            "activation_rate": activation_rate,
            "growth_rate": growth_rate
        },
        "comparisons": {
            "current_period": {
                "campaigns": current_period_campaigns,
                "period_days": period
            },
            "previous_period": {
                "campaigns": previous_period_campaigns,
                "period_days": period
            },
            "change_percentage": growth_rate
        },
        "trends": {
            "daily": [
                {
                    "date": str(row[0]),
                    "total": row[1],
                    "active": row[2]
                }
                for row in daily_trend
            ]
        },
        "performance": {
            "by_type": [
                {
                    "type": row[0],
                    "count": row[1],
                    "avg_priority": round(row[2], 2) if row[2] else 0
                }
                for row in campaign_performance
            ]
        },
        "top_creators": [
            {
                "username": row[0],
                "email": row[1],
                "campaigns": row[2]
            }
            for row in top_creators
        ],
        "status_distribution": [
            {
                "status": row[0],
                "count": row[1],
                "percentage": float(row[2])
            }
            for row in status_distribution
        ],
        "images_statistics": {
            "average_per_campaign": round(avg_images[0], 2) if avg_images[0] else 0,
            "min": avg_images[1] if avg_images[1] else 0,
            "max": avg_images[2] if avg_images[2] else 0
        }
    }


@router.get("/comparison", summary="Comparação entre períodos")
async def analytics_comparison(
    period1_start: Optional[datetime] = Query(None, description="Início do primeiro período"),
    period1_end: Optional[datetime] = Query(None, description="Fim do primeiro período"),
    period2_start: Optional[datetime] = Query(None, description="Início do segundo período"),
    period2_end: Optional[datetime] = Query(None, description="Fim do segundo período"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Compara métricas entre dois períodos específicos.
    Se não especificados, compara últimos 30 dias com 30 dias anteriores.
    """
    now = datetime.utcnow()
    
    # Definir períodos padrão se não especificados
    if not period1_end:
        period1_end = now
    if not period1_start:
        period1_start = period1_end - timedelta(days=30)
    if not period2_end:
        period2_end = period1_start
    if not period2_start:
        period2_start = period2_end - timedelta(days=30)
    
    def get_period_metrics(start: datetime, end: datetime):
        campaigns = db.query(Campaign).filter(
            and_(
                Campaign.created_at >= start,
                Campaign.created_at <= end,
                Campaign.is_deleted == False
            )
        ).all()
        
        total = len(campaigns)
        active = len([c for c in campaigns if c.status == "active"])
        
        images_count = db.query(func.count(CampaignImage.id)).join(Campaign).filter(
            and_(
                Campaign.created_at >= start,
                Campaign.created_at <= end,
                Campaign.is_deleted == False
            )
        ).scalar() or 0
        
        return {
            "total_campaigns": total,
            "active_campaigns": active,
            "total_images": images_count,
            "activation_rate": round((active / total * 100) if total > 0 else 0, 2)
        }
    
    period1_metrics = get_period_metrics(period1_start, period1_end)
    period2_metrics = get_period_metrics(period2_start, period2_end)
    
    # Calcular variações
    variations = {}
    for key in period1_metrics.keys():
        if period1_metrics[key] > 0:
            variation = ((period2_metrics[key] - period1_metrics[key]) / period1_metrics[key]) * 100
        else:
            variation = 100.0 if period2_metrics[key] > 0 else 0.0
        variations[f"{key}_variation"] = round(variation, 2)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "period1": {
            "start": period1_start.isoformat(),
            "end": period1_end.isoformat(),
            "metrics": period1_metrics
        },
        "period2": {
            "start": period2_start.isoformat(),
            "end": period2_end.isoformat(),
            "metrics": period2_metrics
        },
        "variations": variations
    }


@router.get("/regions", summary="Analytics por região")
async def analytics_by_region(
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna analytics agrupadas por região geográfica.
    """
    from app.utils.regions import REGIONS_MAPPING
    
    regions_data = {}
    
    for region, states in REGIONS_MAPPING.items():
        # Contar campanhas que incluem estações da região
        region_campaigns = []
        all_campaigns = db.query(Campaign).filter(
            Campaign.is_deleted == False
        ).all()
        
        for campaign in all_campaigns:
            if campaign.regions and region in campaign.regions:
                region_campaigns.append(campaign)
            elif campaign.stations:
                # Verificar se alguma estação é da região
                for station_id in campaign.stations:
                    if "-" in station_id:
                        uf = station_id.split("-")[0]
                        if uf in states:
                            region_campaigns.append(campaign)
                            break
        
        total = len(region_campaigns)
        active = len([c for c in region_campaigns if c.status == "active"])
        
        regions_data[region] = {
            "total_campaigns": total,
            "active_campaigns": active,
            "activation_rate": round((active / total * 100) if total > 0 else 0, 2),
            "states": states
        }
    
    # Calcular totais
    total_all = sum(r["total_campaigns"] for r in regions_data.values())
    active_all = sum(r["active_campaigns"] for r in regions_data.values())
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "regions": regions_data,
        "summary": {
            "total_campaigns": total_all,
            "active_campaigns": active_all,
            "average_activation_rate": round((active_all / total_all * 100) if total_all > 0 else 0, 2)
        }
    }