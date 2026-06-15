"""Unit tests for the CircuitBreaker and GeoCache improvements."""

from __future__ import annotations

import time
from pathlib import Path

from src.enrichment.geo_cache import GeoCache
from src.utils.rate_limiter import CircuitBreaker


def test_circuit_breaker_opens_after_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=3, cooldown=60.0)
    assert breaker.is_open("src") is False
    breaker.record_failure("src")
    breaker.record_failure("src")
    assert breaker.is_open("src") is False  # below threshold
    breaker.record_failure("src")
    assert breaker.is_open("src") is True  # threshold reached -> open


def test_circuit_breaker_resets_on_success() -> None:
    breaker = CircuitBreaker(failure_threshold=2, cooldown=60.0)
    breaker.record_failure("src")
    breaker.record_success("src")
    breaker.record_failure("src")
    # Success reset the counter, so a single new failure is still below threshold.
    assert breaker.is_open("src") is False


def test_circuit_breaker_cooldown_elapses() -> None:
    breaker = CircuitBreaker(failure_threshold=1, cooldown=0.05)
    breaker.record_failure("src")
    assert breaker.is_open("src") is True
    time.sleep(0.06)
    # After cooldown the circuit closes again and allows a retry.
    assert breaker.is_open("src") is False


def test_geo_cache_set_get_and_persist(tmp_path: Path) -> None:
    cache_file = tmp_path / "geo.json"
    cache = GeoCache(str(cache_file))
    assert cache.get("1.2.3.4") is None
    cache.set("1.2.3.4", {"code": "US", "name": "United States"})
    cache.flush()
    assert cache_file.exists()

    # A fresh instance should load the persisted entry.
    reloaded = GeoCache(str(cache_file))
    entry = reloaded.get("1.2.3.4")
    assert entry is not None
    assert entry["code"] == "US"


def test_geo_cache_handles_corrupt_file(tmp_path: Path) -> None:
    cache_file = tmp_path / "geo.json"
    cache_file.write_text("{ not valid json", encoding="utf-8")
    # Should not raise; starts with an empty cache instead.
    cache = GeoCache(str(cache_file))
    assert cache.get("9.9.9.9") is None
