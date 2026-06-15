"""Aggregate statistics produced by a full pipeline run."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ValidationStats(BaseModel):
    """Counters and metrics describing a single run."""

    started_at: str = Field(default_factory=_utc_now)
    finished_at: str | None = None

    sources_total: int = 0
    sources_ok: int = 0
    sources_failed: int = 0

    raw_collected: int = 0
    after_dedup: int = 0
    alive: int = 0
    dead: int = 0

    average_latency_ms: float = 0.0

    by_protocol: dict[str, int] = Field(default_factory=dict)
    by_anonymity: dict[str, int] = Field(default_factory=dict)
    by_country: dict[str, int] = Field(default_factory=dict)

    def mark_finished(self) -> None:
        self.finished_at = _utc_now()
