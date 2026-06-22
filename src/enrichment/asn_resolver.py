"""Resolve ASN / ISP information from an offline MaxMind ASN database."""

from __future__ import annotations

import logging
from typing import Any

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class AsnResolver:
    """Add autonomous-system number and organisation name to a proxy."""

    def __init__(self, asn_db_path: str) -> None:
        self._reader: Any = None
        try:
            import geoip2.database

            self._reader = geoip2.database.Reader(asn_db_path)
            logger.info("Loaded GeoIP ASN database: %s", asn_db_path)
        except Exception as exc:
            logger.warning("ASN database unavailable (%s); skipping ASN", exc)
            self._reader = None

    def resolve(self, proxy: Proxy) -> tuple[int | None, str | None]:
        if self._reader is None:
            return None, None
        try:
            response = self._reader.asn(proxy.ip)
            return (
                response.autonomous_system_number,
                response.autonomous_system_organization,
            )
        except Exception:
            return None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
