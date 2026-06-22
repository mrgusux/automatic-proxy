"""Dimension 5: offline geolocation via MaxMind GeoLite2 .mmdb."""

from __future__ import annotations

import logging
from typing import Any

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class GeoLocator:
    """Resolve country code/name from an offline MaxMind database."""

    def __init__(self, country_db_path: str) -> None:
        self._reader: Any = None
        try:
            import geoip2.database

            self._reader = geoip2.database.Reader(country_db_path)
            logger.info("Loaded GeoIP country database: %s", country_db_path)
        except Exception as exc:
            logger.warning("GeoIP database unavailable (%s); skipping geo", exc)
            self._reader = None

    def locate(self, proxy: Proxy) -> tuple[str | None, str | None]:
        if self._reader is None:
            return None, None
        try:
            response = self._reader.country(proxy.ip)
            return response.country.iso_code, response.country.name
        except Exception:
            return None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()
