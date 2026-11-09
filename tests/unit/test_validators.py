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


@pytest.mark.asyncio
async def test_https_proxy_scheme_normalization() -> None:
    import importlib
    anon_mod = importlib.import_module("src.validators.03_anonymity_check")
    lat_mod = importlib.import_module("src.validators.04_latency_tester")

    p = Proxy(ip="1.2.3.4", port=8443, protocol=Protocol.HTTPS)
    sess_anon, req_anon = anon_mod._build_session(p, 5.0)
    sess_lat, req_lat = lat_mod._build_session(p, 5.0)
    await sess_anon.close()
    await sess_lat.close()

    assert req_anon == "http://1.2.3.4:8443"
    assert req_lat == "http://1.2.3.4:8443"


@pytest.mark.asyncio
async def test_dnsbl_ignores_open_resolver_responses(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.enrichment.spam_blacklist_check import SpamBlacklistChecker
    checker = SpamBlacklistChecker(enabled=True)

    # Simulate getaddrinfo returning 127.255.255.254 (Spamhaus open-resolver rejection)
    async def fake_getaddrinfo(host: str, port: int, family: int = 0) -> list:
        return [(2, 1, 0, "", ("127.255.255.254", 0))]

    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "getaddrinfo", fake_getaddrinfo)

    is_listed = await checker._query_dnsbl("zen.spamhaus.org", "4.3.2.1")
    assert is_listed is False


@pytest.mark.asyncio
async def test_dnsbl_ignores_hijacked_public_nxdomain(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.enrichment.spam_blacklist_check import SpamBlacklistChecker
    checker = SpamBlacklistChecker(enabled=True)

    # Simulate getaddrinfo returning an ISP NXDOMAIN hijack public IP (not 127.0.0.0/8)
    async def fake_getaddrinfo(host: str, port: int, family: int = 0) -> list:
        return [(2, 1, 0, "", ("92.242.140.21", 0))]

    loop = asyncio.get_running_loop()
    monkeypatch.setattr(loop, "getaddrinfo", fake_getaddrinfo)

    is_listed = await checker._query_dnsbl("zen.spamhaus.org", "4.3.2.1")
    assert is_listed is False


@pytest.mark.asyncio
async def test_dnsbl_rejects_invalid_ip() -> None:
    from src.enrichment.spam_blacklist_check import SpamBlacklistChecker
    checker = SpamBlacklistChecker(enabled=True)
    assert await checker._check_dnsbl("invalid.ip") is False
    assert await checker._check_dnsbl("2001:db8::1") is False


def test_geo_locator_city_and_country_databases() -> None:
    import importlib
    import os
    import pytest
    geo_mod = importlib.import_module("src.validators.05_geo_locator")
    city_db = "data/geoip/GeoLite2-City.mmdb"
    country_db = "data/geoip/GeoLite2-Country.mmdb"

    if not os.path.exists(country_db) and not os.path.exists(city_db):
        pytest.skip("GeoIP mmdb databases not present in environment")

    p = Proxy(ip="8.8.8.8", port=80, protocol=Protocol.HTTP)
    # Test City DB locate
    locator_city = geo_mod.GeoLocator(country_db, city_db)
    code, name, city = locator_city.locate(p)
    assert code == "US"
    assert name == "United States"

    # Test Country DB locate
    locator_country = geo_mod.GeoLocator(country_db)
    code_c, name_c, city_c = locator_country.locate(p)
    assert code_c == "US"
    assert name_c == "United States"
    assert city_c is None


