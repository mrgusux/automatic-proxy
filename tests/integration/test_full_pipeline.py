from __future__ import annotations

from pathlib import Path

import pytest

from src.core.constants import AnonymityLevel, Protocol
from src.exporters.master_file_builder import MasterFileBuilder
from src.models.proxy import Proxy
from src.models.source_metadata import SourceHealth
from src.models.validation_stats import ValidationStats


def _proxy(
    ip: str,
    port: int,
    protocol: Protocol,
    country_code: str,
    anonymity: AnonymityLevel,
    keep_alive: bool = False,
    software: str | None = None,
) -> Proxy:
    return Proxy(
        ip=ip,
        port=port,
        protocol=protocol,
        is_alive=True,
        country_code=country_code,
        anonymity=anonymity,
        keep_alive=keep_alive,
        software=software,
        quality_score=90,
    )


@pytest.mark.integration
def test_export_structure_end_to_end(tmp_path: Path) -> None:
    exporter = MasterFileBuilder(output_dir=str(tmp_path))

    proxies = [
        _proxy("1.1.1.1", 8080, Protocol.HTTP, "BD", AnonymityLevel.ELITE, True, "squid"),
        _proxy("2.2.2.2", 1080, Protocol.SOCKS5, "BD", AnonymityLevel.ANONYMOUS, False, "mikrotik"),
        _proxy("3.3.3.3", 1080, Protocol.SOCKS4, "US", AnonymityLevel.TRANSPARENT, True, None),
        _proxy("4.4.4.4", 8080, Protocol.HTTP, "UNKNOWN", AnonymityLevel.UNKNOWN, False, None),
    ]

    stats = ValidationStats(
        raw_collected=10,
        after_dedup=8,
        alive=4,
        dead=4,
        sources_total=2,
        sources_ok=2,
        sources_failed=0,
        average_latency_ms=120.0,
    )
    health: list[SourceHealth] = []

    exporter.export(proxies, stats, health)

    # Master
    assert (tmp_path / "proxies.txt").exists()

    # Global segmented
    assert (tmp_path / "by_protocol" / "http.txt").exists()
    assert (tmp_path / "by_protocol" / "socks4.txt").exists()
    assert (tmp_path / "by_protocol" / "socks5.txt").exists()

    assert (tmp_path / "by_anonymity" / "elite.txt").exists()
    assert (tmp_path / "by_anonymity" / "anonymous.txt").exists()
    assert (tmp_path / "by_anonymity" / "transparent.txt").exists()
    assert (tmp_path / "by_anonymity" / "unknown.txt").exists()

    # Country folders
    bd = tmp_path / "by_country" / "BD_proxies"
    us = tmp_path / "by_country" / "US_proxies"
    unk = tmp_path / "by_country" / "UNKNOWN_proxies"

    assert bd.exists()
    assert us.exists()
    assert unk.exists()

    assert (bd / "BD_all.txt").exists()
    assert (bd / "http.txt").exists()
    assert (bd / "socks5.txt").exists()
    assert (bd / "keep_alive.txt").exists()
    assert (bd / "software_squid.txt").exists()
    assert (bd / "software_mikrotik.txt").exists()

    assert (us / "US_all.txt").exists()
    assert (us / "socks4.txt").exists()
    assert (us / "keep_alive.txt").exists()

    assert (unk / "UNKNOWN_all.txt").exists()

    # Metadata
    assert (tmp_path / "metadata" / "manifest.json").exists()
