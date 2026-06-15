# Runbook

Operational guide for failures during GitHub Actions runs.

## Pipeline produced zero alive proxies
1. Check the `03 - Health Monitor` workflow and `outputs/metadata/source_health_report.json`.
2. If most sources failed, the runner IP may be rate-limited. Re-run later; the
   `TokenBucket` and User-Agent rotator reduce, but cannot eliminate, this.
3. Verify upstream source URLs in `config/proxy_sources_registry.yaml` are still live.

## GeoIP / ASN data missing
The `.mmdb` databases are not committed (licensed, large). Run
`scripts/update_geoip_db.py` or set the `MAXMIND_LICENSE_KEY` secret. The pipeline
degrades gracefully (country/ASN become null) if they are absent.

## Workflow cannot push outputs
Ensure the `01 - Main Orchestrator` job has `permissions: contents: write`. On GitHub,
repository Settings -> Actions -> Workflow permissions must allow writes.

## High latency / timeouts
Tune `scrape_timeout`, `tcp_timeout`, and `validate_timeout` in `config/settings.yaml`.
Lower `validate_concurrency` if the runner exhausts file descriptors.

## Recovering a corrupted output
Outputs are written atomically, so corruption should be impossible. If an output is
missing, simply re-run `01 - Main Orchestrator` (or `python -m src.main run`).
