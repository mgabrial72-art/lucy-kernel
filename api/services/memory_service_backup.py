"""
Serviço de memória usando Mem0 (100% local com Ollama)
"""
import os
from pathlib import Path
from mem0 import Memory

# Garante que não vai tentar OpenAI
os.environ["OPENAI_API_KEY"] = ""

USER_ID = "capitao"
CONFIG = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "lucy_memories",
            "embedding_model_dims": 768,
            "on_disk": True,
            "path": str(Path(__file__).parent.parent.parent / "memory" / "qdrant_data")
        }
    },
    "embedder": {
        "provider": "ollama",
        "config": {"model": "nomic-embed-text:latest"}
    },
    "llm": {
        "provider": "ollama",
        "config": {"model": "qwen2.5:0.5b", "temperature": 0.1}
    }
}

# Instância única (singleton)
_memory = None

def get_memory() -> Memory:
    global _memory
    if _memory is None:
        _memory = Memory.from_config(CONFIG)
    return _memory

def add_memory(text: str, user_id: str = USER_ID) -> dict:
    """Adiciona uma nova memória."""
    m = get_memory()
    return m.add(text, user_id=user_id)

def search_memories(query: str, limit: int = 5, user_id: str = USER_ID) -> list:
    """Busca memórias relevantes."""
    m = get_memory()
    results = m.search(query, filters={"user_id": user_id}, limit=limit)
    return [r.get("memory", "") for r in results.get("results", [])]

def get_all_memories(user_id: str = USER_ID) -> list:
    """Retorna todas as memórias do usuário."""
    m = get_memory()
    # API nova do Mem0: user_id vai em filters
    results = m.get_all(filters={"user_id": user_id})
    return [r.get("memory", "") for r in results.get("results", [])]

def delete_memory(memory_id: str, user_id: str = USER_ID) -> bool:
    """Deleta uma memória específica."""
    try:
        m = get_memory()
        m.delete(memory_id, user_id=user_id)
        return True
    except Exception:
        return False

def format_memories_for_prompt(query: str, limit: int = 3) -> str:
    """Formata memórias relevantes para o prompt do LLM."""
    memories = search_memories(query, limit=limit)
    if not memories:
        return ""
    lines = ["MEMÓRIAS RELEVANTES DO CAPITÃO:"]
    for mem in memories:
        lines.append(f"  - {mem[:200]}")
    return "\n".join(lines)
