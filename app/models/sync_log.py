"""
Modelo para logs de sincronização
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class SyncLog(Base):
    """Modelo para registrar histórico de sincronizações"""
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False)  # 'branches', 'campaigns', etc
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer)
    status = Column(String(20))  # 'success', 'error', 'partial'
    
    # Estatísticas
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Detalhes e erros
    error_message = Column(Text)
    details = Column(JSON)  # Detalhes adicionais em JSON
    
    # Metadados
    triggered_by = Column(String(50))  # 'manual', 'scheduler', 'api'
    user_id = Column(String(100))  # ID do usuário que triggou (se manual)
    created_at = Column(DateTime, server_default=func.now())