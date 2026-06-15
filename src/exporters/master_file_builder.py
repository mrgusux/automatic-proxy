"""Build the master proxies.txt file + the top-level exporter orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path

from src.exporters.atomic_writer import atomic_write_text
from src.exporters.json_manifest_builder import JsonManifestBuilder
from src.exporters.segmented_builder import SegmentedBuilder
from src.models.proxy import Proxy
from src.models.source_metadata import SourceHealth
from src.models.validation_stats import ValidationStats

logger = logging.getLogger(__name__)


class MasterFileBuilder:
    """Write the master best-proxies list and delegate segmented/manifest output."""

    def __init__(self, output_dir: str) -> None:
        self._output_dir = Path(output_dir)
        self._segmented = SegmentedBuilder(output_dir)
        self._manifest = JsonManifestBuilder(output_dir)

    def _write_master(self, proxies: list[Proxy]) -> None:
        lines = [p.line() for p in proxies]
        atomic_write_text(self._output_dir / "proxies.txt", "\n".join(lines) + "\n")
        logger.info("Wrote master file with %d proxies", len(lines))

    def export(
        self,
        proxies: list[Proxy],
        stats: ValidationStats,
        source_health: list[SourceHealth],
    ) -> None:
        self._write_master(proxies)
        self._segmented.build(proxies)
        self._manifest.build(stats, source_health)


def build_exporter(settings) -> MasterFileBuilder:
    return MasterFileBuilder(output_dir=settings.output_dir)
