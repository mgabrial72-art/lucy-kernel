"""
Endpoint de lembretes - SQLite simples
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from api.services.reminder_service import (
    create_reminder, list_reminders, get_due_reminders,
    mark_delivered, delete_reminder
)

router = APIRouter()

class ReminderCreate(BaseModel):
    title: str
    scheduled_for: str  # ISO format
    content: Optional[str] = ""
    recurrence: str = "once"

@router.post("/reminders")
async def create(reminder: ReminderCreate):
    result = create_reminder(
        title=reminder.title,
        scheduled_for=reminder.scheduled_for,
        content=reminder.content or reminder.title,
        recurrence=reminder.recurrence
    )
    return result

@router.get("/reminders")
async def list_all():
    return {"reminders": list_reminders()}

@router.get("/reminders/due")
async def due():
    """Tasker chama aqui periodicamente pra saber o que disparar."""
    return {"due": get_due_reminders()}

@router.post("/reminders/{reminder_id}/delivered")
async def delivered(reminder_id: int):
    mark_delivered(reminder_id)
    return {"status": "delivered"}

@router.delete("/reminders/{reminder_id}")
async def delete(reminder_id: int):
    delete_reminder(reminder_id)
    return {"status": "deleted"}
