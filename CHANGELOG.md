# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- SOCKS-aware validation: anonymity and latency checks route SOCKS4/SOCKS5 proxies
  through `aiohttp_socks.ProxyConnector` (added `aiohttp-socks` dependency).
- `CircuitBreaker` that skips repeatedly failing sources for a cooldown window.
- `GeoCache`: disk-backed JSON cache for geolocation lookups, flushed atomically.
- Header-aware HTML table scraper that maps country / anonymity / protocol columns.
- Full-jitter exponential backoff in the HTTP client.
- `06_ci.yml` GitHub Actions workflow running ruff, mypy and pytest.
- Expanded source registry to 60+ verified public proxy sources.
- Unit tests for the circuit breaker, geo cache, and header-aware HTML scraper.

### Changed
- Verification engine now preserves geo metadata supplied by a scraper when the
  GeoIP database has no entry for an IP.

## [1.0.0] - 2026-06-14

### Added
- Initial release of the Ultimate God-Tier Automated Proxy Collector.
- Async collection layer with HTML table, JSON API, GitHub raw, and regex extractors.
- Token-bucket rate limiting and User-Agent rotation.
- Bloom-filter + set early aggregation deduplication.
- 5-dimensional verification engine (TCP liveliness, protocol, anonymity, latency, geo).
- ASN/blacklist enrichment and 0-100 quality scoring.
- Atomic exporters: master list, segmented (country/protocol/anonymity), JSON manifest.
- Five GitHub Actions workflows (orchestrator, security audit, health monitor, release, cache cleanup).
- Docker + docker-compose (with Redis) local stack.
- Unit + integration test suite.
