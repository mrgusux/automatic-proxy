"""Dimension 5: offline geolocation via MaxMind GeoLite2 .mmdb."""

from __future__ import annotations

import logging
from typing import Optional

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class GeoLocator:
    """Resolve country code/name from an offline MaxMind database.

    Falls back gracefully to ``None`` country data if the .mmdb file or the
    geoip2 package is missing, so the pipeline never crashes on geo lookups.
    """

    def __init__(self, country_db_path: str) -> None:
        self._reader = None
        try:
            import geoip2.database  # type: ignore

            self._reader = geoip2.database.Reader(country_db_path)
            logger.info("Loaded GeoIP country database: %s", country_db_path)
        except Exception as exc:  # noqa: BLE001 - DB optional/large
            logger.warning("GeoIP database unavailable (%s); skipping geo", exc)
            self._reader = None

    def locate(self, proxy: Proxy) -> tuple[Optional[str], Optional[str]]:
        if self._reader is None:
            return None, None
        try:
            response = self._reader.country(proxy.ip)
            return response.country.iso_code, response.country.name
        except Exception:  # noqa: BLE001 - address not in DB
            return None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
