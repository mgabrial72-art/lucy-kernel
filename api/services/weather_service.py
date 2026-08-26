"""Serviço de clima usando Open-Meteo (gratuito, preciso, sem API key)."""
import requests
from datetime import datetime
from loguru import logger
from config.settings import settings


def get_weather_sao_paulo() -> dict:
    """Retorna clima atual de São Paulo usando Open-Meteo."""
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": settings.sp_latitude,
            "longitude": settings.sp_longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m",
            "timezone": "America/Sao_Paulo",
            "forecast_days": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current = data.get("current", {})
        
        temp_c = current.get("temperature_2m")
        feels_like = current.get("apparent_temperature")
        humidity = current.get("relative_humidity_2m")
        wind_kmh = current.get("wind_speed_10m")
        weather_code = current.get("weather_code", 0)
        
        weather_codes_pt = {
            0: "Céu limpo",
            1: "Predominantemente limpo",
            2: "Parcialmente nublado",
            3: "Nublado",
            45: "Neblina",
            48: "Neblina com geada",
            51: "Garoa fraca",
            53: "Garoa moderada",
            55: "Garoa intensa",
            61: "Chuva fraca",
            63: "Chuva moderada",
            65: "Chuva forte",
            66: "Chuva congelante fraca",
            67: "Chuva congelante forte",
            71: "Neve fraca",
            73: "Neve moderada",
            75: "Neve forte",
            77: "Grãos de neve",
            80: "Pancadas de chuva fracas",
            81: "Pancadas de chuva moderadas",
            82: "Pancadas de chuva violentas",
            85: "Pancadas de neve fracas",
            86: "Pancadas de neve fortes",
            95: "Tempestade",
            96: "Tempestade com granizo fraco",
            99: "Tempestade com granizo forte"
        }
        
        description_pt = weather_codes_pt.get(weather_code, f"Código {weather_code}")
        
        return {
            "temperature": f"{temp_c}°C",
            "feels_like": f"{feels_like}°C",
            "humidity": f"{humidity}%",
            "description": description_pt,
            "wind": f"{wind_kmh} km/h",
            "location": "São Paulo",
            "source": "Open-Meteo",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[WEATHER] Erro: {e}")
        return {"error": str(e)}


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
