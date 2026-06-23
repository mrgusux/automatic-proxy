"""Verification engine: orchestrates the 5 validation dimensions with judge servers."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType

from src.core.constants import AnonymityLevel, Protocol
from src.enrichment.geo_cache import GeoCache
from src.models.proxy import Proxy
from src.utils.async_semaphore_pool import AsyncSemaphorePool
from src.utils.config_loader import Settings, load_minimum_anonymity
from src.validators.judge_servers import JudgeServers

logger = logging.getLogger(__name__)

_VALIDATORS_DIR = Path(__file__).parent

_ANONYMITY_RANK: dict[AnonymityLevel, int] = {
    AnonymityLevel.UNKNOWN: 0,
    AnonymityLevel.TRANSPARENT: 1,
    AnonymityLevel.ANONYMOUS: 2,
    AnonymityLevel.ELITE: 3,
}

_MAX_API_GEO_QUERIES = 5000


def _load(module_filename: str) -> ModuleType:
    path = _VALIDATORS_DIR / module_filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load validator module {module_filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VerificationEngine:
    """Run all five validation stages with judge server rotation."""

    def __init__(
        self,
        concurrency: int,
        tcp_timeout: float,
        validate_timeout: float,
        max_latency_ms: float,
        geoip_country_db: str,
        geoip_city_db: str | None = None,
        geo_cache_file: str | None = None,
        minimum_anonymity: str = "transparent",
        real_ip: str | None = None,
        max_retries: int = 2,
    ) -> None:
        self._pool = AsyncSemaphorePool(concurrency)
        self._tcp_timeout = tcp_timeout
        self._validate_timeout = validate_timeout
        self._max_latency_ms = max_latency_ms
        self._real_ip = real_ip
        self._max_retries = max_retries
        self._cache = GeoCache(geo_cache_file) if geo_cache_file else None
        self._min_anonymity_rank = _ANONYMITY_RANK.get(
            AnonymityLevel(minimum_anonymity), 1
        )

        self._liveliness = _load("01_liveliness_tcp.py")
        self._protocol = _load("02_protocol_detector.py")
        self._anonymity = _load("03_anonymity_check.py")
        self._latency = _load("04_latency_tester.py")
        geo_module = _load("05_geo_locator.py")
        self._geo = geo_module.GeoLocator(geoip_country_db, geoip_city_db)
        self._api_geo = geo_module.ApiGeoLocator()
        self._judges = JudgeServers()

    async def _verify_one(self, proxy: Proxy) -> Proxy:
        alive = await self._liveliness.check_liveliness(proxy, self._tcp_timeout)
        if not alive:
            proxy.is_alive = False
            return proxy

        proxy.protocol = await self._protocol.detect_protocol(proxy, self._tcp_timeout)

        judge = self._pick_judge(proxy.protocol)
        latency = await self._latency.measure_latency(
            proxy, self._validate_timeout, judge_url=judge, retries=self._max_retries
        )
        if latency is None or latency > self._max_latency_ms:
            proxy.is_alive = False
            return proxy
        proxy.latency_ms = latency

        anon_judge = self._pick_anon_judge()
        proxy.anonymity = await self._anonymity.check_anonymity(
            proxy, self._real_ip, self._validate_timeout,
            judge_url=anon_judge, retries=self._max_retries,
        )
        if proxy.anonymity == AnonymityLevel.UNKNOWN:
            proxy.anonymity = AnonymityLevel.TRANSPARENT

        if _ANONYMITY_RANK.get(proxy.anonymity, 0) < self._min_anonymity_rank:
            proxy.is_alive = False
            return proxy

        code, name, city = self._resolve_geo(proxy)
        if code:
            proxy.country_code = code
        if name:
            proxy.country_name = name
        if city:
            proxy.city = city

        proxy.is_alive = True
        return proxy

    def _pick_judge(self, protocol: Protocol) -> str | None:
        if protocol == Protocol.HTTPS:
            return self._judges.get_ssl()
        return self._judges.get_usual() or self._judges.get_any()

    def _pick_anon_judge(self) -> str | None:
        return self._judges.get_usual() or self._judges.get_any()

    def _resolve_geo(self, proxy: Proxy) -> tuple[str | None, str | None, str | None]:
        if self._cache is not None:
            cached = self._cache.get(proxy.ip)
            if cached is not None:
                return cached.get("code"), cached.get("name"), cached.get("city")
        code, name, city = self._geo.locate(proxy)
        if self._cache is not None:
            self._cache.set(proxy.ip, {"code": code, "name": name, "city": city})
        return code, name, city

    async def _apply_api_geo(self, proxies: list[Proxy]) -> None:
        needs_geo = [p for p in proxies if not p.country_code]
        if not needs_geo:
            return
        if len(needs_geo) > _MAX_API_GEO_QUERIES:
            logger.warning(
                "API geo: %d proxies need geo but cap is %d, skipping rest",
                len(needs_geo), _MAX_API_GEO_QUERIES,
            )
            needs_geo = needs_geo[:_MAX_API_GEO_QUERIES]
        logger.info("API geolocation: querying %d IPs", len(needs_geo))
        results = await self._api_geo.locate_batch(needs_geo)
        for p in needs_geo:
            code, name, city = results.get(p.ip, (None, None, None))
            if code:
                p.country_code = code
            if name:
                p.country_name = name
            if city:
                p.city = city

    async def verify_all(self, proxies: list[Proxy]) -> list[Proxy]:
        logger.info("Verifying %d proxies (concurrency-bounded)", len(proxies))

        await self._judges.ping_all(timeout=self._tcp_timeout)
        if self._judges.alive_count == 0:
            logger.warning("No alive judge servers! Using fallback URLs.")

        verified = await self._pool.map(self._verify_one, proxies)
        self._geo.close()
        if self._cache is not None:
            self._cache.flush()

        alive = [p for p in verified if p.is_alive]
        await self._apply_api_geo(alive)

        return verified


def build_verifier(settings: Settings) -> VerificationEngine:
    return VerificationEngine(
        concurrency=settings.validate_concurrency,
        tcp_timeout=settings.tcp_timeout,
        validate_timeout=settings.validate_timeout,
        max_latency_ms=settings.max_latency_ms,
        geoip_country_db=settings.geoip_country_db,
        geoip_city_db=settings.geoip_city_db,
        geo_cache_file=settings.geo_cache_file,
        minimum_anonymity=load_minimum_anonymity(settings.validation_rules_file),
        max_retries=settings.max_retries,
    )
