"""Structured, colorful JSON-aware logging setup."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

try:
    from rich.logging import RichHandler  # type: ignore[import-untyped]
except ImportError:
    RichHandler = None


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON (for CI log aggregation)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", json_output: bool = False) -> None:
    """Configure the root logger.

    Uses Rich for colorful console output locally, or compact JSON when
    ``json_output`` is set (recommended for GitHub Actions).
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler: logging.Handler
    if json_output or RichHandler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
    else:
        handler = RichHandler(rich_tracebacks=True, show_path=False)
        handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
