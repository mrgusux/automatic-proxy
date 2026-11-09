"""Real DNSBL blacklist checker for proxy IPs."""

from __future__ import annotations

import asyncio
import logging
import socket

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)

DNSBL_SERVERS: list[str] = [
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "b.barracudacentral.org",
]


class SpamBlacklistChecker:
    """Check if a proxy IP is listed in DNSBL servers."""

    def __init__(self, enabled: bool = True, timeout: float = 1.0) -> None:
        self._enabled = enabled
        self._timeout = timeout
        self._cache: dict[str, bool] = {}

    async def is_blacklisted(self, proxy: Proxy) -> bool:
        if not self._enabled:
            return False
        if proxy.ip in self._cache:
            return self._cache[proxy.ip]
        result = await self._check_dnsbl(proxy.ip)
        self._cache[proxy.ip] = result
        return result

    async def _check_dnsbl(self, ip: str) -> bool:
        parts = ip.strip().split(".")
        if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
            return False
        reversed_ip = ".".join(reversed(parts))
        tasks = [
            asyncio.create_task(self._query_dnsbl(server, reversed_ip))
            for server in DNSBL_SERVERS
        ]
        try:
            for fut in asyncio.as_completed(tasks):
                try:
                    res = await fut
                    if res is True:
                        # Cancel remaining tasks early
                        for t in tasks:
                            if not t.done():
                                t.cancel()
                        logger.info("IP %s found in DNSBL", ip)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    async def _query_dnsbl(self, dnsbl_server: str, reversed_ip: str) -> bool:
        query = f"{reversed_ip}.{dnsbl_server}"
        try:
            addr_info = await asyncio.wait_for(
                asyncio.get_running_loop().getaddrinfo(query, None, family=socket.AF_INET),
                timeout=self._timeout,
            )
            if not addr_info:
                return False
            # Filter out open resolver rejection / query error responses (e.g. 127.255.255.X from Spamhaus)
            # A valid DNSBL listing response must be in 127.0.0.0/8 and not in 127.255.255.0/24
            valid_listed = [
                entry[4][0]
                for entry in addr_info
                if entry[4]
                and isinstance(entry[4][0], str)
                and entry[4][0].startswith("127.")
                and not entry[4][0].startswith("127.255.255.")
            ]
            return len(valid_listed) > 0
        except (asyncio.TimeoutError, socket.gaierror, OSError):
            return False

    async def check_batch(
        self, proxies: list[Proxy]
    ) -> dict[str, bool]:
        logger.info("DNSBL check: testing %d proxies", len(proxies))
        tasks = [self.is_blacklisted(p) for p in proxies]
        results: list[bool | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)
        output: dict[str, bool] = {}
        for i, proxy in enumerate(proxies):
            r = results[i]
            output[proxy.ip] = r is True
        return output

    def get_listed_servers(self) -> list[str]:
        return DNSBL_SERVERS.copy()
