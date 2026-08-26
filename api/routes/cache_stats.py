"""Endpoint para visualizar estatísticas de cache."""
from fastapi import APIRouter
from api.services.cache_lru import weather_cache, context_cache, tts_cache

router = APIRouter()


@router.get("/cache/stats")
async def cache_stats():
    """Estatísticas de todos os caches."""
    return {
        "weather": weather_cache.stats(),
        "context": context_cache.stats(),
        "tts": tts_cache.stats()
    }


@router.post("/cache/clear")
async def clear_all_caches():
    """Limpa todos os caches."""
    weather_cache.clear()
    context_cache.clear()
    tts_cache.clear()
    return {"status": "ok", "message": "Todos os caches limpos"}
