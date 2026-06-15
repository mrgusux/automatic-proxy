"""Early aggregation deduplicator (Set + Bloom filter combined)."""

from __future__ import annotations

import logging

from src.deduplication.bloom_filter import BloomFilter
from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class EarlyAggregator:
    """Deduplicate proxies by their ip:port key.

    For correctness a Python set holds the authoritative keys; a Bloom filter
    fronts it to keep the common 'already seen' path cheap on huge inputs.
    """

    def __init__(self, expected_items: int = 1_000_000) -> None:
        self._bloom = BloomFilter(expected_items=expected_items)
        self._seen: set[str] = set()

    def deduplicate(self, proxies: list[Proxy]) -> list[Proxy]:
        unique: list[Proxy] = []
        for proxy in proxies:
            key = proxy.key
            # Bloom says 'definitely new' -> accept fast.
            if key not in self._bloom:
                self._bloom.add(key)
                self._seen.add(key)
                unique.append(proxy)
                continue
            # Bloom may be a false positive; confirm against the exact set.
            if key not in self._seen:
                self._seen.add(key)
                unique.append(proxy)
        logger.info("Deduplicated %d -> %d proxies", len(proxies), len(unique))
        return unique


def build_deduplicator(settings) -> EarlyAggregator:  # noqa: ARG001 - uniform factory
    return EarlyAggregator()
