"""Testes do endpoint de chat."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_validation_empty_message(client: AsyncClient):
    response = await client.post("/v1/chat", json={
        "message": "",
        "session_id": "test_empty"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_chat_validation_long_message(client: AsyncClient):
    response = await client.post("/v1/chat", json={
        "message": "x" * 3000,
        "session_id": "test_long"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_chat_basic(client: AsyncClient):
    response = await client.post("/v1/chat", json={
        "message": "Oi Lucy",
        "session_id": "test_basic"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "time_ms" in data
    assert data["time_ms"] > 0
