# app/core/cache.py

import json
import os
from typing import Any, Optional, Type
from redis import Redis
from redis.connection import BlockingConnectionPool
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

_pool = BlockingConnectionPool.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=20,
    timeout=5,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
)
_redis = Redis(connection_pool=_pool)


def cache_get_json(key: str, model_cls: Optional[Type[BaseModel]] = None) -> Optional[Any]:
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
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao recuperar {key}: {e}")
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 0) -> None:
    try:
        payload = json.dumps(value, default=str)  # garante UUID/datetime serializáveis
        if ttl_seconds > 0:
            _redis.setex(key, ttl_seconds, payload)
        else:
            _redis.set(key, payload)
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao salvar {key}: {e}")


def cache_delete(key: str) -> None:
    try:
        _redis.delete(key)
    except Exception as e:
        print(f"[CACHE ERROR] Falha ao deletar {key}: {e}")


def cache_ping() -> bool:
    try:
        return _redis.ping()
    except Exception:
        return False
