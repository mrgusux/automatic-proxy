"""Load and validate YAML/JSON configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from src.core.exceptions import ConfigError
from src.models.source_metadata import SourceMetadata


class Settings(BaseModel):
    output_dir: str = "outputs"
    scrape_concurrency: int = 50
    validate_concurrency: int = 500
    tcp_timeout: float = 5.0
    validate_timeout: float = 10.0
    max_retries: int = 3
    rate_limit_per_sec: float = 20.0
    rate_limit_burst: int = 40
    max_latency_ms: int = 8000
    max_alive_output: int = 50000


def _read_yaml(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")

    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"Failed to parse YAML: {file_path}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Top-level YAML must be a mapping: {file_path}")
    return data


def load_settings(path: str | Path) -> Settings:
    raw = _read_yaml(path)
    try:
        return Settings(**raw)
    except Exception as exc:  # noqa: BLE001
        raise ConfigError(f"Invalid settings in {path}") from exc


def load_sources(path: str | Path) -> list[SourceMetadata]:
    raw = _read_yaml(path)

    sources_data = raw.get("sources", raw if isinstance(raw, list) else None)
    if not isinstance(sources_data, list):
        raise ConfigError("Sources config must be a list or contain a 'sources' list")

    items: list[SourceMetadata] = []
    for entry in sources_data:
        if not isinstance(entry, dict):
            continue
        try:
            items.append(SourceMetadata(**entry))
        except Exception as exc:  # noqa: BLE001
            raise ConfigError("Invalid source entry in sources config") from exc
    return items
