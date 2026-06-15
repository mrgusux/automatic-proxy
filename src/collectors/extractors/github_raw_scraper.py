"""Extract proxies from raw GitHub text files (ip:port per line)."""

from __future__ import annotations

import re

from src.collectors.base_scraper import BaseScraper
from src.models.proxy import Proxy
from src.models.source_metadata import SourceMetadata

_LINE_RE = re.compile(
    r"(?:(?P<scheme>socks5|socks4|https?)://)?"
    r"(?P<ip>(?:\d{1,3}\.){3}\d{1,3}):(?P<port>\d{1,5})"
)


class GithubRawScraper(BaseScraper):
    """Parse plain-text proxy lists hosted on raw.githubusercontent.com etc."""

    def parse(self, content: str, source: SourceMetadata) -> list[Proxy]:
        proxies: list[Proxy] = []
        seen: set[str] = set()
        for match in _LINE_RE.finditer(content):
            ip = match.group("ip")
            port = match.group("port")
            key = f"{ip}:{port}"
            if key in seen:
                continue
            seen.add(key)
            proxy = self.make_proxy(ip, port, source)
            if proxy is not None:
                # Respect an explicit scheme prefix if present.
                scheme = match.group("scheme")
                if scheme:
                    try:
                        from src.core.constants import Protocol

                        proxy.protocol = Protocol(scheme.lower())
                    except ValueError:
                        pass
                proxies.append(proxy)
        return proxies
