# 🧠 Lucy Frankenstein

Assistente pessoal Jarvis-like 100% local e privado.

## 🎯 Funcionalidades

- 🗣️ **Voz**: Edge TTS (voz feminina PT-BR) + Whisper STT
- 🧠 **LLM**: Mistral 7B customizado (lucy-optimized)
- 💾 **Memória**: Mem0 com Qdrant local
- 📅 **Agendamentos**: Sistema de lembretes JSON
- 🌤️ **Clima**: Open-Meteo (São Paulo tempo real)
- 🕐 **Hora**: Fuso America/Sao_Paulo
- 🔄 **Contexto**: Background updater 15min
- 🔒 **Privacidade**: 100% local, sem nuvem

## 🏗️ ArquiteturaTasker → POST /v1/voice → Lucy API → {Context, LLM, Memory, TTS}## 📁 Estruturalucy-kernel/
├── api/
│   ├── main.py
│   ├── routes/ (chat, voice, schedule, weather, status, debug)
│   └── services/ (llm, memory, tts, weather, schedule, time, context_cache)
├── config/ (settings.py, identity.py)
├── scripts/ (warmup.sh)
├── Modelfile
└── requirements.txt## 🚀 Instalação

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

## 📱 Tasker## 🔒 Privacidade

- 100% local
- Sem APIs pagas
- Nunca menciona condições de saúde (regra absoluta)

---

**Feito com ❤️ para o Capitão Marcelo**
