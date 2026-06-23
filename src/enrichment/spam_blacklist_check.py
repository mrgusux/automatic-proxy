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
    "dnsbl-1.uceprotect.net",
    "dnsbl-2.uceprotect.net",
    "dnsbl-3.uceprotect.net",
    "cbl.abuseat.org",
    "dyna.spamrats.com",
    "noptr.spamrats.com",
    "spam.spamrats.com",
    "all.s5h.net",
    "rbl.interserver.net",
    "dynip.rocksor.com",
    "netscan.rbl.msrbl.net",
    "vedges.ca",
    "bl.mailspike.org",
]


class SpamBlacklistChecker:
    """Check if a proxy IP is listed in DNSBL servers."""

    def __init__(self, enabled: bool = True, timeout: float = 3.0) -> None:
        self._enabled = enabled
        self._timeout = timeout

    async def is_blacklisted(self, proxy: Proxy) -> bool:
        if not self._enabled:
            return False
        return await self._check_dnsbl(proxy.ip)

    async def _check_dnsbl(self, ip: str) -> bool:
        reversed_ip = ".".join(reversed(ip.split(".")))
        tasks = [
            self._query_dnsbl(server, reversed_ip) for server in DNSBL_SERVERS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        listed_count = sum(1 for r in results if r is True)
        if listed_count > 0:
            logger.info("IP %s found in %d DNSBL servers", ip, listed_count)
        return listed_count > 0

    async def _query_dnsbl(self, dnsbl_server: str, reversed_ip: str) -> bool:
        query = f"{reversed_ip}.{dnsbl_server}"
        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.getaddrinfo(query, None, family=socket.AF_INET),
                timeout=self._timeout,
            )
            return True
        except (asyncio.TimeoutError, socket.gaierror, OSError):
            return False

    async def check_batch(
        self, proxies: list[Proxy]
    ) -> dict[str, bool]:
        logger.info("DNSBL check: testing %d proxies", len(proxies))
        tasks = [self.is_blacklisted(p) for p in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            proxies[i].ip: results[i] if isinstance(results[i], bool) else False
            for i in range(len(proxies))
        }

    def get_listed_servers(self) -> list[str]:
        return DNSBL_SERVERS.copy()
