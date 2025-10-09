import functools
import inspect
from typing import Callable, Any, List, Optional
from app.core.cache import cache_get_json, cache_set_json, cache_delete
from app.core.logger_config import debug, error

def cacheable( 
    key_prefix: Optional[str] = None, 
    key_params: Optional[List[str]] = None,
    ttl_seconds: int = 300
):
    """
    Decorator para cachear métodos que retornam dados serializáveis em JSON.

    :param ttl_seconds: TTL em segundos (default=300, 0 = infinito).
    :param key_prefix: Prefixo fixo para a chave no Redis (default = nome do método).
    :param key_params: Lista de parâmetros a considerar na chave do cache.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__

            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()

            # Se key_params foi definido, filtra apenas eles
            params = bound.arguments
            if key_params:
                params = {k: v for k, v in params.items() if k in key_params}

            # Monta chave determinística
            params_key = ":".join(f"{k}={v}" for k, v in params.items())
            cache_key = f"{prefix}:{params_key}" if params_key else prefix

            # Consulta cache
            cached = cache_get_json(cache_key)
            if cached:
                debug(f"[CACHE HIT] {cache_key}")
                return cached

            # Executa método real
            result = await func(*args, **kwargs)

            # Serializa antes de salvar
            try:
                if hasattr(result, "model_dump"):
                    value = result.model_dump()
                elif isinstance(result, list) and result and hasattr(result[0], "model_dump"):
                    value = [i.model_dump() for i in result]
                else:
                    value = result

                cache_set_json(cache_key, value, ttl_seconds)
                debug(f"[CACHE SET] {cache_key} (ttl={ttl_seconds})")
            except Exception as e:
                error(f"[Cacheable] Falha ao salvar cache ({cache_key}): {e}")

            return result
        return wrapper
    return decorator


def cache_evict(keys: list[str], key_params: list[str] = None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            sig = inspect.signature(func)
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            params = bound.arguments

            for key_prefix in keys:
                cache_key = None

                # Se o prefixo tiver placeholders -> substitui
                if "{" in key_prefix and "}" in key_prefix:
                    try:
                        cache_key = key_prefix.format(**params)
                    except KeyError:
                        cache_key = key_prefix
                # Se não tiver placeholder, usa literal SEM concatenar key_params
                else:
                    cache_key = key_prefix

                cache_delete(cache_key)
                debug(f"[CACHE DELETE] {cache_key}")
                
            return result
        return wrapper
    return decorator
