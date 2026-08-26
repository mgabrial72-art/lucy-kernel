"""Serviço de histórico persistente usando SQLite assíncrono."""
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any
from loguru import logger
from config.settings import settings


DB_PATH = settings.memory_dir / "history.db"
MAX_HISTORY = 20  # últimas 20 mensagens por sessão


async def init_db():
    """Inicializa banco de dados e cria tabelas."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Criar tabela SEM índices inline (SQLite não suporta)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Criar índices separadamente
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_session 
            ON conversations(session_id)
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_created 
            ON conversations(created_at)
        """)
        
        await db.commit()
    
    logger.info(f"✅ Banco de histórico inicializado: {DB_PATH}")


async def add_message(session_id: str, role: str, content: str) -> int:
    """Adiciona mensagem ao histórico."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO conversations (session_id, role, content, created_at)
               VALUES (?, ?, ?, ?)""",
            (session_id, role, content, datetime.now().isoformat())
        )
        await db.commit()
        
        # Limpa mensagens antigas (mantém últimas MAX_HISTORY)
        await db.execute(
            """DELETE FROM conversations 
               WHERE session_id = ? AND id NOT IN (
                   SELECT id FROM conversations 
                   WHERE session_id = ? 
                   ORDER BY created_at DESC 
                   LIMIT ?
               )""",
            (session_id, session_id, MAX_HISTORY)
        )
        await db.commit()
        return cursor.lastrowid


async def get_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retorna histórico da sessão."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """SELECT role, content FROM conversations 
               WHERE session_id = ? 
               ORDER BY created_at DESC 
               LIMIT ?""",
            (session_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


async def clear_history(session_id: str) -> int:
    """Limpa histórico da sessão."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM conversations WHERE session_id = ?",
            (session_id,)
        )
        await db.commit()
        logger.info(f"🗑️ Histórico limpo: session={session_id}, removidas={cursor.rowcount}")
        return cursor.rowcount


async def get_all_sessions() -> List[str]:
    """Retorna todas as sessões ativas."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT DISTINCT session_id FROM conversations ORDER BY session_id"
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_stats() -> Dict[str, Any]:
    """Estatísticas do histórico."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*), COUNT(DISTINCT session_id) FROM conversations")
        row = await cursor.fetchone()
        return {
            "total_messages": row[0] or 0,
            "total_sessions": row[1] or 0,
            "db_size_kb": round(DB_PATH.stat().st_size / 1024, 2) if DB_PATH.exists() else 0
        }
