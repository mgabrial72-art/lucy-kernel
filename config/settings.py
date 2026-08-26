"""Configurações centralizadas usando Pydantic BaseSettings"""
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Todas as configurações do sistema Lucy."""
    
    # API
    api_host: str = Field(default="0.0.0.0", description="Host da API")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Porta da API")
    environment: str = Field(default="production", description="Ambiente (dev/prod)")
    cors_origins: List[str] = Field(
        default=["http://localhost:8000"],
        description="Origens permitidas para CORS"
    )
    
    # Ollama
    ollama_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="lucy-optimized")
    ollama_timeout: int = Field(default=180, ge=10)
    
    # Paths
    base_dir: Path = Field(default=Path(__file__).parent.parent)
    memory_dir: Path = Field(default=Path(__file__).parent.parent / "memory")
    voice_dir: Path = Field(default=Path(__file__).parent.parent / "voice")
    logs_dir: Path = Field(default=Path(__file__).parent.parent / "logs")
    
    # Voice
    whisper_model: str = Field(default="tiny")
    piper_voice: str = Field(default="pt_BR-faber-medium")
    
    # Memory
    user_id: str = Field(default="capitao")
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/lucy.log")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=60, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)
    
    # Weather
    sp_latitude: float = Field(default=-23.5505)
    sp_longitude: float = Field(default=-46.6333)
    weather_cache_ttl: int = Field(default=300, description="Cache em segundos")
    
    # Modelos
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Instância global
settings = Settings()

# Garantir diretórios
settings.memory_dir.mkdir(parents=True, exist_ok=True)
settings.logs_dir.mkdir(parents=True, exist_ok=True)

# Compatibilidade retroativa (código antigo)
API_HOST = settings.api_host
API_PORT = settings.api_port
OLLAMA_URL = settings.ollama_url
OLLAMA_MODEL = settings.ollama_model
OLLAMA_TIMEOUT = settings.ollama_timeout
BASE_DIR = settings.base_dir
MEMORY_DIR = settings.memory_dir
VOICE_DIR = settings.voice_dir
WHISPER_MODEL = settings.whisper_model
PIPER_VOICE = settings.piper_voice
