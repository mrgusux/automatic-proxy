"""Rate limiting primitives: Token Bucket + a simple circuit breaker."""

from __future__ import annotations

import asyncio
import time


class TokenBucket:
    """Async token-bucket rate limiter.

    Tokens refill continuously at ``rate`` tokens/second up to ``capacity``.
    Each :meth:`acquire` consumes one token, sleeping if necessary. This keeps
    the outbound request rate polite and avoids tripping source-side bans.
    """

    def __init__(self, rate: float, capacity: int) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._rate = rate
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._updated = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire ``tokens``, sleeping until enough are available."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                wait_for = deficit / self._rate
            await asyncio.sleep(wait_for)

    async def __aenter__(self) -> "TokenBucket":
        await self.acquire()
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None


class CircuitBreaker:
    """Track per-key failures and temporarily open the circuit after a threshold.

    Used to skip sources that keep failing, saving time and avoiding hammering a
    down endpoint. A key is 'open' (skipped) for ``cooldown`` seconds once it
    reaches ``failure_threshold`` consecutive failures.
    """

    def __init__(self, failure_threshold: int = 3, cooldown: float = 1800.0) -> None:
        self._threshold = failure_threshold
        self._cooldown = cooldown
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}

    def is_open(self, key: str) -> bool:
        """Return True if the key is currently in cooldown (should be skipped)."""
        until = self._open_until.get(key)
        if until is None:
            return False
        if time.monotonic() >= until:
            # Cooldown elapsed; reset and allow a retry.
            self._open_until.pop(key, None)
            self._failures[key] = 0
            return False
        return True

    def record_success(self, key: str) -> None:
        self._failures[key] = 0
        self._open_until.pop(key, None)

    def record_failure(self, key: str) -> None:
        count = self._failures.get(key, 0) + 1
        self._failures[key] = count
        if count >= self._threshold:
            self._open_until[key] = time.monotonic() + self._cooldown
