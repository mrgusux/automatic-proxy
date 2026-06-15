#!/usr/bin/env python3
"""Interactive CLI wizard to append a new source to the registry."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REGISTRY = Path("config/proxy_sources_registry.yaml")
SCRAPER_TYPES = ("html_table", "json_api", "github_raw", "regex_text")
PROTOCOLS = ("http", "https", "socks4", "socks5")


def _prompt(label: str, options: tuple[str, ...] | None = None) -> str:
    while True:
        suffix = f" {options}" if options else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            print("  Value required.")
            continue
        if options and value not in options:
            print(f"  Must be one of {options}.")
            continue
        return value


def main() -> int:
    if not REGISTRY.exists():
        print(f"Registry not found: {REGISTRY}", file=sys.stderr)
        return 1

    data = yaml.safe_load(REGISTRY.read_text()) or {"sources": []}
    sources = data.setdefault("sources", [])

    name = _prompt("Source name")
    if any(s.get("name") == name for s in sources):
        print("  A source with that name already exists.", file=sys.stderr)
        return 1

    entry = {
        "name": name,
        "url": _prompt("Source URL"),
        "scraper_type": _prompt("Scraper type", SCRAPER_TYPES),
        "default_protocol": _prompt("Default protocol", PROTOCOLS),
        "enabled": True,
    }
    sources.append(entry)
    REGISTRY.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print(f"Added source '{name}'. Total sources: {len(sources)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
