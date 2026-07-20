"""Command-line boundary for generating one local IMS forecast Story PNG."""

import argparse
from datetime import date
import logging
from pathlib import Path
import re
from typing import Sequence

from dotenv import load_dotenv

from src.app_paths import AppPaths
from src.application import (
    FIXTURE_DEFAULT_DATE,
    ForecastRunError,
    GenerationRequest,
    GenerationResult,
    RunStage,
    SourceMode,
    generate_forecast_image,
)
from src.clock import SystemClock
from src.rendering.template_renderer import TemplateRenderer
from src.settings import ConfigurationError, load_settings
from src.utils.logger import configure_logging


logger = logging.getLogger(__name__)

_EXIT_BY_STAGE = {
    RunStage.SOURCE: 4,
    RunStage.FORECAST: 5,
    RunStage.RENDER: 6,
    RunStage.OUTPUT: 7,
}


def _iso_date(value: str) -> date:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise argparse.ArgumentTypeError("date must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid calendar date: {value}") from error


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI values without reading configuration, time, or the filesystem."""
    parser = argparse.ArgumentParser(
        description="Generate one local 1080x1920 IMS forecast Story PNG."
    )
    parser.add_argument(
        "--source",
        choices=[mode.value for mode in SourceMode],
        default=SourceMode.LIVE.value,
        help="Data source: live IMS or committed local sample fixtures (default: live).",
    )
    parser.add_argument(
        "--date",
        type=_iso_date,
        help=(
            "Exact forecast date (YYYY-MM-DD). Defaults to the Israel run-start "
            "date for live data and 2025-12-18 for fixtures."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "PNG destination directory (default: repository output/). An explicit "
            "relative path is resolved from the repository root."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Initialize the application boundary once and return a stable process exit."""
    arguments = parse_arguments(argv)

    try:
        paths = AppPaths.from_repository()
        load_dotenv(dotenv_path=paths.root / ".env", override=False)
        now = SystemClock().now()
        configure_logging(paths.logs, now)
        settings = load_settings(paths)

        source_mode = SourceMode(arguments.source)
        target_date = arguments.date or (
            FIXTURE_DEFAULT_DATE
            if source_mode is SourceMode.FIXTURE
            else now.date()
        )
        output_directory = _resolve_output_directory(arguments.output_dir, paths)

        renderer = TemplateRenderer()
        result = generate_forecast_image(
            GenerationRequest(
                target_date=target_date,
                source_mode=source_mode,
                output_directory=output_directory,
            ),
            paths=paths,
            settings=settings,
            now=now,
            renderer=renderer,
        )
    except ConfigurationError as error:
        logger.error("%s", error)
        return 3
    except ForecastRunError as error:
        logger.error("%s", error)
        return _EXIT_BY_STAGE[error.stage]
    except Exception:
        logger.exception("Unexpected forecast generation error")
        return 1

    _print_success(result)
    return 0


def _resolve_output_directory(value: Path | None, paths: AppPaths) -> Path:
    if value is None:
        return paths.output
    if value.is_absolute():
        return value.resolve()
    return (paths.root / value).resolve()


def _print_success(result: GenerationResult) -> None:
    source_text = {
        SourceMode.LIVE: "live IMS",
        SourceMode.FIXTURE: "local fixture",
    }[result.source_mode]
    fallback_text = (
        f"yes ({result.fallback_value_count} values)"
        if result.used_fallback
        else "no"
    )
    print("Forecast image created.")
    print(f"Date: {result.target_date.isoformat()}")
    print(f"Data source requested: {source_text}")
    print(f"Exact-date archived values used: {fallback_text}")
    print(f"PNG: {result.output_path}")


if __name__ == "__main__":
    raise SystemExit(main())
