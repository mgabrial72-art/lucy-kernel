"""FastAPI Application - Lucy Frankenstein v6.0"""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded

from config.logging_config import logger
from config.settings import settings
from api.services.history_service import init_db
from api.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from api.middleware.error_handler import global_exception_handler, validation_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicação."""
    logger.info("🚀 Iniciando Lucy Frankenstein...")
    
    # Inicializa banco
    await init_db()
    
    # Inicia background updater
    from api.services.context_cache_service import start_background_updater
    start_background_updater(interval_seconds=900)
    
    logger.info(f"✅ Lucy pronta em {settings.api_host}:{settings.api_port}")
    logger.info(f"📚 Docs: http://{settings.api_host}:{settings.api_port}/docs")
    
    yield
    
    logger.info("🛑 Finalizando Lucy...")


app = FastAPI(
    title="Lucy Frankenstein API",
    version="6.0.0",
    description="Assistente pessoal Jarvis-like 100% local e privado",
    lifespan=lifespan
)

# CORS restrito
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Response-Text", "X-Lucy-Session", "X-Request-ID"]
)

# Rate limiting - usa handler customizado
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Error handling global
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)


# Middleware de request ID
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
async def root():
    return {
        "name": "Lucy Frankenstein API",
        "version": "6.0.0",
        "status": "running",
        "model": settings.ollama_model
    }


@app.get("/health")
async def health():
    """Health check detalhado."""
    import psutil
    import requests as req
    
    ollama_ok = False
    try:
        resp = req.get(f"{settings.ollama_url}/api/tags", timeout=2)
        ollama_ok = resp.status_code == 200
    except:
        pass
    
    from api.services.history_service import get_stats
    try:
        stats = await get_stats()
        db_ok = True
    except:
        stats = {"error": "db unavailable"}
        db_ok = False
    
    return {
        "status": "ok" if ollama_ok else "degraded",
        "components": {
            "api": True,
            "ollama": ollama_ok,
            "database": db_ok
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent
        },
        "history": stats,
        "version": "6.0.0"
    }


# Rotas
from api.routes import chat, voice, reminders, debug, schedule, weather, status
app.include_router(chat.router, prefix="/v1")
app.include_router(voice.router, prefix="/v1")
app.include_router(reminders.router, prefix="/v1")
app.include_router(debug.router, prefix="/v1")
app.include_router(schedule.router, prefix="/v1")
app.include_router(weather.router, prefix="/v1")
app.include_router(status.router, prefix="/v1")

logger.info("✅ Aplicação Lucy inicializada")
