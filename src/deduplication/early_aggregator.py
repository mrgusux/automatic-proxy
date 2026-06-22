"""Early aggregation deduplicator (Set + Bloom filter combined)."""

from __future__ import annotations

import logging
from typing import Any

from src.deduplication.bloom_filter import BloomFilter
from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class EarlyAggregator:
    """Deduplicate proxies by their ip:port key."""

    def __init__(self, expected_items: int = 1_000_000) -> None:
        self._bloom = BloomFilter(expected_items=expected_items)
        self._seen: set[str] = set()

    def deduplicate(self, proxies: list[Proxy]) -> list[Proxy]:
        unique: list[Proxy] = []
        for proxy in proxies:
            key = proxy.key
            if key not in self._bloom:
                self._bloom.add(key)
                self._seen.add(key)
                unique.append(proxy)
                continue
            if key not in self._seen:
                self._seen.add(key)
                unique.append(proxy)
        logger.info("Deduplicated %d -> %d proxies", len(proxies), len(unique))
        return unique


def build_deduplicator(settings: Any) -> EarlyAggregator:
    return EarlyAggregator()
