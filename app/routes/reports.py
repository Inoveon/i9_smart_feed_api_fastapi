"""
Endpoints de relatórios e exportação.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Literal
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import text, func, and_
from sqlalchemy.orm import Session
import csv
import io
import json

from app.config.database import get_db
from app.dependencies.auth import require_role
from app.models.campaign import Campaign
from app.models.image import CampaignImage
from app.models.user import User

router = APIRouter(tags=["reports"])


@router.get("", summary="Gerar relatórios customizados")
async def generate_report(
    report_type: Literal["campaigns", "activity", "performance", "summary"] = Query("summary"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    group_by: Optional[Literal["day", "week", "month", "status", "region"]] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Gera relatórios customizáveis com filtros e agrupamentos.
    """
    now = datetime.utcnow()
    
    # Definir período padrão se não especificado
    if not end_date:
        end_date = now
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    report_data = {
        "timestamp": now.isoformat(),
        "parameters": {
            "type": report_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {
                "status": status,
                "group_by": group_by
            }
        }
    }
    
    if report_type == "campaigns":
        # Relatório de campanhas
        query = db.query(Campaign).filter(
            and_(
                Campaign.created_at >= start_date,
                Campaign.created_at <= end_date,
                Campaign.is_deleted == False
            )
        )
        
        if status:
            query = query.filter(Campaign.status == status)
        
        campaigns = query.all()
        
        if group_by == "status":
            grouped = {}
            for campaign in campaigns:
                if campaign.status not in grouped:
                    grouped[campaign.status] = []
                grouped[campaign.status].append({
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "priority": campaign.priority,
                    "created_at": campaign.created_at.isoformat()
                })
            report_data["data"] = grouped
        else:
            report_data["data"] = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "status": c.status,
                    "priority": c.priority,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat(),
                    "created_at": c.created_at.isoformat()
                }
                for c in campaigns
            ]
    
    elif report_type == "activity":
        # Relatório de atividade
        activity_data = db.execute(text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as campaigns_created,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_campaigns
            FROM campaigns
            WHERE created_at BETWEEN :start_date AND :end_date
                AND is_deleted = false
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        report_data["data"] = [
            {
                "date": str(row[0]),
                "campaigns_created": row[1],
                "active_campaigns": row[2]
            }
            for row in activity_data
        ]
    
    elif report_type == "performance":
        # Relatório de performance
        performance = db.execute(text("""
            SELECT 
                c.id,
                c.name,
                c.status,
                c.priority,
                COUNT(DISTINCT ci.id) as image_count,
                c.created_at,
                c.updated_at
            FROM campaigns c
            LEFT JOIN campaign_images ci ON c.id = ci.campaign_id
            WHERE c.created_at BETWEEN :start_date AND :end_date
                AND c.is_deleted = false
            GROUP BY c.id, c.name, c.status, c.priority, c.created_at, c.updated_at
            ORDER BY c.priority DESC, image_count DESC
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        report_data["data"] = [
            {
                "id": str(row[0]),
                "name": row[1],
                "status": row[2],
                "priority": row[3],
                "image_count": row[4],
                "created_at": row[5].isoformat(),
                "updated_at": row[6].isoformat()
            }
            for row in performance
        ]
    
    else:  # summary
        # Relatório resumo
        total_campaigns = db.query(Campaign).filter(
            and_(
                Campaign.created_at >= start_date,
                Campaign.created_at <= end_date,
                Campaign.is_deleted == False
            )
        ).count()
        
        status_summary = db.execute(text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM campaigns
            WHERE created_at BETWEEN :start_date AND :end_date
                AND is_deleted = false
            GROUP BY status
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        images_summary = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                AVG(size_bytes) as avg_size
            FROM campaign_images ci
            JOIN campaigns c ON ci.campaign_id = c.id
            WHERE c.created_at BETWEEN :start_date AND :end_date
                AND c.is_deleted = false
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchone()
        
        report_data["data"] = {
            "total_campaigns": total_campaigns,
            "by_status": {
                row[0]: row[1]
                for row in status_summary
            },
            "images": {
                "total": images_summary[0] if images_summary else 0,
                "average_size_bytes": round(images_summary[1], 2) if images_summary and images_summary[1] else 0
            }
        }
    
    report_data["summary"] = {
        "total_records": len(report_data["data"]) if isinstance(report_data["data"], list) else 1,
        "generated_at": now.isoformat()
    }
    
    return report_data


@router.get("/export", summary="Exportar métricas")
async def export_metrics(
    format: Literal["csv", "json"] = Query("json"),
    data_type: Literal["campaigns", "images", "activity", "full"] = Query("campaigns"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: dict = Depends(require_role(["admin", "editor"]))
) -> Response:
    """
    Exporta métricas em diferentes formatos (CSV ou JSON).
    """
    now = datetime.utcnow()
    
    # Definir período padrão
    if not end_date:
        end_date = now
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    if data_type == "campaigns":
        # Exportar dados de campanhas
        campaigns = db.query(Campaign).filter(
            and_(
                Campaign.created_at >= start_date,
                Campaign.created_at <= end_date,
                Campaign.is_deleted == False
            )
        ).all()
        
        data = [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "status": c.status,
                "priority": c.priority,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat(),
                "default_display_time": c.default_display_time,
                "stations_count": len(c.stations) if c.stations else 0,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in campaigns
        ]
    
    elif data_type == "images":
        # Exportar dados de imagens
        images = db.execute(text("""
            SELECT 
                ci.id,
                ci.filename,
                ci.title,
                ci.display_time,
                ci.order_index,
                ci.size_bytes,
                ci.mime_type,
                c.name as campaign_name,
                c.status as campaign_status,
                ci.created_at
            FROM campaign_images ci
            JOIN campaigns c ON ci.campaign_id = c.id
            WHERE c.created_at BETWEEN :start_date AND :end_date
                AND c.is_deleted = false
            ORDER BY c.name, ci.order_index
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        data = [
            {
                "id": str(row[0]),
                "filename": row[1],
                "title": row[2],
                "display_time": row[3],
                "order": row[4],
                "size_bytes": row[5],
                "mime_type": row[6],
                "campaign": row[7],
                "campaign_status": row[8],
                "created_at": row[9].isoformat()
            }
            for row in images
        ]
    
    elif data_type == "activity":
        # Exportar dados de atividade
        activity = db.execute(text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as campaigns_created,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN status = 'paused' THEN 1 ELSE 0 END) as paused,
                SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired
            FROM campaigns
            WHERE created_at BETWEEN :start_date AND :end_date
                AND is_deleted = false
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        data = [
            {
                "date": str(row[0]),
                "total_created": row[1],
                "active": row[2],
                "scheduled": row[3],
                "paused": row[4],
                "expired": row[5]
            }
            for row in activity
        ]
    
    else:  # full
        # Exportar dados completos
        data = {
            "export_info": {
                "generated_at": now.isoformat(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "campaigns": [],
            "images": [],
            "activity": []
        }
        
        # Adicionar campanhas
        campaigns = db.query(Campaign).filter(
            and_(
                Campaign.created_at >= start_date,
                Campaign.created_at <= end_date,
                Campaign.is_deleted == False
            )
        ).all()
        
        for c in campaigns:
            data["campaigns"].append({
                "id": str(c.id),
                "name": c.name,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at.isoformat()
            })
        
        # Adicionar atividade
        activity = db.execute(text("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM campaigns
            WHERE created_at BETWEEN :start_date AND :end_date
                AND is_deleted = false
            GROUP BY DATE(created_at)
        """), {
            "start_date": start_date,
            "end_date": end_date
        }).fetchall()
        
        for row in activity:
            data["activity"].append({
                "date": str(row[0]),
                "campaigns_created": row[1]
            })
    
    # Gerar resposta baseada no formato
    if format == "csv":
        # Converter para CSV
        output = io.StringIO()
        
        if isinstance(data, list) and data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            # Para dados estruturados, criar CSV simples
            writer = csv.writer(output)
            writer.writerow(["key", "value"])
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            writer.writerow([f"{key}.{sub_key}", str(sub_value)])
                    else:
                        writer.writerow([key, str(value)])
        
        output.seek(0)
        filename = f"export_{data_type}_{now.strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    else:  # JSON
        filename = f"export_{data_type}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )


@router.get("/templates", summary="Templates de relatórios")
async def report_templates(
    _: dict = Depends(require_role(["admin", "editor", "viewer"]))
) -> Dict[str, Any]:
    """
    Retorna templates pré-configurados de relatórios.
    """
    return {
        "templates": [
            {
                "id": "daily_summary",
                "name": "Resumo Diário",
                "description": "Resumo das atividades do dia",
                "parameters": {
                    "report_type": "summary",
                    "period": "1d"
                }
            },
            {
                "id": "weekly_performance",
                "name": "Performance Semanal",
                "description": "Análise de performance da última semana",
                "parameters": {
                    "report_type": "performance",
                    "period": "7d",
                    "group_by": "day"
                }
            },
            {
                "id": "monthly_campaigns",
                "name": "Campanhas Mensais",
                "description": "Relatório completo de campanhas do mês",
                "parameters": {
                    "report_type": "campaigns",
                    "period": "30d",
                    "group_by": "status"
                }
            },
            {
                "id": "activity_trend",
                "name": "Tendência de Atividade",
                "description": "Análise de tendências de atividade",
                "parameters": {
                    "report_type": "activity",
                    "period": "90d",
                    "group_by": "week"
                }
            }
        ]
    }