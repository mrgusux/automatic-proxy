"""Scraper factory + the collector that drives concurrent scraping."""

from __future__ import annotations

import logging
from typing import Any

from src.collectors.base_scraper import BaseScraper
from src.collectors.extractors.github_raw_scraper import GithubRawScraper
from src.collectors.extractors.html_table_scraper import HtmlTableScraper
from src.collectors.extractors.json_api_scraper import JsonApiScraper
from src.collectors.extractors.regex_text_scraper import RegexTextScraper
from src.collectors.rotators.user_agent_rotator import UserAgentRotator
from src.models.proxy import Proxy
from src.models.source_metadata import ScraperType, SourceHealth, SourceMetadata
from src.utils.async_semaphore_pool import AsyncSemaphorePool
from src.utils.http_client import HttpClient
from src.utils.rate_limiter import CircuitBreaker, TokenBucket

logger = logging.getLogger(__name__)

_SCRAPER_MAP: dict[ScraperType, type[BaseScraper]] = {
    ScraperType.HTML_TABLE: HtmlTableScraper,
    ScraperType.JSON_API: JsonApiScraper,
    ScraperType.GITHUB_RAW: GithubRawScraper,
    ScraperType.REGEX_TEXT: RegexTextScraper,
}


class ScraperFactory:
    """Return the right scraper instance for a given source type."""

    def __init__(self, ua_rotator: UserAgentRotator | None = None) -> None:
        self._ua = ua_rotator or UserAgentRotator()
        self._cache: dict[ScraperType, BaseScraper] = {}

    def get(self, scraper_type: ScraperType) -> BaseScraper:
        if scraper_type not in self._cache:
            cls = _SCRAPER_MAP[scraper_type]
            self._cache[scraper_type] = cls(ua_rotator=self._ua)
        return self._cache[scraper_type]


class Collector:
    """Concurrently scrape all sources and aggregate raw proxies + health."""

    def __init__(
        self,
        concurrency: int,
        timeout: float,
        max_retries: int,
        backoff: float,
        rate_per_sec: float,
        rate_burst: int,
    ) -> None:
        self._factory = ScraperFactory()
        self._pool = AsyncSemaphorePool(concurrency)
        self._breaker = CircuitBreaker()
        self._timeout = timeout
        self._max_retries = max_retries
        self._backoff = backoff
        self._rate_per_sec = rate_per_sec
        self._rate_burst = rate_burst

    async def collect(
        self, sources: list[SourceMetadata]
    ) -> tuple[list[Proxy], list[SourceHealth]]:
        limiter = TokenBucket(self._rate_per_sec, self._rate_burst)
        async with HttpClient(
            timeout=self._timeout,
            max_retries=self._max_retries,
            backoff=self._backoff,
            rate_limiter=limiter,
        ) as client:

            async def worker(
                source: SourceMetadata,
            ) -> tuple[list[Proxy], SourceHealth]:
                if self._breaker.is_open(source.name):
                    logger.info("Skipping %s (circuit open)", source.name)
                    health = SourceHealth(
                        name=source.name,
                        url=source.url,
                        success=False,
                        error="circuit open (recent repeated failures)",
                    )
                    return [], health
                scraper = self._factory.get(source.scraper_type)
                proxies, health = await scraper.scrape(source, client)
                if health.success:
                    self._breaker.record_success(source.name)
                else:
                    self._breaker.record_failure(source.name)
                return proxies, health

            results = await self._pool.map(worker, sources)

        all_proxies: list[Proxy] = []
        health: list[SourceHealth] = []
        for proxies, source_health in results:
            source_health.health_score = 100.0 if source_health.success else 0.0
            all_proxies.extend(proxies)
            health.append(source_health)
        logger.info(
            "Collected %d raw proxies from %d sources",
            len(all_proxies),
            len(health),
        )
        return all_proxies, health


def build_collector(settings: Any) -> Collector:
    return Collector(
        concurrency=settings.scrape_concurrency,
        timeout=settings.scrape_timeout,
        max_retries=settings.max_retries,
        backoff=settings.retry_backoff,
        rate_per_sec=settings.rate_limit_per_sec,
        rate_burst=settings.rate_limit_burst,
    )
