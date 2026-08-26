"""Serviço de LLM com contexto dinâmico."""
import re
import requests
from loguru import logger
from config.settings import settings
from api.services.context_cache_service import get_context, is_context_question, get_status_summary


OLLAMA_MODEL = settings.ollama_model
OLLAMA_GENERATE_URL = f"{settings.ollama_url}/api/generate"


def build_prompt_with_context(user_message: str, conversation_history: list = None) -> str:
    """Constrói prompt com contexto cacheado."""
    
    context = get_context()
    summary = context.get("summary", "")
    
    if not summary:
        summary = get_status_summary()
    
    # Histórico
    if conversation_history and len(conversation_history) > 0:
        history_lines = []
        for msg in conversation_history[-8:]:
            if msg.get("role") == "user":
                history_lines.append(f"Capitão: {msg.get('content', '')}")
            elif msg.get("role") == "assistant":
                history_lines.append(f"Lucy: {msg.get('content', '')}")
        
        history_text = "\n".join(history_lines)
        prompt = f"CONTEXTO ATUAL: {summary}\n\n{history_text}\nCapitão: {user_message}\nLucy:"
        
        logger.debug(f"[LLM] Histórico: {len(conversation_history)} mensagens")
    else:
        prompt = f"CONTEXTO ATUAL: {summary}\n\nCapitão: {user_message}\nLucy:"
    
    # Se for pergunta contextual, reforça
    if is_context_question(user_message):
        prompt = f"INSTRUÇÃO: O Capitão quer saber o status atual. Use APENAS os dados do CONTEXTO ATUAL e responda em português natural.\n\n{prompt}"
    
    return prompt


def generate_response(
    user_message: str,
    conversation_history: list = None,
    num_predict: int = 100,
    temperature: float = 0.2,
    timeout: int = None
) -> str:
    """Gera resposta."""
    
    if timeout is None:
        timeout = settings.ollama_timeout
    
    prompt = build_prompt_with_context(user_message, conversation_history)
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": 2048,
            "num_predict": num_predict,
            "temperature": temperature,
            "top_p": 0.9,
            "repeat_penalty": 1.2,
            "stop": ["Capitão:", "Pergunta:", "\n\n"]
        }
    }
    
    try:
        response = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        result = data.get("response", "").strip()
        
        # Limpeza de erros comuns
        replacements = {
            r"nuvemado": "nublado",
            r"nuvemoso": "nublado",
            r"sentido térmico": "sensação térmica",
            r"sentido termico": "sensação térmica",
            r"Capitão Marcelo": "Capitão",
            r"capitão marcelo": "Capitão"
        }
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        for stop in ["Capitão:", "Pergunta:"]:
            if stop in result:
                result = result.split(stop)[0].strip()
        
        if len(result) > 500:
            result = result[:500].rsplit('.', 1)[0] + "."
        
        logger.debug(f"[LLM] Resposta: {result[:100]}")
        return result
        
    except Exception as e:
        logger.error(f"[LLM] Erro: {e}")
        return f"Desculpa Capitão, tive um problema: {str(e)[:50]}"
