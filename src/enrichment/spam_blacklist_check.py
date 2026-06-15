"""Check proxy IPs against DNS-based blacklists (DNSBL / Spamhaus style)."""

from __future__ import annotations

import asyncio
import logging

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)

# Public DNSBL zones. A listing means the IP is flagged as spammy/abusive.
_DNSBL_ZONES = (
    "zen.spamhaus.org",
    "bl.spamcop.net",
    "dnsbl.sorbs.net",
)


class SpamBlacklistChecker:
    """Reverse-IP DNSBL lookups using aiodns when available."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled
        self._resolver = None
        if enabled:
            try:
                import aiodns  # type: ignore

                self._resolver = aiodns.DNSResolver(timeout=3.0)
            except Exception as exc:  # noqa: BLE001
                logger.info("aiodns unavailable (%s); blacklist check disabled", exc)
                self._enabled = False

    @staticmethod
    def _reverse(ip: str) -> str:
        return ".".join(reversed(ip.split(".")))

    async def is_blacklisted(self, proxy: Proxy) -> bool:
        if not self._enabled or self._resolver is None:
            return False
        if ":" in proxy.ip:  # IPv6 not supported by these zones here.
            return False
        reversed_ip = self._reverse(proxy.ip)
        for zone in _DNSBL_ZONES:
            query = f"{reversed_ip}.{zone}"
            try:
                result = await self._resolver.query(query, "A")
                if result:
                    return True
            except Exception:  # noqa: BLE001 - NXDOMAIN means not listed
                continue
        return False
