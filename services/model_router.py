"""
Lucy Model Router — Versão Limpa
Usa Mark-L (JSON) como fonte única de memória.
"""
import time
import json
import requests
from config.identity import LUCY_SYSTEM_PROMPT
from database.db import save_chat, get_recent_history
from services.behavior_engine import get_behavior
from services.mark_l.memory_manager import load_memory, format_memory_for_prompt
from services.task_scheduler import create_reminder, list_active_tasks
import re
from datetime import datetime, timedelta
from config.timezone import now_sp
import sqlite3
import os

MODEL = "huihui_ai/qwen3-abliterated:8b"

DB_PATH = '/home/ubuntu/lucy-kernel/database/lucy_memory.db'
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"





def _get_weather_text() -> str:
    """Retorna texto do clima cacheado (rápido, sem modelo)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT value FROM proactive_cache WHERE key='weather:santo_andre'")
        row = cur.fetchone()
        conn.close()
        if row:
            import json
            w = json.loads(row[0])
            return f"Clima em Santo André: {w.get('temperature_c')}°C, {w.get('description')}."
    except Exception as e:
        print(f"[WEATHER] Erro: {e}", flush=True)
    return ""

def _get_user_reminders_text() -> str:
    """Lista lembretes criados pelo usuario (exclui tarefas proativas do sistema)."""
    try:
        tasks = list_active_tasks()
        user_rem = []
        skip_words = ["clima", "weather", "ruby", "bebe", "aniversario", "dasn", "mei", "keepalive", "ping", "atualizar"]
        for t in tasks:
            text = t.get("content") or t.get("title") or ""
            low = str(text).lower()
            if not text or any(w in low for w in skip_words):
                continue
            user_rem.append(str(text))
        if user_rem:
            return "Seus lembretes: " + "; ".join(user_rem[:3]) + "."
    except Exception as e:
        print(f"[REMINDERS] Erro: {e}", flush=True)
    return "Sem lembretes seus."

def _get_ruby_text() -> str:
    """Contagem Ruby se < 30 dias."""
    try:
        from datetime import datetime
        ruby_date = datetime(2026, 11, 19)
        now = datetime.now()
        days_left = (ruby_date - now).days
        if 0 <= days_left <= 30:
            return f"Ruby: faltam {days_left} dias."
    except Exception as e:
        print(f"[RUBY] Erro: {e}", flush=True)
    return ""

def try_direct_answer(user_message: str):
    """
    Hard Routing — respostas DIRETAS sem chamar o modelo.
    Retorna string (resposta) ou None (vai pro modelo).
    """
    msg = user_message.lower().strip()

    # ===== LEMBRETES =====
    reminder_keywords = ["me lembra", "me lembre", "lembra de", "agenda lembrete",
                         "me avisa", "nao esquece", "não esquece"]
    if any(kw in msg for kw in reminder_keywords):
        try:
            content_text = user_message
            for kw in reminder_keywords:
                content_text = content_text.lower().replace(kw, "").strip()
            content_text = re.sub(r"^(de|do|da|para|pra|que|sobre)\s+", "", content_text)
            
            if not content_text:
                return "Claro, Capitão! Mas me diz o que quer que eu lembre?"
            
            scheduled_for = None
            recurrence = "once"
            
            if "amanha" in msg or "amanhã" in msg:
                scheduled_for = now_sp() + timedelta(days=1)
                scheduled_for = scheduled_for.replace(hour=8, minute=0, second=0)
            elif "semana que vem" in msg or "proxima semana" in msg:
                scheduled_for = now_sp() + timedelta(weeks=1)
            elif "todos os dias" in msg or "diariamente" in msg:
                recurrence = "daily"
            elif "toda semana" in msg or "semanalmente" in msg:
                recurrence = "weekly"
            
            task_id = create_reminder(
                title=content_text[:50],
                content=content_text,
                scheduled_for=scheduled_for,
                recurrence=recurrence,
                priority=4
            )
            
            if recurrence == "once" and scheduled_for:
                date_str = scheduled_for.strftime("%d/%m/%Y às %H:%M")
                return f"Pronto, Capitão! Vou te lembrar de \"{content_text[:60]}\" no dia {date_str}."
            elif recurrence == "daily":
                return f"Pronto, Capitão! Vou te lembrar de \"{content_text[:60]}\" todos os dias."
            elif recurrence == "weekly":
                return f"Pronto, Capitão! Vou te lembrar de \"{content_text[:60]}\" toda semana."
            else:
                return f"Pronto, Capitão! Lembrete criado: \"{content_text[:60]}\"."
        except Exception as e:
            return f"Erro criando lembrete: {e}"
    
    # Lista de lembretes
    list_keywords = ["meus lembretes", "listar lembretes", "quais sao meus lembretes",
                     "mostra meus lembretes", "minhas tarefas"]
    if any(kw in msg for kw in list_keywords):
        try:
            tasks = list_active_tasks()
            if not tasks:
                return "Você não tem nenhum lembrete ativo, Capitão."
            
            response = f"Você tem {len(tasks)} lembrete(s) ativo(s):\n"
            for t in tasks[:10]:
                task_type = "[L]" if t['task_type'] == 'reminder' else "[M]"
                response += f"{task_type} {t['title'][:50]}\n"
            return response
        except Exception as e:
            return f"Erro listando: {e}"

    # ===== FAMÍLIA (HARD ROUTING) =====
    family_keywords = ["quem é a julya", "quem e a julya", "quem é a isis", "quem e a isis",
                       "quem é a ruby", "quem e a ruby", "quem é a jully", "quem e a jully",
                       "minha família", "minha familia", "quem são minhas filhas", "quem sao minhas filhas"]
    if any(k in msg for k in family_keywords):
        if "julya" in msg:
            return "Julya é sua noiva, Capitão. Nasceu em 09/05/2005 (21 anos). Vocês ficaram noivos em 30/04/2026. Ela está grávida da Ruby, que nasce até 19/11/2026."
        elif "isis" in msg:
            return "Isis é sua filha, Capitão. Nasceu em 17/08/2022 e vai fazer 4 anos em 17/08/2026. Ela mora com a mãe e você pega nos fins de semana. Está fazendo tratamento de estrabismo."
        elif "ruby" in msg:
            return "Ruby é a bebê que está por vir, Capitão. Filha sua com a Julya. Nasce até 19/11/2026."
        elif "jully" in msg:
            return "Jully é a cachorra da família, Capitão. Companheira da casa."
        else:
            return "Sua família: Julya (noiva grávida da Ruby), Isis (filha de 4 anos), Ruby (bebê a caminho), Jully (cachorra)."

    # ===== TRABALHO (HARD ROUTING) =====
    work_keywords = ["onde eu trabalho", "onde trabalho", "onde você trabalha", "onde voce trabalha",
                     "meu trabalho", "qual meu turno", "que horas eu trabalho", "que horas trabalho",
                     "escala de trabalho", "qual é meu trabalho", "qual e meu trabalho",
                     "o que eu faço", "o que eu faco", "minha profissão", "minha profissao"]
    if any(k in msg for k in work_keywords):
        return "Você trabalha como porteiro em São Caetano do Sul, Capitão. Turno fixo das 06:00 às 18:00. Acorda às 03:30, sai de casa às 04:15. Também é MEI com registro ativo."

    # ===== HOBBIES (HARD ROUTING) =====
    hobbies_keywords = ["meus hobbies", "o que eu gosto de fazer",
                        "meus interesses", "o que eu curto", "hobbies"]
    if any(k in msg for k in hobbies_keywords):
        return "Seus hobbies, Capitão: PUBG Mobile, Oxide: Survival Island, Minecraft modificado (com luvas e controles dedicados), fotografia noturna de estrelas e constelações, eletrônica e robótica DIY. Você também curte trap, ufologia, ficção científica e mistérios de civilizações antigas."

    # ===== RUBY COUNTDOWN =====
    ruby_keywords = ["ruby", "bebê nascer", "bebe nascer", "dias faltam",
                     "quantos dias", "contagem regressiva", "gestação", "gestacao"]
    if any(k in msg for k in ruby_keywords):
        today = datetime.now()
        window_limit = datetime(2026, 11, 19)
        days = (window_limit - today).days
        if days < 0:
            return "A Ruby já nasceu ou está nascendo, Capitão! 🎉"
        elif days <= 7:
            return f"Capitão, faltam só {days} dias pra data limite da Ruby (19/11)! Última semana!"
        elif days <= 30:
            return f"Faltam {days} dias pra data limite da Ruby (19/11/2026). Reta final!"
        else:
            return f"Faltam {days} dias pra data limite da Ruby (19/11/2026)."

    # ===== DATA/HORA =====
    date_keywords = ["que dia é hoje", "que dia e hoje", "data de hoje",
                     "que horas são", "que horas sao", "dia da semana"]
    if any(k in msg for k in date_keywords):
        now = now_sp()
        weekdays = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
        return f"Hoje é {weekdays[now.weekday()]}, {now.strftime('%d/%m/%Y')}, {now.strftime('%H:%M')}."

    # ===== CLIMA =====
    weather_keywords = ["clima", "tempo hoje", "temperatura", "vai chover", "previsão"]
    if any(k in msg for k in weather_keywords):
        try:
            import sqlite3, json as j
            conn = sqlite3.connect("/home/ubuntu/lucy-kernel/database/lucy_memory.db")
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='proactive_cache'")
            if cur.fetchone():
                cur.execute(
                    "SELECT value FROM proactive_cache WHERE key='weather:santo_andre' AND expires_at > ?",
                    (datetime.now(),)
                )
                row = cur.fetchone()
                conn.close()
                if row:
                    w = j.loads(row[0])
                    return f"Em Santo André: {w.get('temperature_c')}°C, {w.get('description')}, umidade {w.get('humidity')}%."
            conn.close()
        except Exception:
            pass

    # ---- AGENDA / COMPROMISSO (hard route) ----
    msg_lower = user_message.lower()
    if any(k in msg_lower for k in ["agendado", "agenda", "compromisso", "marcado", "tenho algo"]):
        return f"Capitao, {_get_user_reminders_text()}"
    
    # ---- OI / OLA com briefing util (sem modelo, <1s) ----
    is_greeting = (
        msg_lower.startswith("oi")
        or msg_lower.startswith("ola") or msg_lower.startswith("olá")
        or msg_lower.startswith("e ai") or msg_lower.startswith("e aí")
        or msg_lower.startswith("bom dia") or msg_lower.startswith("boa tarde") or msg_lower.startswith("boa noite")
        or msg_lower.startswith("opa")
    )
    if is_greeting:
        parts = ["Oi, Capitao!"]
        weather = _get_weather_text()
        if weather:
            parts.append(weather)
        reminders = _get_user_reminders_text()
        if "Sem lembretes" not in reminders:
            parts.append(reminders)
        ruby = _get_ruby_text()
        if ruby:
            parts.append(ruby)
        parts.append("O que manda?")
        return " ".join(parts)
    
    return None




def _format_history(history_list):
    """Converte lista de dicts do db em texto legivel pro modelo."""
    if not history_list:
        return ""
    lines = []
    for msg in history_list:
        role = msg.get("role", "")
        content = str(msg.get("content", ""))
        if role == "user":
            lines.append(f"Marcelo: {content[:100]}")
        elif role == "assistant":
            lines.append(f"Lucy: {content[:150]}")
    return "\n".join(lines)

def generate_response(user_message: str, mode: str = "auto", external_context=None) -> str:
    """
    Gera resposta usando Mark-L como fonte única de memória.
    """
    _t0 = time.perf_counter()

    # 1. Hard routing primeiro
    direct_answer = try_direct_answer(user_message)
    if direct_answer:
        print(f"[TIMING] Resposta direta: {time.perf_counter() - _t0:.3f}s", flush=True)
        save_chat(user_message, direct_answer, MODEL)
        return direct_answer

    # 2. Behavior engine (modo ativo + prompt especializado)
    behavior_instruction = ""
    try:
        behavior = get_behavior(user_message, "trabalho")
        num_predict = behavior.num_predict
        temperature = behavior.temperature
        top_p = behavior.top_p
        behavior_instruction = behavior.system_instruction
    except Exception:
        num_predict, temperature, top_p = 128, 0.7, 0.9

    # 3. Carrega memória do Mark-L (JSON completo)
    try:
        full_memory = load_memory()
        memory_block = format_memory_for_prompt(full_memory)[:1900]
        print(f"[MEMÓRIA-MARKL] {len(memory_block)} chars injetados (teto 500)", flush=True)
    except Exception as e:
        print(f"[MEMÓRIA-MARKL] Erro: {e}", flush=True)
        memory_block = ""

    # 4. System prompt + historico de conversa
    history_block = get_recent_history(limit=1)[:250]
    
    print(f"[ROUTER] Historico: {len(history_block)} chars", flush=True)
    if history_block:
        print(f"[ROUTER] Historico preview: {history_block[:200]}...", flush=True)
    
    system_prompt = f"{LUCY_SYSTEM_PROMPT}\n\n{memory_block}\n\n"
    
    if history_block:
        system_prompt += f"CONVERSA RECENTE (use como contexto):\n{history_block}\n\n"
    
    print(f"[ROUTER] System prompt final: {len(system_prompt)} chars", flush=True)

    # 5. Monta prompt completo (formato /api/generate)
    full_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_message}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    
    print(f"[ROUTER] Prompt completo enviado ({len(full_prompt)} chars):", flush=True)
    print(f"[ROUTER] {full_prompt[:500]}...", flush=True)

    # 6. Payload (formato /api/generate)
    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "options": {
            "num_ctx": 1024,
            "num_thread": 4,
            "num_predict": num_predict,
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": 1.1,
            "stop": ["<|im_end|>"]
        }
    }

    # 7. Chamada ao Ollama
    try:
        _t1 = time.perf_counter()
        response = requests.post(OLLAMA_URL, json=payload, timeout=300)
        print(f"[TIMING] Ollama: {time.perf_counter() - _t1:.1f}s", flush=True)

        response.raise_for_status()
        
        # Log do tipo de resposta
        raw_text = response.text
        print(f"[OLLAMA] Response type: {type(response)}", flush=True)
        print(f"[OLLAMA] Status code: {response.status_code}", flush=True)
        
        # Tenta parsear JSON
        try:
            data = response.json()
            print(f"[OLLAMA] JSON parsed successfully, type: {type(data)}", flush=True)
        except Exception as json_err:
            print(f"[OLLAMA] JSON parse error: {json_err}", flush=True)
            print(f"[OLLAMA] Raw response (first 200 chars): {raw_text[:200]}", flush=True)
            return "Desculpa Capitão, erro ao processar resposta do modelo."
        
        # Extrai resposta
        if isinstance(data, dict):
            bot_response = str(data.get("response", "")).strip()
        else:
            print(f"[OLLAMA] ERROR: data is not dict, it's {type(data)}", flush=True)
            return "Desculpa Capitão, formato de resposta inválido."

        if not bot_response:
            return "Desculpa Capitão, não consegui gerar a resposta."

        save_chat(user_message, bot_response, MODEL)
        print(f"[TIMING] Total: {time.perf_counter() - _t0:.1f}s", flush=True)
        return bot_response

    except Exception as e:
        import traceback
        print(f"[ERROR] Ollama call failed: {e}", flush=True)
        traceback.print_exc()
        return f"Erro ao comunicar com o Ollama: {str(e)}"


def generate_response_stream(user_message: str, mode: str = "auto", external_context=None):
    """Streaming REAL: entrega tokens conforme o modelo gera (Ollama stream=True)."""
    # 1. Hard routing
    direct_answer = try_direct_answer(user_message)
    if direct_answer:
        save_chat(user_message, direct_answer, MODEL)
        yield direct_answer
        return

    # 2. Behavior engine (modo ativo + prompt especializado)
    behavior_instruction = ""
    try:
        behavior = get_behavior(user_message, "trabalho")
        num_predict = behavior.num_predict
        temperature = behavior.temperature
        top_p = behavior.top_p
        behavior_instruction = behavior.system_instruction
    except Exception:
        num_predict, temperature, top_p = 128, 0.7, 0.9

    # 3. Memoria Mark-L
    try:
        full_memory = load_memory()
        memory_block = format_memory_for_prompt(full_memory)
    except Exception:
        memory_block = ""

    # 4. System prompt + historico
    history_block = get_recent_history(limit=1)[:250]
    system_prompt = f"{LUCY_SYSTEM_PROMPT}\n\n{memory_block}\n\n"
    if history_block:
        system_prompt += f"CONVERSA RECENTE:\n{history_block}\n\n"

    if behavior_instruction:
        system_prompt += f"{behavior_instruction}\n"

    full_prompt = (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"<|im_start|>user\n{user_message}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": True,
        "keep_alive": -1,
        "options": {
            "num_ctx": 1024,
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": num_predict,
            "num_thread": 4,
            "stop": ["<|im_end|>", "<|im_start|>user", "<|im_start|>system"],
        },
    }

    collected = []
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except Exception:
                    continue
                token = chunk.get("response", "")
                if token:
                    collected.append(token)
                    yield token
                if chunk.get("done", False):
                    break
    except Exception as e:
        print(f"[STREAM] Erro: {e}", flush=True)
        yield "Desculpa Capitão, travei no streaming. Pode repetir?"
        return

    save_chat(user_message, "".join(collected), MODEL)

