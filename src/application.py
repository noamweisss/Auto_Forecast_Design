"""One readable application workflow from IMS-shaped source data to a local PNG."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from src.app_paths import AppPaths
from src.clock import ISRAEL_TIMEZONE
from src.data.archive import SnapshotArchiveError, SnapshotStore
from src.data.fetcher import FetchResult, fetch_feed
from src.data.parser import ForecastDataError, parse_daily_forecast
from src.data.snapshots import (
    FeedType,
    ForecastSnapshot,
    SnapshotSource,
    SnapshotValidationError,
    build_snapshot,
)
from src.design.render_context import (
    RenderContextError,
    StoryRenderContext,
    build_story_render_context,
)
from src.delivery.file_saver import OutputSaveError, save_forecast_png
from src.rendering.template_renderer import TemplateRenderError
from src.settings import AppSettings


FIXTURE_DEFAULT_DATE = date(2025, 12, 18)
FIXTURE_FETCHED_AT = datetime(2025, 12, 17, 5, 0, tzinfo=ISRAEL_TIMEZONE)
_FIXTURE_FILES = {
    FeedType.COUNTRY: "country_forecast.xml",
    FeedType.CITIES: "cities_forecast.xml",
}


class SourceMode(str, Enum):
    LIVE = "live"
    FIXTURE = "fixture"


@dataclass(frozen=True)
class GenerationRequest:
    target_date: date
    source_mode: SourceMode
    output_directory: Path


@dataclass(frozen=True)
class GenerationResult:
    target_date: date
    source_mode: SourceMode
    output_path: Path
    used_fallback: bool
    fallback_value_count: int


class RunStage(str, Enum):
    SOURCE = "source"
    FORECAST = "forecast"
    RENDER = "render"
    OUTPUT = "output"


class ForecastRunError(RuntimeError):
    """An expected application boundary failed at a named run stage."""

    stage: RunStage

    def __init__(self, stage: RunStage, message: str) -> None:
        self.stage = stage
        super().__init__(message)


class PngRenderer(Protocol):
    """Smallest rendering boundary needed by the application workflow."""

    def render(self, context: StoryRenderContext) -> bytes:
        """Turn one validated Story packing list into canonical PNG bytes."""
        ...


FetchFeed = Callable[[FeedType], FetchResult]
SavePng = Callable[[bytes, date, Path], Path]


def generate_forecast_image(
    request: GenerationRequest,
    *,
    paths: AppPaths,
    settings: AppSettings,
    now: datetime,
    renderer: PngRenderer,
    fetch_feed_fn: FetchFeed = fetch_feed,
    snapshot_store: SnapshotStore | None = None,
    save_png_fn: SavePng = save_forecast_png,
) -> GenerationResult:
    """Generate exactly one complete exact-date Story PNG."""
    _require_aware(now)

    # 1. Obtain preferred-first country and city snapshot candidates.
    candidates, failure_reasons = _obtain_candidates(
        request,
        paths=paths,
        now=now,
        fetch_feed_fn=fetch_feed_fn,
        snapshot_store=snapshot_store,
    )

    # 2. Parse one complete forecast for the requested date, never a nearby day.
    try:
        forecast = parse_daily_forecast(
            candidates[FeedType.COUNTRY],
            candidates[FeedType.CITIES],
            request.target_date,
            settings=settings,
            feed_failure_reasons=failure_reasons,
        )
    except ForecastDataError as error:
        raise ForecastRunError(RunStage.FORECAST, str(error)) from error

    # 3. Build the checked, template-ready Story packing list.
    try:
        context = build_story_render_context(forecast, settings, paths)
    except RenderContextError as error:
        raise ForecastRunError(RunStage.RENDER, str(error)) from error

    # 4. Render one canonical 1080x1920 PNG in Chromium.
    try:
        png_bytes = renderer.render(context)
    except TemplateRenderError as error:
        raise ForecastRunError(RunStage.RENDER, str(error)) from error

    # 5. Publish that PNG atomically at its canonical date-based path.
    try:
        output_path = save_png_fn(
            png_bytes,
            request.target_date,
            request.output_directory,
        )
    except OutputSaveError as error:
        raise ForecastRunError(RunStage.OUTPUT, str(error)) from error

    # 6. Return only the short facts a caller needs for a success summary.
    fallback_value_count = int(forecast.country_forecast.is_fallback) + sum(
        city.is_fallback for city in forecast.city_forecasts
    )
    return GenerationResult(
        target_date=request.target_date,
        source_mode=request.source_mode,
        output_path=output_path,
        used_fallback=fallback_value_count > 0,
        fallback_value_count=fallback_value_count,
    )


def _obtain_candidates(
    request: GenerationRequest,
    *,
    paths: AppPaths,
    now: datetime,
    fetch_feed_fn: FetchFeed,
    snapshot_store: SnapshotStore | None,
) -> tuple[dict[FeedType, list[ForecastSnapshot]], dict[FeedType, str]]:
    if request.source_mode is SourceMode.FIXTURE:
        return _fixture_candidates(request.target_date, paths), {}
    if request.source_mode is SourceMode.LIVE:
        store = snapshot_store or SnapshotStore(paths.archive)
        return _live_candidates(
            request.target_date,
            now=now,
            fetch_feed_fn=fetch_feed_fn,
            store=store,
        )
    raise ValueError(f"Unsupported source mode: {request.source_mode!r}")


def _fixture_candidates(
    target_date: date,
    paths: AppPaths,
) -> dict[FeedType, list[ForecastSnapshot]]:
    snapshots: dict[FeedType, ForecastSnapshot] = {}
    for feed_type in FeedType:
        fixture_path = paths.ims_fixtures / _FIXTURE_FILES[feed_type]
        try:
            xml = fixture_path.read_text(encoding="utf-8")
            snapshot = build_snapshot(
                xml,
                feed_type,
                source=SnapshotSource.FIXTURE,
                fetched_at=FIXTURE_FETCHED_AT,
            )
        except (OSError, UnicodeDecodeError, SnapshotValidationError) as error:
            raise ForecastRunError(
                RunStage.SOURCE,
                f"Fixture {feed_type.value} source is invalid: {error}",
            ) from error
        snapshots[feed_type] = snapshot

    jointly_available = set(snapshots[FeedType.COUNTRY].forecast_dates).intersection(
        snapshots[FeedType.CITIES].forecast_dates
    )
    if target_date not in jointly_available:
        available_text = ", ".join(
            item.isoformat() for item in sorted(jointly_available)
        ) or "none"
        raise ForecastRunError(
            RunStage.SOURCE,
            f"Fixture date {target_date.isoformat()} is unavailable; "
            f"jointly available dates: {available_text}",
        )

    return {feed_type: [snapshots[feed_type]] for feed_type in FeedType}


def _live_candidates(
    target_date: date,
    *,
    now: datetime,
    fetch_feed_fn: FetchFeed,
    store: SnapshotStore,
) -> tuple[dict[FeedType, list[ForecastSnapshot]], dict[FeedType, str]]:
    candidates: dict[FeedType, list[ForecastSnapshot]] = {}
    failure_reasons: dict[FeedType, str] = {}
    live_advertised_dates: dict[FeedType, tuple[date, ...]] = {}

    for feed_type in FeedType:
        try:
            archived = list(
                store.find_for_date(
                    feed_type,
                    target_date,
                    as_of=now,
                    strict=True,
                )
            )
        except SnapshotArchiveError as error:
            raise ForecastRunError(
                RunStage.SOURCE,
                f"Could not read {feed_type.value} archive for "
                f"{target_date.isoformat()}: {error}",
            ) from error

        exact_archives = [
            snapshot
            for snapshot in archived
            if snapshot.feed_type is feed_type
            and target_date in snapshot.forecast_dates
        ]
        feed_candidates: list[ForecastSnapshot] = []
        result = fetch_feed_fn(feed_type)
        if result.feed_type is not feed_type:
            raise ValueError(
                f"Fetcher returned {result.feed_type.value} for requested {feed_type.value}"
            )

        if result.xml is None:
            failure = result.failure
            detail = failure.message if failure is not None else "unknown fetch failure"
            failure_reasons[feed_type] = (
                f"live {feed_type.value} fetch failed after "
                f"{result.attempt_count} attempt(s): {detail}"
            )
        else:
            try:
                live = build_snapshot(
                    result.xml,
                    feed_type,
                    source=SnapshotSource.LIVE,
                    fetched_at=now,
                )
            except SnapshotValidationError as error:
                failure_reasons[feed_type] = (
                    f"invalid live {feed_type.value} snapshot: {error}"
                )
            else:
                try:
                    store.save(live)
                except SnapshotArchiveError as error:
                    raise ForecastRunError(
                        RunStage.SOURCE,
                        f"Could not save live {feed_type.value} snapshot: {error}",
                    ) from error
                live_advertised_dates[feed_type] = live.forecast_dates
                if target_date in live.forecast_dates:
                    feed_candidates.append(live)
                else:
                    advertised = ", ".join(
                        item.isoformat() for item in live.forecast_dates
                    )
                    failure_reasons[feed_type] = (
                        f"live {feed_type.value} snapshot does not advertise "
                        f"{target_date.isoformat()}; advertised dates: {advertised}"
                    )

        seen_ids = {snapshot.snapshot_id for snapshot in feed_candidates}
        for archived_snapshot in exact_archives:
            if archived_snapshot.snapshot_id in seen_ids:
                continue
            feed_candidates.append(archived_snapshot)
            seen_ids.add(archived_snapshot.snapshot_id)
        candidates[feed_type] = feed_candidates

    if (
        not candidates[FeedType.COUNTRY]
        and not candidates[FeedType.CITIES]
        and set(live_advertised_dates) == set(FeedType)
    ):
        jointly_advertised = set(
            live_advertised_dates[FeedType.COUNTRY]
        ).intersection(live_advertised_dates[FeedType.CITIES])
        joint_text = ", ".join(
            item.isoformat() for item in sorted(jointly_advertised)
        ) or "none"
        raise ForecastRunError(
            RunStage.SOURCE,
            f"Live country and cities feeds do not advertise "
            f"{target_date.isoformat()}; jointly advertised dates: {joint_text}",
        )

    for feed_type in FeedType:
        if candidates[feed_type]:
            continue
        reason = failure_reasons.get(feed_type, "no exact-date candidate")
        raise ForecastRunError(
            RunStage.SOURCE,
            f"No exact-date {feed_type.value} source for "
            f"{target_date.isoformat()}: {reason}",
        )

    return candidates, failure_reasons


def _require_aware(value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
