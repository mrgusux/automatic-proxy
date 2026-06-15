"""Application settings model and YAML loaders."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from src.core.exceptions import ConfigError
from src.models.source_metadata import ScraperType, SourceMetadata


class Settings(BaseModel):
    """Core system configuration loaded from config/settings.yaml."""

    # Concurrency.
    scrape_concurrency: int = 50
    validate_concurrency: int = 500

    # Timeouts (seconds).
    scrape_timeout: float = 20.0
    tcp_timeout: float = 5.0
    validate_timeout: float = 10.0

    # Retry.
    max_retries: int = 3
    retry_backoff: float = 0.5

    # Rate limiting (token bucket).
    rate_limit_per_sec: float = 20.0
    rate_limit_burst: int = 40

    # Validation thresholds.
    max_latency_ms: float = 8000.0

    # Output.
    max_alive_output: int = 50_000
    output_dir: str = "outputs"

    # GeoIP / cache paths.
    geoip_country_db: str = "data/geoip/GeoLite2-Country.mmdb"
    geoip_asn_db: str = "data/geoip/GeoLite2-ASN.mmdb"
    geo_cache_file: str = "data/cache/geolocation_cache.json"
    country_mapping_file: str = "config/country_mapping.json"

    # Enrichment toggles.
    enable_blacklist_check: bool = True
    enable_asn_resolution: bool = True

    # Validation rules file (scoring weights, latency buckets).
    validation_rules_file: str = "config/validation_rules.yaml"


def _read_yaml(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    try:
        with file.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"Failed to parse YAML {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a mapping at the top of {path}")
    return data


def load_settings(path: str = "config/settings.yaml") -> Settings:
    """Load and validate the core settings file."""
    return Settings(**_read_yaml(path))


def load_scoring_rules(path: str = "config/validation_rules.yaml") -> dict:
    """Load scoring weights and latency buckets from the rules file.

    Returns a normalised dict with sensible defaults so the scoring engine can
    run even if the rules file is partial or absent.
    """
    try:
        data = _read_yaml(path)
    except ConfigError:
        data = {}
    scoring = data.get("scoring", {}) if isinstance(data, dict) else {}
    latency = data.get("latency", {}) if isinstance(data, dict) else {}
    return {
        "weight_latency": int(scoring.get("weight_latency", 40)),
        "weight_anonymity": int(scoring.get("weight_anonymity", 35)),
        "weight_protocol": int(scoring.get("weight_protocol", 15)),
        "weight_clean_blacklist": int(scoring.get("weight_clean_blacklist", 10)),
        "excellent_below": float(latency.get("excellent_below", 500)),
        "good_below": float(latency.get("good_below", 1500)),
        "acceptable_below": float(latency.get("acceptable_below", 4000)),
    }


def load_minimum_anonymity(path: str = "config/validation_rules.yaml") -> str:
    """Load the minimum acceptable anonymity level from the rules file.

    Returns one of: transparent | anonymous | elite. Defaults to 'transparent'
    (accept everything) when the rules file is missing or partial.
    """
    try:
        data = _read_yaml(path)
    except ConfigError:
        return "transparent"
    anonymity = data.get("anonymity", {}) if isinstance(data, dict) else {}
    level = str(anonymity.get("minimum_level", "transparent")).lower()
    if level not in ("transparent", "anonymous", "elite"):
        return "transparent"
    return level


def load_sources(path: str = "config/proxy_sources_registry.yaml") -> list[SourceMetadata]:
    """Load the source registry, returning only enabled sources."""
    data = _read_yaml(path)
    raw_sources = data.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ConfigError("'sources' must be a list in the registry file")

    sources: list[SourceMetadata] = []
    for entry in raw_sources:
        try:
            source = SourceMetadata(**entry)
        except Exception as exc:  # noqa: BLE001 - surface bad config clearly
            raise ConfigError(f"Invalid source entry {entry!r}: {exc}") from exc
        if source.enabled:
            sources.append(source)

    if not sources:
        raise ConfigError("No enabled sources found in the registry")
    # Validate scraper types are recognised.
    valid = {t.value for t in ScraperType}
    for source in sources:
        if source.scraper_type.value not in valid:
            raise ConfigError(f"Unknown scraper_type for source {source.name}")
    return sources
