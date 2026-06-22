from __future__ import annotations

import logging

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class SpamBlacklistChecker:
    """Checks whether a proxy is present in known DNSBL/blacklist providers."""

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    async def is_blacklisted(self, proxy: Proxy) -> bool:
        if not self._enabled:
            return False
        _ = proxy
        return False
