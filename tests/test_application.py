"""Thin application workflow contracts from source selection to one PNG."""

from datetime import date, datetime, timedelta
import importlib
from pathlib import Path

from lxml import etree
from PIL import Image
import pytest

from src.app_paths import AppPaths, PATHS
from src.clock import ISRAEL_TIMEZONE
from src.data.archive import SnapshotArchiveError, SnapshotStore
from src.data.fetcher import (
    CITIES_FORECAST_URL,
    COUNTRY_FORECAST_URL,
    FetchFailure,
    FetchFailureKind,
    FetchResult,
)
from src.data.snapshots import FeedType, SnapshotSource, build_snapshot
from src.design.render_context import RenderContextError
from src.rendering.template_renderer import TemplateRenderError, TemplateRenderer
from tests.conftest import load_ims_fixture


TARGET_DATE = date(2025, 12, 18)
NOW = datetime(2025, 12, 17, 10, 0, tzinfo=ISRAEL_TIMEZONE)
FEED_URLS = {
    FeedType.COUNTRY: COUNTRY_FORECAST_URL,
    FeedType.CITIES: CITIES_FORECAST_URL,
}
FIXTURE_NAMES = {
    FeedType.COUNTRY: "country_forecast.xml",
    FeedType.CITIES: "cities_forecast.xml",
}


def _application_module():
    return importlib.import_module("src.application")


def _fixture_xml(feed_type: FeedType) -> str:
    return load_ims_fixture(FIXTURE_NAMES[feed_type])


def _fetch_success(xml_by_feed: dict[FeedType, str] | None = None):
    documents = xml_by_feed or {feed_type: _fixture_xml(feed_type) for feed_type in FeedType}

    def fetch(feed_type: FeedType) -> FetchResult:
        return FetchResult(
            feed_type=feed_type,
            url=FEED_URLS[feed_type],
            attempt_count=1,
            xml=documents[feed_type],
        )

    return fetch


def _fetch_failure(failed_feeds: set[FeedType]):
    success = _fetch_success()

    def fetch(feed_type: FeedType) -> FetchResult:
        if feed_type not in failed_feeds:
            return success(feed_type)
        return FetchResult(
            feed_type=feed_type,
            url=FEED_URLS[feed_type],
            attempt_count=3,
            failure=FetchFailure(
                FetchFailureKind.CONNECTION,
                f"{feed_type.value} connection unavailable",
            ),
        )

    return fetch


def _store_archives(
    store: SnapshotStore,
    *feed_types: FeedType,
    fetched_at: datetime | None = None,
) -> None:
    archive_time = fetched_at or NOW - timedelta(hours=1)
    for feed_type in feed_types:
        store.save(
            build_snapshot(
                _fixture_xml(feed_type),
                feed_type,
                source=SnapshotSource.LIVE,
                fetched_at=archive_time,
            )
        )


def _mutate_city_maximum(xml: str, value: str | None) -> str:
    root = etree.fromstring(xml.encode("utf-8"))
    city = next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == "520"
    )
    time_unit = next(
        item
        for item in city.findall("LocationData/TimeUnitData")
        if item.findtext("Date") == TARGET_DATE.isoformat()
    )
    element = next(
        item
        for item in time_unit.findall("Element")
        if item.findtext("ElementName") == "Maximum temperature"
    )
    if value is None:
        time_unit.remove(element)
    else:
        element.find("ElementValue").text = value
    return etree.tostring(root, encoding="unicode")


def _remove_city(xml: str, city_id: str = "520") -> str:
    root = etree.fromstring(xml.encode("utf-8"))
    city = next(
        location
        for location in root.findall("Location")
        if location.findtext("LocationMetaData/LocationId") == city_id
    )
    root.remove(city)
    return etree.tostring(root, encoding="unicode")


def _blank_country_hebrew(xml: str) -> str:
    root = etree.fromstring(xml.encode("utf-8"))
    time_unit = next(
        item
        for item in root.findall("Location/LocationData/TimeUnitData")
        if item.findtext("Date") == TARGET_DATE.isoformat()
    )
    element = next(
        item
        for item in time_unit.findall("Element")
        if item.findtext("ElementName") == "Weather in Hebrew"
    )
    element.find("ElementValue").text = "   "
    return etree.tostring(root, encoding="unicode")


class RecordingRenderer:
    def __init__(self, png_bytes: bytes = b"rendered png") -> None:
        self.png_bytes = png_bytes
        self.contexts = []

    def render(self, context) -> bytes:
        self.contexts.append(context)
        return self.png_bytes


def _recording_saver(calls: list):
    def save_png(png_bytes: bytes, target_date: date, output_directory: Path) -> Path:
        calls.append((png_bytes, target_date, output_directory))
        return (output_directory / f"forecast_{target_date.isoformat()}.png").resolve()

    return save_png


def _request(application, source_mode, output_directory: Path, target_date=TARGET_DATE):
    return application.GenerationRequest(
        target_date=target_date,
        source_mode=source_mode,
        output_directory=output_directory,
    )


def _capture_forecast(monkeypatch, application):
    captured = {}
    real_builder = application.build_story_render_context

    def capture(forecast, settings, paths):
        captured["forecast"] = forecast
        return real_builder(forecast, settings, paths)

    monkeypatch.setattr(application, "build_story_render_context", capture)
    return captured


def test_app_paths_exposes_committed_ims_fixture_directory():
    paths = AppPaths(root=Path("C:/repository"))

    assert paths.ims_fixtures == paths.root / "tests" / "fixtures" / "ims"


def test_fixture_mode_builds_15_city_context_renders_once_and_saves_one_png(
    app_settings,
    tmp_path,
):
    application = _application_module()
    renderer = RecordingRenderer()
    save_calls = []

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.FIXTURE, tmp_path),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=renderer,
        fetch_feed_fn=lambda _feed: pytest.fail("fixture mode called HTTP"),
        save_png_fn=_recording_saver(save_calls),
    )

    assert len(renderer.contexts) == 1
    assert renderer.contexts[0].target_date_iso == "2025-12-18"
    assert len(renderer.contexts[0].cities) == 15
    assert save_calls == [(b"rendered png", TARGET_DATE, tmp_path)]
    assert result.target_date == TARGET_DATE
    assert result.source_mode is application.SourceMode.FIXTURE
    assert result.output_path.is_absolute()
    assert result.used_fallback is False
    assert result.fallback_value_count == 0


def test_fixture_mode_is_deterministic_and_never_touches_http_or_archives(
    app_settings,
    tmp_path,
):
    application = _application_module()

    class ForbiddenStore:
        def find_for_date(self, *args, **kwargs):
            pytest.fail("fixture mode read archives")

        def save(self, *args, **kwargs):
            pytest.fail("fixture mode wrote archives")

    def forbidden_fetch(_feed):
        pytest.fail("fixture mode called HTTP")

    renderers = [RecordingRenderer(), RecordingRenderer()]
    results = []
    for renderer, now in zip(
        renderers,
        [
            datetime(2025, 1, 1, 1, 0, tzinfo=ISRAEL_TIMEZONE),
            datetime(2035, 6, 1, 22, 0, tzinfo=ISRAEL_TIMEZONE),
        ],
        strict=True,
    ):
        results.append(
            application.generate_forecast_image(
                _request(application, application.SourceMode.FIXTURE, tmp_path),
                paths=PATHS,
                settings=app_settings,
                now=now,
                renderer=renderer,
                fetch_feed_fn=forbidden_fetch,
                snapshot_store=ForbiddenStore(),
                save_png_fn=_recording_saver([]),
            )
        )

    assert renderers[0].contexts == renderers[1].contexts
    assert results[0] == results[1]


def test_missing_fixture_date_lists_jointly_available_dates(app_settings, tmp_path):
    application = _application_module()
    renderer = RecordingRenderer()

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(
                application,
                application.SourceMode.FIXTURE,
                tmp_path,
                target_date=date(2030, 1, 1),
            ),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=lambda _feed: pytest.fail("fixture mode called HTTP"),
            save_png_fn=_recording_saver([]),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "2030-01-01" in str(raised.value)
    assert "jointly available dates" in str(raised.value)
    assert "2025-12-17, 2025-12-18, 2025-12-19, 2025-12-20" in str(raised.value)
    assert renderer.contexts == []


def test_valid_live_feeds_are_saved_and_preferred_over_exact_date_archives(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.COUNTRY, FeedType.CITIES)
    captured = _capture_forecast(monkeypatch, application)

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_success(),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    forecast = captured["forecast"]
    assert forecast.country_forecast.provenance.source is SnapshotSource.LIVE
    assert all(
        city.provenance.source is SnapshotSource.LIVE
        for city in forecast.city_forecasts
    )
    assert len(list((tmp_path / "archive").glob("*.snapshot.json"))) == 4
    assert result.used_fallback is False
    assert result.fallback_value_count == 0


def test_fetch_failure_uses_exact_date_archive_with_truthful_fallback(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.COUNTRY)
    captured = _capture_forecast(monkeypatch, application)

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_failure({FeedType.COUNTRY}),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    country = captured["forecast"].country_forecast
    assert country.provenance.source is SnapshotSource.ARCHIVE
    assert "country connection unavailable" in country.provenance.fallback_reason
    assert result.used_fallback is True
    assert result.fallback_value_count == 1


def test_one_invalid_live_city_falls_back_while_fourteen_remain_live(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.CITIES)
    live_documents = {
        FeedType.COUNTRY: _fixture_xml(FeedType.COUNTRY),
        FeedType.CITIES: _mutate_city_maximum(_fixture_xml(FeedType.CITIES), None),
    }
    captured = _capture_forecast(monkeypatch, application)

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_success(live_documents),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    cities = captured["forecast"].city_forecasts
    assert sum(city.provenance.source is SnapshotSource.LIVE for city in cities) == 14
    assert sum(city.provenance.source is SnapshotSource.ARCHIVE for city in cities) == 1
    assert result.used_fallback is True
    assert result.fallback_value_count == 1


def test_valid_wrong_date_live_feed_is_archived_but_not_used_before_archive(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.COUNTRY, FeedType.CITIES)
    wrong_date_documents = {
        feed_type: _fixture_xml(feed_type).replace(
            "<Date>2025-12-18</Date>",
            "<Date>2025-12-23</Date>",
        )
        for feed_type in FeedType
    }
    captured = _capture_forecast(monkeypatch, application)

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_success(wrong_date_documents),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    forecast = captured["forecast"]
    assert forecast.country_forecast.provenance.source is SnapshotSource.ARCHIVE
    assert all(
        city.provenance.source is SnapshotSource.ARCHIVE
        for city in forecast.city_forecasts
    )
    assert len(list((tmp_path / "archive").glob("*.snapshot.json"))) == 4
    assert result.fallback_value_count == 16


def test_wrong_date_live_feeds_report_exact_joint_dates_for_an_explicit_rerun(
    app_settings,
    tmp_path,
):
    application = _application_module()
    wrong_date_documents = {
        feed_type: _fixture_xml(feed_type).replace(
            "<Date>2025-12-18</Date>",
            "<Date>2025-12-23</Date>",
        )
        for feed_type in FeedType
    }

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path / "output"),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=RecordingRenderer(),
            fetch_feed_fn=_fetch_success(wrong_date_documents),
            snapshot_store=SnapshotStore(tmp_path / "archive"),
            save_png_fn=_recording_saver([]),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "jointly advertised dates" in str(raised.value)
    assert "2025-12-17, 2025-12-19, 2025-12-20, 2025-12-23" in str(raised.value)


def test_invalid_live_xml_is_not_saved_and_exact_date_archive_may_be_used(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.COUNTRY)
    documents = {
        FeedType.COUNTRY: "not XML",
        FeedType.CITIES: _fixture_xml(FeedType.CITIES),
    }
    captured = _capture_forecast(monkeypatch, application)

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_success(documents),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    country = captured["forecast"].country_forecast
    assert country.provenance.source is SnapshotSource.ARCHIVE
    assert "invalid live country snapshot" in country.provenance.fallback_reason
    assert len(list((tmp_path / "archive").glob("*.snapshot.json"))) == 2
    assert result.fallback_value_count == 1


def test_wrong_date_archive_is_never_used(app_settings, tmp_path):
    application = _application_module()
    wrong_date_snapshot = build_snapshot(
        _fixture_xml(FeedType.COUNTRY),
        FeedType.COUNTRY,
        source=SnapshotSource.ARCHIVE,
        fetched_at=NOW - timedelta(hours=1),
    )

    class WrongDateStore:
        def find_for_date(self, feed_type, target_date, *, as_of, strict):
            assert strict is True
            assert target_date == date(2025, 12, 21)
            return (wrong_date_snapshot,)

        def save(self, snapshot):
            pytest.fail("fetch failed, so no snapshot should be saved")

    renderer = RecordingRenderer()
    save_calls = []
    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(
                application,
                application.SourceMode.LIVE,
                tmp_path,
                target_date=date(2025, 12, 21),
            ),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=_fetch_failure(set(FeedType)),
            snapshot_store=WrongDateStore(),
            save_png_fn=_recording_saver(save_calls),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "country" in str(raised.value)
    assert "2025-12-21" in str(raised.value)
    assert renderer.contexts == []
    assert save_calls == []


def test_source_failure_without_archive_stops_before_render_and_output(
    app_settings,
    tmp_path,
):
    application = _application_module()
    renderer = RecordingRenderer()
    save_calls = []

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=_fetch_failure({FeedType.COUNTRY}),
            snapshot_store=SnapshotStore(tmp_path / "archive"),
            save_png_fn=_recording_saver(save_calls),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "country connection unavailable" in str(raised.value)
    assert renderer.contexts == []
    assert save_calls == []


@pytest.mark.parametrize("failure_point", ["read", "save"])
def test_archive_read_or_save_failure_stops_before_render_and_output(
    app_settings,
    tmp_path,
    failure_point,
):
    application = _application_module()

    class BrokenStore:
        def find_for_date(self, feed_type, target_date, *, as_of, strict):
            assert strict is True
            if failure_point == "read":
                raise SnapshotArchiveError("archive read blocked")
            return ()

        def save(self, snapshot):
            raise SnapshotArchiveError("archive save blocked")

    renderer = RecordingRenderer()
    save_calls = []
    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=_fetch_success(),
            snapshot_store=BrokenStore(),
            save_png_fn=_recording_saver(save_calls),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert f"archive {failure_point} blocked" in str(raised.value)
    assert renderer.contexts == []
    assert save_calls == []


def test_corrupt_real_archive_record_is_a_source_failure(
    app_settings,
    tmp_path,
):
    application = _application_module()
    archive_directory = tmp_path / "archive"
    archive_directory.mkdir()
    (archive_directory / "broken.snapshot.json").write_text(
        "{not json",
        encoding="utf-8",
    )
    renderer = RecordingRenderer()
    save_calls = []

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path / "output"),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=_fetch_success(),
            snapshot_store=SnapshotStore(archive_directory),
            save_png_fn=_recording_saver(save_calls),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "broken.snapshot.json" in str(raised.value)
    assert renderer.contexts == []
    assert save_calls == []


def test_archive_directory_enumeration_error_is_a_source_failure(
    app_settings,
    tmp_path,
    monkeypatch,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")

    def fail_enumeration():
        raise OSError("archive directory unreadable")

    monkeypatch.setattr(store, "_record_paths", fail_enumeration)

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path / "output"),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=RecordingRenderer(),
            fetch_feed_fn=_fetch_success(),
            snapshot_store=store,
            save_png_fn=_recording_saver([]),
        )

    assert raised.value.stage is application.RunStage.SOURCE
    assert "archive directory unreadable" in str(raised.value)


def test_incomplete_parsed_data_maps_to_forecast_stage(app_settings, tmp_path):
    application = _application_module()
    documents = {
        FeedType.COUNTRY: _fixture_xml(FeedType.COUNTRY),
        FeedType.CITIES: _remove_city(_fixture_xml(FeedType.CITIES)),
    }
    renderer = RecordingRenderer()
    save_calls = []

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.LIVE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            fetch_feed_fn=_fetch_success(documents),
            snapshot_store=SnapshotStore(tmp_path / "archive"),
            save_png_fn=_recording_saver(save_calls),
        )

    assert raised.value.stage is application.RunStage.FORECAST
    assert "unresolved" in str(raised.value)
    assert renderer.contexts == []
    assert save_calls == []


def test_context_failure_maps_to_render_stage(app_settings, tmp_path, monkeypatch):
    application = _application_module()
    monkeypatch.setattr(
        application,
        "build_story_render_context",
        lambda *args: (_ for _ in ()).throw(RenderContextError("bad visual context")),
    )
    renderer = RecordingRenderer()

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.FIXTURE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=renderer,
            save_png_fn=_recording_saver([]),
        )

    assert raised.value.stage is application.RunStage.RENDER
    assert "bad visual context" in str(raised.value)
    assert renderer.contexts == []


def test_renderer_failure_maps_to_render_stage(app_settings, tmp_path):
    application = _application_module()

    class BrokenRenderer:
        def render(self, context):
            raise TemplateRenderError("browser unavailable")

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.FIXTURE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=BrokenRenderer(),
            save_png_fn=_recording_saver([]),
        )

    assert raised.value.stage is application.RunStage.RENDER
    assert "browser unavailable" in str(raised.value)


def test_saver_failure_maps_to_output_stage(app_settings, tmp_path):
    application = _application_module()
    file_saver = importlib.import_module("src.delivery.file_saver")

    def fail_save(*args):
        raise file_saver.OutputSaveError("disk unavailable")

    with pytest.raises(application.ForecastRunError) as raised:
        application.generate_forecast_image(
            _request(application, application.SourceMode.FIXTURE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=NOW,
            renderer=RecordingRenderer(),
            save_png_fn=fail_save,
        )

    assert raised.value.stage is application.RunStage.OUTPUT
    assert "disk unavailable" in str(raised.value)


def test_fallback_count_includes_country_and_each_fallback_city(
    app_settings,
    tmp_path,
):
    application = _application_module()
    store = SnapshotStore(tmp_path / "archive")
    _store_archives(store, FeedType.COUNTRY, FeedType.CITIES)
    documents = {
        FeedType.COUNTRY: _blank_country_hebrew(_fixture_xml(FeedType.COUNTRY)),
        FeedType.CITIES: _mutate_city_maximum(_fixture_xml(FeedType.CITIES), None),
    }

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.LIVE, tmp_path / "output"),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=RecordingRenderer(),
        fetch_feed_fn=_fetch_success(documents),
        snapshot_store=store,
        save_png_fn=_recording_saver([]),
    )

    assert result.used_fallback is True
    assert result.fallback_value_count == 2


def test_naive_application_time_is_rejected_as_a_programmer_error(app_settings, tmp_path):
    application = _application_module()

    with pytest.raises(ValueError, match="timezone-aware"):
        application.generate_forecast_image(
            _request(application, application.SourceMode.FIXTURE, tmp_path),
            paths=PATHS,
            settings=app_settings,
            now=datetime(2025, 12, 17, 10, 0),
            renderer=RecordingRenderer(),
            save_png_fn=_recording_saver([]),
        )


@pytest.mark.browser
def test_fixture_xml_to_atomic_browser_png_vertical_integration(
    app_settings,
    tmp_path,
):
    application = _application_module()
    output_directory = tmp_path / "vertical" / "output"

    result = application.generate_forecast_image(
        _request(application, application.SourceMode.FIXTURE, output_directory),
        paths=PATHS,
        settings=app_settings,
        now=NOW,
        renderer=TemplateRenderer(),
    )

    assert result.output_path == (
        output_directory / "forecast_2025-12-18.png"
    ).resolve()
    with Image.open(result.output_path) as image:
        image.load()
        assert image.format == "PNG"
        assert image.size == (1080, 1920)
    assert result.used_fallback is False
    assert result.fallback_value_count == 0
