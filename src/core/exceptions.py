"""Custom exception hierarchy for the proxy collector."""

from __future__ import annotations


class ProxyCollectorError(Exception):
    """Base class for all application-specific errors."""


class ConfigError(ProxyCollectorError):
    """Raised when configuration files are missing or invalid."""


class SourceError(ProxyCollectorError):
    """Raised when a proxy source cannot be fetched or parsed."""

    def __init__(self, source_name: str, message: str) -> None:
        self.source_name = source_name
        super().__init__(f"[{source_name}] {message}")


class ScraperError(SourceError):
    """Raised when a scraper fails to extract proxies."""


class ProxyValidationError(ProxyCollectorError):
    """Raised when a proxy fails a validation stage unexpectedly."""


class ExportError(ProxyCollectorError):
    """Raised when writing output artifacts fails."""


class RateLimitExceeded(ProxyCollectorError):
    """Raised when the token bucket cannot grant a token in time."""
