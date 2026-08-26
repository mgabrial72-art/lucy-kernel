"""Schemas Pydantic para chat."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request de chat com validação."""
    message: str = Field(..., min_length=1, max_length=2000, description="Mensagem do usuário")
    session_id: str = Field(default="default", min_length=1, max_length=100)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Oi Lucy, como estamos?",
                "session_id": "capitao"
            }
        }
    }


class ChatResponse(BaseModel):
    """Response de chat."""
    response: str
    mode: str = "auto"
    time_ms: float
    history_size: int
    cached_context: bool = False
