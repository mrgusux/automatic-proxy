"""Extract proxies from JSON API responses with configurable field mapping."""

from __future__ import annotations

import json
from typing import Any

from src.collectors.base_scraper import BaseScraper
from src.models.proxy import Proxy
from src.models.source_metadata import SourceMetadata


class JsonApiScraper(BaseScraper):
    """Parse a JSON payload into proxies.

    The source config may specify ``json_ip_field`` and ``json_port_field``.
    The scraper also handles common shapes: a top-level list, or a dict with a
    ``data``/``proxies`` list, and ``ip:port`` combined string fields.
    """

    def parse(self, content: str, source: SourceMetadata) -> list[Proxy]:
        try:
            payload: Any = json.loads(content)
        except json.JSONDecodeError:
            return []

        records = self._extract_records(payload)
        ip_field = source.json_ip_field or "ip"
        port_field = source.json_port_field or "port"

        proxies: list[Proxy] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            ip = record.get(ip_field)
            port = record.get(port_field)
            # Handle combined "ip:port" in a single field.
            if port is None and isinstance(ip, str) and ":" in ip:
                ip, _, port = ip.partition(":")
            if ip is None or port is None:
                continue
            proxy = self.make_proxy(str(ip), port, source)
            if proxy is not None:
                proxies.append(proxy)
        return proxies

    @staticmethod
    def _extract_records(payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "proxies", "result", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            return [payload]
        return []
