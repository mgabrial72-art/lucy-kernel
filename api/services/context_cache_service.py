"""Cache de contexto em tempo real - OTIMIZADO."""
import threading
import time
from datetime import datetime
from typing import Optional
import pytz
import requests
from loguru import logger

from api.services.weather_service import (
    get_weather_sao_paulo, get_rain_forecast, get_air_quality
)
from api.services.schedule_service import get_upcoming_schedules
from api.services.time_service import get_sao_paulo_time
from config.settings import settings


_cache_lock = threading.Lock()
_cached_context = {
    "updated_at": None,
    "time": {},
    "weather": {},
    "schedules_today": [],
    "next_schedule": None,
    "summary": "",
    "rain_forecast": None,
    "air_quality": {}
}

SP_TZ = pytz.timezone("America/Sao_Paulo")


def _get_period_of_day(hour: int) -> str:
    if 5 <= hour < 12: return "manhã"
    elif 12 <= hour < 18: return "tarde"
    return "noite"


def _get_greeting() -> str:
    hour = datetime.now(SP_TZ).hour
    if 5 <= hour < 12: return "Bom dia"
    elif 12 <= hour < 18: return "Boa tarde"
    return "Boa noite"


def _get_today_schedules() -> list:
    all_schedules = get_upcoming_schedules(limit=50)
    today = datetime.now(SP_TZ).date()
    
    today_schedules = []
    for sched in all_schedules:
        try:
            sched_dt = datetime.fromisoformat(sched["datetime"])
            if sched_dt.tzinfo is None:
                sched_dt = SP_TZ.localize(sched_dt)
            if sched_dt.date() == today:
                today_schedules.append({
                    "title": sched["title"],
                    "time": sched_dt.strftime("%H:%M"),
                    "notes": sched.get("notes", ""),
                    "datetime": sched["datetime"]
                })
        except:
            continue
    
    today_schedules.sort(key=lambda x: x["time"])
    return today_schedules


def _get_next_schedule() -> Optional[dict]:
    all_schedules = get_upcoming_schedules(limit=10)
    now = datetime.now(SP_TZ)
    
    for sched in all_schedules:
        try:
            sched_dt = datetime.fromisoformat(sched["datetime"])
            if sched_dt.tzinfo is None:
                sched_dt = SP_TZ.localize(sched_dt)
            if sched_dt > now:
                diff = sched_dt - now
                hours = diff.total_seconds() / 3600
                if hours < 1:
                    time_until = f"{int(diff.total_seconds() / 60)} min"
                elif hours < 24:
                    time_until = f"{hours:.1f} horas"
                else:
                    time_until = f"{hours/24:.1f} dias"
                return {
                    "title": sched["title"],
                    "datetime": sched["datetime"],
                    "time": sched_dt.strftime("%H:%M"),
                    "date": sched_dt.strftime("%d/%m/%Y"),
                    "time_until": time_until,
                    "notes": sched.get("notes", "")
                }
        except:
            continue
    return None


def _build_summary(context: dict) -> str:
    parts = []
    
    greeting = _get_greeting()
    time_info = context.get("time", {})
    parts.append(f"{greeting}, Capitão! São {time_info.get('time', '')} de {time_info.get('day_of_week', '')}, {time_info.get('date', '')}.")
    
    weather = context.get("weather", {})
    if weather:
        parts.append(f"Clima: {weather.get('description', 'desconhecido')}, {weather.get('temperature', '')} (sensação {weather.get('feels_like', '')}).")
    
    rain = context.get("rain_forecast", {})
    if rain and rain.get("will_rain") is not None:
        if rain.get("will_rain"):
            parts.append(f"Há {rain.get('max_probability', 0)}% de chance de chuva hoje.")
        else:
            parts.append("Sem previsão de chuva hoje.")
    
    air = context.get("air_quality", {})
    if air.get("quality"):
        parts.append(f"Qualidade do ar: {air.get('quality')} (AQI {air.get('aqi', '?')}).")
    
    schedules = context.get("schedules_today", [])
    if schedules:
        if len(schedules) == 1:
            s = schedules[0]
            parts.append(f"Você tem 1 agendamento hoje: {s['title']} às {s['time']}.")
        else:
            parts.append(f"Você tem {len(schedules)} agendamentos hoje.")
            for s in schedules[:3]:
                parts.append(f"  - {s['title']} às {s['time']}")
    else:
        parts.append("Sem agendamentos hoje.")
    
    next_sched = context.get("next_schedule")
    if next_sched:
        parts.append(f"Próximo: {next_sched['title']} em {next_sched['time_until']} ({next_sched['date']} às {next_sched['time']}).")
    
    return " ".join(parts)


def update_context():
    """Atualiza todos os dados em cache."""
    global _cached_context
    
    logger.debug("[CONTEXT] Atualizando contexto...")
    start = time.perf_counter()
    
    try:
        time_data = get_sao_paulo_time()
        time_data["period"] = _get_period_of_day(time_data["datetime"].hour)
        
        days_pt = {
            "Monday": "segunda-feira", "Tuesday": "terça-feira",
            "Wednesday": "quarta-feira", "Thursday": "quinta-feira",
            "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"
        }
        time_data["day_of_week"] = days_pt.get(time_data["day_of_week"], time_data["day_of_week"])
        
        # Usa weather cacheado (1 request combinado!)
        weather = get_weather_sao_paulo()
        rain_forecast = get_rain_forecast()
        air_quality = get_air_quality()
        
        schedules_today = _get_today_schedules()
        next_schedule = _get_next_schedule()
        
        with _cache_lock:
            _cached_context = {
                "updated_at": datetime.now(SP_TZ).isoformat(),
                "time": time_data,
                "weather": weather,
                "rain_forecast": rain_forecast,
                "air_quality": air_quality,
                "schedules_today": schedules_today,
                "next_schedule": next_schedule,
                "summary": ""
            }
            _cached_context["summary"] = _build_summary(_cached_context)
        
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"[CONTEXT] ✅ Contexto atualizado em {elapsed:.0f}ms")
        
    except Exception as e:
        logger.error(f"[CONTEXT] ❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def get_context() -> dict:
    with _cache_lock:
        return _cached_context.copy()


def get_status_summary() -> str:
    ctx = get_context()
    return ctx.get("summary", "Contexto não disponível ainda.")


def is_context_question(message: str) -> bool:
    """Detecta perguntas contextuais."""
    msg = message.lower().strip()
    
    context_phrases = [
        "como estamos", "como tá", "como está", "e aí", "eia",
        "me atualiza", "atualiza aí", "qual a situação", "situação",
        "o que tá rolando", "o que está rolando", "me dá o resumo",
        "resumo do dia", "me conta as novidades", "novidades",
        "como vai o dia", "status", "panorama"
    ]
    
    for phrase in context_phrases:
        if phrase in msg:
            return True
    
    if len(msg.split()) <= 3 and "?" in message:
        short_words = ["e aí", "oi", "tudo bem", "como estamos"]
        if any(w in msg for w in short_words):
            return True
    
    return False


_updater_thread = None
_stop_updater = threading.Event()


def _background_updater(interval_seconds: int = 900):
    """Thread que atualiza contexto periodicamente."""
    update_context()
    
    while not _stop_updater.is_set():
        if _stop_updater.wait(timeout=interval_seconds):
            break
        update_context()
        
        # Ping Ollama pra manter quente
        try:
            requests.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": "OK",
                    "stream": False,
                    "keep_alive": "24h",
                    "options": {"num_predict": 2}
                },
                timeout=30
            )
            logger.debug("[CONTEXT] 🌡️ Modelo mantido quente")
        except Exception as e:
            logger.warning(f"[CONTEXT] Ping falhou: {e}")


def start_background_updater(interval_seconds: int = 900):
    global _updater_thread
    if _updater_thread is not None and _updater_thread.is_alive():
        return
    
    _stop_updater.clear()
    _updater_thread = threading.Thread(
        target=_background_updater,
        args=(interval_seconds,),
        daemon=True,
        name="ContextUpdater"
    )
    _updater_thread.start()
    logger.info(f"[CONTEXT] 🚀 Background updater iniciado (a cada {interval_seconds}s)")


def stop_background_updater():
    _stop_updater.set()
