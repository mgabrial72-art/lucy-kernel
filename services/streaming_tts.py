"""
Streaming TTS — Gera áudio em paralelo enquanto o modelo ainda está escrevendo.
"""
import asyncio
import edge_tts
import io
import re
from typing import AsyncGenerator

async def stream_response_with_tts(
    text_generator,
    voice: str = "pt-BR-FranciscaNeural"
) -> AsyncGenerator[bytes, None]:
    """
    Recebe texto em chunks, detecta frases completas, e gera TTS em paralelo.
    Retorna chunks de áudio MP3 conforme ficam prontos.
    """
    buffer = ""
    sentence_pattern = re.compile(r'([^.!?]+[.!?]+)\s*')
    
    async for text_chunk in text_generator:
        buffer += text_chunk
        
        # Procura frases completas
        while True:
            match = sentence_pattern.search(buffer)
            if not match:
                break
            
            sentence = match.group(1).strip()
            buffer = buffer[match.end():]
            
            # Remove markdown e formatações
            sentence_clean = re.sub(r'[*_#\[\]()]', '', sentence).strip()
            
            if len(sentence_clean) < 5:
                continue
            
            # Gera TTS desta frase
            try:
                communicate = edge_tts.Communicate(sentence_clean, voice)
                audio_buffer = io.BytesIO()
                
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])
                
                audio_buffer.seek(0)
                yield audio_buffer.getvalue()
                
            except Exception as e:
                print(f"[STREAM-TTS] Erro: {e}", flush=True)
    
    # Processa o que sobrou no buffer
    if buffer.strip():
        sentence_clean = re.sub(r'[*_#\[\]()]', '', buffer).strip()
        if len(sentence_clean) >= 5:
            try:
                communicate = edge_tts.Communicate(sentence_clean, voice)
                audio_buffer = io.BytesIO()
                
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buffer.write(chunk["data"])
                
                audio_buffer.seek(0)
                yield audio_buffer.getvalue()
            except Exception as e:
                print(f"[STREAM-TTS] Erro final: {e}", flush=True)


async def generate_streaming_text(user_message: str, model: str, system_prompt: str):
    """Gera texto em streaming do Ollama."""
    import requests
    
    full_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_message}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": True,  # Streaming real
        "think": False,
        "keep_alive": "24h",
        "options": {
            "num_ctx": 768,
            "num_thread": 4,
            "num_predict": 128,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1,
            "stop": ["<|im_end|>"]
        }
    }
    
    try:
        with requests.post(
            "http://127.0.0.1:11434/api/generate",
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
    except Exception as e:
        print(f"[STREAM-TEXT] Erro: {e}", flush=True)
        yield "Desculpa capitão, tive um problema aqui."
