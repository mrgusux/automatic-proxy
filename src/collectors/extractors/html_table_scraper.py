"""Extract proxies from HTML tables with header-aware column detection."""

from __future__ import annotations

import re
from html.parser import HTMLParser

from src.collectors.base_scraper import BaseScraper
from src.core.constants import AnonymityLevel, Protocol
from src.models.proxy import Proxy
from src.models.source_metadata import SourceMetadata

_IP_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
_PORT_RE = re.compile(r"^\d{1,5}$")


class _TableParser(HTMLParser):
    """Collect header labels and the text content of every row's cells."""

    def __init__(self) -> None:
        super().__init__()
        self.headers: list[str] = []
        self.rows: list[list[str]] = []
        self._current: list[str] = []
        self._cell: list[str] = []
        self._in_cell = False
        self._in_header = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._current = []
        elif tag == "th":
            self._in_header = True
            self._in_cell = True
            self._cell = []
        elif tag == "td":
            self._in_cell = True
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self._in_cell = False
            self._in_header = False
            label = "".join(self._cell).strip().lower()
            if label and label not in self.headers:
                self.headers.append(label)
        elif tag == "td":
            self._in_cell = False
            self._current.append("".join(self._cell).strip())
        elif tag == "tr" and self._current:
            self.rows.append(self._current)
            self._current = []

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell.append(data)


class HtmlTableScraper(BaseScraper):
    """Parse proxy tables, mapping extra columns (country, anonymity, protocol)."""

    def parse(self, content: str, source: SourceMetadata) -> list[Proxy]:
        parser = _TableParser()
        parser.feed(content)
        col = self._map_columns(parser.headers)
        proxies: list[Proxy] = []
        for row in parser.rows:
            proxy = self._row_to_proxy(row, col, source)
            if proxy is not None:
                proxies.append(proxy)
        return proxies

    @staticmethod
    def _map_columns(headers: list[str]) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for idx, label in enumerate(headers):
            if "ip" in label and "ip" not in mapping:
                mapping["ip"] = idx
            elif "port" in label and "port" not in mapping:
                mapping["port"] = idx
            elif ("code" in label or "country" in label) and "country" not in mapping:
                mapping["country"] = idx
            elif "anonym" in label and "anonymity" not in mapping:
                mapping["anonymity"] = idx
            elif ("https" in label or "protocol" in label) and "protocol" not in mapping:
                mapping["protocol"] = idx
        return mapping

    def _row_to_proxy(
        self, row: list[str], col: dict[str, int], source: SourceMetadata
    ) -> Proxy | None:
        if "ip" in col and "port" in col:
            ip = self._cell(row, col["ip"])
            port = self._cell(row, col["port"])
        else:
            ip = next((c for c in row if _IP_RE.match(c)), None)
            port = next((c for c in row if _PORT_RE.match(c)), None)
        if not ip or not port or not _IP_RE.match(ip) or not _PORT_RE.match(port):
            return None
        proxy = self.make_proxy(ip, port, source)
        if proxy is None:
            return None
        self._apply_metadata(proxy, row, col)
        return proxy

    @staticmethod
    def _cell(row: list[str], idx: int) -> str | None:
        return row[idx] if 0 <= idx < len(row) else None

    def _apply_metadata(
        self, proxy: Proxy, row: list[str], col: dict[str, int]
    ) -> None:
        if "country" in col:
            value = self._cell(row, col["country"])
            if value and len(value) <= 3:
                proxy.country_code = value.upper()
        if "anonymity" in col:
            value = (self._cell(row, col["anonymity"]) or "").lower()
            if "elite" in value:
                proxy.anonymity = AnonymityLevel.ELITE
            elif "anonymous" in value:
                proxy.anonymity = AnonymityLevel.ANONYMOUS
            elif "transparent" in value:
                proxy.anonymity = AnonymityLevel.TRANSPARENT
        if "protocol" in col:
            value = (self._cell(row, col["protocol"]) or "").lower()
            if value in ("yes", "https"):
                proxy.protocol = Protocol.HTTPS
