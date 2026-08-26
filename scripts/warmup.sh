#!/bin/bash
# Warm-up otimizado (rápido)

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
  "options": {"num_predict": 3, "num_ctx": 1024}
}' > /dev/null

echo "[WARMUP] Aquecendo prompt simples..."
curl -s http://localhost:11434/api/generate -d '{
  "model": "lucy-optimized",
  "prompt": "Capitão: Oi\nLucy:",
  "stream": false,
  "keep_alive": -1,
  "options": {"num_predict": 10, "num_ctx": 1024}
}' > /dev/null

echo "[WARMUP] ✅ Pronto!"
