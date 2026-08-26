"""Serviço de memória usando Mem0 (Qdrant local)"""
import os
from pathlib import Path

os.environ["OPENAI_API_KEY"] = ""  # Evita warning do Mem0

try:
    from mem0 import Memory
    
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

    _memory = None

    def get_memory():
        """Retorna instância do Mem0 (singleton)."""
        global _memory
        if _memory is None:
            _memory = Memory.from_config(CONFIG)
        return _memory

    def add_memory(text: str, user_id: str = USER_ID) -> dict:
        """Adiciona memória."""
        try:
            m = get_memory()
            return m.add(text, user_id=user_id)
        except Exception as e:
            print(f"[MEM0] Erro ao adicionar: {e}")
            return {}

    def search_memories(query: str, limit: int = 3, user_id: str = USER_ID) -> list:
        """Busca memórias relevantes."""
        try:
            m = get_memory()
            results = m.search(query, filters={"user_id": user_id}, limit=limit)
            return [r.get("memory", "") for r in results.get("results", [])]
        except Exception as e:
            print(f"[MEM0] Erro ao buscar: {e}")
            return []

    def get_all_memories(user_id: str = USER_ID) -> list:
        """Lista todas as memórias."""
        try:
            m = get_memory()
            results = m.get_all(filters={"user_id": user_id})
            return [r.get("memory", "") for r in results.get("results", [])]
        except Exception as e:
            print(f"[MEM0] Erro: {e}")
            return []

    def format_memories_for_prompt(query: str, limit: int = 3) -> str:
        """Formata memórias para o prompt."""
        memories = search_memories(query, limit=limit)
        if not memories:
            return ""
        lines = ["MEMÓRIAS RELEVANTES:"]
        for mem in memories:
            lines.append(f"  - {mem[:200]}")
        return "\n".join(lines)

except ImportError:
    print("[MEM0] Mem0 não instalado. Usando stub.")
    
    def get_memory(): return None
    def add_memory(*args, **kwargs): return {}
    def search_memories(*args, **kwargs): return []
    def get_all_memories(*args, **kwargs): return []
    def format_memories_for_prompt(*args, **kwargs): return ""
