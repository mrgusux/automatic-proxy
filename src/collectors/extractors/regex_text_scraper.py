"""Generic regex extractor for unstructured text/HTML pages."""

from __future__ import annotations

import re

from src.collectors.base_scraper import BaseScraper
from src.models.proxy import Proxy
from src.models.source_metadata import SourceMetadata

# Matches "ip:port" possibly separated by spaces, tabs, or common delimiters.
_PROXY_RE = re.compile(
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\s*[:|\s]\s*(?P<port>\d{2,5})"
)


class RegexTextScraper(BaseScraper):
    """Last-resort scraper: pull every ip/port pair from arbitrary text."""

    def parse(self, content: str, source: SourceMetadata) -> list[Proxy]:
        proxies: list[Proxy] = []
        seen: set[str] = set()
        for match in _PROXY_RE.finditer(content):
            ip = match.group("ip")
            port = match.group("port")
            key = f"{ip}:{port}"
            if key in seen:
                continue
            seen.add(key)
            proxy = self.make_proxy(ip, port, source)
            if proxy is not None:
                proxies.append(proxy)
        return proxies
