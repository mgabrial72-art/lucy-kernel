"""
Serviço de Text-to-Speech usando Edge TTS (voz feminina PT-BR)
Fallback para Piper se Edge TTS falhar
"""
import asyncio
import tempfile
import os
from pathlib import Path

# Tenta importar edge-tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[TTS] edge-tts não instalado")

# Voz feminina PT-BR da Microsoft
EDGE_VOICE = "pt-BR-FranciscaNeural"

# Fallback para Piper
PIPER_VOICE = "pt_BR-faber-medium"
BASE_DIR = Path(__file__).parent.parent.parent
VOICE_MODELS_DIR = BASE_DIR / "voice" / "models"

def text_to_speech(text: str) -> bytes:
    """Converte texto em áudio usando Edge TTS (feminina) ou Piper (fallback)."""
    
    # Limpa texto
    clean_text = text.replace("**", "").replace("*", "").replace("`", "")
    clean_text = clean_text.replace("😎", "").replace("😏", "").replace("🙏", "")
    
    if not clean_text.strip():
        clean_text = "Desculpa Capitão, não consegui processar."
    
    # Tenta Edge TTS primeiro (voz feminina)
    if EDGE_TTS_AVAILABLE:
        try:
            audio_data = _edge_tts_sync(clean_text)
            if audio_data:
                print(f"[TTS] Edge TTS: {len(audio_data)} bytes (voz feminina)")
                return audio_data
        except Exception as e:
            print(f"[TTS] Edge TTS falhou: {e}")
    
    # Fallback para Piper (voz masculina)
    print("[TTS] Usando Piper (fallback)")
    return _piper_tts(clean_text)

def _edge_tts_sync(text: str) -> bytes:
    """Edge TTS síncrono (wrapper para async)."""
    async def _generate():
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            communicate = edge_tts.Communicate(text, EDGE_VOICE)
            await communicate.save(tmp_path)
            
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    return asyncio.run(_generate())

def _piper_tts(text: str) -> bytes:
    """Piper TTS (fallback)."""
    import subprocess
    
    voice_path = VOICE_MODELS_DIR / f"{PIPER_VOICE}.onnx"
    
    if not voice_path.exists():
        print(f"[TTS] Piper voice não encontrada: {voice_path}")
        return b""
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        result = subprocess.run(
            ["piper", "--model", str(voice_path), "--output_file", tmp_path],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"[TTS] Piper erro: {result.stderr.decode()[:200]}")
            return b""
        
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
