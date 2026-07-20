"""Structural contracts for the deterministic Story template renderer."""

from dataclasses import replace
from io import BytesIO
import os
from pathlib import Path

from lxml import html as lxml_html
from PIL import Image
from playwright.sync_api import sync_playwright
import pytest

from src.app_paths import PATHS
from src.design.render_context import build_story_render_context
from src.rendering import template_renderer
from tests.reference_fixture import build_story_reference_forecast


@pytest.fixture
def story_context(app_settings):
    forecast = build_story_reference_forecast(app_settings)
    return build_story_render_context(forecast, app_settings, PATHS)


def _render_html(context) -> str:
    return template_renderer.TemplateRenderer()._render_html(context)


@pytest.fixture(scope="session")
def chromium_browser() -> None:
    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
    if not executable.is_file():
        if os.getenv("CI", "").lower() == "true":
            pytest.fail(f"CI requires Playwright Chromium: {executable}")
        pytest.skip(f"Playwright Chromium is not installed: {executable}")


def _write_browser_template(
    directory: Path,
    *,
    canvas_style: str = "width:1080px;height:1920px",
    body: str = "",
    script: str = "",
) -> None:
    template = f"""<!doctype html>
<html lang="he" dir="rtl">
<head><meta charset="utf-8"><style>
@font-face {{
  font-family: "IMS Story Black";
  src: url("{{{{ context.assets.black_font_uri }}}}");
  font-weight: 900;
  font-display: block;
}}
@font-face {{
  font-family: "IMS Story SemiBold";
  src: url("{{{{ context.assets.semibold_font_uri }}}}");
  font-weight: 600;
  font-display: block;
}}
html, body {{ margin: 0; overflow: hidden; }}
#story-canvas {{ {canvas_style}; font-family: "IMS Story Black"; }}
.semibold-probe {{ font-family: "IMS Story SemiBold"; }}
</style></head>
<body><main id="story-canvas">{body}<span class="semibold-probe">בדיקה</span></main>
{script}</body></html>
"""
    (directory / "browser-test.html").write_text(template, encoding="utf-8")


def _custom_renderer(directory: Path, **kwargs):
    return template_renderer.TemplateRenderer(
        template_directory=directory,
        template_name="browser-test.html",
        **kwargs,
    )


def _measure_rendered_page(tmp_path: Path, story_context) -> dict:
    rendered_html = template_renderer.TemplateRenderer()._render_html(story_context)
    html_path = tmp_path / "measured-story.html"
    html_path.write_text(rendered_html, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--allow-file-access-from-files"],
        )
        try:
            browser_context = browser.new_context(
                viewport={"width": 1080, "height": 1920},
                device_scale_factor=1,
                color_scheme="light",
                reduced_motion="reduce",
            )
            try:
                page = browser_context.new_page()
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.evaluate(
                    """async () => {
                      await document.fonts.ready;
                      await document.fonts.load('900 24px "IMS Story Black"', "אבג");
                      await document.fonts.load('600 24px "IMS Story SemiBold"', "אבג");
                      await Promise.all(Array.from(document.images).map(image => image.decode()));
                    }"""
                )
                return page.evaluate(
                    """() => {
                      const box = selector => {
                        const rect = document.querySelector(selector).getBoundingClientRect();
                        return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
                      };
                      return {
                        canvas: box("#story-canvas"),
                        headerLine: box("#header-line"),
                        headerGregorian: box("#header-gregorian"),
                        headerHebrew: box("#header-hebrew"),
                        headerSeparator: box("#header-separator"),
                        mapTarget: box("#story-map"),
                        mapImage: box("#israel-map"),
                        description: box("#country-description"),
                        mot: box("#mot-logo"),
                        ims: box("#ims-logo"),
                        page: {
                          width: document.documentElement.scrollWidth,
                          height: document.documentElement.scrollHeight,
                          clientWidth: document.documentElement.clientWidth,
                          clientHeight: document.documentElement.clientHeight,
                        },
                        fonts: {
                          black: document.fonts.check('900 24px "IMS Story Black"', "אבג"),
                          semibold: document.fonts.check('600 24px "IMS Story SemiBold"', "אבג"),
                        },
                        images: Array.from(document.images).map(image => ({
                          src: image.currentSrc,
                          naturalWidth: image.naturalWidth,
                          naturalHeight: image.naturalHeight,
                        })),
                        cities: Array.from(document.querySelectorAll("[data-city-key]")).map(city => ({
                          key: city.dataset.cityKey,
                          classes: Array.from(city.classList),
                          box: box(`[data-city-key="${city.dataset.cityKey}"]`),
                          icon: box(`[data-city-key="${city.dataset.cityKey}"] .city-icon`),
                          copy: box(`[data-city-key="${city.dataset.cityKey}"] .city-copy`),
                          name: box(`[data-city-key="${city.dataset.cityKey}"] .city-name`),
                          temperature: box(`[data-city-key="${city.dataset.cityKey}"] .temperature`),
                        })),
                      };
                    }"""
                )
            finally:
                browser_context.close()
        finally:
            browser.close()


def _assert_box(actual: dict, expected: tuple[float, float, float, float]) -> None:
    for key, value in zip(("x", "y", "width", "height"), expected, strict=True):
        assert actual[key] == pytest.approx(value, abs=0.02)


def test_template_uses_strict_undefined_and_reports_template_stage(
    tmp_path: Path, story_context
):
    (tmp_path / "broken.html").write_text(
        "<!doctype html><title>{{ context.field_that_does_not_exist }}</title>",
        encoding="utf-8",
    )
    renderer = template_renderer.TemplateRenderer(
        template_directory=tmp_path,
        template_name="broken.html",
    )

    with pytest.raises(template_renderer.TemplateRenderError, match="^template:"):
        renderer._render_html(story_context)


def test_dynamic_hebrew_is_escaped_and_cannot_create_script(story_context):
    unsafe = '<script>window.storyWasCompromised = true</script>'
    cities = (replace(story_context.cities[0], name_hebrew=unsafe),) + tuple(
        story_context.cities[1:]
    )
    context = replace(
        story_context,
        country_description_hebrew=unsafe,
        cities=cities,
    )

    rendered = _render_html(context)
    document = lxml_html.fromstring(rendered)

    assert document.xpath("//script") == []
    assert unsafe not in rendered
    assert rendered.count("&lt;script&gt;") == 2


def test_template_has_exact_city_keys_positions_layouts_and_bidi(story_context):
    rendered = _render_html(story_context)
    document = lxml_html.fromstring(rendered)
    cities = document.xpath('//*[@data-city-key]')

    assert len(cities) == 15
    assert [item.get("data-city-key") for item in cities] == [
        city.internal_key for city in story_context.cities
    ]
    for element, city in zip(cities, story_context.cities, strict=True):
        classes = set(element.get("class", "").split())
        style = element.get("style", "")
        assert f"layout-{city.layout.value.lower()}" in classes
        assert f"left: {city.x:g}px" in style
        assert f"top: {city.y:g}px" in style
        assert "right:" not in style
        assert "inset-inline" not in style
        temperature = element.xpath('.//bdi[@dir="ltr"]')
        assert len(temperature) == 1
        assert temperature[0].text_content() == city.temperature_text


def test_template_inlines_assets_header_and_fixed_story_structure(story_context):
    rendered = _render_html(story_context)
    document = lxml_html.fromstring(rendered)

    assert document.get("lang") == "he"
    assert document.get("dir") == "rtl"
    assert document.xpath('//link[@rel="stylesheet"]') == []
    assert len(document.xpath('//*[@id="story-canvas"]')) == 1
    assert len(document.xpath('//section[@id="forecast-layer"]')) == 1
    assert len(document.xpath('//*[@id="story-map"]')) == 1
    assert document.xpath('//img[@id="israel-map"]/@src') == [
        story_context.assets.map_uri
    ]
    assert document.xpath('//img[@id="mot-logo"]/@src') == [
        story_context.assets.mot_logo_uri
    ]
    assert document.xpath('//img[@id="ims-logo"]/@src') == [
        story_context.assets.ims_logo_uri
    ]
    assert document.xpath('//p[@id="country-description"]/@dir') == ["rtl"]
    assert document.xpath('//span[@id="header-gregorian"]/@dir') == ["ltr"]
    assert document.xpath('//span[@id="header-hebrew"]/@dir') == ["rtl"]
    assert document.xpath('//*[@id="header-line"]/*/@id') == [
        "header-hebrew",
        "header-gregorian",
    ]
    assert story_context.assets.black_font_uri in rendered
    assert story_context.assets.semibold_font_uri in rendered
    assert "#dcff57 -62.599%" in rendered
    assert "Placeholder" not in rendered
    assert "{{" not in rendered
    assert "{%" not in rendered


def test_default_template_resolution_does_not_depend_on_cwd(
    monkeypatch, tmp_path: Path, story_context
):
    monkeypatch.chdir(tmp_path)

    rendered = _render_html(story_context)

    assert 'id="story-canvas"' in rendered
    assert str(PATHS.root) not in rendered


@pytest.mark.browser
def test_frozen_context_renders_repeatable_png_bytes(story_context, chromium_browser):
    renderer = template_renderer.TemplateRenderer()

    first = renderer.render(story_context)
    second = renderer.render(story_context)

    assert first == second
    with Image.open(BytesIO(first)) as image:
        assert image.format == "PNG"
        assert image.size == (1080, 1920)


@pytest.mark.browser
@pytest.mark.parametrize(
    ("script", "message"),
    [
        ("<script>throw new Error('fixture page boom')</script>", "page.*fixture page boom"),
        ("<script>console.error('fixture console boom')</script>", "console.*fixture console boom"),
    ],
)
def test_page_and_console_errors_are_rejected(
    tmp_path: Path, story_context, chromium_browser, script: str, message: str
):
    _write_browser_template(tmp_path, script=script)

    with pytest.raises(template_renderer.TemplateRenderError, match=message):
        _custom_renderer(tmp_path).render(story_context)


@pytest.mark.browser
def test_failed_local_image_is_rejected(
    tmp_path: Path, story_context, chromium_browser
):
    _write_browser_template(tmp_path, body='<img src="missing-local-image.png" alt="">')

    with pytest.raises(
        template_renderer.TemplateRenderError,
        match="(asset|image readiness).*missing-local-image",
    ):
        _custom_renderer(tmp_path).render(story_context)


@pytest.mark.browser
def test_failed_font_is_rejected(story_context, chromium_browser):
    broken_assets = replace(
        story_context.assets,
        semibold_font_uri="file:///definitely-missing-story-font.ttf",
    )

    with pytest.raises(
        template_renderer.TemplateRenderError,
        match="(asset|font/image readiness).*font",
    ):
        template_renderer.TemplateRenderer().render(
            replace(story_context, assets=broken_assets)
        )


@pytest.mark.browser
def test_wrong_canvas_size_is_rejected(
    tmp_path: Path, story_context, chromium_browser
):
    _write_browser_template(tmp_path, canvas_style="width:1079px;height:1920px")

    with pytest.raises(
        template_renderer.TemplateRenderError,
        match=r"layout validation:.*1079.*1920",
    ):
        _custom_renderer(tmp_path).render(story_context)


@pytest.mark.browser
def test_country_description_that_reaches_branding_is_rejected(
    story_context, chromium_browser
):
    context = replace(
        story_context,
        country_description_hebrew=("תחזית ארוכה במיוחד " * 80).strip(),
    )

    with pytest.raises(
        template_renderer.TemplateRenderError,
        match=r"layout validation: country description.*(overflow|branding)",
    ):
        template_renderer.TemplateRenderer().render(context)


@pytest.mark.browser
def test_browser_launch_failure_identifies_stage(story_context, chromium_browser):
    renderer = template_renderer.TemplateRenderer(
        launch_options={"executable_path": "definitely-missing-chromium"}
    )

    with pytest.raises(
        template_renderer.TemplateRenderError,
        match="^browser launch:",
    ):
        renderer.render(story_context)


@pytest.mark.browser
def test_browser_geometry_assets_fonts_and_physical_city_anchors(
    tmp_path: Path, story_context, chromium_browser
):
    metrics = _measure_rendered_page(tmp_path, story_context)

    _assert_box(metrics["canvas"], (0, 0, 1080, 1920))
    _assert_box(metrics["headerLine"], (100, 57, 880, 90))
    _assert_box(metrics["headerSeparator"], (100, 155, 880, 7))
    header_gap = metrics["headerGregorian"]["x"] - (
        metrics["headerHebrew"]["x"] + metrics["headerHebrew"]["width"]
    )
    assert header_gap == pytest.approx(6)
    _assert_box(metrics["mapTarget"], (258, 288.3, 533.371, 1495.196))
    _assert_box(metrics["mapImage"], (247.2, 277.5, 555, 1517))
    _assert_box(metrics["description"], (740, 1234, 239, 396))
    _assert_box(metrics["mot"], (633, 1709, 199, 150))
    _assert_box(metrics["ims"], (856, 1712.5, 119, 143))
    assert metrics["page"] == {
        "width": 1080,
        "height": 1920,
        "clientWidth": 1080,
        "clientHeight": 1920,
    }
    assert metrics["fonts"] == {"black": True, "semibold": True}
    assert len(metrics["images"]) == 18
    assert all(image["naturalWidth"] > 0 for image in metrics["images"])
    assert all(image["naturalHeight"] > 0 for image in metrics["images"])

    measured = {city["key"]: city for city in metrics["cities"]}
    assert set(measured) == {city.internal_key for city in story_context.cities}
    for city in story_context.cities:
        actual = measured[city.internal_key]
        assert f"layout-{city.layout.value.lower()}" in actual["classes"]
        assert actual["box"]["x"] == pytest.approx(city.x)
        assert actual["box"]["y"] == pytest.approx(city.y)
        assert actual["temperature"]["y"] - actual["name"]["y"] == pytest.approx(31)
        if city.layout.value == "RTL":
            assert actual["icon"]["x"] == pytest.approx(city.x + 10)
            assert actual["copy"]["x"] == pytest.approx(city.x + 76)
            assert actual["copy"]["y"] == pytest.approx(city.y + 15)
        elif city.layout.value == "LTR":
            assert actual["copy"]["y"] == pytest.approx(city.y + 15)
        elif city.layout.value == "TTB":
            assert actual["icon"]["y"] == pytest.approx(city.y + 10)
            assert actual["copy"]["y"] == pytest.approx(city.y + 65)
            assert actual["temperature"]["y"] == pytest.approx(city.y + 96)
