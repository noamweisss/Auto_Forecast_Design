"""Offline contracts for the frozen Figma Story reference package."""

import hashlib
import json
from pathlib import Path

from PIL import Image

from src.app_paths import PATHS
from src.design.render_context import build_story_render_context
from tests.reference_fixture import (
    build_story_reference_forecast,
    load_story_reference_document,
)


REFERENCE_DIR = PATHS.root / "docs" / "design-reference"
REFERENCE_PNG = REFERENCE_DIR / "forecast-story-node-1-2.png"
REFERENCE_METADATA = REFERENCE_DIR / "forecast-story-node-1-2.metadata.json"
REFERENCE_README = REFERENCE_DIR / "README.md"
CI_WORKFLOW = PATHS.root / ".github" / "workflows" / "ci.yml"
CLOUD_SETUP = PATHS.root / "scripts" / "setup_codex_cloud.sh"
REFERENCE_FIXTURE = (
    PATHS.root / "tests" / "fixtures" / "render" / "forecast_story_reference.json"
)

EXPECTED_PNG_BYTES = 1_227_358
EXPECTED_PNG_SHA256 = (
    "2b9f19776daf5310dca821aa45b0fcb83308ffa2a33a1bd83709d45ae4a5762e"
)
EXPECTED_COUNTRY_HEBREW = (
    'היום: מעונן חלקית עד מעונן בעננות בגובה רב. תחול עלייה בטמפרטורות והן '
    'יחזרו להיות רגילות לעונה. בשעות הבוקר ינשבו רוחות מזרחיות ערות בהרי '
    'הצפון. הלילה: בהיר בד"כ. ינשבו רוחות מזרחיות חזקות בהרי הצפון והמרכז.'
)
EXPECTED_ASSET_PATHS = {
    "map": "assets/Map/Israel Map 01.svg",
    "mot_logo": "assets/Logos/mot_logo.svg",
    "ims_logo": "assets/Logos/ims_logo.svg",
    "black_font": "assets/Fonts/NotoSansHebrew-Black.ttf",
    "semibold_font": "assets/Fonts/NotoSansHebrew-SemiBold.ttf",
    "weather_icon": "assets/Weather_Icons/partly_cloudy_rain.png",
}


def _metadata() -> dict:
    return json.loads(REFERENCE_METADATA.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_lfs_pointer(path: Path) -> bool:
    return path.read_bytes()[:200].startswith(
        b"version https://git-lfs.github.com/spec/v1"
    )


def test_reference_png_is_exact_hydrated_export_and_runners_hydrate_lfs():
    assert REFERENCE_PNG.is_file()
    assert not _is_lfs_pointer(REFERENCE_PNG)
    assert REFERENCE_PNG.stat().st_size == EXPECTED_PNG_BYTES
    assert _sha256(REFERENCE_PNG) == EXPECTED_PNG_SHA256

    with Image.open(REFERENCE_PNG) as image:
        assert image.format == "PNG"
        assert image.size == (1080, 1920)

    ci_text = CI_WORKFLOW.read_text(encoding="utf-8")
    assert "      - uses: actions/checkout@v4\n        with:\n          lfs: true" in ci_text
    assert "git lfs fsck" in ci_text
    assert ci_text.index("git lfs fsck") < ci_text.index("python -m pytest tests")

    setup_text = CLOUD_SETUP.read_text(encoding="utf-8")
    assert "command -v git-lfs" in setup_text
    assert "Git LFS is required" in setup_text
    assert "git lfs install --local" in setup_text
    assert "git lfs pull" in setup_text
    assert "git lfs fsck" in setup_text
    assert setup_text.index("git lfs fsck") < setup_text.index(
        '"${forecast_python}" -m pip'
    )


def test_pull_requests_run_unskippable_browser_render_smoke_job():
    ci_text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "  render-smoke:" in ci_text
    assert "if: github.event_name == 'pull_request'" in ci_text
    assert "python -m playwright install --with-deps chromium" in ci_text
    assert "python -m pytest tests/test_template_renderer.py" in ci_text
    assert "-m browser" in ci_text
    assert 'CI: "true"' in ci_text
    assert "continue-on-error" not in ci_text


def test_metadata_identifies_exact_figma_source_export_and_fixture():
    metadata = _metadata()

    assert metadata["schema_version"] == 1
    assert metadata["figma"] == {
        "file_key": "YVPUc24KCJIFrHpoXKrHz7",
        "node_id": "1:2",
        "node_name": "Instagram Story 01",
        "source_url": (
            "https://www.figma.com/design/YVPUc24KCJIFrHpoXKrHz7/"
            "Story-Layout-V2.0?node-id=1-2"
        ),
    }
    assert metadata["export"]["path"] == (
        "docs/design-reference/forecast-story-node-1-2.png"
    )
    assert metadata["export"]["exported_on"] == "2026-07-20"
    assert metadata["export"]["reviewed_on"] == "2026-07-20"
    assert metadata["export"]["width"] == 1080
    assert metadata["export"]["height"] == 1920
    assert metadata["export"]["byte_size"] == EXPECTED_PNG_BYTES
    assert metadata["export"]["sha256"] == EXPECTED_PNG_SHA256
    assert metadata["matching_fixture"] == (
        "tests/fixtures/render/forecast_story_reference.json"
    )
    assert metadata["visual_policy"]["version"]
    assert "HTML/CSS" in metadata["visual_policy"]["note"]


def test_every_recorded_asset_is_hydrated_and_matches_its_hash():
    assets = _metadata()["assets"]

    assert {key: value["path"] for key, value in assets.items()} == EXPECTED_ASSET_PATHS
    for asset in assets.values():
        path = PATHS.root / asset["path"]
        assert path.is_file()
        assert not _is_lfs_pointer(path)
        assert _sha256(path) == asset["sha256"]


def test_fixture_is_sanitized_and_matches_all_visible_mock_values(app_settings):
    fixture = load_story_reference_document()
    expected_cities = list(app_settings.cities.values())

    assert fixture["schema_version"] == 1
    assert fixture["_meta"]["kind"] == "sanitized_design_reference"
    assert fixture["_meta"]["is_real_ims_forecast"] is False
    assert fixture["target_date"] == "2025-11-17"
    assert fixture["expected_header"] == {
        "gregorian_numeric": "17/11/2025",
        "hebrew_calendar": "כ״ו בחשוון התשפ״ו",
    }
    assert fixture["country"]["description_hebrew"] == EXPECTED_COUNTRY_HEBREW
    assert fixture["provenance"]["source"] == "fixture"
    assert "live" not in json.dumps(fixture, ensure_ascii=False).lower()

    assert [city["city_id"] for city in fixture["cities"]] == [
        city.id for city in expected_cities
    ]
    assert [city["internal_key"] for city in fixture["cities"]] == [
        city.internal_key for city in expected_cities
    ]
    assert len({city["city_id"] for city in fixture["cities"]}) == 15
    for item, configured in zip(fixture["cities"], expected_cities, strict=True):
        assert item["name_hebrew"] == configured.name_hebrew
        assert item["name_english"] == configured.name_english
        assert item["min_temp"] == 19
        assert item["max_temp"] == 27
        assert item["weather_code"] == "1530"


def test_tel_aviv_display_name_matches_frozen_reference(app_settings):
    fixture = load_story_reference_document()
    tel_aviv = next(city for city in fixture["cities"] if city["city_id"] == "402")

    assert tel_aviv["name_hebrew"] == "תל אביב"
    assert app_settings.cities["402"].name_hebrew == "תל אביב"
    assert tel_aviv["internal_key"] == "tel_aviv"
    assert tel_aviv["name_english"] == "Tel Aviv - Yafo"


def test_fixture_builds_real_forecast_and_exact_render_context(app_settings):
    fixture = load_story_reference_document()
    forecast = build_story_reference_forecast(app_settings)
    context = build_story_render_context(forecast, app_settings, PATHS)

    assert forecast.forecast_date.isoformat() == fixture["target_date"]
    assert forecast.is_fallback is False
    assert context.canvas_width == 1080
    assert context.canvas_height == 1920
    assert context.header_gregorian_numeric == "17/11/2025"
    assert context.header_hebrew_calendar == "כ״ו בחשוון התשפ״ו"
    assert context.country_description_hebrew == EXPECTED_COUNTRY_HEBREW
    assert len(context.cities) == 15
    for city in context.cities:
        configured = app_settings.cities[city.city_id]
        position = app_settings.design_tokens["city_positions"][city.internal_key]
        assert city.name_hebrew == configured.name_hebrew
        assert city.temperature_text == "19° - 27°"
        assert city.weather_code == "1530"
        assert city.icon_uri.endswith("partly_cloudy_rain.png")
        assert (city.x, city.y, city.layout.value) == (
            float(position["x"]),
            float(position["y"]),
            position["layout"],
        )


def test_readme_explains_offline_visual_policy_and_refresh_process():
    text = REFERENCE_README.read_text(encoding="utf-8").lower()
    normalized_text = " ".join(text.split())

    assert "html/css" in text
    assert "without figma" in text
    assert "normal size" in text
    assert "no differences" in text
    assert "another forecast" in text
    assert "1x" in text
    assert "recompute" in text
    assert "tests" in text
    assert "pull request" in text
    assert "תל אביב" in text
    assert "tel aviv - yafo" in text
    assert "`402`" in text
    assert "`tel_aviv`" in text
    assert "does not alter ims source forecast data" in normalized_text
