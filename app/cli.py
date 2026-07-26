"""Simple CLI entrypoint for local Profile Agent demos."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from app.agents.profile import ProfileAnalyzerAgent
from app.config import get_settings
from app.models.profile import ProfileInput


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
        help="Path to a ProfileInput JSON file",
    )

    args = parser.parse_args(argv)
    settings = get_settings()
    _configure_logging(settings.log_level)

    if args.command == "analyze-profile":
        raise SystemExit(asyncio.run(_run_profile_analysis(args.profile_path)))

    parser.error(f"Unknown command: {args.command}")
    raise SystemExit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
