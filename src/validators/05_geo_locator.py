"""Dimension 5: offline geolocation via MaxMind GeoLite2 .mmdb with API fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class GeoLocator:
    """Resolve country code/name from an offline MaxMind database.

    Falls back to ip-api.com (free, no key needed) when .mmdb is unavailable.
    """

    _API_URL = "http://ip-api.com/json/{ip}?fields=status,countryCode,country"
    _BATCH_API_URL = "http://ip-api.com/batch"

    def __init__(self, country_db_path: str) -> None:
        self._reader: Any = None
        try:
            import geoip2.database

            self._reader = geoip2.database.Reader(country_db_path)
            logger.info("Loaded GeoIP country database: %s", country_db_path)
        except Exception as exc:
            logger.warning("GeoIP database unavailable (%s); using API fallback", exc)
            self._reader = None

    def locate(self, proxy: Proxy) -> tuple[str | None, str | None]:
        if self._reader is not None:
            try:
                response = self._reader.country(proxy.ip)
                return response.country.iso_code, response.country.name
            except Exception:
                pass
        return None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()


class ApiGeoLocator:
    """Batch geolocation using ip-api.com (free, 45 req/min limit)."""

    _BATCH_URL = "http://ip-api.com/batch?fields=status,countryCode,country"

    def __init__(self) -> None:
        self._cache: dict[str, tuple[str | None, str | None]] = {}

    async def locate_batch(self, proxies: list[Proxy]) -> dict[str, tuple[str | None, str | None]]:
        to_query: list[Proxy] = []
        for p in proxies:
            if p.ip not in self._cache:
                to_query.append(p)

        if not to_query:
            return {p.ip: self._cache.get(p.ip, (None, None)) for p in proxies}

        logger.info("API geolocation: querying %d IPs", len(to_query))
        batch_size = 100
        for i in range(0, len(to_query), batch_size):
            batch = to_query[i : i + batch_size]
            payload = [{"query": p.ip} for p in batch]
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self._BATCH_URL, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            results = await resp.json()
                            for item in results:
                                if item.get("status") == "success":
                                    code = item.get("countryCode")
                                    name = item.get("country")
                                    self._cache[item["query"]] = (code, name)
                                else:
                                    self._cache[item["query"]] = (None, None)
                        else:
                            for p in batch:
                                self._cache[p.ip] = (None, None)
            except Exception as exc:
                logger.warning("API geolocation batch failed: %s", exc)
                for p in batch:
                    if p.ip not in self._cache:
                        self._cache[p.ip] = (None, None)
            if i + batch_size < len(to_query):
                await asyncio.sleep(1)

        return {p.ip: self._cache.get(p.ip, (None, None)) for p in proxies}
