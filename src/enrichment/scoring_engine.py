"""Quality scoring engine (0-100) + enrichment orchestration.

Scoring weights and latency buckets are loaded from
``config/validation_rules.yaml`` so the scoring policy can be tuned without
code changes.
"""

from __future__ import annotations

import logging

from src.core.constants import AnonymityLevel, Protocol
from src.enrichment.asn_resolver import AsnResolver
from src.enrichment.spam_blacklist_check import SpamBlacklistChecker
from src.models.proxy import Proxy
from src.utils.async_semaphore_pool import AsyncSemaphorePool
from src.utils.config_loader import load_scoring_rules

logger = logging.getLogger(__name__)

# Relative weighting of each anonymity level (scaled by the configured weight).
_ANONYMITY_FACTOR = {
    AnonymityLevel.ELITE: 1.0,
    AnonymityLevel.ANONYMOUS: 0.63,
    AnonymityLevel.TRANSPARENT: 0.23,
    AnonymityLevel.UNKNOWN: 0.0,
}

# Relative weighting of each protocol (scaled by the configured weight).
_PROTOCOL_FACTOR = {
    Protocol.SOCKS5: 1.0,
    Protocol.HTTPS: 0.87,
    Protocol.SOCKS4: 0.6,
    Protocol.HTTP: 0.47,
}


class ScoringEngine:
    """Enrich each proxy with ASN/blacklist data, then compute a 0-100 score."""

    def __init__(
        self,
        asn_db_path: str,
        enable_asn: bool,
        enable_blacklist: bool,
        rules: dict | None = None,
        concurrency: int = 200,
    ) -> None:
        self._asn = AsnResolver(asn_db_path) if enable_asn else None
        self._blacklist = SpamBlacklistChecker(enabled=enable_blacklist)
        self._pool = AsyncSemaphorePool(concurrency)
        self._rules = rules or load_scoring_rules()

    def _latency_points(self, latency_ms: float | None) -> float:
        weight = self._rules["weight_latency"]
        if latency_ms is None:
            return 0.0
        if latency_ms < self._rules["excellent_below"]:
            return weight
        if latency_ms < self._rules["good_below"]:
            return weight * 0.75
        if latency_ms < self._rules["acceptable_below"]:
            return weight * 0.45
        return weight * 0.2

    def score(self, proxy: Proxy) -> int:
        total = (
            self._latency_points(proxy.latency_ms)
            + self._rules["weight_anonymity"] * _ANONYMITY_FACTOR.get(proxy.anonymity, 0.0)
            + self._rules["weight_protocol"] * _PROTOCOL_FACTOR.get(proxy.protocol, 0.0)
        )
        if not proxy.is_blacklisted:
            total += self._rules["weight_clean_blacklist"]
        return max(0, min(100, round(total)))

    async def _enrich_one(self, proxy: Proxy) -> Proxy:
        if self._asn is not None:
            asn, isp = self._asn.resolve(proxy)
            proxy.asn = asn
            proxy.isp = isp
        proxy.is_blacklisted = await self._blacklist.is_blacklisted(proxy)
        proxy.quality_score = self.score(proxy)
        return proxy

    async def enrich_all(self, proxies: list[Proxy]) -> list[Proxy]:
        logger.info("Enriching + scoring %d proxies", len(proxies))
        enriched = await self._pool.map(self._enrich_one, proxies)
        if self._asn is not None:
            self._asn.close()
        return enriched


def build_enricher(settings) -> ScoringEngine:
    return ScoringEngine(
        asn_db_path=settings.geoip_asn_db,
        enable_asn=settings.enable_asn_resolution,
        enable_blacklist=settings.enable_blacklist_check,
        rules=load_scoring_rules(settings.validation_rules_file),
    )
