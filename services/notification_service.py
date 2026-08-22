"""
Notification Service — Sistema de notificações da Lucy.
Atualmente: log local + webhook (futuro: push pro celular).
"""
import sqlite3
import json
import requests
from datetime import datetime
from typing import Optional

DB_PATH = "/home/ubuntu/lucy-kernel/database/lucy_memory.db"

# URL de webhook (configurar quando tiver app celular)
WEBHOOK_URL = None  # Ex: "https://seu-app.com/webhook"

def send_notification(
    task_id: Optional[int],
    title: str,
    content: str,
    priority: int = 3
) -> bool:
    """
    Envia uma notificação (atualmente log + webhook futuro).
    
    Args:
        task_id: ID da tarefa relacionada (opcional)
        title: Título da notificação
        content: Conteúdo da notificação
        priority: 1-5 (5 = mais importante)
    
    Returns:
        True se enviada com sucesso
    """
    # Log local
    print(f"[{datetime.now():%H:%M}] 🔔 NOTIFICAÇÃO: [{title}] {content}", flush=True)
    
    # Webhook (futuro: push pro celular)
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={
                "task_id": task_id,
                "title": title,
                "content": content,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            }, timeout=10)
        except Exception as e:
            print(f"[{datetime.now():%H:%M}] ⚠️ Erro webhook: {e}", flush=True)
    
    # Salva histórico no banco
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO notifications (task_id, notification_type, content)
            VALUES (?, ?, ?)
        ''', (task_id, 'log', f"[{title}] {content}"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[{datetime.now():%H:%M}] ⚠️ Erro salvando notificação: {e}", flush=True)
    
    return True


def send_reminder_notification(task_id: int, title: str, content: str, priority: int = 3):
    """
    Envia notificação de lembrete vencido.
    """
    return send_notification(
        task_id=task_id,
        title=f"⏰ {title}",
        content=content,
        priority=priority
    )


def send_monitor_notification(task_id: int, title: str, content: str):
    """
    Envia notificação de monitor (novo resultado encontrado).
    """
    return send_notification(
        task_id=task_id,
        title=f"📡 {title}",
        content=content,
        priority=2
    )
