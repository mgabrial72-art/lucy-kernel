"""Cache LRU simples com TTL em memória."""
import time
from functools import wraps
from threading import Lock
from typing import Any, Callable, Optional
from loguru import logger


class TTLCache:
    """Cache em memória com time-to-live."""
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 100):
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: dict = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Retorna valor se existir e não expirado."""
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expires_at = self._cache[key]
            if time.time() > expires_at:
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any):
        """Define valor com TTL."""
        with self._lock:
            # Limpa itens antigos se exceder tamanho
            if len(self._cache) >= self.max_size:
                # Remove o mais antigo
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[key] = (value, time.time() + self.ttl)
    
    def clear(self):
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> dict:
        """Estatísticas do cache."""
        with self._lock:
            now = time.time()
            valid = sum(1 for (_, exp) in self._cache.values() if now < exp)
            return {
                "size": len(self._cache),
                "valid": valid,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl
            }


def cached(ttl_seconds: int = 300):
    """Decorator para cachear resultado de função."""
    cache = TTLCache(ttl_seconds=ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gera chave baseada em args
            key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            result = cache.get(key)
            if result is not None:
                logger.debug(f"💾 Cache hit: {func.__name__}")
                return result
            
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        wrapper.cache = cache
        wrapper.cache_clear = cache.clear
        wrapper.cache_stats = cache.stats
        return wrapper
    
    return decorator


# Caches globais
weather_cache = TTLCache(ttl_seconds=300)  # 5 min
context_cache = TTLCache(ttl_seconds=60)   # 1 min (só p/ requests síncronos)
tts_cache = TTLCache(ttl_seconds=3600)     # 1 hora (frases comuns)

# Frases comuns para cache de TTS
COMMON_PHRASES = {
    "oi", "olá", "ola", "oi lucy", "olá lucy",
    "tudo bem", "como você está", "como vai",
    "bom dia", "boa tarde", "boa noite",
    "obrigado", "obrigada", "valeu",
    "sim", "não", "talvez"
}
