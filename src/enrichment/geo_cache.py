"""Persistent JSON cache for geolocation/ASN lookups to save repeated work."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.exporters.atomic_writer import atomic_write_json

logger = logging.getLogger(__name__)


class GeoCache:
    """A simple disk-backed cache keyed by IP."""

    def __init__(self, cache_file: str) -> None:
        self._path = Path(cache_file)
        self._data: dict[str, dict[str, str | None]] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                loaded: dict[str, dict[str, str | None]] = json.loads(
                    self._path.read_text(encoding="utf-8")
                )
                self._data = loaded
                logger.info("Loaded geo cache with %d entries", len(self._data))
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not read geo cache (%s); starting fresh", exc)
                self._data = {}

    def get(self, ip: str) -> dict[str, str | None] | None:
        return self._data.get(ip)

    def set(self, ip: str, value: dict[str, str | None]) -> None:
        self._data[ip] = value
        self._dirty = True

    def flush(self) -> None:
        """Persist the cache to disk atomically if it changed."""
        if not self._dirty:
            return
        try:
            atomic_write_json(self._path, self._data)
            self._dirty = False
            logger.info("Flushed geo cache (%d entries)", len(self._data))
        except OSError as exc:
            logger.warning("Could not flush geo cache: %s", exc)
