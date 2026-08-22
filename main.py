import json

import edge_tts
from fastapi.responses import StreamingResponse
import io

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse

app = FastAPI()

# ============================================================
# AUTH — API Key (Bearer ou X-API-Key)
# ============================================================
from fastapi import Header, HTTPException, Depends
from pathlib import Path as _Path

def _load_api_key() -> str:
    key_file = _Path(__file__).resolve().parent / ".api_key"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()
    # fallback de emergência (não ideal)
    return ""

API_KEY = _load_api_key()

async def verify_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if not API_KEY:
        # sem chave configurada = libera (modo degradado)
        return
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    elif x_api_key:
        provided = x_api_key.strip()
    if not provided or provided != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized — API key inválida ou ausente")

MODEL_NAME = "huihui_ai/qwen3-abliterated:8b"


def build_openai_json(text: str):
    return {
        "id": "chatcmpl-lucy",
        "object": "chat.completion",
        "created": 1700000000,
        "model": MODEL_NAME,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": text},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }


def stream_openai_chunks(user_msg: str):
    from services.model_router import generate_response, generate_response_turbo_stream
    try:
        for token in generate_response_stream(user_msg):
            chunk = {
                "id": "chatcmpl-lucy",
                "object": "chat.completion.chunk",
                "created": 1700000000,
                "model": MODEL_NAME,
                "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        error_chunk = {
            "id": "chatcmpl-lucy",
            "object": "chat.completion.chunk",
            "created": 1700000000,
            "model": MODEL_NAME,
            "choices": [{"index": 0, "delta": {"content": f"[ERRO: {str(e)}]"}, "finish_reason": None}]
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

    final_chunk = {
        "id": "chatcmpl-lucy",
        "object": "chat.completion.chunk",
        "created": 1700000000,
        "model": MODEL_NAME,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


def extract_user_message(body: dict) -> str:
    messages = body.get("messages", [])
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            return m.get("content", "")
    return body.get("message", "")


@app.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/v1", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/v1/models", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.api_route("/models", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def health_and_models(request: Request, _auth=Depends(verify_api_key)):
    if request.method == "POST":
        return await handle_openai_chat(request)
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}


@app.api_route("/v1", methods=["GET", "POST"])
@app.api_route("/v1/chat/completions", methods=["POST"])
@app.api_route("/chat/completions", methods=["POST"])
async def handle_openai_chat(request: Request, _auth=Depends(verify_api_key)):
    try:
        body = await request.json()
    except Exception:
        body = {}


@app.post("/chat")
async def legacy_chat(request: Request, _auth=Depends(verify_api_key)):
    body = await request.json()
    user_msg = body.get("message", "")
    from services.model_router import generate_response
    try:
        text = generate_response(user_msg)
    except Exception as e:
        text = f"Erro ao comunicar com o Ollama: {str(e)}"
    return JSONResponse(content={"response": text, "mode_used": "auto"})


@app.post("/chat/stream")
async def legacy_chat_stream(request: Request, _auth=Depends(verify_api_key)):
    body = await request.json()
    user_msg = body.get("message", "")
    from services.model_router import generate_response_stream

    async def token_generator():
        for token in generate_response_stream(user_msg):
            yield token

    return StreamingResponse(token_generator(), media_type="text/plain")


# ============================================================
# Aceita qualquer caminho/método que o cliente inventar
# ============================================================
@app.post("/v1/audio/speech")
async def generate_speech(
    request: Request,
    _auth=Depends(verify_api_key)
):
    """
    Gera áudio a partir de texto usando Edge TTS (Microsoft).
    Compatível com API OpenAI /v1/audio/speech
    
    Body:
    {
        "input": "Texto a ser falado",
        "voice": "pt-BR-FranciscaNeural",  # ou pt-BR-ThalitaMultilingualNeural
        "model": "tts-1"  # ignorado, mantido pra compatibilidade
    }
    
    Retorna: arquivo MP3 (streaming)
    """
    try:
        body = await request.json()
        text = body.get("input", "").strip()
        voice = body.get("voice", "pt-BR-FranciscaNeural")
        
        if not text:
            raise HTTPException(status_code=400, detail="Campo 'input' é obrigatório")
        
        # Gera áudio com Edge TTS
        communicate = edge_tts.Communicate(text, voice)
        audio_buffer = io.BytesIO()
        
        # Escreve MP3 no buffer
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        
        audio_buffer.seek(0)
        
        # Retorna como streaming de MP3
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar áudio: {str(e)}")







@app.get("/v1/capabilities")
async def capabilities(_auth=Depends(verify_api_key)):
    from services.capabilities import as_dict
    return as_dict()

@app.post("/v1/chat/voice")
async def chat_voice(request: Request, _auth=Depends(verify_api_key)):
    """Tasker / voz: MESMA qualidade do /chat, com memória completa + histórico."""
    import asyncio
    import io
    import re as _re
    
    raw = await request.body()
    question = raw.decode("utf-8", errors="ignore").strip()
    if not question:
        raise HTTPException(status_code=400, detail="pergunta vazia")
    
    print(f"[CHAT-VOICE] 🎙️ Pergunta recebida: {question[:80]}", flush=True)
    
    # USA A MESMA FUNÇÃO DO /chat (memória completa + histórico + contexto)
    try:
        from services.model_router import generate_response
        answer = await asyncio.to_thread(generate_response, question)
        print(f"[CHAT-VOICE] ✅ Resposta gerada ({len(answer)} chars): {answer[:100]}", flush=True)
    except Exception as e:
        print(f"[CHAT-VOICE] ❌ generate_response falhou: {e}", flush=True)
        import traceback
        traceback.print_exc()
        answer = "Desculpa capitão, travei aqui. Pode repetir?"
    
    # Limpa markdown e formatações pra TTS
    answer_clean = _re.sub(r"[*_#`\[\]]", "", answer or "").strip()
    answer_clean = _re.sub(r"\s+", " ", answer_clean)
    
    # Limita tamanho pra voz (máx ~500 chars = ~40s de áudio)
    if len(answer_clean) > 500:
        # Corta na última frase completa
        cut_pos = answer_clean.rfind(".", 0, 500)
        if cut_pos > 250:
            answer_clean = answer_clean[:cut_pos+1]
        else:
            answer_clean = answer_clean[:500] + "..."
    
    print(f"[CHAT-VOICE] 🔊 TTS final: {answer_clean[:150]}", flush=True)
    
    try:
        import edge_tts
        # Voz mais natural em PT-BR
        communicate = edge_tts.Communicate(answer_clean, "pt-BR-ThalitaMultilingualNeural")
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                buf.write(chunk["data"])
        buf.seek(0)
        print(f"[CHAT-VOICE] 🎵 Áudio gerado: {len(buf.getvalue())} bytes", flush=True)
        return StreamingResponse(buf, media_type="audio/mpeg")
    except Exception as e:
        print(f"[CHAT-VOICE] ❌ TTS falhou: {e}", flush=True)
        return JSONResponse({"error": "tts_failed", "text": answer_clean})




@app.post("/v1/chat/voice/stream")
async def chat_voice_stream(request: Request, _auth=Depends(verify_api_key)):
    """Streaming real: texto + TTS em paralelo."""
    from services.streaming_tts import stream_response_with_tts, generate_streaming_text
    from services.model_router import get_recent_history, MODEL, try_direct_answer
    from services.mark_l.memory_manager import load_memory, format_memory_for_prompt
    from config.identity import LUCY_SYSTEM_PROMPT
    
    raw = await request.body()
    question = raw.decode("utf-8", errors="ignore").strip()
    if not question:
        raise HTTPException(status_code=400, detail="pergunta vazia")
    
    # Hard routing primeiro
    direct = try_direct_answer(question)
    if direct:
        async def gen_direct():
            yield direct
        return StreamingResponse(
            stream_response_with_tts(gen_direct(), "pt-BR-FranciscaNeural"),
            media_type="audio/mpeg"
        )
    
    # Monta system prompt com histórico
    try:
        memory_block = format_memory_for_prompt(load_memory())
        history_block = get_recent_history(limit=4)
        system_prompt = (
            f"{LUCY_SYSTEM_PROMPT}\n\n{memory_block}\n\n"
            f"CONVERSA RECENTE:\n{history_block}\n\n"
            "REGRAS: Seja natural, direta, use humor. Chame de 'capitão'."
        )
    except Exception as e:
        print(f"[VOICE-STREAM] Erro montando prompt: {e}", flush=True)
        system_prompt = LUCY_SYSTEM_PROMPT
    
    # Gera streaming
    text_gen = generate_streaming_text(question, MODEL, system_prompt)
    
    return StreamingResponse(
        stream_response_with_tts(text_gen, "pt-BR-FranciscaNeural"),
        media_type="audio/mpeg"
    )



@app.get("/v1/reminders/due")
async def reminders_due(_auth=Depends(verify_api_key)):
    """Retorna lembretes vencidos para o Tasker fazer polling e falar.
    Marca como completed apos retornar (nao repete)."""
    import sqlite3
    from datetime import datetime
    DB = "/home/ubuntu/lucy-kernel/database/lucy_memory.db"
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, content, scheduled_for FROM proactive_tasks
            WHERE task_type='reminder' AND status IN ('active','pending','scheduled')
        """)
        rows = cur.fetchall()
        conn.close()

        now = datetime.now()
        due = []
        for rid, title, cnt, sched in rows:
            if not sched:
                continue  # sem data = nao dispara sozinho (so aparece no briefing)
            try:
                dt = datetime.fromisoformat(sched)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                if dt <= now:
                    due.append({"id": rid, "title": title or cnt, "content": cnt})
            except Exception:
                continue

        # Marca como completed para nao repetir
        if due:
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            for d in due:
                cur.execute("UPDATE proactive_tasks SET status='completed' WHERE id=?", (d["id"],))
            conn.commit()
            conn.close()

        return {"due": due}
    except Exception as e:
        return {"due": [], "error": str(e)}


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all_compat(request: Request, full_path: str, _auth=Depends(verify_api_key)):
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}
    try:
        body = await request.json()
    except Exception:
        body = {}
    if isinstance(body, dict) and body.get("messages"):
        return await handle_openai_chat(request)
    return {"object": "list", "data": [{"id": MODEL_NAME, "object": "model"}]}


# ============================================================
# ENDPOINT DE ÁUDIO (TTS) — Compatível com OpenAI API
# ============================================================

