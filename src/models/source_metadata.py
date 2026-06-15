"""Schema describing a proxy source and its runtime health."""

from __future__ import annotations

from enum import Enum
from typing import Optional

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
    default_protocol: Optional[str] = None
    # Optional JSON field mapping for json_api sources.
    json_ip_field: Optional[str] = None
    json_port_field: Optional[str] = None


class SourceHealth(BaseModel):
    """Runtime health metrics for a source, written to the health report."""

    name: str
    url: str
    success: bool = False
    proxies_found: int = 0
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    health_score: float = Field(default=0.0, ge=0.0, le=100.0)
