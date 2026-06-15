"""Integration test for the full pipeline using stubbed components."""

from __future__ import annotations

import asyncio
from pathlib import Path

from src.core.pipeline_manager import PipelineManager
from src.exporters.master_file_builder import MasterFileBuilder
from src.core.constants import AnonymityLevel, Protocol
from src.deduplication.early_aggregator import EarlyAggregator
from src.models.proxy import Proxy
from src.models.source_metadata import SourceHealth, SourceMetadata


class _StubCollector:
    async def collect(self, sources):
        proxies = [
            Proxy(ip="1.1.1.1", port=80, source="stub"),
            Proxy(ip="1.1.1.1", port=80, source="stub"),  # duplicate
            Proxy(ip="2.2.2.2", port=8080, source="stub"),
        ]
        health = [SourceHealth(name="stub", url="http://x", success=True, proxies_found=3)]
        return proxies, health


class _StubVerifier:
    async def verify_all(self, proxies):
        for p in proxies:
            p.is_alive = True
            p.latency_ms = 250.0
            p.protocol = Protocol.HTTPS
            p.anonymity = AnonymityLevel.ELITE
            p.country_code = "US"
        return proxies


class _StubEnricher:
    async def enrich_all(self, proxies):
        for p in proxies:
            p.quality_score = 90
        return proxies


def test_full_pipeline_writes_outputs(tmp_path: Path) -> None:
    out = tmp_path / "outputs"
    manager = PipelineManager(
        sources=[SourceMetadata(name="stub", url="http://x", scraper_type="github_raw")],
        collector=_StubCollector(),
        deduplicator=EarlyAggregator(),
        verifier=_StubVerifier(),
        enricher=_StubEnricher(),
        exporter=MasterFileBuilder(str(out)),
    )
    result = asyncio.run(manager.run())

    assert result.stats.raw_collected == 3
    assert result.stats.after_dedup == 2
    assert result.stats.alive == 2
    master = (out / "proxies.txt").read_text().strip().splitlines()
    assert set(master) == {"1.1.1.1:80", "2.2.2.2:8080"}
    assert (out / "metadata" / "manifest.json").exists()
    assert (out / "by_protocol" / "https.txt").exists()
    assert (out / "by_country" / "US_proxies.txt").exists()
