"""
Endpoints administrativos para sincronização e gerenciamento
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config.database import get_db
from app.models.sync_log import SyncLog
from app.models.branch import Branch
from app.models.station import Station
from app.services.sync_service import ProtheusSyncService
from app.dependencies.auth import get_current_admin_user
from app.models.user import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)]  # Requer autenticação admin
)


@router.post("/sync/branches")
async def sync_branches(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza filiais do Protheus (SQL Server) para PostgreSQL
    Executa em background e retorna imediatamente
    """
    # Verificar se já existe uma sincronização em andamento
    running_sync = db.query(SyncLog).filter(
        SyncLog.sync_type == "branches",
        SyncLog.status == "running"
    ).first()
    
    if running_sync:
        # Verificar se ainda está realmente rodando (timeout de 10 minutos)
        time_diff = (datetime.now() - running_sync.started_at).total_seconds()
        if time_diff < 600:  # 10 minutos
            raise HTTPException(
                status_code=409,
                detail="Sincronização já em andamento"
            )
        else:
            # Marcar como erro se passou do timeout
            running_sync.status = "error"
            running_sync.error_message = "Timeout - processo interrompido"
            db.commit()
    
    # Criar log de sincronização
    sync_log = SyncLog(
        sync_type="branches",
        started_at=datetime.now(),
        status="running",
        triggered_by="manual",
        user_id=str(current_user.id) if hasattr(current_user, 'id') else current_user.get('email')
    )
    db.add(sync_log)
    db.commit()
    db.refresh(sync_log)
    
    # Executar sincronização em background
    background_tasks.add_task(
        run_sync_task,
        sync_log_id=sync_log.id
    )
    
    return {
        "message": "Sincronização iniciada em background",
        "sync_id": sync_log.id,
        "status": "running"
    }


@router.get("/sync/status/{sync_id}")
async def get_sync_status(
    sync_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna o status de uma sincronização específica
    """
    sync_log = db.query(SyncLog).filter(SyncLog.id == sync_id).first()
    
    if not sync_log:
        raise HTTPException(status_code=404, detail="Sincronização não encontrada")
    
    return {
        "id": sync_log.id,
        "type": sync_log.sync_type,
        "status": sync_log.status,
        "started_at": sync_log.started_at,
        "finished_at": sync_log.finished_at,
        "duration_seconds": sync_log.duration_seconds,
        "statistics": {
            "processed": sync_log.records_processed,
            "created": sync_log.records_created,
            "updated": sync_log.records_updated,
            "failed": sync_log.records_failed
        },
        "error": sync_log.error_message,
        "details": sync_log.details
    }


@router.get("/sync/history")
async def get_sync_history(
    sync_type: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Retorna histórico de sincronizações
    """
    query = db.query(SyncLog)
    
    if sync_type:
        query = query.filter(SyncLog.sync_type == sync_type)
    
    logs = query.order_by(desc(SyncLog.created_at)).limit(limit).all()
    
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "type": log.sync_type,
                "status": log.status,
                "started_at": log.started_at,
                "finished_at": log.finished_at,
                "duration_seconds": log.duration_seconds,
                "records_processed": log.records_processed,
                "records_created": log.records_created,
                "records_updated": log.records_updated,
                "triggered_by": log.triggered_by,
                "error": bool(log.error_message)
            }
            for log in logs
        ]
    }


@router.get("/stats/overview")
async def get_admin_stats(db: Session = Depends(get_db)):
    """
    Retorna estatísticas gerais do sistema
    """
    # Contar totais
    total_branches = db.query(Branch).count()
    active_branches = db.query(Branch).filter(Branch.is_active == True).count()
    total_stations = db.query(Station).count()
    active_stations = db.query(Station).filter(Station.is_active == True).count()
    
    # Última sincronização
    last_sync = db.query(SyncLog).filter(
        SyncLog.sync_type == "branches"
    ).order_by(desc(SyncLog.created_at)).first()
    
    # Próxima sincronização agendada
    from app.services.scheduler_service import scheduler_service
    next_sync = None
    jobs = scheduler_service.get_jobs()
    for job in jobs:
        if job["id"] == "sync_branches_daily":
            next_sync = job["next_run"]
            break
    
    return {
        "branches": {
            "total": total_branches,
            "active": active_branches,
            "inactive": total_branches - active_branches
        },
        "stations": {
            "total": total_stations,
            "active": active_stations,
            "inactive": total_stations - active_stations
        },
        "last_sync": {
            "date": last_sync.started_at if last_sync else None,
            "status": last_sync.status if last_sync else None,
            "records": last_sync.records_processed if last_sync else 0
        } if last_sync else None,
        "next_sync": next_sync,
        "scheduler_running": scheduler_service.is_running
    }


@router.get("/scheduler/jobs")
async def get_scheduled_jobs(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Retorna lista de jobs agendados no scheduler
    """
    from app.services.scheduler_service import scheduler_service
    
    return {
        "scheduler_running": scheduler_service.is_running,
        "jobs": scheduler_service.get_jobs()
    }


@router.post("/scheduler/trigger/{job_id}")
async def trigger_scheduled_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Executa um job agendado manualmente
    """
    from app.services.scheduler_service import scheduler_service
    
    # Executar em background
    background_tasks.add_task(
        scheduler_service.trigger_job,
        job_id=job_id
    )
    
    return {
        "message": f"Job {job_id} disparado para execução em background",
        "job_id": job_id
    }


def run_sync_task(sync_log_id: int):
    """
    Executa a sincronização e atualiza o log
    Esta função roda em background
    """
    from app.config.database import SessionLocal
    
    db = SessionLocal()
    sync_log = db.query(SyncLog).filter(SyncLog.id == sync_log_id).first()
    
    if not sync_log:
        return
    
    try:
        # Executar sincronização
        service = ProtheusSyncService()
        stats = service.sync_branches()
        
        # Atualizar log com sucesso
        sync_log.finished_at = datetime.now()
        sync_log.duration_seconds = int((sync_log.finished_at - sync_log.started_at).total_seconds())
        sync_log.status = stats.get("status", "error")
        sync_log.records_processed = stats.get("branches_processed", 0)
        sync_log.records_created = stats.get("branches_created", 0)
        sync_log.records_updated = stats.get("branches_updated", 0)
        sync_log.records_failed = len(stats.get("errors", []))
        sync_log.details = stats
        
        if stats.get("errors"):
            sync_log.error_message = "; ".join(stats["errors"][:5])  # Primeiros 5 erros
        
        db.commit()
        
    except Exception as e:
        # Atualizar log com erro
        sync_log.finished_at = datetime.now()
        sync_log.duration_seconds = int((sync_log.finished_at - sync_log.started_at).total_seconds())
        sync_log.status = "error"
        sync_log.error_message = str(e)
        db.commit()
        
    finally:
        db.close()