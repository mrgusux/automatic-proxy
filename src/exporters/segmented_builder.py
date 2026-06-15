"""Split proxies into country / protocol / anonymity segmented files."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from src.core.constants import AnonymityLevel
from src.exporters.atomic_writer import atomic_write_text
from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class SegmentedBuilder:
    """Produce by_country / by_protocol / by_anonymity output directories."""

    def __init__(self, output_dir: str) -> None:
        self._root = Path(output_dir)

    def build(self, proxies: list[Proxy]) -> None:
        self._build_by_country(proxies)
        self._build_by_protocol(proxies)
        self._build_by_anonymity(proxies)

    def _build_by_country(self, proxies: list[Proxy]) -> None:
        buckets: dict[str, list[str]] = defaultdict(list)
        for proxy in proxies:
            code = (proxy.country_code or "XX").upper()
            buckets[code].append(proxy.line())
        for code, lines in buckets.items():
            atomic_write_text(
                self._root / "by_country" / f"{code}_proxies.txt",
                "\n".join(lines) + "\n",
            )
        logger.info("Wrote %d country files", len(buckets))

    def _build_by_protocol(self, proxies: list[Proxy]) -> None:
        buckets: dict[str, list[str]] = defaultdict(list)
        for proxy in proxies:
            buckets[proxy.protocol.value].append(proxy.line())
        for protocol, lines in buckets.items():
            atomic_write_text(
                self._root / "by_protocol" / f"{protocol}.txt",
                "\n".join(lines) + "\n",
            )
        logger.info("Wrote %d protocol files", len(buckets))

    def _build_by_anonymity(self, proxies: list[Proxy]) -> None:
        wanted = (AnonymityLevel.ELITE, AnonymityLevel.ANONYMOUS)
        buckets: dict[str, list[str]] = defaultdict(list)
        for proxy in proxies:
            if proxy.anonymity in wanted:
                buckets[proxy.anonymity.value].append(proxy.line())
        for level, lines in buckets.items():
            atomic_write_text(
                self._root / "by_anonymity" / f"{level}.txt",
                "\n".join(lines) + "\n",
            )
        logger.info("Wrote %d anonymity files", len(buckets))
