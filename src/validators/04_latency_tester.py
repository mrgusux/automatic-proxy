"""Dimension 4: latency / round-trip-time measurement with retry."""

from __future__ import annotations

import time
from typing import Any

import aiohttp

from src.core.constants import LATENCY_CHECK_URL, Protocol
from src.models.proxy import Proxy

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None  # type: ignore[assignment,misc]


def _build_session(proxy: Proxy, timeout: float) -> tuple[aiohttp.ClientSession, str | None]:
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    is_socks = proxy.protocol in (Protocol.SOCKS4, Protocol.SOCKS5)
    if is_socks and ProxyConnector is not None:
        connector: Any = ProxyConnector.from_url(proxy.address)
        return aiohttp.ClientSession(connector=connector, timeout=client_timeout), None
    connector = aiohttp.TCPConnector(ssl=False)
    return aiohttp.ClientSession(connector=connector, timeout=client_timeout), proxy.address


async def measure_latency(
    proxy: Proxy,
    timeout: float = 10.0,
    judge_url: str | None = None,
    retries: int = 2,
) -> float | None:
    url = judge_url or LATENCY_CHECK_URL

    for attempt in range(retries + 1):
        session, request_proxy = _build_session(proxy, timeout)
        start = time.monotonic()
        try:
            async with session, session.get(url, proxy=request_proxy) as resp:
                if resp.status >= 400:
                    if attempt < retries:
                        continue
                    return None
                await resp.read()
                return round((time.monotonic() - start) * 1000, 2)
        except Exception:
            if attempt < retries:
                continue
            return None

    return None
