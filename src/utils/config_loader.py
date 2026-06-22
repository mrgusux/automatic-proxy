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
    scrape_timeout: float = 20.0
    tcp_timeout: float = 5.0
    validate_timeout: float = 10.0
    max_retries: int = 3
    retry_backoff: float = 0.5
    rate_limit_per_sec: float = 20.0
    rate_limit_burst: int = 40
    max_latency_ms: float = 8000.0
    max_alive_output: int = 50000
    geoip_country_db: str = "data/geoip/GeoLite2-Country.mmdb"
    geoip_asn_db: str = "data/geoip/GeoLite2-ASN.mmdb"
    geo_cache_file: str | None = "data/cache/geolocation_cache.json"
    country_mapping_file: str = "config/country_mapping.json"
    validation_rules_file: str = "config/validation_rules.yaml"
    enable_blacklist_check: bool = True
    enable_asn_resolution: bool = True


def _read_yaml(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise ConfigError(f"Config file not found: {file_path}")

    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
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
    except Exception as exc:
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
        except Exception as exc:
            raise ConfigError("Invalid source entry in sources config") from exc
    return items


def _read_yaml_any(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def load_minimum_anonymity(validation_rules_file: str | Path) -> str:
    raw = _read_yaml_any(validation_rules_file)
    try:
        return raw["anonymity"]["minimum_level"]
    except (KeyError, TypeError):
        return "transparent"


def load_scoring_rules(validation_rules_file: str | Path | None = None) -> dict[str, Any]:
    if validation_rules_file is not None:
        raw = _read_yaml_any(validation_rules_file)
    else:
        raw = _read_yaml_any("config/validation_rules.yaml")
    try:
        latency = raw["latency"]
        scoring = raw["scoring"]
    except (KeyError, TypeError):
        return {
            "weight_latency": 40,
            "weight_anonymity": 35,
            "weight_protocol": 15,
            "weight_clean_blacklist": 10,
            "excellent_below": 500,
            "good_below": 1500,
            "acceptable_below": 4000,
        }
    return {
        "weight_latency": scoring.get("weight_latency", 40),
        "weight_anonymity": scoring.get("weight_anonymity", 35),
        "weight_protocol": scoring.get("weight_protocol", 15),
        "weight_clean_blacklist": scoring.get("weight_clean_blacklist", 10),
        "excellent_below": latency.get("excellent_below", 500),
        "good_below": latency.get("good_below", 1500),
        "acceptable_below": latency.get("acceptable_below", 4000),
    }
