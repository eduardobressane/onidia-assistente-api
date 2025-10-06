import json
import os
from typing import Any, Optional, Type
from redis import Redis
from redis.connection import BlockingConnectionPool
from pydantic import BaseModel

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://177.153.69.111:6379/0"
)

_pool = BlockingConnectionPool.from_url(
    REDIS_URL,
    decode_responses=True,   # strings (útil p/ JSON)
    max_connections=20,
    timeout=5,               # tempo p/ conseguir uma conexão do pool
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)
_redis = Redis(connection_pool=_pool)


# -------- Helpers -------- #

def cache_get_json(key: str, model_cls: Optional[Type[BaseModel]] = None) -> Optional[Any]:
    """Busca do Redis e opcionalmente valida com Pydantic."""
    try:
        raw = _redis.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        if model_cls:
            if isinstance(data, list):
                return [model_cls(**item) for item in data]
            return model_cls(**data)
        return data
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 0) -> None:
    """Salva no Redis, com TTL opcional (0 = infinito)."""
    try:
        if ttl_seconds and ttl_seconds > 0:
            _redis.setex(key, ttl_seconds, json.dumps(value))
        else:
            _redis.set(key, json.dumps(value))
    except Exception:
        pass


def cache_delete(key: str) -> None:
    try:
        _redis.delete(key)
    except Exception:
        pass


def cache_ping() -> bool:
    try:
        return _redis.ping()
    except Exception:
        return False
