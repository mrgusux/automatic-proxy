from __future__ import annotations

import logging

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class SpamBlacklistChecker:
    """Checks whether a proxy is present in known DNSBL/blacklist providers."""

    def __init__(self) -> None:
        self._enabled = True

    async def is_blacklisted(self, proxy: Proxy) -> bool:
        """Return blacklist status for a proxy.

        Current implementation is a safe placeholder (non-blocking) and can be
        extended with real DNSBL providers later.
        """
        if not self._enabled:
            return False
        _ = proxy
        return False
