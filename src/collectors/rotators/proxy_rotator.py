"""Round-robin rotator over already-collected proxies for self-scraping."""

from __future__ import annotations

import itertools
import threading

from src.models.proxy import Proxy


class ProxyRotator:
    """Provides outbound proxies for scraping, rotating in round-robin order."""

    def __init__(self, proxies: list[Proxy] | None = None) -> None:
        self._proxies: list[Proxy] = list(proxies or [])
        self._lock = threading.Lock()
        self._cycle = itertools.cycle(self._proxies) if self._proxies else None

    def update(self, proxies: list[Proxy]) -> None:
        with self._lock:
            self._proxies = list(proxies)
            self._cycle = itertools.cycle(self._proxies) if self._proxies else None

    def next(self) -> str | None:
        """Return the next proxy address, or None if the pool is empty."""
        with self._lock:
            if self._cycle is None:
                return None
            return next(self._cycle).address

    def __len__(self) -> int:
        return len(self._proxies)
