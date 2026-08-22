"""
Task Scheduler — Gerencia lembretes e tarefas proativas.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from config.timezone import now_sp
from typing import List, Dict, Optional

DB_PATH = "/home/ubuntu/lucy-kernel/database/lucy_memory.db"

def create_reminder(
    title: str,
    content: str,
    scheduled_for: datetime = None,
    recurrence: str = "once",
    priority: int = 3,
    metadata: dict = None
) -> int:
    """
    Cria um lembrete/tarefa agendada.
    
    Args:
        title: Título do lembrete
        content: Descrição detalhada
        scheduled_for: Quando executar (None = agora ou recorrente)
        recurrence: 'once', 'daily', 'weekly', 'monthly'
        priority: 1-5 (5 = mais importante)
        metadata: Dados extras em JSON
    
    Returns:
        ID da tarefa criada
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calcula próxima execução
    if scheduled_for:
        next_exec = scheduled_for
    elif recurrence == "daily":
        next_exec = now_sp() + timedelta(days=1)
    elif recurrence == "weekly":
        next_exec = now_sp() + timedelta(weeks=1)
    elif recurrence == "monthly":
        next_exec = now_sp() + timedelta(days=30)
    else:
        next_exec = now_sp()
    
    cursor.execute('''
        INSERT INTO proactive_tasks 
        (task_type, title, content, scheduled_for, recurrence, next_execution, priority, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'reminder',
        title,
        content,
        scheduled_for.isoformat() if scheduled_for else None,
        recurrence,
        next_exec.isoformat(),
        priority,
        json.dumps(metadata or {})
    ))
    
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return task_id




def get_due_tasks() -> List[Dict]:
    """
    Retorna tarefas que estão vencidas (prontas pra executar).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, task_type, title, content, recurrence, next_execution, priority, metadata
        FROM proactive_tasks
        WHERE status = 'active' AND next_execution <= ?
        ORDER BY priority DESC
    ''', (now_sp().isoformat(),))
    
    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            'id': row[0],
            'task_type': row[1],
            'title': row[2],
            'content': row[3],
            'recurrence': row[4],
            'next_execution': row[5],
            'priority': row[6],
            'metadata': json.loads(row[7]) if row[7] else {}
        })
    
    conn.close()
    return tasks


def mark_task_executed(task_id: int):
    """
    Marca uma tarefa como executada e calcula próxima execução.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pega dados da tarefa
    cursor.execute('SELECT recurrence FROM proactive_tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return
    
    recurrence = row[0]
    
    # Calcula próxima execução
    if recurrence == 'once':
        cursor.execute('''
            UPDATE proactive_tasks 
            SET status = 'completed', last_executed = ?, updated_at = ?
            WHERE id = ?
        ''', (now_sp().isoformat(), now_sp().isoformat(), task_id))
    elif recurrence == 'daily':
        next_exec = now_sp() + timedelta(days=1)
        cursor.execute('''
            UPDATE proactive_tasks 
            SET last_executed = ?, next_execution = ?, updated_at = ?
            WHERE id = ?
        ''', (now_sp().isoformat(), next_exec.isoformat(), now_sp().isoformat(), task_id))
    elif recurrence == 'weekly':
        next_exec = now_sp() + timedelta(weeks=1)
        cursor.execute('''
            UPDATE proactive_tasks 
            SET last_executed = ?, next_execution = ?, updated_at = ?
            WHERE id = ?
        ''', (now_sp().isoformat(), next_exec.isoformat(), now_sp().isoformat(), task_id))
    elif recurrence == 'monthly':
        next_exec = now_sp() + timedelta(days=30)
        cursor.execute('''
            UPDATE proactive_tasks 
            SET last_executed = ?, next_execution = ?, updated_at = ?
            WHERE id = ?
        ''', (now_sp().isoformat(), next_exec.isoformat(), now_sp().isoformat(), task_id))
    else:
        # Recorrência customizada (ex: every_24h)
        if recurrence.startswith('every_'):
            try:
                hours = int(recurrence.split('_')[1].rstrip('h'))
                next_exec = now_sp() + timedelta(hours=hours)
                cursor.execute('''
                    UPDATE proactive_tasks 
                    SET last_executed = ?, next_execution = ?, updated_at = ?
                    WHERE id = ?
                ''', (now_sp().isoformat(), next_exec.isoformat(), now_sp().isoformat(), task_id))
            except:
                pass
    
    conn.commit()
    conn.close()




def list_active_tasks() -> List[Dict]:
    """
    Lista todas as tarefas ativas.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, task_type, title, content, recurrence, next_execution, priority
        FROM proactive_tasks
        WHERE status = 'active'
        ORDER BY priority DESC, next_execution ASC
    ''')
    
    tasks = []
    for row in cursor.fetchall():
        tasks.append({
            'id': row[0],
            'task_type': row[1],
            'title': row[2],
            'content': row[3],
            'recurrence': row[4],
            'next_execution': row[5],
            'priority': row[6]
        })
    
    conn.close()
    return tasks
