#!/bin/bash
# Warm-up agressivo: aquece modelo + cache de prompts comuns

echo "[WARMUP] Verificando Ollama..."
if ! systemctl is-active --quiet ollama; then
    sudo systemctl start ollama
    sleep 3
fi

echo "[WARMUP] Carregando lucy-optimized em RAM..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "lucy-optimized",
  "prompt": "OK",
  "stream": false,
  "keep_alive": -1,
  "options": {"num_predict": 5, "num_ctx": 2048}
}' > /dev/null

echo "[WARMUP] Aquecendo cache (prompt contextual típico)..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "lucy-optimized",
  "prompt": "CONTEXTO ATUAL: Bom dia Capitão. Clima nublado, 17 graus. Sem chuva.\n\nCapitão: E aí Lucy, como estamos?\nLucy:",
  "stream": false,
  "keep_alive": -1,
  "options": {"num_predict": 80, "num_ctx": 2048}
}' > /dev/null

echo "[WARMUP] Aquecendo cache (perguntas comuns)..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "lucy-optimized",
  "prompt": "Capitão: Vai chover hoje?\nLucy:",
  "stream": false,
  "keep_alive": -1,
  "options": {"num_predict": 40, "num_ctx": 2048}
}' > /dev/null

curl -s http://localhost:11434/api/generate -d '{
  "model": "lucy-optimized",
  "prompt": "Capitão: Como tá o tempo?\nLucy:",
  "stream": false,
  "keep_alive": -1,
  "options": {"num_predict": 40, "num_ctx": 2048}
}' > /dev/null

echo "[WARMUP] ✅ Modelo e caches prontos!"
