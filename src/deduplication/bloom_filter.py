"""Memory-efficient Bloom filter for ultra-fast probabilistic dedup."""

from __future__ import annotations

import hashlib
import math


class BloomFilter:
    """A classic Bloom filter using a Python bytearray as the bit array.

    Provides O(1) membership tests with a tunable false-positive rate. Used to
    cheaply skip proxies already seen across very large input sets without
    storing every key in memory.
    """

    def __init__(self, expected_items: int = 1_000_000, false_positive: float = 0.001) -> None:
        if expected_items <= 0:
            raise ValueError("expected_items must be positive")
        if not (0.0 < false_positive < 1.0):
            raise ValueError("false_positive must be in (0, 1)")
        self._size = self._optimal_size(expected_items, false_positive)
        self._hash_count = self._optimal_hashes(self._size, expected_items)
        self._bits = bytearray((self._size + 7) // 8)
        self._count = 0

    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        return max(8, int(-(n * math.log(p)) / (math.log(2) ** 2)))

    @staticmethod
    def _optimal_hashes(m: int, n: int) -> int:
        return max(1, int((m / n) * math.log(2)))

    def _indexes(self, item: str) -> list[int]:
        digest = hashlib.sha256(item.encode("utf-8")).digest()
        h1 = int.from_bytes(digest[:8], "big")
        h2 = int.from_bytes(digest[8:16], "big") | 1
        return [(h1 + i * h2) % self._size for i in range(self._hash_count)]

    def _get_bit(self, index: int) -> bool:
        return bool(self._bits[index // 8] & (1 << (index % 8)))

    def _set_bit(self, index: int) -> None:
        self._bits[index // 8] |= 1 << (index % 8)

    def add(self, item: str) -> bool:
        """Add an item. Returns True if it was probably new, False if seen."""
        indexes = self._indexes(item)
        seen = all(self._get_bit(i) for i in indexes)
        if seen:
            return False
        for i in indexes:
            self._set_bit(i)
        self._count += 1
        return True

    def __contains__(self, item: str) -> bool:
        return all(self._get_bit(i) for i in self._indexes(item))

    def __len__(self) -> int:
        return self._count
