"""
Proactive Executor — Executa tarefas vencidas (lembretes e monitores).
Chamado pelo Worker a cada minuto.
"""
import json
from datetime import datetime
from config.timezone import now_sp
from services.task_scheduler import (
    get_due_tasks,
    mark_task_executed
)
from services.notification_service import (
    send_reminder_notification,
    send_monitor_notification
)
from services.web_search_service import search_web


def execute_due_tasks() -> int:
    """
    Executa todas as tarefas vencidas.
    
    Returns:
        Número de tarefas executadas
    """
    tasks = get_due_tasks()
    
    if not tasks:
        return 0
    
    executed = 0
    
    for task in tasks:
        task_type = task['task_type']
        task_id = task['id']
        title = task['title']
        content = task.get('content', '')
        priority = task.get('priority', 3)
        metadata = task.get('metadata', {})
        
        try:
            if task_type == 'reminder':
                # Envia notificação de lembrete
                send_reminder_notification(task_id, title, content, priority)
                print(f"[{now_sp():%H:%M}] ⏰ Lembrete executado: {title}", flush=True)
            
            elif task_type == 'monitor':
                # Executa monitor de tópicos
                results = run_monitor(task)
                if results:
                    send_monitor_notification(task_id, title, results)
                    print(f"[{now_sp():%H:%M}] 📡 Monitor executado: {title} ({len(results)} resultados)", flush=True)
                else:
                    print(f"[{now_sp():%H:%M}] 📡 Monitor executado: {title} (sem novos resultados)", flush=True)
            
            elif task_type == 'checkin':
                # Check-in contextual (tratado como lembrete simples)
                send_reminder_notification(task_id, title, content, priority)
            
            # Marca como executada
            mark_task_executed(task_id)
            executed += 1
        
        except Exception as e:
            print(f"[{now_sp():%H:%M}] ❌ Erro executando tarefa {task_id}: {e}", flush=True)
    
    return executed


def run_monitor(task: dict) -> str:
    """
    Executa um monitor de tópicos (busca web + comparação com resultados anteriores).
    
    Returns:
        String com novos resultados encontrados
    """
    metadata = task.get('metadata', {})
    keywords = metadata.get('keywords', [])
    last_results = metadata.get('last_results', [])
    
    if not keywords:
        return ""
    
    # Busca por cada keyword
    new_results = []
    
    for keyword in keywords[:2]:  # Limita a 2 keywords por execução
        try:
            search_result = search_web(keyword, max_results=3)
            if search_result.get('success'):
                for result in search_result.get('results', []):
                    title = result.get('title', '')
                    url = result.get('url', '')
                    
                    # Verifica se é novo (não está nos últimos resultados)
                    if title and title not in last_results:
                        new_results.append({
                            'title': title,
                            'url': url,
                            'keyword': keyword
                        })
        
        except Exception as e:
            print(f"[{now_sp():%H:%M}] ⚠️ Erro monitor {keyword}: {e}", flush=True)
    
    if not new_results:
        return ""
    
    # Formata resultado
    formatted = f"Encontrei {len(new_results)} novidades:\n"
    for r in new_results[:3]:
        formatted += f"• {r['title'][:80]}\n"
    
    # Atualiza metadata com novos resultados (mantém últimos 10)
    # Isso será feito na próxima execução
    return formatted


def run_proactive_cycle() -> dict:
    """
    Executa um ciclo completo de proatividade.
    
    Returns:
        Dict com estatísticas do ciclo
    """
    from services.task_scheduler import get_due_tasks
    
    stats = {
        'timestamp': now_sp().isoformat(),
        'due_tasks': 0,
        'executed': 0,
        'errors': 0
    }
    
    try:
        due = get_due_tasks()
        stats['due_tasks'] = len(due)
        
        if due:
            stats['executed'] = execute_due_tasks()
    
    except Exception as e:
        stats['errors'] += 1
        print(f"[{now_sp():%H:%M}] ❌ Erro no ciclo proativo: {e}", flush=True)
    
    return stats
