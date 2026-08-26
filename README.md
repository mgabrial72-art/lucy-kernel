# 🧠 Lucy Frankenstein

<div align="center">

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-6.0-009688.svg)
![Status](https://img.shields.io/badge/status-production%20ready-green.svg)
![Privacy](https://img.shields.io/badge/privacy-100%25%20local-purple.svg)

**Assistente pessoal Jarvis-like 100% local e privado**

</div>

---

## ✨ Funcionalidades

- 🗣️ Voz Neural: Edge TTS (Francisca PT-BR) + Whisper STT
- 🧠 LLM Local: Mistral 7B customizado (lucy-optimized)
- 💾 Memoria Persistente: Mem0 + Qdrant + SQLite
- 📅 Agendamentos: Sistema completo de lembretes
- 🌤️ Clima em Tempo Real: Open-Meteo (Sao Paulo)
- 🕐 Fuso Horario: America/Sao_Paulo automatico
- 🔄 Contexto Automatico: Background updater 15min
- ⚡ Cache Inteligente: LRU com TTL (30-50% mais rapido)
- 🔒 Privacidade Total: 100% local, sem nuvem
- 🛡️ Regra Absoluta: Nunca menciona condicoes de saude

## 🏗️ Arquitetura

Tasker -> POST /v1/voice -> Lucy API -> {Context, LLM, Memory, TTS}

## 🚀 Instalacao

```bash
git clone https://github.com/mgabrial72-art/lucy-kernel.git
cd lucy-kernel
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
ollama pull mistral:latest
ollama create lucy-optimized -f Modelfile
./scripts/warmup.sh
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 📱 Integracao com Tasker

URL: http://SEU_IP:8000/v1/voice?session_id=capitao
Method: POST
Content-Type: text/plain
Body: %gv_heard
Save: Download/lucy_fala.mp3

## 🔒 Privacidade

- 100% Local - nenhum dado sai do servidor
- Sem APIs Pagas
- Memoria Persistente (SQLite + Qdrant)
- Regra Absoluta de Privacidade

---

**Feito com ❤️ para o Capitao Marcelo**
