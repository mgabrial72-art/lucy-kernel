"""Configuração de logging com loguru."""
import sys
from loguru import logger
from config.settings import settings


def setup_logging():
    """Configura loguru para toda a aplicação."""
    
    # Remove handlers padrão
    logger.remove()
    
    # Console (colorido)
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=False if settings.environment == "production" else True
    )
    
    # Arquivo rotativo (máx 10MB, mantém 5 arquivos)
    logger.add(
        settings.log_file,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )
    
    # Arquivo separado para erros
    logger.add(
        settings.log_file.replace(".log", ".error.log"),
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"✅ Logging configurado (nível: {settings.log_level})")


# Inicializar ao importar
setup_logging()
