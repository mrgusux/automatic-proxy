"""Segmented file builder: Dynamic country folders with protocol-specific text files."""

from __future__ import annotations

import os
import logging
from src.models.proxy import Proxy
from src.exporters.atomic_writer import AtomicWriter

logger = logging.getLogger(__name__)


class SegmentedBuilder:
    """Generates country-specific folders containing protocol files and a combined master file."""

    def __init__(self, output_dir: str = "outputs") -> None:
        self._output_dir = output_dir
        self._writer = AtomicWriter()

    def export(self, proxies: list[Proxy]) -> None:
        """Group proxies by country and export them into structured folders and files."""
        # Step 1: Group all proxies by country code
        country_groups: dict[str, list[Proxy]] = {}
        for proxy in proxies:
            cc = (proxy.country_code or "UNKNOWN").upper().strip()
            if cc:
                country_groups.setdefault(cc, []).append(proxy)

        # Step 2: Dynamically process each country
        for country_code, country_proxies in country_groups.items():
            # Create country folder name (e.g., outputs/by_country/BD_proxies)
            folder_name = f"{country_code}_proxies"
            country_folder = os.path.join(self._output_dir, "by_country", folder_name)
            os.makedirs(country_folder, exist_ok=True)

            # 1. Generate the Main combined file for this country (e.g., BD_all.txt)
            main_filename = f"{country_code}_all.txt"
            main_file_path = os.path.join(country_folder, main_filename)
            main_lines = [f"{p.ip}:{p.port}" for p in country_proxies]
            self._writer.write_lines(main_file_path, main_lines)

            # 2. Group this country's proxies by protocol
            protocol_groups: dict[str, list[Proxy]] = {}
            for proxy in country_proxies:
                proto = proxy.protocol.value.lower() if hasattr(proxy.protocol, 'value') else str(proxy.protocol).lower()
                protocol_groups.setdefault(proto, []).append(proxy)

            # 3. Write protocol-specific files inside the country folder (e.g., http.txt, socks5.txt)
            for proto_name, proto_proxies in protocol_groups.items():
                proto_filename = f"{proto_name}.txt"
                proto_file_path = os.path.join(country_folder, proto_filename)
                proto_lines = [f"{p.ip}:{p.port}" for p in proto_proxies]
                self._writer.write_lines(proto_file_path, proto_lines)

        logger.info("Successfully exported structured country folders for %d countries.", len(country_groups))


def build_segmented_exporter(settings) -> SegmentedBuilder:
    """Factory function to build SegmentedBuilder from settings."""
    return SegmentedBuilder(output_dir=getattr(settings, "output_dir", "outputs"))
