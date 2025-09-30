"""
Health check endpoints para monitoramento da aplicação.
"""
from datetime import datetime
from typing import Dict, Any
import os
import psutil
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis

from app.config.database import get_db
from app.config.settings import settings


router = APIRouter(tags=["health"])


@router.get("/", summary="Health check básico")
async def health_check() -> Dict[str, Any]:
    """
    Health check simples para verificar se a API está respondendo.
    Usado para verificações rápidas de disponibilidade.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/live", summary="Liveness probe")
async def liveness() -> Dict[str, str]:
    """
    Liveness probe para Kubernetes/Docker.
    Verifica se a aplicação está viva e respondendo.
    """
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe")
async def readiness(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness probe para Kubernetes/Docker.
    Verifica se a aplicação está pronta para receber requisições.
    """
    try:
        # Testa conexão com banco
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/detailed", summary="Health check detalhado")
async def detailed_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check detalhado com status de todos os componentes.
    Útil para debugging e monitoramento completo.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {}
    }
    
    # 1. Database Check
    try:
        start = datetime.utcnow()
        result = db.execute(text("SELECT 1"))
        db_latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        # Contar registros
        campaigns_count = db.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        health_status["components"]["database"] = {
            "status": "healthy",
            "latency_ms": round(db_latency, 2),
            "stats": {
                "campaigns": campaigns_count,
                "users": users_count
            }
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # 2. Redis Check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        start = datetime.utcnow()
        redis_client.ping()
        redis_latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        info = redis_client.info()
        health_status["components"]["redis"] = {
            "status": "healthy",
            "latency_ms": round(redis_latency, 2),
            "stats": {
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        }
    except Exception as e:
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # 3. System Resources
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["components"]["system"] = {
            "status": "healthy",
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            },
            "disk": {
                "usage_percent": disk.percent,
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2)
            }
        }
        
        # Alertas de recursos
        if cpu_percent > 80:
            health_status["components"]["system"]["warnings"] = health_status["components"]["system"].get("warnings", [])
            health_status["components"]["system"]["warnings"].append("High CPU usage")
        if memory.percent > 85:
            health_status["components"]["system"]["warnings"] = health_status["components"]["system"].get("warnings", [])
            health_status["components"]["system"]["warnings"].append("High memory usage")
        if disk.percent > 90:
            health_status["components"]["system"]["warnings"] = health_status["components"]["system"].get("warnings", [])
            health_status["components"]["system"]["warnings"].append("Low disk space")
            
    except Exception as e:
        health_status["components"]["system"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # 4. MinIO/S3 Check (se configurado)
    if settings.MINIO_ENDPOINT:
        try:
            from minio import Minio
            client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            
            # Tenta listar buckets
            buckets = client.list_buckets()
            health_status["components"]["storage"] = {
                "status": "healthy",
                "endpoint": settings.MINIO_ENDPOINT,
                "bucket": settings.MINIO_BUCKET,
                "buckets_count": len(buckets)
            }
        except Exception as e:
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Status geral
    unhealthy_components = [
        name for name, comp in health_status["components"].items() 
        if comp.get("status") == "unhealthy"
    ]
    
    if unhealthy_components:
        health_status["status"] = "unhealthy"
        health_status["unhealthy_components"] = unhealthy_components
    elif health_status["status"] == "degraded":
        health_status["degraded_components"] = [
            name for name, comp in health_status["components"].items() 
            if comp.get("status") in ["unhealthy", "degraded"]
        ]
    
    return health_status