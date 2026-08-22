# Lucy Kernel v2.0

Assistente pessoal local do Marcelo (Capitao) usando IA offline com Ollama.

## Arquitetura

- **Modelo**: huihui_ai/qwen3-abliterated:8b (Q6_K uncensored)
- **Memoria**: Mark-L JSON unico (services/mark_l/memory/long_term.json)
- **Banco**: SQLite (database/lucy_memory.db)
- **Worker**: Tarefas proativas em background (clima, lembretes, keep-alive)
- **TTS**: Edge TTS (Microsoft)

## Estrutura

lucy-kernel/
- main.py                          # FastAPI + endpoints
- config/
  - identity.py                    # System prompt da Lucy
  - timezone.py                    # Helper timezone Sao Paulo
- database/
  - db.py                          # SQLite (historico + tarefas)
- services/
  - model_router.py                # Hard routing + modelo
  - behavior_engine.py             # Comportamento dinamico
  - streaming_tts.py               # TTS em streaming
  - task_scheduler.py              # Lembretes e tarefas
  - proactive_executor.py          # Execucao de tarefas
  - notification_service.py        # Notificacoes
  - cleanup_service.py             # Limpeza automatica
  - capabilities.py                # Capacidades expostas
  - web_search_service.py          # Busca web
  - mark_l/
    - memory_manager.py            # Gestao de memoria
    - memory/long_term.json        # Memoria persistente
  - worker/
    - proactive_worker.py          # Worker em background

## Endpoints

### Texto
- POST /chat - Conversa (JSON: {"message": "..."})
- POST /chat/stream - Streaming SSE

### Voz (Tasker)
- POST /v1/chat/voice - Texto para MP3 (body: texto puro)
- POST /v1/chat/voice/stream - Streaming com TTS em paralelo

### Compatibilidade OpenAI
- POST /v1/chat/completions - Formato OpenAI (usado pelo Sanna)
- POST /v1/audio/speech - TTS compativel OpenAI

## Performance

- Hard routing: menor que 0.02s (familia, trabalho, hobbies, hora)
- Conversa aberta: 6-15s (modelo quente)
- Voz Tasker: 6s (modelo Forever na RAM)
- Streaming: TTS em paralelo com geracao de texto

## Servicos Systemd

- lucy-kernel.service - API FastAPI (porta 8000)
- lucy-worker.service - Worker proativo
- lucy-tunnel.service - Tunnel ngrok

## Memoria (Mark-L)

Memoria persistente em JSON com categorias:
- identity - Dados pessoais
- preferences - Preferencias
- projects - Projetos ativos
- relationships - Familia (Julya, Isis, Ruby, Jully)
- wishes - Desejos
- notes - Notas livres

## Features

- Hard routing para respostas instantaneas
- Memoria persistente com Mark-L
- Historico de conversas no banco
- Lembretes com recorrencia (once/daily/weekly)
- Clima de Santo Andre cacheado
- Timezone America/Sao_Paulo em todo o sistema
- Keep-alive permanente do modelo

---

Desenvolvido para o Capitao
