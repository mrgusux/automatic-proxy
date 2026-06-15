# Architecture

The collector is a linear, fully asynchronous pipeline:

```
Collect -> Deduplicate -> Verify (5D) -> Enrich -> Export
```

## Components

- **`src/main.py`** - argparse CLI entry point. Installs uvloop (where available),
  loads settings + sources, wires components, and runs `PipelineManager`.
- **`src/core/pipeline_manager.py`** - orchestrates the five stages and accumulates
  `ValidationStats`. Components are dependency-injected so each stage is testable.

### Collect
`src/collectors/factory.py` maps each `ScraperType` to an extractor and drives them
concurrently through an `AsyncSemaphorePool`, bounded by a `TokenBucket` rate limiter
(`src/utils/rate_limiter.py`). Extractors live under `src/collectors/extractors/`.

A `CircuitBreaker` (also in `rate_limiter.py`) tracks per-source failures and skips a
source for a cooldown window after it fails repeatedly, saving time and avoiding
hammering a down endpoint.

The `html_table` extractor is header-aware: it reads the table's `<th>` labels to map
country / anonymity / protocol columns, falling back to a positional scan when no
recognisable header row exists.

### Deduplicate
`src/deduplication/early_aggregator.py` combines an exact `set` with a memory-efficient
`BloomFilter` for fast membership tests over very large inputs.

### Verify (5 dimensions)
`src/validators/engine.py` loads the numbered dimension modules via `importlib`:
1. TCP liveliness (`01_liveliness_tcp.py`)
2. Protocol detection (`02_protocol_detector.py`)
3. Anonymity scoring (`03_anonymity_check.py`)
4. Latency (`04_latency_tester.py`)
5. Geolocation (`05_geo_locator.py`)

Anonymity and latency checks are **protocol-aware**: SOCKS4/SOCKS5 proxies are routed
through an `aiohttp_socks.ProxyConnector`, while HTTP(S) proxies use the standard
`proxy=` request argument.

Geolocation results are cached on disk via `src/enrichment/geo_cache.py` (`GeoCache`),
so repeated IPs within and across runs avoid re-querying the MaxMind reader. The cache
is flushed atomically at the end of a run.

### Enrich
`src/enrichment/scoring_engine.py` adds ASN/ISP + blacklist data and computes a
0-100 quality score.

### Export
`src/exporters/` writes the master list, segmented files, and JSON manifests using
`atomic_writer.py` (temp file + atomic rename) so partial runs never corrupt outputs.

## Resilience features

- **Atomic writes** - outputs and the geo cache are written via temp file + `os.replace`.
- **Circuit breaker** - repeatedly failing sources are skipped for a cooldown window.
- **Retry with full jitter** - the HTTP client retries with exponential backoff plus
  randomised jitter to avoid synchronised retry storms.
- **Graceful degradation** - missing GeoIP/ASN databases, Redis, or aiohttp-socks all
  degrade to no-ops rather than crashing the run.
