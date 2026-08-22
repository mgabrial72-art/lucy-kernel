#!/usr/bin/env python3
"""
Lucy Proactive Worker — mantém modelo quente e coleta dados em background.
Rodar via systemd: lucy-worker.service
"""

# IMPORTANTE: sys.path PRIMEIRO, antes de qualquer import local
import sys
import os
sys.path.insert(0, "/home/ubuntu/lucy-kernel")
os.chdir("/home/ubuntu/lucy-kernel")

# Agora os imports padrão
import time
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from config.timezone import now_sp

# Imports locais (agora funcionam)
from services.cleanup_service import run_full_cleanup
from services.proactive_executor import run_proactive_cycle

DB_PATH = os.path.expanduser("~/lucy-kernel/database/lucy_memory.db")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "huihui_ai/qwen3-abliterated:8b"

def init_cache():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS proactive_cache (
        key TEXT PRIMARY KEY, value TEXT NOT NULL,
        collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        expires_at DATETIME NOT NULL, task_name TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def save_cache(key, value, ttl_min, task):
    exp = now_sp() + timedelta(minutes=ttl_min)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT OR REPLACE INTO proactive_cache VALUES (?,?,?,?,?)',
        (key, json.dumps(value, ensure_ascii=False), now_sp().isoformat(), exp.isoformat(), task))
    conn.commit()
    conn.close()
    print(f"[{now_sp():%H:%M}] 💾 {key} salvo (TTL {ttl_min}min)", flush=True)

def task_keep_alive():
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL, "prompt": "ping", "stream": False,
            "keep_alive": -1,
            "options": {"num_predict": 3, "num_ctx": 512}
        }, timeout=120)
        r.raise_for_status()
        print(f"[{now_sp():%H:%M}] 🔥 Modelo quente", flush=True)
    except Exception as e:
        print(f"[{now_sp():%H:%M}] ⚠️ keep_alive falhou: {e}", flush=True)

def task_weather():
    try:
        # Usa open-meteo (gratuito, sem API key, confiável)
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": "-23.66",
                "longitude": "-46.53",
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "timezone": "America/Sao_Paulo",
            },
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()["current"]
        
        # Converte weather_code para descrição
        wmo_codes = {
            0: "céu limpo", 1: "predominantemente limpo", 2: "parcialmente nublado",
            3: "nublado", 45: "nevoeiro", 48: "nevoeiro com geada",
            51: "garoa leve", 53: "garoa moderada", 55: "garoa intensa",
            61: "chuva leve", 63: "chuva moderada", 65: "chuva forte",
            71: "neve leve", 73: "neve moderada", 75: "neve forte",
            80: "pancadas leves", 81: "pancadas moderadas", 82: "pancadas fortes",
            95: "trovoada", 96: "trovoada com granizo leve", 99: "trovoada com granizo forte"
        }
        
        code = d.get("weather_code", 0)
        description = wmo_codes.get(code, f"código {code}")
        
        save_cache("weather:santo_andre", {
            "temperature_c": d.get("temperature_2m"),
            "feels_like_c": d.get("apparent_temperature"),
            "humidity": d.get("relative_humidity_2m"),
            "description": description,
            "wind_speed": d.get("wind_speed_10m"),
        }, 30, "weather")
        print(f"[{now_sp():%H:%M}] 🌤️ Clima: {d.get('temperature_2m')}°C, {description}", flush=True)
    except Exception as e:
        print(f"[{now_sp():%H:%M}] ⚠️ weather falhou: {e}", flush=True)


def task_system_health():
    try:
        with open("/proc/meminfo") as f:
            mi = f.read()
        total = int([l for l in mi.split('\n') if 'MemTotal' in l][0].split()[1])/1024/1024
        avail = int([l for l in mi.split('\n') if 'MemAvailable' in l][0].split()[1])/1024/1024
        save_cache("system:health", {
            "ram_used_percent": round(((total-avail)/total)*100, 1),
            "ram_available_gb": round(avail, 1)
        }, 60, "system_health")
    except Exception as e:
        print(f"[{now_sp():%H:%M}] ⚠️ health falhou: {e}", flush=True)

def task_cleanup():
    """Executa limpeza automática de duplicatas e dados obsoletos."""
    print(f"[{now_sp():%H:%M}] 🧹 Executando limpeza automática...", flush=True)
    try:
        results = run_full_cleanup()
        total = results.get("total_deleted", 0)
        print(f"[{now_sp():%H:%M}] ✅ Limpeza OK: {total} itens removidos", flush=True)
    except Exception as e:
        print(f"[{now_sp():%H:%M}] ❌ Erro na limpeza: {e}", flush=True)

# Lista de tarefas: (nome, função, intervalo_em_minutos)


def task_proactive_check():
    """Verifica e executa tarefas vencidas (lembretes e monitores)."""
    print(f"[{now_sp():%H:%M}] 🔄 Verificando tarefas proativas...", flush=True)
    try:
        stats = run_proactive_cycle()
        due = stats.get('due_tasks', 0)
        executed = stats.get('executed', 0)
        
        if due > 0:
            print(f"[{now_sp():%H:%M}] ✅ {executed}/{due} tarefas proativas executadas", flush=True)
        else:
            print(f"[{now_sp():%H:%M}] 💤 Nenhuma tarefa proativa vencida", flush=True)
    except Exception as e:
        print(f"[{now_sp():%H:%M}] ❌ Erro no check proativo: {e}", flush=True)


TASKS = [
    ("proactive_check", task_proactive_check, 1),  # 1 minuto
    ("keep_alive", task_keep_alive, 10),      # 20 min
    ("weather", task_weather, 30),            # 30 min
    ("system_health", task_system_health, 60), # 1 hora
    ("cleanup", task_cleanup, 360),           # 6 horas
]

if __name__ == "__main__":
    print(f"[{now_sp():%Y-%m-%d %H:%M}] 🚀 Lucy Worker iniciando", flush=True)
    init_cache()
    last_run = {n: 0 for n, _, _ in TASKS}
    
    # Executa tudo na inicialização
    for name, func, _ in TASKS:
        try:
            func()
            last_run[name] = time.time()
        except Exception as e:
            print(f"Erro {name}: {e}", flush=True)
    
    # Loop infinito
    while True:
        now = time.time()
        for name, func, interval_min in TASKS:
            if now - last_run[name] >= interval_min * 60:
                try:
                    func()
                    last_run[name] = now
                except Exception as e:
                    print(f"Erro {name}: {e}", flush=True)
        time.sleep(30)
