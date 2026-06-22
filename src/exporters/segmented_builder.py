"""Segmented exporter for country/protocol/anonymity/software based outputs."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import Any

from src.exporters.atomic_writer import atomic_write_text
from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class SegmentedBuilder:
    """Create structured output files grouped by country and categories."""

    def __init__(self, output_dir: str = "outputs", country_mapping_path: str = "config/country_mapping.json") -> None:
        self._output_dir = Path(output_dir)
        self._by_country_dir = self._output_dir / "by_country"
        self._by_protocol_dir = self._output_dir / "by_protocol"
        self._by_anonymity_dir = self._output_dir / "by_anonymity"
        self._country_mapping_path = Path(country_mapping_path)

    def export(self, proxies: list[Proxy], stats: Any = None, health: Any = None) -> None:
        """Compatibility alias."""
        self.build(proxies)

    def build(self, proxies: list[Proxy]) -> None:
        self._prepare_directories()

        country_groups: dict[str, list[Proxy]] = {}
        for p in proxies:
            cc = self._normalize_country_code(p.country_code)
            country_groups.setdefault(cc, []).append(p)

        self._write_global_protocol_files(proxies)
        self._write_global_anonymity_files(proxies)

        keep_alive_lines = [p.line() for p in proxies if p.keep_alive]
        if keep_alive_lines:
            atomic_write_text(self._output_dir / "keep_alive_proxies.txt", "\n".join(keep_alive_lines) + "\n")
        else:
            self._safe_unlink(self._output_dir / "keep_alive_proxies.txt")

        for country_code, items in country_groups.items():
            self._write_country_folder(country_code, items)

        logger.info("Segmented export done. countries=%d proxies=%d", len(country_groups), len(proxies))

    def _prepare_directories(self) -> None:
        if self._by_country_dir.exists():
            shutil.rmtree(self._by_country_dir)
        if self._by_protocol_dir.exists():
            shutil.rmtree(self._by_protocol_dir)
        if self._by_anonymity_dir.exists():
            shutil.rmtree(self._by_anonymity_dir)

        self._by_country_dir.mkdir(parents=True, exist_ok=True)
        self._by_protocol_dir.mkdir(parents=True, exist_ok=True)
        self._by_anonymity_dir.mkdir(parents=True, exist_ok=True)

        for legacy in self._by_country_dir.glob("*.txt"):
            self._safe_unlink(legacy)

    def _write_country_folder(self, country_code: str, proxies: list[Proxy]) -> None:
        folder = self._by_country_dir / f"{country_code}_proxies"
        folder.mkdir(parents=True, exist_ok=True)

        all_path = folder / f"{country_code}_all.txt"
        atomic_write_text(all_path, "\n".join([p.line() for p in proxies]) + "\n")

        protocol_groups: dict[str, list[Proxy]] = {}
        for p in proxies:
            proto = self._normalize_protocol(p)
            protocol_groups.setdefault(proto, []).append(p)

        for proto, items in protocol_groups.items():
            atomic_write_text(folder / f"{proto}.txt", "\n".join([x.line() for x in items]) + "\n")

        keep_alive = [p.line() for p in proxies if p.keep_alive]
        if keep_alive:
            atomic_write_text(folder / "keep_alive.txt", "\n".join(keep_alive) + "\n")
        else:
            self._safe_unlink(folder / "keep_alive.txt")

        software_groups: dict[str, list[Proxy]] = {}
        for p in proxies:
            if p.software:
                key = self._sanitize_filename(p.software.lower())
                if key:
                    software_groups.setdefault(key, []).append(p)

        for software_name, items in software_groups.items():
            atomic_write_text(
                folder / f"software_{software_name}.txt",
                "\n".join([x.line() for x in items]) + "\n",
            )

    def _write_global_protocol_files(self, proxies: list[Proxy]) -> None:
        grouped: dict[str, list[Proxy]] = {}
        for p in proxies:
            proto = self._normalize_protocol(p)
            grouped.setdefault(proto, []).append(p)

        for proto, items in grouped.items():
            atomic_write_text(self._by_protocol_dir / f"{proto}.txt", "\n".join([x.line() for x in items]) + "\n")

    def _write_global_anonymity_files(self, proxies: list[Proxy]) -> None:
        grouped: dict[str, list[Proxy]] = {}
        for p in proxies:
            an = self._normalize_anonymity(p)
            grouped.setdefault(an, []).append(p)

        for an, items in grouped.items():
            atomic_write_text(self._by_anonymity_dir / f"{an}.txt", "\n".join([x.line() for x in items]) + "\n")

    @staticmethod
    def _normalize_country_code(country_code: str | None) -> str:
        if not country_code:
            return "UNKNOWN"
        cc = country_code.strip().upper()
        return cc if cc else "UNKNOWN"

    @staticmethod
    def _normalize_protocol(proxy: Proxy) -> str:
        val = proxy.protocol.value if hasattr(proxy.protocol, "value") else str(proxy.protocol)
        v = val.strip().lower()
        return v if v else "unknown"

    @staticmethod
    def _normalize_anonymity(proxy: Proxy) -> str:
        val = proxy.anonymity.value if hasattr(proxy.anonymity, "value") else str(proxy.anonymity)
        v = val.strip().lower().replace(" ", "_")
        return v if v else "unknown"

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        cleaned = re.sub(r"[^a-z0-9_-]+", "_", name).strip("_")
        return cleaned[:80]

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            logger.warning("Failed to remove file: %s", path)
