import sqlite3
import os
from datetime import datetime
from config.timezone import now_sp

DB_PATH = os.path.expanduser("~/lucy-kernel/database/lucy_memory.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de Histórico de Conversas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            lucy_response TEXT NOT NULL,
            model_used TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de Estados do Sistema (Máquina de Estados e Throttling)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de Memórias Estruturadas (Projetos, Hábitos, Lembretes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS structured_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            importance INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Definir estado inicial padrão
    cursor.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('activity_mode', 'folga')")
    cursor.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('throttling_level', '0')")
    
    conn.commit()
    conn.close()

def save_chat(user_msg: str, lucy_msg: str, model: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO history (user_message, lucy_response, model_used) VALUES (?, ?, ?)",
        (user_msg, lucy_msg, model)
    )
    conn.commit()
    conn.close()

def get_recent_history(limit: int = 6):
    """
    Retorna histórico recente seguro para envio ao modelo.
    Interações que contenham indicadores de informação sensível
    não entram no contexto do modelo.
    """
    import re

    sensitive_patterns = [
        r"\bsenha\b",
        r"\bpassword\b",
        r"\bpasswd\b",
        r"\bsecret\b",
        r"\btoken\b",
        r"\bapi[_ -]?key\b",
        r"\bchave privada\b",
        r"\bprivate key\b",
        r"\bseed phrase\b",
        r"\bfrase de recuperação\b",
        r"\bnúmero da conta\b",
        r"\bconta bancária\b",
        r"\bcartão de crédito\b",
        r"\bcvv\b",
    ]

    def contains_sensitive(text: str) -> bool:
        normalized = " ".join(str(text).lower().split())
        return any(
            re.search(pattern, normalized)
            for pattern in sensitive_patterns
        )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fetch_limit = max(limit * 10, 50)

    cursor.execute(
        "SELECT user_message, lucy_response "
        "FROM history ORDER BY id DESC LIMIT ?",
        (fetch_limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    history = []
    accepted = 0

    for user_msg, lucy_msg in reversed(rows):
        # FILTRO CRÍTICO: Ignora interações com respostas vazias (lixo de testes)
        if not user_msg or not lucy_msg:
            continue
        if contains_sensitive(user_msg) or contains_sensitive(lucy_msg):
            continue

        history.append({
            "role": "user",
            "content": user_msg
        })

        history.append({
            "role": "assistant",
            "content": lucy_msg
        })

        accepted += 1

        if accepted >= limit:
            break

    return history

# ==============================================================
# MEMÓRIA ESTRUTURADA — FASE 3
# ==============================================================

def update_state(key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO system_state (key, value, updated_at) VALUES (?, ?, ?)",
        (key, str(value), now_sp())
    )
    conn.commit()
    conn.close()

