"""Optional cross-run state persistence via Redis (local/docker use)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class RedisStateManager:
    """Persist seen proxy keys across runs using a Redis set.

    Redis is optional. When the ``redis`` package or a server is unavailable
    the manager degrades gracefully to a no-op so GitHub Actions runs (which
    are stateless) are unaffected.
    """

    def __init__(self, url: str = "redis://localhost:6379/0", key: str = "seen_proxies") -> None:
        self._key = key
        self._client = None
        try:
            import redis  # type: ignore

            self._client = redis.Redis.from_url(url, socket_connect_timeout=2)
            self._client.ping()
            logger.info("Connected to Redis for cross-run dedup state")
        except Exception as exc:  # noqa: BLE001 - optional dependency
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
        except Exception:  # noqa: BLE001
            return False

    def mark_seen(self, keys: list[str]) -> None:
        if self._client is None or not keys:
            return
        try:
            self._client.sadd(self._key, *keys)
        except Exception:  # noqa: BLE001
            pass
