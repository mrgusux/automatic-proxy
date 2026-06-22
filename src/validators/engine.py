"""Verification engine: orchestrates the 5 validation dimensions."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType

from src.core.constants import AnonymityLevel
from src.enrichment.geo_cache import GeoCache
from src.models.proxy import Proxy
from src.utils.async_semaphore_pool import AsyncSemaphorePool
from src.utils.config_loader import Settings, load_minimum_anonymity

logger = logging.getLogger(__name__)

_VALIDATORS_DIR = Path(__file__).parent

_ANONYMITY_RANK: dict[AnonymityLevel, int] = {
    AnonymityLevel.UNKNOWN: 0,
    AnonymityLevel.TRANSPARENT: 1,
    AnonymityLevel.ANONYMOUS: 2,
    AnonymityLevel.ELITE: 3,
}


def _load(module_filename: str) -> ModuleType:
    path = _VALIDATORS_DIR / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load validator module {module_filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerificationEngine:
    """Run all five validation stages over the deduplicated proxy set."""

    def __init__(
        self,
        concurrency: int,
        tcp_timeout: float,
        validate_timeout: float,
        max_latency_ms: float,
        geoip_country_db: str,
        geo_cache_file: str | None = None,
        minimum_anonymity: str = "transparent",
        real_ip: str | None = None,
    ) -> None:
        self._pool = AsyncSemaphorePool(concurrency)
        self._tcp_timeout = tcp_timeout
        self._validate_timeout = validate_timeout
        self._max_latency_ms = max_latency_ms
        self._real_ip = real_ip
        self._cache = GeoCache(geo_cache_file) if geo_cache_file else None
        self._min_anonymity_rank = _ANONYMITY_RANK.get(
            AnonymityLevel(minimum_anonymity), 1
        )

        self._liveliness = _load("01_liveliness_tcp.py")
        self._protocol = _load("02_protocol_detector.py")
        self._anonymity = _load("03_anonymity_check.py")
        self._latency = _load("04_latency_tester.py")
        geo_module = _load("05_geo_locator.py")
        self._geo = geo_module.GeoLocator(geoip_country_db)

    async def _verify_one(self, proxy: Proxy) -> Proxy:
        alive = await self._liveliness.check_liveliness(proxy, self._tcp_timeout)
        if not alive:
            proxy.is_alive = False
            return proxy

        proxy.protocol = await self._protocol.detect_protocol(proxy, self._tcp_timeout)

        latency = await self._latency.measure_latency(proxy, self._validate_timeout)
        if latency is None or latency > self._max_latency_ms:
            proxy.is_alive = False
            return proxy
        proxy.latency_ms = latency

        proxy.anonymity = await self._anonymity.check_anonymity(
            proxy, self._real_ip, self._validate_timeout
        )
        if proxy.anonymity == AnonymityLevel.UNKNOWN:
            proxy.anonymity = AnonymityLevel.TRANSPARENT

        if _ANONYMITY_RANK.get(proxy.anonymity, 0) < self._min_anonymity_rank:
            proxy.is_alive = False
            return proxy

        code, name = self._resolve_geo(proxy)
        if code:
            proxy.country_code = code
        if name:
            proxy.country_name = name

        proxy.is_alive = True
        return proxy

    def _resolve_geo(self, proxy: Proxy) -> tuple[str | None, str | None]:
        if self._cache is not None:
            cached = self._cache.get(proxy.ip)
            if cached is not None:
                return cached.get("code"), cached.get("name")
        code, name = self._geo.locate(proxy)
        if self._cache is not None:
            self._cache.set(proxy.ip, {"code": code, "name": name})
        return code, name

    async def verify_all(self, proxies: list[Proxy]) -> list[Proxy]:
        logger.info("Verifying %d proxies (concurrency-bounded)", len(proxies))
        verified = await self._pool.map(self._verify_one, proxies)
        self._geo.close()
        if self._cache is not None:
            self._cache.flush()
        return verified


def build_verifier(settings: Settings) -> VerificationEngine:
    return VerificationEngine(
        concurrency=settings.validate_concurrency,
        tcp_timeout=settings.tcp_timeout,
        validate_timeout=settings.validate_timeout,
        max_latency_ms=settings.max_latency_ms,
        geoip_country_db=settings.geoip_country_db,
        geo_cache_file=settings.geo_cache_file,
        minimum_anonymity=load_minimum_anonymity(settings.validation_rules_file),
    )
