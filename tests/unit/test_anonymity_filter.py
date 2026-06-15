"""Unit tests for the configurable minimum-anonymity filtering in the engine."""

from __future__ import annotations

import asyncio

from src.core.constants import AnonymityLevel, Protocol
from src.models.proxy import Proxy
from src.validators.engine import VerificationEngine


def _engine(minimum: str) -> VerificationEngine:
    # No geo cache and an empty DB path: GeoLocator degrades to no-op.
    return VerificationEngine(
        concurrency=10,
        tcp_timeout=1.0,
        validate_timeout=1.0,
        max_latency_ms=8000.0,
        geoip_country_db="",
        geo_cache_file=None,
        minimum_anonymity=minimum,
    )


def _patch_stubs(engine: VerificationEngine, anonymity: AnonymityLevel) -> None:
    """Replace the dynamically loaded dimension modules with fast stubs."""

    async def _alive(proxy: Proxy, timeout: float) -> bool:
        return True

    async def _protocol(proxy: Proxy, timeout: float) -> Protocol:
        return Protocol.HTTP

    async def _latency(proxy: Proxy, timeout: float) -> float:
        return 100.0

    async def _anonymity(proxy: Proxy, real_ip, timeout: float) -> AnonymityLevel:
        return anonymity

    engine._liveliness.check_liveliness = _alive  # type: ignore[attr-defined]
    engine._protocol.detect_protocol = _protocol  # type: ignore[attr-defined]
    engine._latency.measure_latency = _latency  # type: ignore[attr-defined]
    engine._anonymity.check_anonymity = _anonymity  # type: ignore[attr-defined]


def test_elite_minimum_drops_transparent() -> None:
    engine = _engine("elite")
    _patch_stubs(engine, AnonymityLevel.TRANSPARENT)
    result = asyncio.run(engine.verify_all([Proxy(ip="1.1.1.1", port=80)]))
    assert all(not p.is_alive for p in result)


def test_elite_minimum_keeps_elite() -> None:
    engine = _engine("elite")
    _patch_stubs(engine, AnonymityLevel.ELITE)
    result = asyncio.run(engine.verify_all([Proxy(ip="1.1.1.1", port=80)]))
    assert any(p.is_alive for p in result)


def test_transparent_minimum_keeps_everything() -> None:
    engine = _engine("transparent")
    _patch_stubs(engine, AnonymityLevel.TRANSPARENT)
    result = asyncio.run(engine.verify_all([Proxy(ip="1.1.1.1", port=80)]))
    assert any(p.is_alive for p in result)
