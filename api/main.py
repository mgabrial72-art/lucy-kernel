from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia background updater na inicialização."""
    from api.services.context_cache_service import start_background_updater
    
    print("🚀 Iniciando background updater...")
    start_background_updater(interval_seconds=900)  # 15 minutos
    
    yield
    
    print("🛑 Finalizando Lucy...")

app = FastAPI(
    title="Lucy API",
    version="5.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
from api.routes import chat, voice, reminders, debug, schedule, weather, status
app.include_router(chat.router, prefix="/v1")
app.include_router(voice.router, prefix="/v1")
app.include_router(reminders.router, prefix="/v1")
app.include_router(debug.router, prefix="/v1")
app.include_router(schedule.router, prefix="/v1")
app.include_router(weather.router, prefix="/v1")
app.include_router(status.router, prefix="/v1")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "Lucy Frankenstein API", "version": "5.0.0"}
