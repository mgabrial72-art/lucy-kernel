"""Versão sem Mem0 pra testar performance pura"""
import requests
import time
from config.settings import OLLAMA_URL, OLLAMA_MODEL
from config.identity import LUCY_SYSTEM_PROMPT

OLLAMA_GENERATE_URL = f"{OLLAMA_URL}/api/generate"

def generate_response_fast(user_message: str) -> str:
    """Versão rápida sem Mem0"""
    prompt = f"{LUCY_SYSTEM_PROMPT}\n\nCapitão: {user_message}\nLucy:"
    
    full_prompt = (
        f"<|im_start|>system\n{prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_message}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "num_ctx": 1536,
            "num_thread": 4,
            "num_predict": 80,
            "temperature": 0.3,
            "top_p": 0.9
        }
    }
    
    response = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=180)
    return response.json().get("response", "").strip()

if __name__ == "__main__":
    print("Testando versão rápida (sem Mem0)...")
    
    # Teste 1
    t0 = time.perf_counter()
    resp1 = generate_response_fast("Qual minha comida favorita?")
    t1 = time.perf_counter()
    print(f"Teste 1: {(t1-t0)*1000:.0f}ms")
    print(f"Resposta: {resp1[:100]}")
    
    # Teste 2
    t0 = time.perf_counter()
    resp2 = generate_response_fast("Quando foi o pedido de casamento?")
    t1 = time.perf_counter()
    print(f"Teste 2: {(t1-t0)*1000:.0f}ms")
    print(f"Resposta: {resp2[:100]}")
