"""Pipeline orchestrator: Collect -> Dedup -> Verify -> Enrich -> Export."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.models.proxy import Proxy
from src.models.source_metadata import SourceHealth, SourceMetadata
from src.models.validation_stats import ValidationStats

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Final result bundle returned by the pipeline."""

    proxies: list[Proxy] = field(default_factory=list)
    stats: ValidationStats = field(default_factory=ValidationStats)
    source_health: list[SourceHealth] = field(default_factory=list)


class PipelineManager:
    """Coordinates the end-to-end collection workflow."""

    def __init__(
        self,
        sources: list[SourceMetadata],
        collector: object,
        deduplicator: object,
        verifier: object,
        enricher: object,
        exporter: object,
        max_alive_output: int = 50_000,
    ) -> None:
        self._sources = sources
        self._collector = collector
        self._deduplicator = deduplicator
        self._verifier = verifier
        self._enricher = enricher
        self._exporter = exporter
        self._max_alive_output = max_alive_output

    async def run(self) -> PipelineResult:
        stats = ValidationStats(sources_total=len(self._sources))
        result = PipelineResult(stats=stats)

        logger.info("Stage 1/5: collecting from %d sources", len(self._sources))
        raw_proxies, health = await self._collector.collect(self._sources)
        result.source_health = health
        stats.raw_collected = len(raw_proxies)
        stats.sources_ok = sum(1 for h in health if h.success)
        stats.sources_failed = sum(1 for h in health if not h.success)

        logger.info("Stage 2/5: deduplicating %d raw proxies", len(raw_proxies))
        unique = self._deduplicator.deduplicate(raw_proxies)
        stats.after_dedup = len(unique)

        logger.info("Stage 3/5: verifying %d unique proxies", len(unique))
        verified = await self._verifier.verify_all(unique)
        alive = [p for p in verified if p.is_alive]
        stats.alive = len(alive)
        stats.dead = len(verified) - len(alive)

        logger.info("Stage 4/5: enriching %d alive proxies", len(alive))
        enriched = await self._enricher.enrich_all(alive)
        enriched.sort(key=lambda p: p.quality_score, reverse=True)
        enriched = enriched[: self._max_alive_output]

        logger.info("Stage 5/5: exporting %d proxies", len(enriched))
        self._compute_distributions(enriched, stats)
        if enriched:
            stats.average_latency_ms = round(
                sum(p.latency_ms or 0.0 for p in enriched) / len(enriched), 2
            )
        stats.mark_finished()
        self._exporter.export(enriched, stats, result.source_health)

        result.proxies = enriched
        return result

    @staticmethod
    def _compute_distributions(proxies: list[Proxy], stats: ValidationStats) -> None:
        for proxy in proxies:
            stats.by_protocol[proxy.protocol.value] = (
                stats.by_protocol.get(proxy.protocol.value, 0) + 1
            )
            stats.by_anonymity[proxy.anonymity.value] = (
                stats.by_anonymity.get(proxy.anonymity.value, 0) + 1
            )
            if proxy.country_code:
                stats.by_country[proxy.country_code] = (
                    stats.by_country.get(proxy.country_code, 0) + 1
                )
