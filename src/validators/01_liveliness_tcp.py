"""Dimension 1: TCP liveliness check (zero-dead-proxy gate)."""

from __future__ import annotations

import asyncio

from src.models.proxy import Proxy


async def check_liveliness(proxy: Proxy, timeout: float = 5.0) -> bool:
    """Open a raw TCP connection to the proxy host:port.

    Returns True if the socket handshake succeeds within ``timeout`` seconds.
    This is the cheapest gate and removes the bulk of dead proxies before any
    expensive HTTP validation runs.
    """
    try:
        fut = asyncio.open_connection(proxy.ip, proxy.port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
    except (OSError, asyncio.TimeoutError):
        return False
    else:
        writer.close()
        try:
            await writer.wait_closed()
        except (OSError, asyncio.TimeoutError):
            pass
        return True
