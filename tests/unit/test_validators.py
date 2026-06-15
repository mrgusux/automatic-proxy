"""Unit tests for validators, dedup, and scoring logic."""

from __future__ import annotations

import asyncio

import pytest

from src.core.constants import AnonymityLevel, Protocol
from src.deduplication.bloom_filter import BloomFilter
from src.deduplication.early_aggregator import EarlyAggregator
from src.enrichment.scoring_engine import ScoringEngine
from src.models.proxy import Proxy
from src.utils.rate_limiter import TokenBucket


def test_bloom_filter_membership() -> None:
    bloom = BloomFilter(expected_items=1000, false_positive=0.01)
    assert bloom.add("1.2.3.4:80") is True
    assert bloom.add("1.2.3.4:80") is False
    assert "1.2.3.4:80" in bloom
    assert "9.9.9.9:80" not in bloom


def test_early_aggregator_removes_duplicates() -> None:
    proxies = [
        Proxy(ip="1.1.1.1", port=80),
        Proxy(ip="1.1.1.1", port=80),
        Proxy(ip="2.2.2.2", port=8080),
    ]
    unique = EarlyAggregator().deduplicate(proxies)
    assert len(unique) == 2


def test_proxy_rejects_invalid_ip() -> None:
    with pytest.raises(Exception):
        Proxy(ip="999.999.999.999", port=80)


def test_proxy_rejects_invalid_port() -> None:
    with pytest.raises(Exception):
        Proxy(ip="1.1.1.1", port=70000)


def _make_scoring_engine() -> ScoringEngine:
    # ASN/blacklist disabled so the engine constructs without external deps.
    return ScoringEngine(
        asn_db_path="",
        enable_asn=False,
        enable_blacklist=False,
        rules={
            "weight_latency": 40,
            "weight_anonymity": 35,
            "weight_protocol": 15,
            "weight_clean_blacklist": 10,
            "excellent_below": 500,
            "good_below": 1500,
            "acceptable_below": 4000,
        },
    )


def test_scoring_engine_ranges() -> None:
    engine = _make_scoring_engine()
    elite_fast = Proxy(
        ip="1.1.1.1",
        port=1080,
        protocol=Protocol.SOCKS5,
        latency_ms=120.0,
        anonymity=AnonymityLevel.ELITE,
    )
    transparent_slow = Proxy(
        ip="2.2.2.2",
        port=80,
        protocol=Protocol.HTTP,
        latency_ms=5000.0,
        anonymity=AnonymityLevel.TRANSPARENT,
    )
    assert engine.score(elite_fast) > engine.score(transparent_slow)
    assert 0 <= engine.score(transparent_slow) <= 100
    assert 0 <= engine.score(elite_fast) <= 100


def test_token_bucket_rate_limits() -> None:
    async def run() -> float:
        bucket = TokenBucket(rate=10.0, capacity=2)
        import time

        start = time.monotonic()
        for _ in range(4):
            await bucket.acquire()
        return time.monotonic() - start

    elapsed = asyncio.run(run())
    # 2 burst tokens are free; the remaining 2 wait ~0.1s each.
    assert elapsed >= 0.15
