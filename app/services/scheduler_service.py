"""
Service para agendamento de tarefas com APScheduler
Executa sincronização diária das filiais
"""

import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.sync_log import SyncLog
from app.services.sync_service import ProtheusSyncService
from app.config.settings import settings

# Configurar logging
logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service para gerenciar tarefas agendadas
    """
    
    def __init__(self):
        """Inicializa o scheduler"""
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def start(self):
        """
        Inicia o scheduler e configura as tarefas
        """
        if self.is_running:
            logger.warning("⚠️ Scheduler já está rodando")
            return
        
        try:
            # Configurar job de sincronização diária
            # Executa todos os dias às 03:00 AM (horário de menor movimento)
            self.scheduler.add_job(
                func=self.sync_branches_job,
                trigger=CronTrigger(hour=3, minute=0),
                id='sync_branches_daily',
                name='Sincronização diária de filiais',
                replace_existing=True,
                misfire_grace_time=3600  # 1 hora de tolerância
            )
            
            # Iniciar scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("✅ Scheduler iniciado com sucesso")
            logger.info("📅 Sincronização agendada para 03:00 AM diariamente")
            
            # Listar jobs agendados
            jobs = self.scheduler.get_jobs()
            for job in jobs:
                logger.info(f"   📌 Job: {job.name} - Próxima execução: {job.next_run_time}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar scheduler: {str(e)}")
            raise
    
    def stop(self):
        """
        Para o scheduler
        """
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("🛑 Scheduler parado")
        except Exception as e:
            logger.error(f"❌ Erro ao parar scheduler: {str(e)}")
    
    def sync_branches_job(self):
        """
        Job de sincronização de filiais
        Executa em modo síncrono para compatibilidade com APScheduler
        """
        logger.info("=" * 60)
        logger.info("🔄 INICIANDO JOB DE SINCRONIZAÇÃO AUTOMÁTICA")
        logger.info(f"📅 Data/Hora: {datetime.now()}")
        logger.info("=" * 60)
        
        # Criar conexão direta com banco para job
        from app.config.database import SessionLocal
        
        db = SessionLocal()
        sync_log = None
        
        try:
            # Criar log de sincronização
            sync_log = SyncLog(
                sync_type="branches",
                started_at=datetime.now(),
                status="running",
                triggered_by="scheduler",
                user_id="system"
            )
            db.add(sync_log)
            db.commit()
            db.refresh(sync_log)
            
            logger.info(f"📝 Log de sincronização criado: ID {sync_log.id}")
            
            # Executar sincronização
            service = ProtheusSyncService()
            stats = service.sync_branches()
            
            # Atualizar log com resultado
            sync_log.finished_at = datetime.now()
            sync_log.duration_seconds = int((sync_log.finished_at - sync_log.started_at).total_seconds())
            sync_log.status = stats.get("status", "error")
            sync_log.records_processed = stats.get("branches_processed", 0)
            sync_log.records_created = stats.get("branches_created", 0)
            sync_log.records_updated = stats.get("branches_updated", 0)
            sync_log.records_failed = len(stats.get("errors", []))
            sync_log.details = stats
            
            if stats.get("errors"):
                sync_log.error_message = "; ".join(stats["errors"][:5])
            
            db.commit()
            
            logger.info("=" * 60)
            logger.info("✅ JOB DE SINCRONIZAÇÃO CONCLUÍDO")
            logger.info(f"   Status: {sync_log.status}")
            logger.info(f"   Duração: {sync_log.duration_seconds} segundos")
            logger.info(f"   Filiais processadas: {sync_log.records_processed}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Erro no job de sincronização: {str(e)}")
            
            # Atualizar log com erro
            if sync_log:
                sync_log.finished_at = datetime.now()
                sync_log.duration_seconds = int((sync_log.finished_at - sync_log.started_at).total_seconds())
                sync_log.status = "error"
                sync_log.error_message = str(e)
                db.commit()
            
        finally:
            db.close()
    
    def get_jobs(self):
        """
        Retorna lista de jobs agendados
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time,
                "trigger": str(job.trigger)
            })
        return jobs
    
    def trigger_job(self, job_id: str):
        """
        Executa um job manualmente
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"✅ Job {job_id} executado manualmente")
                return True
            else:
                logger.warning(f"⚠️ Job {job_id} não encontrado")
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao executar job {job_id}: {str(e)}")
            return False


# Instância global do scheduler
scheduler_service = SchedulerService()