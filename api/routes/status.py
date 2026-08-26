"""
Endpoint /v1/status - retorna contexto atualizado instantaneamente
"""
from fastapi import APIRouter
from api.services.context_cache_service import get_context, get_status_summary

router = APIRouter()

@router.get("/status")
async def status():
    """Retorna contexto completo (resposta instantânea)."""
    return get_context()

@router.get("/status/summary")
async def status_summary():
    """Retorna resumo natural do contexto."""
    return {"summary": get_status_summary()}

@router.post("/status/refresh")
async def refresh_status():
    """Força atualização do contexto."""
    from api.services.context_cache_service import update_context
    update_context()
    return {"status": "refreshed", "context": get_context()}
