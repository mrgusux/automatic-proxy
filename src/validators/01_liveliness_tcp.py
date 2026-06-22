"""Dimension 1: TCP liveliness check (zero-dead-proxy gate)."""

from __future__ import annotations

import asyncio

from src.models.proxy import Proxy


async def check_liveliness(proxy: Proxy, timeout: float = 5.0) -> bool:
    try:
        fut = asyncio.open_connection(proxy.ip, proxy.port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
    except (OSError, TimeoutError):
        return False
    else:
        writer.close()
        try:
            await writer.wait_closed()
        except (OSError, TimeoutError):
            pass
        return True
