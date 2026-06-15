#!/usr/bin/env python3
"""Local benchmark: measure scraping + dedup throughput on dummy data."""

from __future__ import annotations

import random
import time

from src.deduplication.early_aggregator import EarlyAggregator
from src.models.proxy import Proxy


def _make_dummy(n: int) -> list[Proxy]:
    proxies: list[Proxy] = []
    for _ in range(n):
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        port = random.randint(1, 65535)
        proxies.append(Proxy(ip=ip, port=port))
    # Introduce ~20% duplicates.
    proxies.extend(random.sample(proxies, k=n // 5))
    random.shuffle(proxies)
    return proxies


def main() -> None:
    for size in (10_000, 100_000, 500_000):
        proxies = _make_dummy(size)
        start = time.perf_counter()
        unique = EarlyAggregator(expected_items=size * 2).deduplicate(proxies)
        elapsed = time.perf_counter() - start
        rate = len(proxies) / elapsed if elapsed else 0
        print(
            f"size={len(proxies):>8} unique={len(unique):>8} "
            f"time={elapsed:6.3f}s rate={rate:,.0f}/s"
        )


if __name__ == "__main__":
    main()
