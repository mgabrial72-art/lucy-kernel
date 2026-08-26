"""Testes do sistema de cache."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_cache_stats(client: AsyncClient):
    response = await client.get("/v1/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "weather" in data
    assert "context" in data
    assert "tts" in data

@pytest.mark.asyncio
async def test_cache_clear(client: AsyncClient):
    response = await client.post("/v1/cache/clear")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_ttl_cache_basic():
    from api.services.cache_lru import TTLCache
    cache = TTLCache(ttl_seconds=1, max_size=10)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    assert cache.get("nonexistent") is None
    stats = cache.stats()
    assert stats["size"] == 1
