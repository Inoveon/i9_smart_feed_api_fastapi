from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.config.settings import settings
from app.routes import api_router
from app.routes.health import router as health_router
from app.services.scheduler_service import scheduler_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação
    Inicia o scheduler ao subir a API e para ao desligar
    """
    # Startup
    logger.info("🚀 Iniciando aplicação...")
    try:
        scheduler_service.start()
        logger.info("✅ Scheduler iniciado com sucesso")
    except Exception as e:
        logger.error(f"⚠️ Erro ao iniciar scheduler: {str(e)}")
        # Não falha a aplicação se o scheduler não iniciar
    
    yield
    
    # Shutdown
    logger.info("🛑 Desligando aplicação...")
    try:
        scheduler_service.stop()
        logger.info("✅ Scheduler parado com sucesso")
    except Exception as e:
        logger.error(f"⚠️ Erro ao parar scheduler: {str(e)}")


app = FastAPI(
    title=settings.APP_NAME, 
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS and settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api")

# Health check na raiz (para K8s/Docker)
app.include_router(health_router, prefix="/health", tags=["health"])

# Static files (fallback for uploads when MinIO is unavailable)
app.mount("/static", StaticFiles(directory="static"), name="static")
