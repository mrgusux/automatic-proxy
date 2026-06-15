"""Dimension 4: latency / round-trip-time measurement (protocol-aware)."""

from __future__ import annotations

import time

import aiohttp

from src.core.constants import LATENCY_CHECK_URL, Protocol
from src.models.proxy import Proxy

try:
    from aiohttp_socks import ProxyConnector  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ProxyConnector = None


def _build_session(proxy: Proxy, timeout: float) -> tuple[aiohttp.ClientSession, str | None]:
    """Create a session correctly wired for the proxy's protocol.

    SOCKS proxies require a dedicated connector (aiohttp cannot tunnel SOCKS via
    the ``proxy=`` argument), so we build a ProxyConnector for them. HTTP(S)
    proxies use the standard ``proxy=`` request argument.
    """
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    is_socks = proxy.protocol in (Protocol.SOCKS4, Protocol.SOCKS5)
    if is_socks and ProxyConnector is not None:
        connector = ProxyConnector.from_url(proxy.address)
        return aiohttp.ClientSession(connector=connector, timeout=client_timeout), None
    connector = aiohttp.TCPConnector(ssl=False)
    # For HTTP(S) the proxy is passed per-request.
    return aiohttp.ClientSession(connector=connector, timeout=client_timeout), proxy.address


async def measure_latency(proxy: Proxy, timeout: float = 10.0) -> float | None:
    """Make a request through the proxy and return RTT in milliseconds.

    Returns None if the request fails, signalling the proxy is not usable for
    real traffic even if its TCP port was open. Handles HTTP, HTTPS, SOCKS4 and
    SOCKS5 proxies correctly.
    """
    session, request_proxy = _build_session(proxy, timeout)
    start = time.monotonic()
    try:
        async with session:
            async with session.get(LATENCY_CHECK_URL, proxy=request_proxy) as resp:
                if resp.status >= 400:
                    return None
                await resp.read()
    except Exception:  # noqa: BLE001
        return None
    return round((time.monotonic() - start) * 1000, 2)
