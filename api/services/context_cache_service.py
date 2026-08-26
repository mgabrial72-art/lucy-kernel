"""
Cache de contexto em tempo real.
Atualiza informações de fundo a cada 15 min.
"""
import threading
import time
from datetime import datetime
from typing import Optional
import pytz

from api.services.weather_service import get_weather_sao_paulo
from api.services.schedule_service import get_upcoming_schedules
from api.services.time_service import get_sao_paulo_time

# Dados em cache (thread-safe)
_cache_lock = threading.Lock()
_cached_context = {
    "updated_at": None,
    "time": {},
    "weather": {},
    "schedules_today": [],
    "next_schedule": None,
    "summary": "",
    "rain_forecast": None
}

SP_TZ = pytz.timezone("America/Sao_Paulo")

def _get_period_of_day(hour: int) -> str:
    """Retorna período do dia."""
    if 5 <= hour < 12:
        return "manhã"
    elif 12 <= hour < 18:
        return "tarde"
    else:
        return "noite"

def _get_greeting() -> str:
    """Retorna saudação baseada na hora."""
    now = datetime.now(SP_TZ)
    hour = now.hour
    if 5 <= hour < 12:
        return "Bom dia"
    elif 12 <= hour < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def _get_rain_forecast() -> dict:
    """Busca previsão de chuva para hoje via Open-Meteo hourly."""
    try:
        import requests
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "hourly": "precipitation_probability,precipitation,weather_code",
            "timezone": "America/Sao_Paulo",
            "forecast_days": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hourly = data.get("hourly", {})
        
        times = hourly.get("time", [])
        precip_prob = hourly.get("precipitation_probability", [])
        precip_mm = hourly.get("precipitation", [])
        
        # Filtra horas a partir de AGORA
        now = datetime.now(SP_TZ)
        current_hour_idx = 0
        
        for i, t in enumerate(times):
            try:
                hour_dt = datetime.fromisoformat(t)
                if hour_dt.hour == now.hour:
                    current_hour_idx = i
                    break
            except:
                continue
        
        # Pega próximas horas
        future_probs = precip_prob[current_hour_idx:]
        future_mm = precip_mm[current_hour_idx:]
        
        max_prob = max(future_probs) if future_probs else 0
        total_mm = sum(future_mm) if future_mm else 0
        
        # Determina se vai chover
        if max_prob >= 70:
            will_rain = True
            certainty = "alta"
        elif max_prob >= 40:
            will_rain = True
            certainty = "média"
        else:
            will_rain = False
            certainty = "baixa"
        
        return {
            "will_rain": will_rain,
            "max_probability": max_prob,
            "total_mm": round(total_mm, 1),
            "certainty": certainty
        }
        
    except Exception as e:
        print(f"[CONTEXT] Erro rain forecast: {e}")
        return {"will_rain": None, "max_probability": 0, "certainty": "desconhecida"}

def _get_air_quality() -> dict:
    """Qualidade do ar em SP via Open-Meteo Air Quality."""
    try:
        import requests
        
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "current": "pm2_5,pm10,us_aqi",
            "timezone": "America/Sao_Paulo"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current", {})
        
        aqi = current.get("us_aqi", 0)
        
        # Classifica US AQI
        if aqi <= 50:
            quality = "Boa"
            color = "verde"
        elif aqi <= 100:
            quality = "Moderada"
            color = "amarelo"
        elif aqi <= 150:
            quality = "Ruim para sensíveis"
            color = "laranja"
        elif aqi <= 200:
            quality = "Ruim"
            color = "vermelho"
        else:
            quality = "Muito ruim"
            color = "roxo"
        
        return {
            "aqi": aqi,
            "quality": quality,
            "color": color,
            "pm25": current.get("pm2_5")
        }
        
    except Exception as e:
        print(f"[CONTEXT] Erro air quality: {e}")
        return {"aqi": None, "quality": "desconhecida"}

def _get_today_schedules() -> list:
    """Retorna apenas agendamentos de HOJE."""
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
    
    # Ordena por hora
    today_schedules.sort(key=lambda x: x["time"])
    return today_schedules

def _get_next_schedule() -> Optional[dict]:
    """Retorna próximo agendamento e quanto tempo falta."""
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
                    days = hours / 24
                    time_until = f"{days:.1f} dias"
                
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
    """Constrói resumo natural do contexto atual."""
    parts = []
    
    # Saudação + hora
    greeting = _get_greeting()
    time_info = context.get("time", {})
    parts.append(f"{greeting}, Capitão! São {time_info.get('time', '')} de {time_info.get('day_of_week', '')}, {time_info.get('date', '')}.")
    
    # Clima
    weather = context.get("weather", {})
    if weather:
        parts.append(f"Clima: {weather.get('description', 'desconhecido')}, {weather.get('temperature', '')} (sensação {weather.get('feels_like', '')}).")
    
    # Chuva
    rain = context.get("rain_forecast", {})
    if rain and rain.get("will_rain") is not None:
        if rain.get("will_rain"):
            parts.append(f"Há {rain.get('max_probability', 0)}% de chance de chuva hoje.")
        else:
            parts.append("Sem previsão de chuva hoje.")
    
    # Qualidade do ar
    air = context.get("air_quality", {})
    if air.get("quality"):
        parts.append(f"Qualidade do ar: {air.get('quality')} (AQI {air.get('aqi', '?')}).")
    
    # Agendamentos do dia
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
    
    # Próximo agendamento
    next_sched = context.get("next_schedule")
    if next_sched:
        parts.append(f"Próximo: {next_sched['title']} em {next_sched['time_until']} ({next_sched['date']} às {next_sched['time']}).")
    
    return " ".join(parts)

def update_context():
    """Atualiza todos os dados em cache."""
    global _cached_context
    
    print("[CONTEXT] Atualizando contexto...")
    start = time.perf_counter()
    
    try:
        # Hora atual
        time_data = get_sao_paulo_time()
        time_data["period"] = _get_period_of_day(time_data["datetime"].hour)
        
        # Traduz dia da semana
        days_pt = {
            "Monday": "segunda-feira", "Tuesday": "terça-feira",
            "Wednesday": "quarta-feira", "Thursday": "quinta-feira",
            "Friday": "sexta-feira", "Saturday": "sábado", "Sunday": "domingo"
        }
        time_data["day_of_week"] = days_pt.get(
            time_data["day_of_week"], time_data["day_of_week"]
        )
        
        # Clima
        weather = get_weather_sao_paulo()
        
        # Previsão de chuva
        rain_forecast = _get_rain_forecast()
        
        # Qualidade do ar
        air_quality = _get_air_quality()
        
        # Agendamentos DO DIA
        schedules_today = _get_today_schedules()
        
        # Próximo agendamento
        next_schedule = _get_next_schedule()
        
        # Monta contexto
        with _cache_lock:
            _cached_context = {
                "updated_at": datetime.now(SP_TZ).isoformat(),
                "time": time_data,
                "weather": weather,
                "rain_forecast": rain_forecast,
                "air_quality": air_quality,
                "schedules_today": schedules_today,
                "next_schedule": next_schedule,
                "summary": ""  # Será preenchido depois
            }
            _cached_context["summary"] = _build_summary(_cached_context)
        
        elapsed = (time.perf_counter() - start) * 1000
        print(f"[CONTEXT] ✅ Contexto atualizado em {elapsed:.0f}ms")
        
    except Exception as e:
        print(f"[CONTEXT] ❌ Erro ao atualizar: {e}")
        import traceback
        traceback.print_exc()

def get_context() -> dict:
    """Retorna contexto cacheado."""
    with _cache_lock:
        return _cached_context.copy()

def get_status_summary() -> str:
    """Retorna resumo natural do contexto."""
    ctx = get_context()
    return ctx.get("summary", "Contexto não disponível ainda.")

def is_context_question(message: str) -> bool:
    """Detecta se a mensagem é uma pergunta contextual."""
    message_lower = message.lower().strip()
    
    # Frases que ativam o modo contexto
    context_phrases = [
        "como estamos",
        "como tá",
        "como está",
        "e aí",
        "eia",
        "me atualiza",
        "atualiza aí",
        "qual a situação",
        "situação",
        "o que tá rolando",
        "o que está rolando",
        "me dá o resumo",
        "resumo do dia",
        "me conta as novidades",
        "novidades",
        "como vai o dia",
        "status",
        "como estamos hoje",
        "panorama"
    ]
    
    # Verifica se alguma frase está na mensagem
    for phrase in context_phrases:
        if phrase in message_lower:
            return True
    
    # Se for MUITO curta e terminar com "?" pode ser contextual
    if len(message_lower.split()) <= 3 and "?" in message:
        short_context_words = ["e aí", "oi", "tudo bem", "como estamos"]
        if any(w in message_lower for w in short_context_words):
            return True
    
    return False

# Background updater
_updater_thread = None
_stop_updater = threading.Event()

def _background_updater(interval_seconds: int = 900):
    """Thread que atualiza contexto periodicamente."""
    # Primeira atualização imediata
    update_context()
    
    while not _stop_updater.is_set():
        # Aguarda o intervalo
        if _stop_updater.wait(timeout=interval_seconds):
            break
        
        # Atualiza
        update_context()
        
        # Faz ping no Ollama pra manter quente
        try:
            import requests
            from config.settings import settings
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
            print("[CONTEXT] 🌡️ Modelo mantido quente")
        except Exception as e:
            print(f"[CONTEXT] Ping falhou: {e}")

def start_background_updater(interval_seconds: int = 900):
    """Inicia o atualizador em background."""
    global _updater_thread
    
    if _updater_thread is not None and _updater_thread.is_alive():
        print("[CONTEXT] Updater já está rodando")
        return
    
    _stop_updater.clear()
    _updater_thread = threading.Thread(
        target=_background_updater,
        args=(interval_seconds,),
        daemon=True,
        name="ContextUpdater"
    )
    _updater_thread.start()
    print(f"[CONTEXT] 🚀 Background updater iniciado (a cada {interval_seconds}s)")

def stop_background_updater():
    """Para o atualizador."""
    _stop_updater.set()
    print("[CONTEXT] Updater parado")
