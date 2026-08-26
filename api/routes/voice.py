"""
Endpoint de voz com histórico (MP3 via Edge TTS)
"""
from fastapi import APIRouter, Request, Query
from fastapi.responses import Response
from api.services.llm_service import generate_response
from api.services.tts_service import text_to_speech
from api.routes.chat import conversation_history

router = APIRouter()

@router.post("/voice")
async def voice(request: Request, session_id: str = Query(default="default")):
    """Recebe texto, gera resposta COM histórico, retorna áudio MP3."""
    body = await request.body()
    text = body.decode("utf-8").strip()
    
    if not text:
        return Response(
            content='{"detail":"pergunta vazia"}',
            media_type="application/json",
            status_code=400
        )
    
    session = session_id or "default"
    
    # Pega histórico ANTES
    history = list(conversation_history[session])
    
    # Gera resposta COM histórico
    response_text = generate_response(
        text,
        conversation_history=history
    )
    
    # Adiciona AO histórico DEPOIS
    conversation_history[session].append({"role": "user", "content": text})
    conversation_history[session].append({"role": "assistant", "content": response_text})
    
    # Converte em áudio (Edge TTS retorna MP3)
    audio_data = text_to_speech(response_text)
    
    if not audio_data:
        return Response(
            content='{"detail":"erro ao gerar áudio"}',
            media_type="application/json",
            status_code=500
        )
    
    # Detecta formato: Edge TTS = MP3, Piper = WAV
    is_mp3 = b'ID3' in audio_data[:20] or b'LAME' in audio_data[:100]
    media_type = "audio/mpeg" if is_mp3 else "audio/wav"
    
    print(f"[VOICE] Resposta: {response_text[:100]}")
    print(f"[VOICE] Áudio: {len(audio_data)} bytes, formato: {media_type}")
    
    # Headers customizados
    headers = {
        "X-Response-Text": response_text[:200].replace("\n", " "),
        "X-Lucy-Session": session_id,
        "X-Content-Length": str(len(audio_data))
    }
    
    return Response(
        content=audio_data,
        media_type=media_type,
        headers=headers
    )
