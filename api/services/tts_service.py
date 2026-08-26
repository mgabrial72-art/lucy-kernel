"""TTS Service OTIMIZADO - async correto + cache de frases comuns."""
import asyncio
import tempfile
import os
import subprocess
from pathlib import Path
from loguru import logger

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("[TTS] edge-tts não instalado")

from config.settings import settings
from api.services.cache_lru import tts_cache, COMMON_PHRASES


EDGE_VOICE = "pt-BR-FranciscaNeural"
PIPER_VOICE = "pt_BR-faber-medium"
VOICE_MODELS_DIR = settings.voice_dir / "models"


def _clean_text(text: str) -> str:
    """Limpa texto para TTS."""
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("😎", "").replace("😏", "").replace("🙏", "")
    return text.strip()


def _cache_key(text: str) -> str:
    """Gera chave de cache baseada no texto."""
    normalized = text.lower().strip()
    if normalized in COMMON_PHRASES:
        return f"common:{normalized}"
    # Para textos longos, usa hash
    return f"text:{hash(text)}"


def text_to_speech(text: str) -> bytes:
    """Converte texto em áudio (usa cache para frases comuns)."""
    clean_text = _clean_text(text)
    if not clean_text:
        clean_text = "Desculpa Capitão, não consegui processar."
    
    # Verifica cache
    cache_key = _cache_key(clean_text)
    cached_audio = tts_cache.get(cache_key)
    if cached_audio:
        logger.debug(f"💾 TTS cache hit: {clean_text[:30]}")
        return cached_audio
    
    # Tenta Edge TTS (feminino)
    if EDGE_TTS_AVAILABLE:
        try:
            audio_data = _edge_tts_sync(clean_text)
            if audio_data:
                logger.info(f"[TTS] Edge TTS: {len(audio_data)} bytes (voz feminina)")
                # Cacheia frases comuns
                if clean_text.lower().strip() in COMMON_PHRASES:
                    tts_cache.set(cache_key, audio_data)
                    logger.debug(f"💾 TTS cache set: {clean_text[:30]}")
                return audio_data
        except Exception as e:
            logger.warning(f"[TTS] Edge TTS falhou: {e}")
    
    # Fallback Piper
    logger.info("[TTS] Usando Piper (fallback)")
    return _piper_tts(clean_text)


def _edge_tts_sync(text: str) -> bytes:
    """Edge TTS - usa event loop existente se disponível."""
    async def _generate() -> bytes:
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
    
    # Tenta usar loop existente, senão cria novo
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Estamos em contexto async, cria nova thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate())
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(_generate())
    except RuntimeError:
        return asyncio.run(_generate())


def _piper_tts(text: str) -> bytes:
    """Piper TTS (fallback)."""
    voice_path = VOICE_MODELS_DIR / f"{PIPER_VOICE}.onnx"
    
    if not voice_path.exists():
        logger.error(f"[TTS] Piper voice não encontrada: {voice_path}")
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
            logger.error(f"[TTS] Piper erro: {result.stderr.decode()[:200]}")
            return b""
        
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
