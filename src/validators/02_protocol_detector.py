"""Dimension 2: protocol detection (HTTP/HTTPS/SOCKS4/SOCKS5)."""

from __future__ import annotations

import asyncio
import struct

from src.core.constants import Protocol
from src.models.proxy import Proxy


async def _probe_socks5(ip: str, port: int, timeout: float) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
    except (OSError, TimeoutError):
        return False
    try:
        writer.write(b"\x05\x01\x00")
        await writer.drain()
        resp = await asyncio.wait_for(reader.readexactly(2), timeout=timeout)
        return resp[0] == 0x05
    except (OSError, TimeoutError, asyncio.IncompleteReadError):
        return False
    finally:
        writer.close()


async def _probe_socks4(ip: str, port: int, timeout: float) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
    except (OSError, TimeoutError):
        return False
    try:
        packet = b"\x04\x01" + struct.pack(">H", 80) + bytes([1, 1, 1, 1]) + b"\x00"
        writer.write(packet)
        await writer.drain()
        resp = await asyncio.wait_for(reader.readexactly(8), timeout=timeout)
        return resp[0] == 0x00 and resp[1] in (0x5A, 0x5B, 0x5C, 0x5D)
    except (OSError, TimeoutError, asyncio.IncompleteReadError):
        return False
    finally:
        writer.close()


async def detect_protocol(proxy: Proxy, timeout: float = 5.0) -> Protocol:
    if await _probe_socks5(proxy.ip, proxy.port, timeout):
        return Protocol.SOCKS5
    if await _probe_socks4(proxy.ip, proxy.port, timeout):
        return Protocol.SOCKS4
    return proxy.protocol if proxy.protocol in (Protocol.HTTP, Protocol.HTTPS) else Protocol.HTTP
