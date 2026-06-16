from __future__ import annotations

from pathlib import Path

from src.core.constants import AnonymityLevel, Protocol
from src.exporters.segmented_builder import SegmentedBuilder
from src.models.proxy import Proxy


def _p(
    ip: str,
    port: int,
    protocol: Protocol,
    country_code: str,
    anonymity: AnonymityLevel = AnonymityLevel.UNKNOWN,
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
        quality_score=80,
    )


def test_segmented_builder_country_folder_structure(tmp_path: Path) -> None:
    builder = SegmentedBuilder(output_dir=str(tmp_path))

    proxies = [
        _p("1.1.1.1", 8080, Protocol.HTTP, "BD", AnonymityLevel.ELITE, True, "squid"),
        _p("2.2.2.2", 1080, Protocol.SOCKS5, "BD", AnonymityLevel.ANONYMOUS, False, "mikrotik"),
        _p("3.3.3.3", 1080, Protocol.SOCKS4, "US", AnonymityLevel.TRANSPARENT, True, None),
    ]

    builder.build(proxies)

    bd_dir = tmp_path / "by_country" / "BD_proxies"
    us_dir = tmp_path / "by_country" / "US_proxies"

    assert bd_dir.exists()
    assert us_dir.exists()

    # Country main file
    assert (bd_dir / "BD_all.txt").exists()
    assert (us_dir / "US_all.txt").exists()

    # Protocol files inside country folder
    assert (bd_dir / "http.txt").exists()
    assert (bd_dir / "socks5.txt").exists()
    assert (us_dir / "socks4.txt").exists()

    # Keep alive + software
    assert (bd_dir / "keep_alive.txt").exists()
    assert (bd_dir / "software_squid.txt").exists()
    assert (bd_dir / "software_mikrotik.txt").exists()

    # Global files
    assert (tmp_path / "proxies.txt").exists() is False  # segmented builder does not write master
    assert (tmp_path / "by_protocol" / "http.txt").exists()
    assert (tmp_path / "by_protocol" / "socks4.txt").exists()
    assert (tmp_path / "by_protocol" / "socks5.txt").exists()
    assert (tmp_path / "by_anonymity" / "elite.txt").exists()
    assert (tmp_path / "by_anonymity" / "anonymous.txt").exists()
    assert (tmp_path / "by_anonymity" / "transparent.txt").exists()
    assert (tmp_path / "keep_alive_proxies.txt").exists()
