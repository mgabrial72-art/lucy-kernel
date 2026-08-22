"""Lista de funcionalidades ATIVAS da Lucy."""

CAPABILITIES = [
    {"id": "chat", "nome": "Conversa local", "desc": "Papo, memoria, familia, rotina — modelo local", "ativo": True, "onde": "local"},
    {"id": "voice", "nome": "Voz / Tasker", "desc": "Resposta em audio (/v1/chat/voice)", "ativo": True, "onde": "local+tts"},
    {"id": "memory", "nome": "Memoria Mark-L", "desc": "Identidade, relacionamentos, notas, projetos", "ativo": True, "onde": "local"},
    {"id": "reminders", "nome": "Lembretes", "desc": "Criar e listar lembretes", "ativo": True, "onde": "local"},
    {"id": "weather", "nome": "Clima", "desc": "Temperatura em Santo Andre (Open-Meteo)", "ativo": True, "onde": "local"},
    {"id": "web_research", "nome": "Pesquisa web", "desc": "Noticias, placar, fatos — Gemini + Google Search", "ativo": False, "onde": "gemini"},
    {"id": "maps", "nome": "Mapas / local", "desc": "Lugares e contexto local via Gemini", "ativo": False, "onde": "gemini"},
    {"id": "hard_routing", "nome": "Respostas diretas", "desc": "Familia, trabalho, hobbies sem modelo", "ativo": True, "onde": "local"},
]

def list_active():
    return [c for c in CAPABILITIES if c.get("ativo")]

def format_for_prompt(max_chars: int = 350) -> str:
    lines = ["FUNCIONALIDADES ATIVAS:"]
    for c in list_active():
        lines.append(f"- {c['nome']}: {c['desc']}")
    return "\n".join(lines)[:max_chars]

def as_dict():
    return {"capabilities": list_active()}
