"""Build manifest.json (run stats) and source_health_report.json."""

from __future__ import annotations

import logging
from pathlib import Path

from src.exporters.atomic_writer import atomic_write_json
from src.models.source_metadata import SourceHealth
from src.models.validation_stats import ValidationStats

logger = logging.getLogger(__name__)


class JsonManifestBuilder:
    """Write machine-readable run metadata into outputs/metadata/."""

    def __init__(self, output_dir: str) -> None:
        self._meta_dir = Path(output_dir) / "metadata"

    def build(
        self, stats: ValidationStats, source_health: list[SourceHealth]
    ) -> None:
        manifest = {
            "generated_at": stats.finished_at,
            "started_at": stats.started_at,
            "summary": {
                "sources_total": stats.sources_total,
                "sources_ok": stats.sources_ok,
                "sources_failed": stats.sources_failed,
                "raw_collected": stats.raw_collected,
                "after_dedup": stats.after_dedup,
                "alive": stats.alive,
                "dead": stats.dead,
                "average_latency_ms": stats.average_latency_ms,
            },
            "distribution": {
                "by_protocol": stats.by_protocol,
                "by_anonymity": stats.by_anonymity,
                "by_country": stats.by_country,
            },
        }
        atomic_write_json(self._meta_dir / "manifest.json", manifest)

        health_report = {
            "generated_at": stats.finished_at,
            "sources": [h.model_dump() for h in source_health],
        }
        atomic_write_json(
            self._meta_dir / "source_health_report.json", health_report
        )
        logger.info("Wrote manifest.json and source_health_report.json")
