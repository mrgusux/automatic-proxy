"""Resolve ASN / ISP information from an offline MaxMind ASN database."""

from __future__ import annotations

import logging
from typing import Optional

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class AsnResolver:
    """Add autonomous-system number and organisation name to a proxy."""

    def __init__(self, asn_db_path: str) -> None:
        self._reader = None
        try:
            import geoip2.database  # type: ignore

            self._reader = geoip2.database.Reader(asn_db_path)
            logger.info("Loaded GeoIP ASN database: %s", asn_db_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ASN database unavailable (%s); skipping ASN", exc)
            self._reader = None

    def resolve(self, proxy: Proxy) -> tuple[Optional[int], Optional[str]]:
        if self._reader is None:
            return None, None
        try:
            response = self._reader.asn(proxy.ip)
            return (
                response.autonomous_system_number,
                response.autonomous_system_organization,
            )
        except Exception:  # noqa: BLE001
            return None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
