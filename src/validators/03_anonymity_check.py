"""Dimension 3: anonymity classification + server/keep-alive detection."""

from __future__ import annotations

import json
import re
from typing import Any

import aiohttp

from src.core.constants import AnonymityLevel, Protocol
from src.models.proxy import Proxy

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None  # type: ignore[assignment,misc]

_PROXY_REVEAL_HEADERS = (
    "VIA",
    "X-FORWARDED-FOR",
    "X-FORWARDED",
    "FORWARDED-FOR",
    "FORWARDED",
    "CLIENT-IP",
    "PROXY-CONNECTION",
)

_SOFTWARE_SIGNATURES = {
    r"squid": "Squid",
    r"mikrotik": "MikroTik",
    r"tinyproxy": "Tinyproxy",
    r"litespeed": "LiteSpeed",
    r"varnish": "Varnish",
    r"haproxy": "HAProxy",
}


def _build_session(
    proxy: Proxy, timeout: float
) -> tuple[aiohttp.ClientSession, str | None]:
    client_timeout = aiohttp.ClientTimeout(total=timeout)
    is_socks = proxy.protocol in (Protocol.SOCKS4, Protocol.SOCKS5)
    if is_socks and ProxyConnector is not None:
        connector: Any = ProxyConnector.from_url(proxy.address)
        return aiohttp.ClientSession(connector=connector, timeout=client_timeout), None
    connector = aiohttp.TCPConnector(ssl=False)
    return aiohttp.ClientSession(connector=connector, timeout=client_timeout), proxy.address


def _detect_software(body: str, headers: dict[str, str]) -> str | None:
    body_lower = body.lower()
    headers_str = str(headers).lower()
    for pattern, software_name in _SOFTWARE_SIGNATURES.items():
        if re.search(pattern, body_lower) or re.search(pattern, headers_str):
            return software_name
    return None


def _detect_keep_alive(headers: dict[str, str]) -> bool:
    connection_header = headers.get("connection", "")
    return "keep-alive" in connection_header


def _detect_anonymity(body: str, real_ip: str | None) -> AnonymityLevel:
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


async def check_anonymity(
    proxy: Proxy,
    real_ip: str | None,
    timeout: float = 10.0,
    judge_url: str | None = None,
    retries: int = 2,
) -> AnonymityLevel:
    url = judge_url or "http://httpbin.org/ip"

    for attempt in range(retries + 1):
        session, request_proxy = _build_session(proxy, timeout)
        try:
            async with session, session.get(url, proxy=request_proxy) as resp:
                body = await resp.text()
                headers = {k.lower(): v.lower() for k, v in resp.headers.items()}

                proxy.keep_alive = _detect_keep_alive(headers)
                proxy.software = _detect_software(body, headers)
                return _detect_anonymity(body, real_ip)
        except Exception:
            if attempt < retries:
                continue
            return AnonymityLevel.UNKNOWN

    return AnonymityLevel.UNKNOWN
