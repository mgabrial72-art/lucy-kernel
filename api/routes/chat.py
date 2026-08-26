"""Endpoint de chat com validação Pydantic."""
import time
from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from loguru import logger

from api.schemas.chat_schemas import ChatRequest, ChatResponse
from api.services.llm_service import generate_response
from api.services.history_service import (
    add_message, get_history, clear_history as clear_history_db, get_all_sessions
)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """Chat com histórico persistente e validação Pydantic."""
    start = time.perf_counter()
    session = request.session_id
    
    logger.info(f"💬 Chat [{session}]: {request.message[:50]}...")
    
    history = await get_history(session, limit=10)
    
    response_text = await run_in_threadpool(
        generate_response,
        request.message,
        conversation_history=history
    )
    
    await add_message(session, "user", request.message)
    await add_message(session, "assistant", response_text)
    
    elapsed = (time.perf_counter() - start) * 1000
    
    logger.info(f"✅ Chat respondido em {elapsed:.0f}ms")
    
    return ChatResponse(
        response=response_text,
        mode="auto",
        time_ms=elapsed,
        history_size=len(history) + 2
    )


@router.post("/chat/clear")
async def clear_history(session_id: str = "default"):
    count = await clear_history_db(session_id)
    logger.info(f"🗑️ Histórico limpo: {session_id} ({count} mensagens)")
    return {"status": "ok", "session_id": session_id, "cleared": count}


@router.get("/chat/history/{session_id}")
async def get_session_history(session_id: str):
    messages = await get_history(session_id, limit=50)
    return {"session_id": session_id, "count": len(messages), "messages": messages}


@router.get("/chat/sessions")
async def list_sessions():
    sessions = await get_all_sessions()
    return {"count": len(sessions), "sessions": sessions}
