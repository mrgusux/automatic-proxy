"""Bounded async worker pool built on an asyncio.Semaphore."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


class AsyncSemaphorePool:
    """Run thousands of coroutines with a hard concurrency ceiling.

    Designed for the validation stage where 5000+ proxies must be checked
    concurrently without exhausting file descriptors or memory.
    """

    def __init__(self, concurrency: int) -> None:
        if concurrency <= 0:
            raise ValueError("concurrency must be positive")
        self._semaphore = asyncio.Semaphore(concurrency)

    async def _guarded(
        self, worker: Callable[[T], Awaitable[R]], item: T
    ) -> R | None:
        async with self._semaphore:
            try:
                return await worker(item)
            except Exception:  # noqa: BLE001 - isolate per-item failures
                return None

    async def map(
        self,
        worker: Callable[[T], Awaitable[R]],
        items: Iterable[T],
    ) -> list[R]:
        """Apply ``worker`` to every item, returning successful results only."""
        items_seq: Sequence[T] = list(items)
        tasks = [
            asyncio.create_task(self._guarded(worker, item)) for item in items_seq
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
