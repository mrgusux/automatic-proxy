"""Judge server system: auto-ping test URLs, rotate alive ones."""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)

DEFAULT_JUDGES: list[dict[str, str]] = [
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


@dataclass
class JudgeStatus:
    url: str
    judge_type: str
    alive: bool = False
    latency_ms: float = 0.0
    validate: str = ""


class JudgeServers:
    """Manage judge servers: ping, track alive, rotate usage."""

    def __init__(self, judges: list[dict[str, str]] | None = None) -> None:
        self._judges_data = judges or DEFAULT_JUDGES
        self._statuses: list[JudgeStatus] = []
        self._usual_index = 0
        self._ssl_index = 0
        self._any_list: list[JudgeStatus] = []

    async def ping_all(self, timeout: float = 10.0) -> list[JudgeStatus]:
        logger.info("Pinging %d judge servers...", len(self._judges_data))
        tasks = [self._ping_one(j, timeout) for j in self._judges_data]
        self._statuses = await asyncio.gather(*tasks)

        alive_usual = [s for s in self._statuses if s.alive and s.judge_type == "usual"]
        alive_ssl = [s for s in self._statuses if s.alive and s.judge_type == "ssl"]
        self._any_list = alive_usual + alive_ssl

        logger.info(
            "Judge ping done: %d/%d alive (%d usual, %d ssl)",
            len(self._any_list),
            len(self._judges_data),
            len(alive_usual),
            len(alive_ssl),
        )
        return self._statuses

    async def _ping_one(
        self, judge: dict[str, str], timeout: float
    ) -> JudgeStatus:
        status = JudgeStatus(
            url=judge["url"],
            judge_type=judge.get("type", "usual"),
            validate=judge.get("validate", ""),
        )
        try:
            start = asyncio.get_running_loop().time()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    judge["url"],
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=status.judge_type == "ssl",
                ) as resp:
                    if resp.status == 200:
                        body = await resp.text()
                        if not status.validate or status.validate in body:
                            elapsed = (asyncio.get_running_loop().time() - start) * 1000
                            status.alive = True
                            status.latency_ms = round(elapsed, 2)
        except Exception:
            pass
        return status

    def get_usual(self) -> str | None:
        alive = [s for s in self._statuses if s.alive and s.judge_type == "usual"]
        if not alive:
            return None
        judge = alive[self._usual_index % len(alive)]
        self._usual_index = (self._usual_index + 1) % len(alive)
        return judge.url

    def get_ssl(self) -> str | None:
        alive = [s for s in self._statuses if s.alive and s.judge_type == "ssl"]
        if not alive:
            return None
        judge = alive[self._ssl_index % len(alive)]
        self._ssl_index = (self._ssl_index + 1) % len(alive)
        return judge.url

    def get_any(self) -> str | None:
        if not self._any_list:
            return None
        return random.choice(self._any_list).url

    def validate_response(self, body: str, judge_url: str) -> bool:
        for s in self._statuses:
            if s.url == judge_url and s.validate:
                return s.validate in body
        return True

    @property
    def alive_count(self) -> int:
        return sum(1 for s in self._statuses if s.alive)

    @property
    def has_usual(self) -> bool:
        return any(s.alive and s.judge_type == "usual" for s in self._statuses)

    @property
    def has_ssl(self) -> bool:
        return any(s.alive and s.judge_type == "ssl" for s in self._statuses)
