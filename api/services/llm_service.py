"""Serviço de LLM OTIMIZADO - contexto só em perguntas contextuais."""
import re
import requests
from loguru import logger
from config.settings import settings
from api.services.context_cache_service import (
    is_context_question, get_status_summary
)


OLLAMA_MODEL = settings.ollama_model
OLLAMA_GENERATE_URL = f"{settings.ollama_url}/api/generate"

# Regex de limpeza pré-compilado (mais rápido)
_CLEAN_PATTERNS = [
    (re.compile(r"nuvemado", re.IGNORECASE), "nublado"),
    (re.compile(r"nuvemoso", re.IGNORECASE), "nublado"),
    (re.compile(r"sentido térmico", re.IGNORECASE), "sensação térmica"),
    (re.compile(r"sentido termico", re.IGNORECASE), "sensação térmica"),
    (re.compile(r"Capitão Marcelo", re.IGNORECASE), "Capitão"),
]


def _build_prompt(user_message: str, conversation_history: list = None) -> str:
    """Constrói prompt INCLUINDO contexto APENAS se for pergunta contextual."""
    
    is_contextual = is_context_question(user_message)
    
    # Monta histórico
    history_lines = []
    if conversation_history and len(conversation_history) > 0:
        for msg in conversation_history[-8:]:
            role = "Capitão" if msg.get("role") == "user" else "Lucy"
            history_lines.append(f"{role}: {msg.get('content', '')}")
    
    # Adiciona contexto SÓ se necessário (economia de tokens!)
    context_prefix = ""
    if is_contextual:
        summary = get_status_summary()
        if summary:
            context_prefix = f"CONTEXTO ATUAL: {summary}\n\n"
            logger.debug("[LLM] Contexto incluído (pergunta contextual)")
    
    # Monta prompt completo
    if history_lines:
        history_text = "\n".join(history_lines)
        prompt = f"{context_prefix}{history_text}\nCapitão: {user_message}\nLucy:"
    else:
        prompt = f"{context_prefix}Capitão: {user_message}\nLucy:"
    
    # Instrução reforçada para perguntas contextuais
    if is_contextual:
        prompt = f"INSTRUÇÃO: Use APENAS dados do CONTEXTO ATUAL. Responda em português natural.\n\n{prompt}"
    
    return prompt


def _clean_response(result: str) -> str:
    """Limpa erros comuns de português."""
    for pattern, replacement in _CLEAN_PATTERNS:
        result = pattern.sub(replacement, result)
    
    for stop in ["Capitão:", "Pergunta:"]:
        if stop in result:
            result = result.split(stop)[0].strip()
    
    if len(result) > 500:
        result = result[:500].rsplit('.', 1)[0] + "."
    
    return result


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
    
    prompt = _build_prompt(user_message, conversation_history)
    
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
        
        cleaned = _clean_response(result)
        logger.debug(f"[LLM] Resposta: {cleaned[:100]}")
        return cleaned
        
    except Exception as e:
        logger.error(f"[LLM] Erro: {e}")
        return f"Desculpa Capitão, tive um problema: {str(e)[:50]}"
