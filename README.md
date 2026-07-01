<div align="center">

# 🛰️ Ultimate God-Tier Automated Proxy Collector

**High-concurrency, fully automated public proxy collector — purpose-built for GitHub Actions.**

Scrapes 100+ publicly shared proxy sources, validates them across **5 dimensions**,
enriches metadata, and exports clean, deduplicated, ready-to-use lists — every 3 hours,
with zero servers to maintain..

<br/>

![CI](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)
![Async](https://img.shields.io/badge/powered%20by-asyncio%20%2B%20aiohttp-1f6feb?style=flat-square)
![Pydantic](https://img.shields.io/badge/validation-pydantic%20v2-e92063?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Maintenance](https://img.shields.io/badge/maintained-yes-success?style=flat-square)

<br/>

<!-- Live stats badges (auto-updated from outputs/metadata/manifest.json on GitHub).
     Replace USER/REPO with your GitHub repository path. -->

![Active Proxies](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=2ea44f&label=Live%20Proxies&query=%24.summary.alive&url=https%3A%2F%2Fraw.githubusercontent.com%2FUSER%2FREPO%2Fmain%2Foutputs%2Fmetadata%2Fmanifest.json)
![Avg Latency](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=blue&label=Avg%20Latency%20(ms)&query=%24.summary.average_latency_ms&url=https%3A%2F%2Fraw.githubusercontent.com%2FUSER%2FREPO%2Fmain%2Foutputs%2Fmetadata%2Fmanifest.json)
![Sources OK](https://img.shields.io/badge/dynamic/json?style=for-the-badge&color=orange&label=Sources%20OK&query=%24.summary.sources_ok&url=https%3A%2F%2Fraw.githubusercontent.com%2FUSER%2FREPO%2Fmain%2Foutputs%2Fmetadata%2Fmanifest.json)

</div>

---

## 📑 Table of Contents

- [Why this project](#-why-this-project)
- [Features](#-features)
- [Architecture](#-architecture)
- [The 5-Dimensional Validation Engine](#-the-5-dimensional-validation-engine)
- [Quick Start](#-quick-start)
- [Outputs](#-outputs)
- [Direct download links](#-direct-download-links)
- [Configuration](#-configuration)
- [GitHub Actions Workflows](#-github-actions-workflows)
- [Project Structure](#-project-structure)
- [Quality Scoring](#-quality-scoring)
- [Local Development](#-local-development)
- [Docker](#-docker)
- [FAQ](#-faq)
- [Responsible Use](#-responsible-use)
- [Contributing](#-contributing)
- [License](#-license)

---

## 💡 Why this project

Most public proxy lists are **noisy, duplicated, and full of dead entries**. This
project solves that by running a rigorous, fully automated pipeline that:

- ✅ Collects from **many sources concurrently** (no slow sequential scraping).
- ✅ Removes duplicates with a **memory-efficient Bloom filter + set**.
- ✅ Verifies every proxy across **5 independent dimensions** — so dead proxies never reach you.
- ✅ Runs **entirely on GitHub Actions** — no VPS, no cost, no maintenance.
- ✅ Writes outputs **atomically**, so a crash mid-run can never corrupt your lists.

---

## ✨ Features

| Category | Highlights |
|----------|-----------|
| **Concurrency** | `asyncio` + `aiohttp` with bounded `Semaphore` pools — check thousands of proxies in parallel |
| **Anti-ban** | Token-bucket rate limiter + rotating real-browser User-Agents |
| **Scrapers** | HTML tables, JSON APIs, GitHub raw text, and a generic regex fallback |
| **Validation** | TCP liveliness, protocol detection (HTTP/HTTPS/SOCKS4/SOCKS5), anonymity scoring, latency, geolocation |
| **Deduplication** | Bloom filter (probabilistic) fronting an exact `set` for correctness |
| **Enrichment** | ASN/ISP resolution, DNSBL/Spamhaus blacklist checks, 0–100 quality score |
| **Data integrity** | Atomic file writes (temp file + `os.replace`) — corruption-proof |
| **Outputs** | Master list + segmented by country / protocol / anonymity + JSON manifest |
| **Type safety** | Strict Pydantic v2 models, full `mypy --strict`, `ruff` linting |
| **Automation** | 5 GitHub Actions: orchestrator, security audit, health monitor, auto-release, cache cleanup |

---

## 🏗️ Architecture

```text
          ┌──────────────────────────────────────────────────────────────┐
          │                      PipelineManager                         │
          └──────────────────────────────────────────────────────────────┘
                                       │
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ COLLECT  │──▶│  DEDUP   │──▶│  VERIFY  │──▶│  ENRICH  │──▶│  EXPORT  │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
        │              │              │              │              │
  async scrapers  Bloom + Set   5-D engine     ASN + DNSBL    atomic writes
  (rate-limited)               (concurrent)     + scoring     master/segmented
```

The pipeline is **linear and fully asynchronous**. Every stage is a dependency-injected
component, which keeps the system testable and each layer independently swappable.
See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a deep dive.

---

## 🔬 The 5-Dimensional Validation Engine

Every candidate proxy must survive **all** of these checks before it is exported:

| # | Dimension | Module | What it does |
|---|-----------|--------|--------------|
| 1 | **Liveliness** | `01_liveliness_tcp.py` | Raw TCP handshake — the cheap gate that drops most dead proxies first |
| 2 | **Protocol** | `02_protocol_detector.py` | Probes SOCKS5/SOCKS4 handshakes, falls back to HTTP(S) |
| 3 | **Anonymity** | `03_anonymity_check.py` | Classifies as Elite / Anonymous / Transparent by header leakage |
| 4 | **Latency** | `04_latency_tester.py` | Measures real round-trip time through the proxy |
| 5 | **Geolocation** | `05_geo_locator.py` | Resolves country via offline MaxMind GeoLite2 `.mmdb` |

> The dimension files are loaded dynamically with `importlib` (their numeric names
> aren't valid Python import identifiers), orchestrated by `src/validators/engine.py`.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline
python -m src.main run

# ...or use the Makefile
make run
```

That's it. Validated proxies land in [`outputs/`](outputs/).

> **On GitHub:** just enable Actions and the `01 - Main Orchestrator` workflow runs
> automatically every 3 hours, committing fresh proxies back to the repo.

---

## 📦 Outputs

```text
outputs/
├── proxies.txt                     # Master list — best proxies, highest score first
├── by_country/
│   ├── BD_proxies.txt
│   ├── US_proxies.txt
│   └── <ISO>_proxies.txt
├── by_protocol/
│   ├── http.txt
│   ├── socks4.txt
│   └── socks5.txt
├── by_anonymity/
│   ├── elite.txt
│   └── anonymous.txt
└── metadata/
    ├── manifest.json               # Totals, distribution, average latency
    └── source_health_report.json   # Which sources performed well
```

### 🔗 Direct download links

Once running on GitHub, you can consume lists directly via raw URLs
(replace `USER/REPO`):

```text
https://raw.githubusercontent.com/USER/REPO/main/outputs/proxies.txt
https://raw.githubusercontent.com/USER/REPO/main/outputs/by_protocol/socks5.txt
https://raw.githubusercontent.com/USER/REPO/main/outputs/by_anonymity/elite.txt
```

---

## ⚙️ Configuration

All behaviour is driven by YAML in [`config/`](config/) — no code changes needed.

**`config/settings.yaml`** (core knobs):

| Key | Default | Description |
|-----|---------|-------------|
| `scrape_concurrency` | `50` | Parallel source fetches |
| `validate_concurrency` | `500` | Parallel proxy validations |
| `tcp_timeout` | `5.0` | TCP handshake timeout (s) |
| `validate_timeout` | `10.0` | HTTP validation timeout (s) |
| `max_retries` | `3` | Retries per request |
| `rate_limit_per_sec` | `20.0` | Token-bucket refill rate |
| `rate_limit_burst` | `40` | Token-bucket capacity |
| `max_latency_ms` | `8000` | Drop proxies slower than this |
| `max_alive_output` | `50000` | Cap on exported proxies |

Other config files:

- **`proxy_sources_registry.yaml`** — the central database of sources.
- **`validation_rules.yaml`** — latency buckets, scoring weights, anonymity threshold.
- **`country_mapping.json`** — ISO 3166 codes, names, and flag emojis.

Add a new source interactively:

```bash
python scripts/add_new_source.py
```

---

## 🤖 GitHub Actions Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `01_main_orchestrator.yml` | every 3 hours | Run pipeline, commit fresh proxy lists |
| `02_security_audit.yml` | push / weekly | Trivy + `pip-audit` secret & dependency scan |
| `03_health_monitor.yml` | every 6 hours | Fail if >50% of sources are down |
| `04_auto_release.yml` | weekly | Tag + GitHub release with proxy snapshot |
| `05_cleanup_cache.yml` | daily | Purge old Actions caches |

> ⚠️ **Setup:** On GitHub go to **Settings → Actions → Workflow permissions** and
> enable **Read and write permissions** so the orchestrator can push outputs.

---

## 🗂️ Project Structure

```text
src/
├── main.py                 # CLI entry point
├── core/                   # pipeline_manager, exceptions, constants
├── models/                 # Pydantic schemas (proxy, source, stats)
├── collectors/             # base_scraper, factory, extractors/, rotators/
├── deduplication/          # bloom_filter, early_aggregator, redis_state_manager
├── validators/             # 01..05 dimensions + engine.py
├── enrichment/             # asn_resolver, spam_blacklist_check, scoring_engine
├── exporters/              # atomic_writer, master/segmented/manifest builders
└── utils/                  # rate_limiter, async_semaphore_pool, http_client, logger
```

Full tree and API docs: [`docs/API_REFERENCE.md`](docs/API_REFERENCE.md).

---

## 🏆 Quality Scoring

Each proxy gets a **0–100** score so the master list is sorted best-first:

| Factor | Max points | Best case |
|--------|-----------|-----------|
| Latency | 40 | `< 500 ms` |
| Anonymity | 35 | Elite |
| Protocol | 15 | SOCKS5 |
| Clean (not blacklisted) | 10 | Not on any DNSBL |

Weights are configurable in `config/validation_rules.yaml`.

---

## 🧪 Local Development

```bash
make install     # install dependencies
make test        # run unit + integration tests (pytest)
make lint        # ruff check + mypy --strict
make format      # auto-format with ruff
make clean       # remove caches
make run         # run the pipeline locally
```

Benchmark dedup throughput on synthetic data:

```bash
python scripts/local_benchmark.py
```

---

## 🐳 Docker

Run the full local stack (collector + Redis for cross-run state):

```bash
docker compose -f docker/docker-compose.yml up --build
```

The image is based on lightweight `python:3.11-alpine`.

---

## ❓ FAQ

**Do I need the MaxMind databases?**
No. Geolocation and ASN data are optional. Without the `.mmdb` files the pipeline
still runs — country/ASN fields are simply left empty. To enable them, set a
`MAXMIND_LICENSE_KEY` secret and run `python scripts/update_geoip_db.py`.

**Why are `outputs/` files empty in the repo?**
They are generated on each run. The first GitHub Actions run will populate them.

**Why do validator files start with numbers (`01_...`)?**
It mirrors the documented architecture order. Since `01_foo` isn't a valid Python
import name, `engine.py` loads them dynamically via `importlib` — fully functional.

**Is Redis required?**
No. Redis only adds optional cross-run dedup state for local/Docker use. On GitHub
Actions (stateless) it gracefully degrades to a no-op.

---

## 🛡️ Responsible Use

This tool **only** collects proxies that are publicly and freely shared. The built-in
token-bucket rate limiter and User-Agent rotation exist to be a **polite client**, not
to bypass protections. Always respect each source's terms of service and applicable
laws. You are responsible for how you use the collected proxies.

---

## 🤝 Contributing

Contributions are welcome! To suggest a new source, open a **New source request** issue
(template provided) or run `scripts/add_new_source.py` and submit a PR. Please ensure
`make lint` and `make test` pass before opening a pull request.

---

## 📄 License

Released under the **MIT License** — see [`LICENSE`](LICENSE).

<div align="center">
<sub>Built with ⚡ asyncio, 🧬 Pydantic, and ❤️ for the open-source community.</sub>
</div>
