"""Dimension 4: latency / round-trip-time measurement (protocol-aware)."""

from __future__ import annotations

import time
from typing import Any

import aiohttp

from src.core.constants import LATENCY_CHECK_URL, Protocol
from src.models.proxy import Proxy

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None


def _build_session(proxy: Proxy, timeout: float) -> tuple[aiohttp.ClientSession, str | None]:
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    is_socks = proxy.protocol in (Protocol.SOCKS4, Protocol.SOCKS5)
    if is_socks and ProxyConnector is not None:
        connector: Any = ProxyConnector.from_url(proxy.address)
        return aiohttp.ClientSession(connector=connector, timeout=client_timeout), None
    connector = aiohttp.TCPConnector(ssl=False)
    return aiohttp.ClientSession(connector=connector, timeout=client_timeout), proxy.address


async def measure_latency(proxy: Proxy, timeout: float = 10.0) -> float | None:
    session, request_proxy = _build_session(proxy, timeout)
    start = time.monotonic()
    try:
        async with session, session.get(LATENCY_CHECK_URL, proxy=request_proxy) as resp:
            if resp.status >= 400:
                return None
            await resp.read()
    except Exception:
        return None
    return round((time.monotonic() - start) * 1000, 2)
