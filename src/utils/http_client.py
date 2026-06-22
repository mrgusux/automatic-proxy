"""Async HTTP client wrapper with retry, jitter and timeout handling."""

from __future__ import annotations

import asyncio
import logging
import random
import socket
from types import TracebackType

import aiohttp

from src.core.constants import DEFAULT_HEADERS
from src.utils.rate_limiter import TokenBucket

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(
        self,
        timeout: float = 20.0,
        max_retries: int = 3,
        backoff: float = 0.5,
        rate_limiter: TokenBucket | None = None,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=float(timeout))
        self._max_retries = int(max_retries)
        self._backoff = float(backoff)
        self._rate_limiter = rate_limiter
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> HttpClient:
        resolver = aiohttp.ThreadedResolver()
        connector = aiohttp.TCPConnector(
            resolver=resolver,
            ssl=False,
            family=socket.AF_INET,
            limit=0,
        )
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self._timeout,
            headers=DEFAULT_HEADERS,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def get_text(
        self, url: str, headers: dict[str, str] | None = None
    ) -> str:
        if self._session is None:
            raise RuntimeError("HttpClient must be used as an async context manager")

        safe_headers = headers if isinstance(headers, dict) else {}
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                if self._rate_limiter is not None:
                    await self._rate_limiter.acquire()

                async with self._session.get(url, headers=safe_headers) as resp:
                    resp.raise_for_status()
                    return await resp.text()
            except Exception as exc:
                last_exc = exc
                base = self._backoff * (2 ** (attempt - 1))
                wait = random.uniform(0, base)
                await asyncio.sleep(wait)

        logger.error(
            "Failed to fetch %s after %d attempts. Error: %s",
            url, self._max_retries, last_exc,
        )
        raise RuntimeError(f"GET {url} failed: {last_exc}")
