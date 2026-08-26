"""TTS Service - Cache com hash estável (MD5)."""
import asyncio
import hashlib
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
    text = text.replace("**", "").replace("*", "").replace("`", "")
    text = text.replace("😎", "").replace("😏", "").replace("🙏", "")
    return text.strip()


def _cache_key(text: str) -> str:
    """Hash estável usando MD5 (não muda entre execuções)."""
    normalized = text.lower().strip()
    if normalized in COMMON_PHRASES:
        return f"common:{normalized}"
    text_hash = hashlib.md5(normalized.encode('utf-8')).hexdigest()[:16]
    return f"text:{text_hash}"


def text_to_speech(text: str) -> bytes:
    """Converte texto em áudio (com cache estável)."""
    clean_text = _clean_text(text)
    if not clean_text:
        clean_text = "Desculpa Capitão, não consegui processar."
    
    cache_key = _cache_key(clean_text)
    cached_audio = tts_cache.get(cache_key)
    if cached_audio:
        logger.info(f"💾 TTS cache hit: {clean_text[:30]}")
        return cached_audio
    
    if EDGE_TTS_AVAILABLE:
        try:
            audio_data = _edge_tts_sync(clean_text)
            if audio_data:
                logger.info(f"[TTS] Edge TTS: {len(audio_data)} bytes")
                if clean_text.lower().strip() in COMMON_PHRASES or len(clean_text) < 100:
                    tts_cache.set(cache_key, audio_data)
                return audio_data
        except Exception as e:
            logger.warning(f"[TTS] Edge TTS falhou: {e}")
    
    return _piper_tts(clean_text)


def _edge_tts_sync(text: str) -> bytes:
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
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _generate())
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(_generate())
    except RuntimeError:
        return asyncio.run(_generate())


def _piper_tts(text: str) -> bytes:
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
            return b""
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
