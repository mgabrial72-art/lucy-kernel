"""
Lucy Cleanup Service — Limpa dados obsoletos do sistema.
Versão simplificada para o novo schema (Mark-L JSON + tabelas mínimas).
"""
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = "/home/ubuntu/lucy-kernel/database/lucy_memory.db"

def run_full_cleanup():
    """Executa limpeza completa do sistema."""
    print(f"[Cleanup] Iniciando limpeza automática...")
    results = {"total_deleted": 0, "details": []}
    
    try:
        results = cleanup_history(results)
    except Exception as e:
        print(f"[Cleanup] Erro no history: {e}")
    
    try:
        results = cleanup_proactive_cache(results)
    except Exception as e:
        print(f"[Cleanup] Erro no proactive_cache: {e}")
    
    try:
        results = cleanup_expired_cache(results)
    except Exception as e:
        print(f"[Cleanup] Erro no expired_cache: {e}")
    
    print(f"[Cleanup] Concluído: {results['total_deleted']} itens removidos")
    return results


def cleanup_history(results):
    """Remove histórico com mais de 30 dias."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM history 
            WHERE created_at < datetime('now', '-30 days')
        """)
        deleted = cursor.rowcount
        if deleted > 0:
            results["total_deleted"] += deleted
            results["details"].append(f"history: {deleted} mensagens antigas")
            print(f"[Cleanup] History: {deleted} mensagens removidas")
        conn.commit()
    finally:
        conn.close()
    
    return results


def cleanup_proactive_cache(results):
    """Remove cache expirado."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM proactive_cache 
            WHERE expires_at < datetime('now')
        """)
        deleted = cursor.rowcount
        if deleted > 0:
            results["total_deleted"] += deleted
            results["details"].append(f"proactive_cache: {deleted} entradas expiradas")
            print(f"[Cleanup] Cache: {deleted} entradas expiradas removidas")
        conn.commit()
    finally:
        conn.close()
    
    return results


def cleanup_expired_cache(results):
    """Placeholder para compatibilidade."""
    return results
