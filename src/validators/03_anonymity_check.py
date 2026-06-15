"""Dimension 3: anonymity classification (elite/anonymous/transparent)."""

from __future__ import annotations

import json

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
    """Classify anonymity by inspecting what the echo endpoint reports.

    - Transparent: our real IP is exposed.
    - Anonymous: real IP hidden but proxy-identifying headers present.
    - Elite: no leakage at all.
    """
    url = IP_CHECK_URLS[0]
    session, request_proxy = _build_session(proxy, timeout)
    try:
        async with session:
            async with session.get(url, proxy=request_proxy) as resp:
                body = await resp.text()
    except Exception:  # noqa: BLE001
        return AnonymityLevel.UNKNOWN

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
