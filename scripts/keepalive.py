#!/usr/bin/env python3
"""Keep-alive: ping Ollama (1 token) + atualiza cache de clima. 15min via timer."""
import requests
import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = "/home/ubuntu/lucy-kernel/database/lucy_memory.db"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "huihui_ai/qwen3-abliterated:8b"

def ping_ollama():
    try:
        r = requests.post(OLLAMA_URL,
            json={"model": MODEL, "prompt": "ping", "stream": False,
                  "keep_alive": "24h", "options": {"num_predict": 1, "num_ctx": 1024, "num_thread": 4}},
            timeout=90)
        print(f"[{datetime.now()}] Ollama ping: {r.status_code}")
    except Exception as e:
        print(f"[{datetime.now()}] Ollama erro: {e}")

def update_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": -23.66, "longitude": -46.54,
                  "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
                  "timezone": "America/Sao_Paulo"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            print(f"[{datetime.now()}] Clima HTTP {r.status_code}")
            return
        d = r.json().get("current", {})
        weather = {"temperature_c": d.get("temperature_2m"),
                   "description": f"codigo {d.get('weather_code')}",
                   "humidity": d.get("relative_humidity_2m"),
                   "wind_kmh": d.get("wind_speed_10m")}

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        expires = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        # Schema: key, value, collected_at, expires_at, task_name
        cur.execute("""
            INSERT OR REPLACE INTO proactive_cache (key, value, collected_at, expires_at, task_name)
            VALUES (?, ?, ?, ?, ?)
        """, ("weather:santo_andre", json.dumps(weather), now, expires, "weather_update"))
        conn.commit()
        conn.close()
        print(f"[{datetime.now()}] Clima: {weather['temperature_c']}C (expires {expires[:16]})")
    except Exception as e:
        print(f"[{datetime.now()}] Clima erro: {e}")

if __name__ == "__main__":
    ping_ollama()
    update_weather()
