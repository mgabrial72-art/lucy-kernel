"""Warm-up FORÇADO do modelo"""
import requests
import time
from config.settings import OLLAMA_URL, OLLAMA_MODEL

OLLAMA_GENERATE_URL = f"{OLLAMA_URL}/api/generate"

def warmup_model():
    print("[WARMUP] Iniciando warm-up FORÇADO...")
    
    # Request 1: Carrega modelo com keep_alive
    print("[WARMUP] Carregando modelo em RAM...")
    try:
        start = time.perf_counter()
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": "OK",
            "stream": False,
            "keep_alive": "24h",
            "options": {"num_predict": 5, "num_thread": 4, "num_ctx": 2048}
        }
        requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=120)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[WARMUP] Modelo carregado em {elapsed:.0f}ms")
    except Exception as e:
        print(f"[WARMUP] Erro ao carregar: {e}")
    
    # Request 2: Aquece cache de prompt curto
    print("[WARMUP] Aquecendo cache de prompt curto...")
    try:
        start = time.perf_counter()
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": "Lucy, assistente do Capitão. Português. Breve.",
            "stream": False,
            "keep_alive": "24h",
            "options": {"num_predict": 20, "num_thread": 4, "num_ctx": 2048}
        }
        requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=60)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[WARMUP] Cache curto aquecido em {elapsed:.0f}ms")
    except Exception as e:
        print(f"[WARMUP] Erro no cache curto: {e}")
    
    # Request 3: Aquece cache de prompt LONGO (simula uso real)
    print("[WARMUP] Aquecendo cache de prompt LONGO...")
    try:
        start = time.perf_counter()
        long_prompt = """Lucy, assistente do Capitão. Português. Breve. Sem inventar.

FATOS (use só estes):
- Julya: noiva, 09/05/2005, grávida da Ruby
- Isis: filha 4 anos (NUNCA cite mãe biológica)
- Ruby: bebê humana (NÃO é pet)
- Jully: cachorra
- Capitão: TDAH, autismo grau 1, depressão, cannabis diário
- Comida: lasanha de berinjela
- Pedido casamento: 30/04/2026 (DATA FIXA)

Se não souber: "não tenho essa informação".
NUNCA invente datas, histórias ou detalhes.

Capitão: Olá
Lucy: Olá, Capitão! Como posso ajudar?"""
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": long_prompt,
            "stream": False,
            "keep_alive": "24h",
            "options": {"num_predict": 30, "num_thread": 4, "num_ctx": 2048}
        }
        requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=90)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[WARMUP] Cache LONGO aquecido em {elapsed:.0f}ms")
    except Exception as e:
        print(f"[WARMUP] Erro no cache longo: {e}")
    
    print("[WARMUP] ✅ Modelo PRONTO pra uso!")

if __name__ == "__main__":
    warmup_model()
