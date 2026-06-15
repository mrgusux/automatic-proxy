### File: src/exporters/segmented_builder.py

"""Segmented file builder: Dynamic country folders with advanced proxy features."""

from __future__ import annotations

import os
import logging
from src.models.proxy import Proxy
from src.exporters.atomic_writer import atomic_write_text

logger = logging.getLogger(__name__)


class SegmentedBuilder:
    """Generates country-specific folders containing protocol files, software files, and keep-alive files."""

    def __init__(self, output_dir: str = "outputs") -> None:
        self._output_dir = output_dir

    def export(self, proxies: list[Proxy], stats=None, health=None) -> None:
        """Alias for build to ensure cross-compatibility with engine."""
        self.build(proxies)

    def build(self, proxies: list[Proxy]) -> None:
        """Group proxies by country and export them into structured folders and files."""
        country_groups: dict[str, list[Proxy]] = {}
        for proxy in proxies:
            cc = (proxy.country_code or "UNKNOWN").upper().strip()
            if cc:
                country_groups.setdefault(cc, []).append(proxy)

        for country_code, country_proxies in country_groups.items():
            folder_name = f"{country_code}_proxies"
            country_folder = os.path.join(self._output_dir, "by_country", folder_name)
            os.makedirs(country_folder, exist_ok=True)

            # 1. Combined Master File for this country
            main_filename = f"{country_code}_all.txt"
            main_file_path = os.path.join(country_folder, main_filename)
            atomic_write_text(main_file_path, "\n".join([p.line() for p in country_proxies]) + "\n")

            # 2. Protocol Files
            protocol_groups: dict[str, list[Proxy]] = {}
            for proxy in country_proxies:
                proto = proxy.protocol.value.lower() if hasattr(proxy.protocol, 'value') else str(proxy.protocol).lower()
                protocol_groups.setdefault(proto, []).append(proxy)

            for proto_name, proto_proxies in protocol_groups.items():
                proto_file_path = os.path.join(country_folder, f"{proto_name}.txt")
                atomic_write_text(proto_file_path, "\n".join([p.line() for p in proto_proxies]) + "\n")

            # 3. Keep-Alive File (Only exported if keep-alive proxies exist)
            keep_alive_proxies = [p for p in country_proxies if p.keep_alive]
            if keep_alive_proxies:
                ka_file_path = os.path.join(country_folder, "keep_alive.txt")
                atomic_write_text(ka_file_path, "\n".join([p.line() for p in keep_alive_proxies]) + "\n")

            # 4. Software Files (e.g., software_squid.txt, software_mikrotik.txt)
            software_groups: dict[str, list[Proxy]] = {}
            for proxy in country_proxies:
                if proxy.software:
                    software_groups.setdefault(proxy.software.lower(), []).append(proxy)
                    
            for sw_name, sw_proxies in software_groups.items():
                sw_file_path = os.path.join(country_folder, f"software_{sw_name}.txt")
                atomic_write_text(sw_file_path, "\n".join([p.line() for p in sw_proxies]) + "\n")

        # Create a GLOBAL Keep-Alive master list inside the root outputs folder
        global_keep_alive = [p.line() for p in proxies if p.keep_alive]
        if global_keep_alive:
            ka_global_path = os.path.join(self._output_dir, "keep_alive_proxies.txt")
            atomic_write_text(ka_global_path, "\n".join(global_keep_alive) + "\n")

        logger.info("Successfully exported structured country folders for %d countries.", len(country_groups))


def build_segmented_exporter(settings) -> SegmentedBuilder:
    """Factory function to build SegmentedBuilder from settings."""
    return SegmentedBuilder(output_dir=getattr(settings, "output_dir", "outputs"))
