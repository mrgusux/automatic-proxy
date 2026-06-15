"""Hardcoded constants: HTTP headers, default ports, and protocol enums."""

from __future__ import annotations

from enum import Enum

# Endpoints used to detect a proxy's outbound (public) IP and check anonymity.
IP_CHECK_URLS: tuple[str, ...] = (
    "http://httpbin.org/ip",
    "http://api.ipify.org?format=json",
)

# Endpoint used to measure latency and confirm a working HTTP path.
LATENCY_CHECK_URL: str = "http://httpbin.org/get"

# Default request headers for scraping. User-Agent is overridden by the rotator.
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

# Common proxy ports used as a fallback heuristic when a source omits the port.
COMMON_PROXY_PORTS: tuple[int, ...] = (80, 8080, 3128, 8000, 8888, 1080, 9050)

# Network bounds.
MIN_PORT: int = 1
MAX_PORT: int = 65535

# IPv4 regex (octet ranges validated by the Proxy model).
IPV4_REGEX: str = r"(?:\d{1,3}\.){3}\d{1,3}"
PROXY_LINE_REGEX: str = rf"{IPV4_REGEX}:\d{{1,5}}"


class Protocol(str, Enum):
    """Supported proxy protocols."""

    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class AnonymityLevel(str, Enum):
    """Anonymity classification based on header leakage."""

    TRANSPARENT = "transparent"
    ANONYMOUS = "anonymous"
    ELITE = "elite"
    UNKNOWN = "unknown"
