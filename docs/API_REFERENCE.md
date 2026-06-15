# API Reference

Key public classes and functions.

## `src.models.proxy.Proxy`
Pydantic model. Fields: `ip`, `port`, `protocol`, `is_alive`, `latency_ms`,
`anonymity`, `country_code`, `country_name`, `asn`, `isp`, `is_blacklisted`,
`quality_score`, `source`.
- `key` -> `"ip:port"` (dedup identity)
- `address` -> `"protocol://ip:port"`
- `line()` -> `"ip:port"`

## `src.core.pipeline_manager.PipelineManager`
`PipelineManager(sources, collector, deduplicator, verifier, enricher, exporter, max_alive_output)`
- `await run() -> PipelineResult`

## `src.utils.rate_limiter.TokenBucket`
`TokenBucket(rate, capacity)` -> `await acquire(tokens=1.0)`

## `src.utils.rate_limiter.CircuitBreaker`
`CircuitBreaker(failure_threshold=3, cooldown=1800.0)`
- `is_open(key) -> bool` - True while the key is in cooldown (should be skipped)
- `record_success(key)` - reset the failure counter
- `record_failure(key)` - increment failures; opens the circuit at the threshold

## `src.utils.async_semaphore_pool.AsyncSemaphorePool`
`AsyncSemaphorePool(concurrency)` -> `await map(worker, items) -> list`

## `src.deduplication.bloom_filter.BloomFilter`
`BloomFilter(expected_items, false_positive)` -> `add(item) -> bool`, `item in bloom`

## `src.enrichment.geo_cache.GeoCache`
Disk-backed JSON cache for geolocation lookups.
`GeoCache(cache_file)`
- `get(ip) -> dict | None`
- `set(ip, value)` - record a `{"code": ..., "name": ...}` entry
- `flush()` - atomically persist the cache if it changed

## Validation dimensions (`src/validators/`)
- `check_liveliness(proxy, timeout) -> bool`
- `detect_protocol(proxy, timeout) -> Protocol`
- `check_anonymity(proxy, real_ip, timeout) -> AnonymityLevel` (SOCKS-aware)
- `measure_latency(proxy, timeout) -> float | None` (SOCKS-aware)
- `GeoLocator(country_db_path).locate(proxy) -> (code, name)`

## `src.validators.engine.VerificationEngine`
`VerificationEngine(concurrency, tcp_timeout, validate_timeout, max_latency_ms, geoip_country_db, geo_cache_file=None, real_ip=None)`
- `await verify_all(proxies) -> list[Proxy]`

## Exporters
- `MasterFileBuilder(output_dir).export(proxies, stats, source_health)`
- `atomic_write_text(path, content)` / `atomic_write_json(path, data)`
