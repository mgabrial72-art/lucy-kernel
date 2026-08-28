"""
Speech-to-Text usando faster-whisper (local, CPU-only)
"""
from faster_whisper import WhisperModel
import tempfile
import os

_model = None
WHISPER_MODEL = "tiny"  # Leve pra CPU

def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    return _model

def transcribe(audio_bytes: bytes) -> str:
    """Transcreve áudio em bytes para texto."""
    # Salva em arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    
    try:
        model = get_model()
        segments, info = model.transcribe(tmp_path, beam_size=5, language="pt")
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
    except Exception as e:
        print(f"[STT] Erro: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
