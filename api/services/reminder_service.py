"""
Serviço de lembretes usando Mem0 + SQLite simples
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "reminders.db"

def _ensure_db():
    """Cria o banco de lembretes se não existir."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            scheduled_for TEXT NOT NULL,
            recurrence TEXT DEFAULT 'once',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_ensure_db()

def create_reminder(title: str, scheduled_for: str, content: str = "", recurrence: str = "once") -> dict:
    """Cria um novo lembrete."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (title, content, scheduled_for, recurrence) VALUES (?, ?, ?, ?)",
        (title, content, scheduled_for, recurrence)
    )
    reminder_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": reminder_id, "title": title, "scheduled_for": scheduled_for}

def list_reminders(status: str = "active") -> list:
    """Lista lembretes ativos."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, title, scheduled_for, recurrence, status FROM reminders WHERE status = ?", (status,))
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "scheduled_for": r[2], "recurrence": r[3], "status": r[4]} for r in rows]

def get_due_reminders() -> list:
    """Retorna lembretes que já passaram da hora."""
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, content, scheduled_for FROM reminders WHERE status = 'active' AND scheduled_for <= ?",
        (now,)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "content": r[2], "scheduled_for": r[3]} for r in rows]

def mark_delivered(reminder_id: int):
    """Marca lembrete como entregue."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET status = 'delivered' WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()

def delete_reminder(reminder_id: int):
    """Deleta um lembrete."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()
