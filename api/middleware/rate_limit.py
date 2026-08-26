"""Rate limiting usando slowapi com handler customizado."""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from config.settings import settings
from loguru import logger


# Limiter global
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_period} seconds"]
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler customizado quando rate limit é excedido."""
    logger.warning(f"⚠️ Rate limit excedido: {request.client.host} em {request.url}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Muitas requisições",
            "detail": "Tente novamente em alguns segundos",
            "retry_after": 60
        }
    )
