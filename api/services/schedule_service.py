"""
Sistema de agendamentos simples (JSON local)
"""
import json
from pathlib import Path
from datetime import datetime
import pytz
from typing import List, Optional

SCHEDULES_FILE = Path(__file__).parent.parent.parent / "memory" / "schedules" / "capitao.json"

def _load_schedules() -> List[dict]:
    """Carrega agendamentos do arquivo."""
    if not SCHEDULES_FILE.exists():
        return []
    
    try:
        with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def _save_schedules(schedules: List[dict]):
    """Salva agendamentos no arquivo."""
    SCHEDULES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
        json.dump(schedules, f, ensure_ascii=False, indent=2)

def create_schedule(title: str, datetime_str: str, notes: str = "") -> dict:
    """Cria um novo agendamento.
    
    Args:
        title: Título do agendamento
        datetime_str: Data/hora em formato ISO (2026-08-27T14:30:00)
        notes: Notas adicionais
    """
    schedules = _load_schedules()
    
    sp_tz = pytz.timezone("America/Sao_Paulo")
    created_at = datetime.now(sp_tz).isoformat()
    
    new_schedule = {
        "id": len(schedules) + 1,
        "title": title,
        "datetime": datetime_str,
        "notes": notes,
        "created_at": created_at,
        "completed": False
    }
    
    schedules.append(new_schedule)
    _save_schedules(schedules)
    
    return new_schedule

def get_upcoming_schedules(limit: int = 5) -> List[dict]:
    """Retorna próximos agendamentos."""
    schedules = _load_schedules()
    sp_tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(sp_tz)
    
    # Filtra agendamentos futuros e não completados
    upcoming = []
    for sched in schedules:
        if sched.get("completed"):
            continue
        
        try:
            sched_dt = datetime.fromisoformat(sched["datetime"])
            if sched_dt.tzinfo is None:
                sched_dt = sp_tz.localize(sched_dt)
            
            if sched_dt >= now:
                upcoming.append(sched)
        except:
            continue
    
    # Ordena por data
    upcoming.sort(key=lambda x: x["datetime"])
    
    return upcoming[:limit]

def get_all_schedules() -> List[dict]:
    """Retorna todos os agendamentos."""
    return _load_schedules()

def cancel_schedule(schedule_id: int) -> bool:
    """Cancela um agendamento."""
    schedules = _load_schedules()
    
    for sched in schedules:
        if sched["id"] == schedule_id:
            sched["completed"] = True
            _save_schedules(schedules)
            return True
    
    return False

def format_schedules_for_prompt() -> str:
    """Formata agendamentos para o prompt."""
    upcoming = get_upcoming_schedules(limit=3)
    
    if not upcoming:
        return ""
    
    lines = ["AGENDAMENTOS FUTUROS:"]
    for sched in upcoming:
        dt = datetime.fromisoformat(sched["datetime"])
        dt_str = dt.strftime("%d/%m/%Y às %H:%M")
        lines.append(f"  - {sched['title']} ({dt_str})")
    
    return "\n".join(lines)

if __name__ == "__main__":
    print("Testando agendamentos:")
    
    # Cria agendamento de teste
    new = create_schedule(
        "Consulta médica",
        "2026-08-28T14:00:00",
        "Levar exames"
    )
    print(f"Criado: {new}")
    
    # Lista próximos
    upcoming = get_upcoming_schedules()
    print(f"Próximos: {len(upcoming)}")
    for s in upcoming:
        print(f"  - {s['title']} em {s['datetime']}")
