"""Serviço de clima usando Open-Meteo - OTIMIZADO (1 request)."""
import requests
from datetime import datetime
from loguru import logger
from config.settings import settings
from api.services.cache_lru import weather_cache


def _fetch_all_weather_data() -> dict:
    """Busca TODOS os dados do clima em 1 ÚNICO request."""
    cache_key = f"weather_{settings.sp_latitude}_{settings.sp_longitude}"
    
    cached_data = weather_cache.get(cache_key)
    if cached_data:
        logger.debug("💾 Weather cache hit")
        return cached_data
    
    try:
        # 1 request combinando current + hourly + air_quality
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": settings.sp_latitude,
            "longitude": settings.sp_longitude,
            # Dados atuais
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
            # Previsão horária (próximas 24h para chuva)
            "hourly": "precipitation_probability,precipitation,weather_code",
            "timezone": "America/Sao_Paulo",
            "forecast_days": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        current_data = response.json()
        
        # Qualidade do ar (API separada mas cacheada)
        air_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        air_params = {
            "latitude": settings.sp_latitude,
            "longitude": settings.sp_longitude,
            "current": "pm2_5,pm10,us_aqi",
            "timezone": "America/Sao_Paulo"
        }
        
        try:
            air_response = requests.get(air_url, params=air_params, timeout=5)
            air_response.raise_for_status()
            air_data = air_response.json()
        except Exception as e:
            logger.warning(f"[WEATHER] Air quality falhou: {e}")
            air_data = {"current": {"us_aqi": None, "pm2_5": None}}
        
        result = {
            "current": current_data.get("current", {}),
            "hourly": current_data.get("hourly", {}),
            "air_quality": air_data.get("current", {}),
            "fetched_at": datetime.now().isoformat()
        }
        
        # Cacheia por 5 minutos
        weather_cache.set(cache_key, result)
        logger.debug("💾 Weather cache set (5 min)")
        
        return result
        
    except Exception as e:
        logger.error(f"[WEATHER] Erro: {e}")
        return {"error": str(e)}


def get_weather_sao_paulo() -> dict:
    """Retorna clima atual de São Paulo (usa cache)."""
    data = _fetch_all_weather_data()
    
    if "error" in data:
        return data
    
    current = data.get("current", {})
    
    temp_c = current.get("temperature_2m")
    feels_like = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind_kmh = current.get("wind_speed_10m")
    weather_code = current.get("weather_code", 0)
    
    weather_codes_pt = {
        0: "Céu limpo", 1: "Predominantemente limpo",
        2: "Parcialmente nublado", 3: "Nublado",
        45: "Neblina", 48: "Neblina com geada",
        51: "Garoa fraca", 53: "Garoa moderada", 55: "Garoa intensa",
        61: "Chuva fraca", 63: "Chuva moderada", 65: "Chuva forte",
        66: "Chuva congelante fraca", 67: "Chuva congelante forte",
        71: "Neve fraca", 73: "Neve moderada", 75: "Neve forte",
        77: "Grãos de neve",
        80: "Pancadas de chuva fracas", 81: "Pancadas de chuva moderadas",
        82: "Pancadas de chuva violentas",
        85: "Pancadas de neve fracas", 86: "Pancadas de neve fortes",
        95: "Tempestade", 96: "Tempestade com granizo fraco",
        99: "Tempestade com granizo forte"
    }
    
    return {
        "temperature": f"{temp_c}°C",
        "feels_like": f"{feels_like}°C",
        "humidity": f"{humidity}%",
        "description": weather_codes_pt.get(weather_code, f"Código {weather_code}"),
        "wind": f"{wind_kmh} km/h",
        "location": "São Paulo",
        "source": "Open-Meteo",
        "timestamp": datetime.now().isoformat()
    }


def get_rain_forecast() -> dict:
    """Previsão de chuva (usa dados já cacheados)."""
    data = _fetch_all_weather_data()
    
    if "error" in data:
        return {"will_rain": None, "max_probability": 0, "certainty": "desconhecida"}
    
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    precip_prob = hourly.get("precipitation_probability", [])
    precip_mm = hourly.get("precipitation", [])
    
    # Filtra horas futuras
    now = datetime.now()
    current_hour_idx = 0
    for i, t in enumerate(times):
        try:
            hour_dt = datetime.fromisoformat(t)
            if hour_dt.hour == now.hour:
                current_hour_idx = i
                break
        except:
            continue
    
    future_probs = precip_prob[current_hour_idx:]
    future_mm = precip_mm[current_hour_idx:]
    
    max_prob = max(future_probs) if future_probs else 0
    total_mm = sum(future_mm) if future_mm else 0
    
    if max_prob >= 70:
        will_rain, certainty = True, "alta"
    elif max_prob >= 40:
        will_rain, certainty = True, "média"
    else:
        will_rain, certainty = False, "baixa"
    
    return {
        "will_rain": will_rain,
        "max_probability": max_prob,
        "total_mm": round(total_mm, 1),
        "certainty": certainty
    }


def get_air_quality() -> dict:
    """Qualidade do ar (usa dados já cacheados)."""
    data = _fetch_all_weather_data()
    
    if "error" in data:
        return {"aqi": None, "quality": "desconhecida"}
    
    current = data.get("air_quality", {})
    aqi = current.get("us_aqi")
    
    if aqi is None:
        return {"aqi": None, "quality": "desconhecida"}
    
    if aqi <= 50:
        quality, color = "Boa", "verde"
    elif aqi <= 100:
        quality, color = "Moderada", "amarelo"
    elif aqi <= 150:
        quality, color = "Ruim para sensíveis", "laranja"
    elif aqi <= 200:
        quality, color = "Ruim", "vermelho"
    else:
        quality, color = "Muito ruim", "roxo"
    
    return {
        "aqi": aqi,
        "quality": quality,
        "color": color,
        "pm25": current.get("pm2_5")
    }


def get_weather_summary() -> str:
    """Retorna resumo do clima em texto."""
    weather = get_weather_sao_paulo()
    if "error" in weather:
        return "Não consegui obter o clima agora."
    
    return (
        f"Clima em São Paulo: {weather['description']}, "
        f"{weather['temperature']} (sensação {weather['feels_like']}), "
        f"umidade {weather['humidity']}, vento {weather['wind']}"
    )
