"""
Endpoints de clima e hora
"""
from fastapi import APIRouter
from api.services.weather_service import get_weather_sao_paulo, get_weather_summary
from api.services.time_service import get_sao_paulo_time, get_time_summary

router = APIRouter()

@router.get("/weather")
async def weather():
    """Retorna clima atual de São Paulo."""
    return get_weather_sao_paulo()

@router.get("/weather/summary")
async def weather_summary():
    """Retorna resumo do clima em texto."""
    return {"summary": get_weather_summary()}

@router.get("/time")
async def time():
    """Retorna hora atual de São Paulo."""
    return get_sao_paulo_time()

@router.get("/time/summary")
async def time_summary():
    """Retorna hora em texto."""
    return {"summary": get_time_summary()}
