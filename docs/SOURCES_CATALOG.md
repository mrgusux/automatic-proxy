# Sources Catalog

The live source registry is `config/proxy_sources_registry.yaml`. Each entry has a
`name`, `url`, `scraper_type`, and `default_protocol`.

## Scraper types

| Type | Use for |
|------|---------|
| `html_table` | Sites that list proxies in HTML `<table>` rows |
| `json_api` | Endpoints returning JSON (configurable field mapping) |
| `github_raw` | Raw text proxy lists (`ip:port` per line) on GitHub |
| `regex_text` | Any unstructured text/HTML; extracts every `ip:port` |

## Adding a source

Use the CLI wizard:

```bash
python scripts/add_new_source.py
```

Or open a **New source request** issue. All sources must be publicly and freely
shared lists; private or paywalled lists are not accepted.

## Current sources

See `config/proxy_sources_registry.yaml` for the authoritative, version-controlled
list (ProxyScrape API, TheSpeedX, monosans, clarketm, jetkai, proxyspace, and more).
