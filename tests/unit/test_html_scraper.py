"""Unit tests for the header-aware HTML table scraper."""

from __future__ import annotations

from src.collectors.extractors.html_table_scraper import HtmlTableScraper
from src.core.constants import AnonymityLevel
from src.models.source_metadata import ScraperType, SourceMetadata


def _source() -> SourceMetadata:
    return SourceMetadata(
        name="test",
        url="http://example.com",
        scraper_type=ScraperType.HTML_TABLE,
        default_protocol="http",
    )


def test_header_aware_extraction_maps_metadata() -> None:
    content = (
        "<table>"
        "<tr><th>IP Address</th><th>Port</th><th>Code</th><th>Anonymity</th></tr>"
        "<tr><td>123.45.67.89</td><td>8080</td><td>US</td><td>elite proxy</td></tr>"
        "</table>"
    )
    proxies = HtmlTableScraper().parse(content, _source())
    assert len(proxies) == 1
    proxy = proxies[0]
    assert proxy.key == "123.45.67.89:8080"
    assert proxy.country_code == "US"
    assert proxy.anonymity == AnonymityLevel.ELITE


def test_positional_fallback_without_headers() -> None:
    content = (
        "<table>"
        "<tr><td>98.76.54.32</td><td>3128</td></tr>"
        "</table>"
    )
    proxies = HtmlTableScraper().parse(content, _source())
    assert len(proxies) == 1
    assert proxies[0].key == "98.76.54.32:3128"
