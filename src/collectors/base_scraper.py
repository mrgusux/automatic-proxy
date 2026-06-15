"""Abstract base scraper defining the fetch -> parse contract."""

from __future__ import annotations

import abc
import logging
import time

from src.core.constants import MAX_PORT, MIN_PORT, Protocol
from src.models.proxy import Proxy
from src.models.source_metadata import SourceHealth, SourceMetadata
from src.utils.http_client import HttpClient
from src.collectors.rotators.user_agent_rotator import UserAgentRotator

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    """Common scraping workflow: fetch raw content, then parse into proxies."""

    def __init__(self, ua_rotator: UserAgentRotator | None = None) -> None:
        self._ua = ua_rotator or UserAgentRotator()

    @abc.abstractmethod
    def parse(self, content: str, source: SourceMetadata) -> list[Proxy]:
        """Parse raw content into a list of Proxy objects."""

    async def scrape(
        self, source: SourceMetadata, client: HttpClient
    ) -> tuple[list[Proxy], SourceHealth]:
        """Fetch and parse a single source, capturing health metrics."""
        health = SourceHealth(name=source.name, url=source.url)
        start = time.monotonic()
        try:
            content = await client.get_text(source.url, headers=self._ua.headers())
            proxies = self.parse(content, source)
            health.success = True
            health.proxies_found = len(proxies)
        except Exception as exc:  # noqa: BLE001 - record, never crash the run
            logger.warning("Source %s failed: %s", source.name, exc)
            health.success = False
            health.error = str(exc)
            proxies = []
        finally:
            health.elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        return proxies, health

    @staticmethod
    def make_proxy(
        ip: str, port: int | str, source: SourceMetadata
    ) -> Proxy | None:
        """Safely construct a Proxy, returning None on invalid data."""
        try:
            port_int = int(str(port).strip())
        except (TypeError, ValueError):
            return None
        if not (MIN_PORT <= port_int <= MAX_PORT):
            return None
        protocol = Protocol.HTTP
        if source.default_protocol:
            try:
                protocol = Protocol(source.default_protocol.lower())
            except ValueError:
                protocol = Protocol.HTTP
        try:
            return Proxy(
                ip=ip.strip(),
                port=port_int,
                protocol=protocol,
                source=source.name,
            )
        except Exception:  # noqa: BLE001 - invalid IP etc.
            return None
