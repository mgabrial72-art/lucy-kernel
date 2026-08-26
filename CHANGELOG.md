# Changelog

Todas as mudancas notaveis deste projeto serao documentadas neste arquivo.

## [6.0.0] - 2026-08-26

### 🎉 Estagio 3: Testes & Polimento
- ✅ Estrutura de testes (pytest + httpx)
- ✅ GitHub Actions CI
- ✅ Dockerfile + docker-compose
- ✅ Pre-commit hooks (ruff)
- ✅ pyproject.toml
- ✅ README com badges
- 🐛 Cache TTS corrigido (MD5 estavel)

### ⚡ Estagio 2: Performance
- ✅ Cache LRU com TTL
- ✅ 1 request Open-Meteo combinado
- ✅ Contexto condicional
- ✅ TTS com cache
- 🚀 30-50% mais rapido

### 🔒 Estagio 1: Seguranca
- ✅ Pydantic BaseSettings
- ✅ Logging loguru
- ✅ SQLite persistente
- ✅ Rate limiting
- ✅ CORS restrito

## [5.0.0] - 2026-08-26
- Contexto em tempo real (background 15min)
- Voz Edge TTS (Francisca PT-BR)
- Mem0 com Qdrant
- Agendamentos
- Anti-alucinacao forte
- Regra absoluta de privacidade
