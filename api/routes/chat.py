"""Endpoint de chat com histórico persistente (SQLite)."""
import time
from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from api.services.llm_service import generate_response
from api.services.history_service import (
    add_message, get_history, clear_history as clear_history_db, get_all_sessions
)
from loguru import logger


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    mode: str = "auto"
    time_ms: float
    history_size: int


@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    """Chat com histórico persistente."""
    start = time.perf_counter()
    session = request.session_id or "default"
    
    logger.info(f"💬 Chat [{session}]: {request.message[:50]}...")
    
    # Histórico do SQLite
    history = await get_history(session, limit=10)
    
    # Gera resposta em thread pool
    response_text = await run_in_threadpool(
        generate_response,
        request.message,
        conversation_history=history
    )
    
    # Salva no SQLite
    await add_message(session, "user", request.message)
    await add_message(session, "assistant", response_text)
    
    elapsed = (time.perf_counter() - start) * 1000
    history_size = len(history) + 2
    
    logger.info(f"✅ Chat respondido em {elapsed:.0f}ms")
    
    return ChatResponse(
        response=response_text,
        mode="auto",
        time_ms=elapsed,
        history_size=history_size
    )


@router.post("/chat/clear")
async def clear_history(session_id: str = "default"):
    """Limpa o histórico de uma sessão."""
    count = await clear_history_db(session_id)
    logger.info(f"🗑️ Histórico limpo: {session_id} ({count} mensagens)")
    return {"status": "ok", "session_id": session_id, "cleared": count}


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    """Retorna o histórico de uma sessão."""
    messages = await get_history(session_id, limit=50)
    return {"session_id": session_id, "count": len(messages), "messages": messages}


@router.get("/chat/sessions")
async def list_sessions():
    """Lista todas as sessões ativas."""
    sessions = await get_all_sessions()
    return {"count": len(sessions), "sessions": sessions}
