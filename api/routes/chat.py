"""
Endpoint de chat com HISTÓRICO de conversação
"""
import time
from collections import defaultdict, deque
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.llm_service import generate_response

router = APIRouter()

# HISTÓRICO por sessão (em memória)
conversation_history = defaultdict(lambda: deque(maxlen=10))

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    mode: str = "auto"
    time_ms: float
    history_size: int

@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat com histórico de conversação."""
    start = time.perf_counter()
    
    session = request.session_id or "default"
    
    # CRÍTICO: Pega histórico ANTES de adicionar a nova mensagem
    history = list(conversation_history[session])
    
    # Gera resposta PASSANDO O HISTÓRICO
    response_text = generate_response(
        request.message,
        conversation_history=history
    )
    
    # Adiciona AO HISTÓRICO depois
    conversation_history[session].append({"role": "user", "content": request.message})
    conversation_history[session].append({"role": "assistant", "content": response_text})
    
    elapsed = (time.perf_counter() - start) * 1000
    
    return ChatResponse(
        response=response_text,
        mode="auto",
        time_ms=elapsed,
        history_size=len(conversation_history[session])
    )

@router.post("/chat/clear")
async def clear_history(session_id: str = "default"):
    """Limpa o histórico de uma sessão."""
    if session_id in conversation_history:
        conversation_history[session_id].clear()
    return {"status": "ok", "session_id": session_id}

@router.get("/chat/history/{session_id}")
async def get_history(session_id: str):
    """Retorna o histórico de uma sessão."""
    return {
        "session_id": session_id,
        "messages": list(conversation_history.get(session_id, []))
    }
