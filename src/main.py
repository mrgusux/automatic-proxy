"""CLI entry point and orchestrator trigger."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

try:
    import uvloop  # type: ignore[import-untyped]
except ImportError:
    uvloop = None  # type: ignore[assignment]

logger = logging.getLogger("proxy_collector")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="proxy-collector",
        description="Ultimate God-Tier Automated Proxy Collector",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Run the full collection pipeline")
    run_cmd.add_argument(
        "--config", default="config/settings.yaml", help="Path to settings.yaml"
    )
    run_cmd.add_argument(
        "--sources",
        default="config/proxy_sources_registry.yaml",
        help="Path to the sources registry",
    )
    run_cmd.add_argument(
        "--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING)"
    )
    return parser


async def _run_pipeline(config_path: str, sources_path: str) -> int:
    from src.collectors.factory import build_collector
    from src.core.pipeline_manager import PipelineManager
    from src.deduplication.early_aggregator import build_deduplicator
    from src.enrichment.scoring_engine import build_enricher
    from src.exporters.master_file_builder import build_exporter
    from src.utils.config_loader import load_settings, load_sources
    from src.validators.engine import build_verifier

    settings = load_settings(config_path)
    sources = load_sources(sources_path)

    manager = PipelineManager(
        sources=sources,
        collector=build_collector(settings),
        deduplicator=build_deduplicator(settings),
        verifier=build_verifier(settings),
        enricher=build_enricher(settings),
        exporter=build_exporter(settings),
        max_alive_output=settings.max_alive_output,
    )
    result = await manager.run()
    logger.info(
        "Done. alive=%d dead=%d sources_ok=%d/%d avg_latency=%.1fms",
        result.stats.alive,
        result.stats.dead,
        result.stats.sources_ok,
        result.stats.sources_total,
        result.stats.average_latency_ms,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.command == "run":
        if uvloop is not None:
            uvloop.install()
        return asyncio.run(_run_pipeline(args.config, args.sources))

    return 1


if __name__ == "__main__":
    sys.exit(main())
