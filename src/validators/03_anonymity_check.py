### File: src/validators/03_anonymity_check.py

"""Dimension 3: anonymity classification (elite/anonymous/transparent) + Advanced Fingerprinting."""

from __future__ import annotations

import json
import re

import aiohttp

from src.core.constants import IP_CHECK_URLS, AnonymityLevel, Protocol
from src.models.proxy import Proxy

try:
    from aiohttp_socks import ProxyConnector  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ProxyConnector = None

# Headers that leak the originating client IP when present.
_PROXY_REVEAL_HEADERS = (
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "FORWARDED-FOR",
    "FORWARDED",
    "CLIENT-IP",
    "PROXY-CONNECTION",
)

# Software signatures to detect from response body/headers
_SOFTWARE_SIGNATURES = {
    r"squid": "Squid",
    r"mikrotik": "MikroTik",
    r"tinyproxy": "Tinyproxy",
    r"litespeed": "LiteSpeed",
    r"varnish": "Varnish",
    r"haproxy": "HAProxy"
}


def _build_session(
    proxy: Proxy, timeout: float
) -> tuple[aiohttp.ClientSession, str | None]:
    """Build a session wired for the proxy's protocol (SOCKS-aware)."""
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    is_socks = proxy.protocol in (Protocol.SOCKS4, Protocol.SOCKS5)
    if is_socks and ProxyConnector is not None:
        connector = ProxyConnector.from_url(proxy.address)
        return aiohttp.ClientSession(connector=connector, timeout=client_timeout), None
    connector = aiohttp.TCPConnector(ssl=False)
    return aiohttp.ClientSession(connector=connector, timeout=client_timeout), proxy.address


async def check_anonymity(
    proxy: Proxy, real_ip: str | None, timeout: float = 10.0
) -> AnonymityLevel:
    """Classify anonymity and detect proxy software / keep-alive support."""
    url = IP_CHECK_URLS[0]
    session, request_proxy = _build_session(proxy, timeout)
    try:
        async with session:
            async with session.get(url, proxy=request_proxy) as resp:
                body = await resp.text()
                headers = {k.lower(): v.lower() for k, v in resp.headers.items()}
    except Exception:  # noqa: BLE001
        return AnonymityLevel.UNKNOWN

    # --- Feature 1: Keep-Alive Detection ---
    connection_header = headers.get("connection", "")
    if "keep-alive" in headers or "keep-alive" in connection_header:
        proxy.keep_alive = True

    # --- Feature 2: Proxy Software Detection ---
    body_lower = body.lower()
    for pattern, software_name in _SOFTWARE_SIGNATURES.items():
        if re.search(pattern, body_lower) or re.search(pattern, str(headers)):
            proxy.software = software_name
            break

    # --- Original Anonymity Detection ---
    body_upper = body.upper()
    if real_ip and real_ip in body:
        return AnonymityLevel.TRANSPARENT
    try:
        data = json.loads(body)
        seen = json.dumps(data).upper()
    except json.JSONDecodeError:
        seen = body_upper
    if any(h in seen for h in _PROXY_REVEAL_HEADERS):
        return AnonymityLevel.ANONYMOUS
    return AnonymityLevel.ELITE
