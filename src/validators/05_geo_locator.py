"""Dimension 5: offline geolocation via MaxMind GeoLite2 with API fallback."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from src.models.proxy import Proxy

logger = logging.getLogger(__name__)


class GeoLocator:
    """Resolve country code/name and city from an offline MaxMind database.

    Tries GeoLite2-City.mmdb first (includes city), falls back to
    GeoLite2-Country.mmdb, then to ip-api.com API.
    """

    def __init__(self, country_db_path: str, city_db_path: str | None = None) -> None:
        self._reader: Any = None
        self._has_city = False
        try:
            import geoip2.database

            if city_db_path:
                try:
                    self._reader = geoip2.database.Reader(city_db_path)
                    self._has_city = True
                    logger.info("Loaded GeoIP City database: %s", city_db_path)
                except Exception:
                    self._reader = None

            if self._reader is None:
                try:
                    self._reader = geoip2.database.Reader(country_db_path)
                    self._has_city = False
                    logger.info("Loaded GeoIP Country database: %s", country_db_path)
                except Exception:
                    self._reader = None

            if self._reader is None:
                logger.warning("No GeoIP database available; using API fallback")

        except ImportError:
            logger.warning("geoip2 not installed; using API fallback")

    def locate(self, proxy: Proxy) -> tuple[str | None, str | None, str | None]:
        if self._reader is not None:
            try:
                response = self._reader.country(proxy.ip)
                code = response.country.iso_code
                name = response.country.name
                city = None
                if self._has_city:
                    try:
                        city = response.city.names.get("en")
                    except Exception:
                        pass
                return code, name, city
            except Exception:
                pass
        return None, None, None

    def close(self) -> None:
        if self._reader is not None:
            self._reader.close()


class ApiGeoLocator:
    """Batch geolocation using ip-api.com (free, 45 req/min limit)."""

    _BATCH_URL = "http://ip-api.com/batch?fields=status,countryCode,country,city,query"

    def __init__(self) -> None:
        self._cache: dict[str, tuple[str | None, str | None, str | None]] = {}

    async def locate_batch(
        self, proxies: list[Proxy]
    ) -> dict[str, tuple[str | None, str | None, str | None]]:
        to_query: list[Proxy] = []
        for p in proxies:
            if p.ip not in self._cache:
                to_query.append(p)

        if not to_query:
            return {p.ip: self._cache.get(p.ip, (None, None, None)) for p in proxies}

        logger.info("API geolocation: querying %d IPs", len(to_query))
        batch_size = 30
        for i in range(0, len(to_query), batch_size):
            batch = to_query[i : i + batch_size]
            payload = [{"query": p.ip} for p in batch]
            try:
                async with (
                    aiohttp.ClientSession() as session,
                    session.post(
                        self._BATCH_URL,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=20),
                    ) as resp,
                ):
                    if resp.status == 200:
                        results = await resp.json()
                        if isinstance(results, list):
                            for item in results:
                                if isinstance(item, dict) and item.get("status") == "success":
                                    ip_addr = item.get("query", "")
                                    code = item.get("countryCode")
                                    name = item.get("country")
                                    city = item.get("city")
                                    if ip_addr:
                                        self._cache[ip_addr] = (code, name, city)
                            queried_ips = {item.get("query") for item in results if isinstance(item, dict)}
                            for p in batch:
                                if p.ip not in queried_ips:
                                    self._cache[p.ip] = (None, None, None)
                        else:
                            for p in batch:
                                self._cache[p.ip] = (None, None, None)
                    else:
                        for p in batch:
                            self._cache[p.ip] = (None, None, None)
            except Exception as exc:
                logger.warning("API geolocation batch failed: %s", exc)
                for p in batch:
                    if p.ip not in self._cache:
                        self._cache[p.ip] = (None, None, None)
            if i + batch_size < len(to_query):
                await asyncio.sleep(2)

        return {p.ip: self._cache.get(p.ip, (None, None, None)) for p in proxies}
