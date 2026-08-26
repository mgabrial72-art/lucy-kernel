"""
Endpoint de debug: mostra timing de cada etapa (versão simplificada)
"""
import time
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.llm_service import generate_response
from api.services.personal_data_service import load_personal_facts
import requests

router = APIRouter()

class DebugRequest(BaseModel):
    message: str
    skip_memory: bool = False

@router.post("/debug/timing")
async def timing(request: DebugRequest):
    """Retorna timing detalhado de cada etapa."""
    timings = {}
    
    # Etapa 1: Carregar dados pessoais
    t0 = time.perf_counter()
    personal_facts = load_personal_facts() if not request.skip_memory else ""
    timings["load_personal_facts"] = round((time.perf_counter() - t0) * 1000, 2)
    timings["personal_facts_size"] = len(personal_facts)
    
    # Etapa 2: Gerar resposta (timing total do Ollama)
    t0 = time.perf_counter()
    response_text = generate_response(request.message)
    timings["ollama_total"] = round((time.perf_counter() - t0) * 1000, 2)
    
    # Tenta extrair métricas do Ollama (via request direto)
    try:
        from config.settings import OLLAMA_URL
        payload = {
            "model": "lucy-optimized",
            "prompt": f"Capitão: {request.message}\nLucy:",
            "stream": False,
            "options": {"num_predict": 20, "num_ctx": 2048}
        }
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            timings["ollama_load_duration_ms"] = round(data.get("load_duration", 0) / 1_000_000, 2)
            timings["ollama_prompt_eval_duration_ms"] = round(data.get("prompt_eval_duration", 0) / 1_000_000, 2)
            timings["ollama_eval_duration_ms"] = round(data.get("eval_duration", 0) / 1_000_000, 2)
            timings["ollama_tokens_per_second"] = round(
                data.get("eval_count", 0) / (data.get("eval_duration", 1) / 1_000_000_000), 2
            )
    except Exception as e:
        timings["ollama_metrics_error"] = str(e)
    
    timings["total"] = round(sum(v for k, v in timings.items() 
                                  if isinstance(v, (int, float)) and "ms" in k), 2)
    
    return {
        "timings": timings,
        "response": response_text[:200]
    }

@router.get("/debug/models")
async def models():
    """Lista modelos em RAM."""
    import subprocess
    result = subprocess.run(["ollama", "ps"], capture_output=True, text=True)
    return {"models": result.stdout}

@router.get("/debug/cpu")
async def cpu():
    """Status de CPU."""
    import subprocess
    result = subprocess.run(
        ["top", "-bn1"],
        capture_output=True,
        text=True
    )
    cpu_lines = [l for l in result.stdout.split("\n") if "Cpu" in l][:1]
    return {"cpu": cpu_lines}
