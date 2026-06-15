"""Unit tests for the scraping extractors."""

from __future__ import annotations

from src.collectors.extractors.github_raw_scraper import GithubRawScraper
from src.collectors.extractors.html_table_scraper import HtmlTableScraper
from src.collectors.extractors.json_api_scraper import JsonApiScraper
from src.collectors.extractors.regex_text_scraper import RegexTextScraper
from src.core.constants import Protocol
from src.models.source_metadata import ScraperType, SourceMetadata


def _source(scraper_type: ScraperType, protocol: str = "http") -> SourceMetadata:
    return SourceMetadata(
        name="test",
        url="http://example.com",
        scraper_type=scraper_type,
        default_protocol=protocol,
    )


def test_github_raw_scraper_parses_lines() -> None:
    content = "1.2.3.4:8080\n5.6.7.8:3128\ninvalid-line\n9.9.9.9:99999\n"
    proxies = GithubRawScraper().parse(content, _source(ScraperType.GITHUB_RAW))
    keys = {p.key for p in proxies}
    assert "1.2.3.4:8080" in keys
    assert "5.6.7.8:3128" in keys
    # Port out of range is rejected.
    assert "9.9.9.9:99999" not in keys


def test_github_raw_scraper_respects_scheme_prefix() -> None:
    content = "socks5://1.2.3.4:1080\n"
    proxies = GithubRawScraper().parse(content, _source(ScraperType.GITHUB_RAW))
    assert proxies[0].protocol == Protocol.SOCKS5


def test_regex_text_scraper_handles_mixed_delimiters() -> None:
    content = "Proxy 10.0.0.1:80 found; also 10.0.0.2 8080 here."
    proxies = RegexTextScraper().parse(content, _source(ScraperType.REGEX_TEXT))
    keys = {p.key for p in proxies}
    assert "10.0.0.1:80" in keys
    assert "10.0.0.2:8080" in keys


def test_json_api_scraper_field_mapping() -> None:
    content = '{"data": [{"ip": "8.8.8.8", "port": 8080}, {"ip": "1.1.1.1", "port": 80}]}'
    proxies = JsonApiScraper().parse(content, _source(ScraperType.JSON_API))
    assert {p.key for p in proxies} == {"8.8.8.8:8080", "1.1.1.1:80"}


def test_json_api_scraper_combined_field() -> None:
    content = '[{"ip": "8.8.4.4:3128"}]'
    proxies = JsonApiScraper().parse(content, _source(ScraperType.JSON_API))
    assert proxies[0].key == "8.8.4.4:3128"


def test_html_table_scraper_extracts_rows() -> None:
    content = (
        "<table><tr><td>123.45.67.89</td><td>8080</td><td>HTTP</td></tr>"
        "<tr><td>98.76.54.32</td><td>3128</td></tr></table>"
    )
    proxies = HtmlTableScraper().parse(content, _source(ScraperType.HTML_TABLE))
    assert {p.key for p in proxies} == {"123.45.67.89:8080", "98.76.54.32:3128"}
