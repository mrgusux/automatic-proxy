"""Schema describing a proxy source and its runtime health."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ScraperType(str, Enum):
    """Which extractor should handle a source."""

    HTML_TABLE = "html_table"
    JSON_API = "json_api"
    GITHUB_RAW = "github_raw"
    REGEX_TEXT = "regex_text"


class SourceMetadata(BaseModel):
    """Static configuration for a single proxy source."""

    name: str
    url: str
    scraper_type: ScraperType
    enabled: bool = True
    default_protocol: str | None = None
    json_ip_field: str | None = None
    json_port_field: str | None = None


class SourceHealth(BaseModel):
    """Runtime health metrics for a source, written to the health report."""

    name: str
    url: str
    success: bool = False
    proxies_found: int = 0
    elapsed_ms: float = 0.0
    error: str | None = None
    health_score: float = Field(default=0.0, ge=0.0, le=100.0)
