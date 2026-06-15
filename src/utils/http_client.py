"""Async HTTP client wrapper with retry, jitter and timeout handling."""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Optional

import aiohttp

from src.core.constants import DEFAULT_HEADERS
from src.utils.rate_limiter import TokenBucket

logger = logging.getLogger(__name__)


class HttpClient:
    """Thin wrapper around aiohttp with retries, timeout and rate limiting."""

    def __init__(
        self,
        timeout: float = 20.0,
        max_retries: int = 3,
        backoff: float = 0.5,
        rate_limiter: Optional[TokenBucket] = None,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._max_retries = max_retries
        self._backoff = backoff
        self._rate_limiter = rate_limiter
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "HttpClient":
        self._session = aiohttp.ClientSession(
            timeout=self._timeout, headers=DEFAULT_HEADERS
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def get_text(
        self, url: str, headers: Optional[dict[str, str]] = None
    ) -> str:
        """GET a URL and return the body text, retrying on transient errors.

        Uses exponential backoff with full jitter to avoid synchronised retry
        storms (thundering herd) when many sources fail at once.
        """
        if self._session is None:
            raise RuntimeError("HttpClient must be used as an async context manager")

        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            if self._rate_limiter is not None:
                await self._rate_limiter.acquire()
            try:
                async with self._session.get(url, headers=headers) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_exc = exc
                base = self._backoff * (2 ** (attempt - 1))
                wait = random.uniform(0, base)  # full jitter
                logger.debug(
                    "GET %s failed (attempt %d/%d): %s",
                    url,
                    attempt,
                    self._max_retries,
                    exc,
                )
                await asyncio.sleep(wait)
        raise RuntimeError(f"GET {url} failed after {self._max_retries} retries: {last_exc}")
