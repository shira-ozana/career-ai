"""CLI entrypoints for profile analysis and text profile extraction."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from app.agents.profile import ProfileAnalyzerAgent, ProfileExtractionAgent
from app.config import get_settings
from app.models.profile import ProfileInput
from app.models.profile_ingestion import ProfileIngestionRequest
from app.tools.mock_llm import MockStructuredLLM
from app.workflows.profile_ingestion import (
    ProfileIngestionFlow,
    UnsupportedProfileSourceError,
)


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def _run_profile_analysis(profile_path: Path) -> int:
    raw = json.loads(profile_path.read_text(encoding="utf-8"))
    profile = ProfileInput.model_validate(raw)
    agent = ProfileAnalyzerAgent()
    analysis = await agent.analyze(profile)
    print(analysis.model_dump_json(indent=2))
    return 0


async def _run_profile_extraction(request_path: Path, *, use_mock: bool) -> int:
    raw = json.loads(request_path.read_text(encoding="utf-8"))
    request = ProfileIngestionRequest.model_validate(raw)
    if use_mock:
        logging.getLogger(__name__).info(
            "extract-profile using MockStructuredLLM (no external API)"
        )
        agent = ProfileExtractionAgent(llm=MockStructuredLLM())
    else:
        agent = ProfileExtractionAgent()
    flow = ProfileIngestionFlow(agent=agent)
    try:
        result = await flow.run(request)
    except UnsupportedProfileSourceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(result.model_dump_json(indent=2))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="career-ai",
        description="Career AI Assistant CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze-profile",
        help="Analyze a profile JSON file with the Profile Agent",
    )
    analyze.add_argument(
        "profile_path",
        type=Path,
        help="Path to a Profile Analyzer input JSON file (ProfileInput)",
    )

    extract = subparsers.add_parser(
        "extract-profile",
        help="Extract per-source profile facts from a ProfileIngestionRequest JSON file",
    )
    extract.add_argument(
        "request_path",
        type=Path,
        help="Path to a ProfileIngestionRequest JSON file",
    )
    extract.add_argument(
        "--mock",
        action="store_true",
        help="Use the deterministic mock LLM instead of OpenAI",
    )

    args = parser.parse_args(argv)
    settings = get_settings()
    _configure_logging(settings.log_level)

    if args.command == "analyze-profile":
        raise SystemExit(asyncio.run(_run_profile_analysis(args.profile_path)))
    if args.command == "extract-profile":
        raise SystemExit(
            asyncio.run(
                _run_profile_extraction(args.request_path, use_mock=args.mock),
            )
        )

    parser.error(f"Unknown command: {args.command}")
    raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
