"""Optional cross-run state persistence via Redis (local/docker use)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RedisStateManager:
    """Persist seen proxy keys across runs using a Redis set."""

    def __init__(self, url: str = "redis://localhost:6379/0", key: str = "seen_proxies") -> None:
        self._key = key
        self._client: Any = None
        try:
            import redis

            self._client = redis.Redis.from_url(url, socket_connect_timeout=2)
            self._client.ping()
            logger.info("Connected to Redis for cross-run dedup state")
        except Exception as exc:
            logger.info("Redis unavailable (%s); cross-run state disabled", exc)
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def is_seen(self, key: str) -> bool:
        if self._client is None:
            return False
        try:
            return bool(self._client.sismember(self._key, key))
        except Exception:
            return False

    def mark_seen(self, keys: list[str]) -> None:
        if self._client is None or not keys:
            return
        try:
            self._client.sadd(self._key, *keys)
        except Exception:
            pass
