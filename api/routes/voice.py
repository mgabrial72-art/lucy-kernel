"""Endpoint de voz com histórico persistente."""
from fastapi import APIRouter, Request, Query
from fastapi.responses import Response
from fastapi.concurrency import run_in_threadpool
from loguru import logger

from api.services.llm_service import generate_response
from api.services.tts_service import text_to_speech
from api.services.history_service import add_message, get_history


router = APIRouter()


@router.post("/voice")
async def voice(request: Request, session_id: str = Query(default="default")):
    """Recebe texto, gera resposta COM histórico, retorna áudio."""
    body = await request.body()
    text = body.decode("utf-8").strip()
    
    if not text:
        return Response(
            content='{"detail":"pergunta vazia"}',
            media_type="application/json",
            status_code=400
        )
    
    session = session_id or "default"
    logger.info(f"🎤 Voice [{session}]: {text[:50]}...")
    
    # Histórico persistente
    history = await get_history(session, limit=10)
    
    # Gera resposta em thread pool
    response_text = await run_in_threadpool(
        generate_response,
        text,
        conversation_history=history
    )
    
    # Salva no histórico
    await add_message(session, "user", text)
    await add_message(session, "assistant", response_text)
    
    # Converte em áudio em thread pool
    audio_data = await run_in_threadpool(text_to_speech, response_text)
    
    if not audio_data:
        return Response(
            content='{"detail":"erro ao gerar áudio"}',
            media_type="application/json",
            status_code=500
        )
    
    # Detecta formato
    is_mp3 = b'ID3' in audio_data[:20] or b'LAME' in audio_data[:100]
    media_type = "audio/mpeg" if is_mp3 else "audio/wav"
    
    logger.info(f"🔊 Áudio gerado: {len(audio_data)} bytes ({media_type})")
    
    return Response(
        content=audio_data,
        media_type=media_type,
        headers={
            "X-Response-Text": response_text[:200].replace("\n", " "),
            "X-Lucy-Session": session_id
        }
    )
