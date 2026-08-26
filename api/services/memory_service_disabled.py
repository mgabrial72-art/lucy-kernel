"""Mem0 desabilitado temporariamente pra testar performance"""

def add_memory(text: str, user_id: str = "capitao") -> dict:
    return {"status": "disabled"}

def search_memories(query: str, limit: int = 5, user_id: str = "capitao") -> list:
    return []

def get_all_memories(user_id: str = "capitao") -> list:
    return []

def format_memories_for_prompt(query: str, limit: int = 3) -> str:
    return ""
