#!/usr/bin/env python3
"""Pre-flight script: ping candidate judge URLs, save alive ones to JSON."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CANDIDATE_JUDGES: list[dict[str, str]] = [
    {"url": "http://httpbin.org/ip", "validate": "origin", "type": "usual"},
    {"url": "http://api.ipify.org?format=json", "validate": "ip", "type": "usual"},
    {"url": "http://icanhazip.com", "validate": "", "type": "usual"},
    {"url": "http://ifconfig.me/ip", "validate": "", "type": "usual"},
    {"url": "http://checkip.amazonaws.com", "validate": "", "type": "usual"},
    {"url": "http://ipecho.net/plain", "validate": "", "type": "usual"},
    {"url": "http://myip.dnsomatic.com", "validate": "", "type": "usual"},
    {"url": "http://www.trackip.net/ip", "validate": "", "type": "usual"},
    {"url": "https://api.ipify.org?format=json", "validate": "ip", "type": "ssl"},
    {"url": "https://icanhazip.com", "validate": "", "type": "ssl"},
    {"url": "https://ifconfig.me/ip", "validate": "", "type": "ssl"},
    {"url": "https://ipecho.net/plain", "validate": "", "type": "ssl"},
    {"url": "https://www.trackip.net/ip", "validate": "", "type": "ssl"},
    {"url": "https://checkip.amazonaws.com", "validate": "", "type": "ssl"},
    {"url": "http://pubproxy.com/api/proxy?type=http", "validate": "ip", "type": "usual"},
    {"url": "http://www.songkroh.com/api/clientip.php", "validate": "", "type": "usual"},
]

TIMEOUT_SECONDS = 10.0
OUTPUT_PATH = Path("data/cache/judge_servers.json")


async def ping_one(
    session: aiohttp.ClientSession,
    judge: dict[str, str],
) -> dict[str, object]:
    url = judge["url"]
    validate = judge.get("validate", "")
    judge_type = judge.get("type", "usual")
    result: dict[str, object] = {
        "url": url,
        "type": judge_type,
        "validate": validate,
        "alive": False,
        "latency_ms": 0.0,
    }
    try:
        start = time.monotonic()
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
            ssl=(judge_type == "ssl"),
        ) as resp:
            if resp.status == 200:
                body = await resp.text()
                if not validate or validate in body:
                    elapsed = round((time.monotonic() - start) * 1000, 2)
                    result["alive"] = True
                    result["latency_ms"] = elapsed
    except Exception:
        pass
    return result


async def fetch_all_judges() -> list[dict[str, object]]:
    logger.info("Pinging %d candidate judge servers...", len(CANDIDATE_JUDGES))
    async with aiohttp.ClientSession() as session:
        tasks = [ping_one(session, j) for j in CANDIDATE_JUDGES]
        results = await asyncio.gather(*tasks)

    alive = [r for r in results if r["alive"]]
    dead = [r for r in results if not r["alive"]]

    logger.info("Alive: %d / %d", len(alive), len(results))
    for r in alive:
        logger.info("  OK  %s (%sms) [%s]", r["url"], r["latency_ms"], r["type"])
    for r in dead:
        logger.info("  FAIL %s", r["url"])

    return results


def save_results(results: list[dict[str, object]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    alive_only = [r for r in results if r["alive"]]
    alive_only.sort(key=lambda r: float(r["latency_ms"]))

    OUTPUT_PATH.write_text(
        json.dumps(alive_only, indent=2),
        encoding="utf-8",
    )
    logger.info("Saved %d alive judges to %s", len(alive_only), OUTPUT_PATH)


def main() -> int:
    results = asyncio.run(fetch_all_judges())
    alive_count = sum(1 for r in results if r["alive"])
    if alive_count == 0:
        logger.error("No alive judge servers found!")
        return 1
    save_results(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
