"""
Endpoints de agendamentos
"""
from fastapi import APIRouter
from pydantic import BaseModel
from api.services.schedule_service import (
    create_schedule,
    get_upcoming_schedules,
    get_all_schedules,
    cancel_schedule
)

router = APIRouter()

class ScheduleRequest(BaseModel):
    title: str
    datetime: str  # ISO format: 2026-08-27T14:30:00
    notes: str = ""

@router.post("/schedule")
async def create_new_schedule(request: ScheduleRequest):
    """Cria um novo agendamento."""
    schedule = create_schedule(
        title=request.title,
        datetime_str=request.datetime,
        notes=request.notes
    )
    return {"status": "created", "schedule": schedule}

@router.get("/schedule/upcoming")
async def upcoming_schedules(limit: int = 5):
    """Retorna próximos agendamentos."""
    schedules = get_upcoming_schedules(limit=limit)
    return {"count": len(schedules), "schedules": schedules}

@router.get("/schedule/all")
async def all_schedules():
    """Retorna todos os agendamentos."""
    schedules = get_all_schedules()
    return {"count": len(schedules), "schedules": schedules}

@router.delete("/schedule/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """Cancela um agendamento."""
    success = cancel_schedule(schedule_id)
    return {"status": "cancelled" if success else "not_found"}
