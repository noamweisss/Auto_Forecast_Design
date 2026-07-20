"""Render one validated Story packing list through Jinja and Chromium."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)
from PIL import Image, UnidentifiedImageError
from playwright.sync_api import (
    Browser,
    BrowserContext,
    ConsoleMessage,
    Error as PlaywrightError,
    Page,
    Request,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from src.design.render_context import StoryRenderContext


class TemplateRenderError(RuntimeError):
    """The checked Story page could not become a canonical PNG."""


class TemplateRenderer:
    """Turn one validated Story context into the fixed HTML design and PNG."""

    def __init__(
        self,
        template_directory: Path | None = None,
        template_name: str = "forecast_story.html",
        *,
        timeout_ms: int = 15_000,
        launch_options: Mapping[str, Any] | None = None,
    ) -> None:
        self.template_directory = (
            Path(template_directory).resolve()
            if template_directory is not None
            else Path(__file__).resolve().parent / "templates"
        )
        self.template_name = template_name
        self.timeout_ms = timeout_ms
        self.launch_options = dict(launch_options or {})
        self._environment = Environment(
            loader=FileSystemLoader(self.template_directory),
            autoescape=select_autoescape(
                enabled_extensions=("html", "xml"),
                default_for_string=True,
            ),
            undefined=StrictUndefined,
        )
        self._environment.filters["css_number"] = _css_number

    def _render_html(self, context: StoryRenderContext) -> str:
        """Render escaped HTML while reporting failures at the template stage."""
        try:
            template = self._environment.get_template(self.template_name)
            return template.render(context=context)
        except (OSError, TemplateError) as error:
            raise TemplateRenderError(f"template: {error}") from error

    def render(self, context: StoryRenderContext) -> bytes:
        """Return one deterministic 1080x1920 PNG as bytes."""
        rendered_html = self._render_html(context)
        try:
            with TemporaryDirectory(prefix="ims-story-") as temporary_directory:
                html_path = Path(temporary_directory) / "forecast-story.html"
                try:
                    html_path.write_text(rendered_html, encoding="utf-8")
                except OSError as error:
                    raise TemplateRenderError(f"temporary HTML: {error}") from error
                png_bytes = self._capture_canvas(html_path)
        except TemplateRenderError:
            raise
        except OSError as error:
            raise TemplateRenderError(f"temporary HTML: {error}") from error

        self._validate_png(png_bytes)
        return png_bytes

    def _capture_canvas(self, html_path: Path) -> bytes:
        playwright = None
        browser: Browser | None = None
        browser_context: BrowserContext | None = None
        page: Page | None = None
        try:
            try:
                playwright = sync_playwright().start()
                options: dict[str, Any] = {
                    "headless": True,
                    "args": ["--allow-file-access-from-files"],
                }
                options.update(self.launch_options)
                browser = playwright.chromium.launch(**options)
            except (OSError, PlaywrightError) as error:
                raise TemplateRenderError(f"browser launch: {error}") from error

            issues: list[str] = []
            try:
                browser.on(
                    "disconnected",
                    lambda _browser: issues.append(
                        "browser disconnected unexpectedly"
                    ),
                )
                browser_context = browser.new_context(
                    viewport={"width": 1080, "height": 1920},
                    device_scale_factor=1,
                    color_scheme="light",
                    reduced_motion="reduce",
                )
                page = browser_context.new_page()
                page.set_default_timeout(self.timeout_ms)
                _register_page_collectors(page, issues)
            except PlaywrightError as error:
                raise TemplateRenderError(f"browser/page/asset error: {error}") from error

            try:
                page.goto(
                    html_path.resolve().as_uri(),
                    wait_until="load",
                    timeout=self.timeout_ms,
                )
            except PlaywrightTimeoutError as error:
                raise TemplateRenderError(f"page load: timed out: {error}") from error
            except PlaywrightError as error:
                raise TemplateRenderError(f"page load: {error}") from error

            self._await_fonts_and_images(page)
            canvas = self._validate_layout(page)
            if issues:
                raise TemplateRenderError(
                    "browser/page/asset error: " + "; ".join(issues)
                )

            try:
                return canvas.screenshot(
                    type="png",
                    animations="disabled",
                    caret="hide",
                    scale="css",
                    timeout=self.timeout_ms,
                )
            except PlaywrightError as error:
                raise TemplateRenderError(f"screenshot: {error}") from error
        finally:
            _close_playwright_object(page)
            _close_playwright_object(browser_context)
            _close_playwright_object(browser)
            if playwright is not None:
                try:
                    playwright.stop()
                except PlaywrightError:
                    pass

    def _await_fonts_and_images(self, page: Page) -> None:
        try:
            result = page.evaluate(
                """async () => {
                  await document.fonts.ready;
                  const specs = [
                    { family: "IMS Story Black", query: '900 24px "IMS Story Black"' },
                    { family: "IMS Story SemiBold", query: '600 24px "IMS Story SemiBold"' },
                  ];
                  const fonts = [];
                  for (const spec of specs) {
                    try {
                      const loaded = await document.fonts.load(spec.query, "אבג 123");
                      fonts.push({
                        family: spec.family,
                        ready: loaded.length > 0 && document.fonts.check(spec.query, "אבג 123"),
                        error: "",
                      });
                    } catch (error) {
                      fonts.push({ family: spec.family, ready: false, error: String(error) });
                    }
                  }
                  const images = await Promise.all(Array.from(document.images).map(async image => {
                    let error = "";
                    try {
                      await image.decode();
                    } catch (decodeError) {
                      error = String(decodeError);
                    }
                    return {
                      src: image.currentSrc || image.src,
                      naturalWidth: image.naturalWidth,
                      naturalHeight: image.naturalHeight,
                      error,
                    };
                  }));
                  return { fonts, images };
                }"""
            )
        except PlaywrightError as error:
            raise TemplateRenderError(f"font/image readiness: {error}") from error

        failures = [
            f"font {item['family']} ({item['error'] or 'not loaded'})"
            for item in result["fonts"]
            if not item["ready"]
        ]
        failures.extend(
            f"image {item['src']} ({item['error'] or 'zero natural size'})"
            for item in result["images"]
            if item["naturalWidth"] <= 0 or item["naturalHeight"] <= 0 or item["error"]
        )
        if failures:
            raise TemplateRenderError("font/image readiness: " + "; ".join(failures))

    def _validate_layout(self, page: Page):
        canvas = page.locator("#story-canvas")
        try:
            count = canvas.count()
            box = canvas.bounding_box() if count == 1 else None
            page_size = page.evaluate(
                """() => ({
                  width: document.documentElement.scrollWidth,
                  height: document.documentElement.scrollHeight,
                  viewportWidth: document.documentElement.clientWidth,
                  viewportHeight: document.documentElement.clientHeight,
                })"""
            )
        except PlaywrightError as error:
            raise TemplateRenderError(f"layout validation: {error}") from error

        if count != 1 or box is None:
            raise TemplateRenderError(
                f"layout validation: expected one #story-canvas, found {count}"
            )
        width = box["width"]
        height = box["height"]
        if (width, height) != (1080, 1920):
            raise TemplateRenderError(
                f"layout validation: #story-canvas is {width:g}x{height:g}, "
                "expected 1080x1920"
            )
        if page_size != {
            "width": 1080,
            "height": 1920,
            "viewportWidth": 1080,
            "viewportHeight": 1920,
        }:
            raise TemplateRenderError(
                f"layout validation: unexpected page scroll geometry {page_size}"
            )
        return canvas

    def _validate_png(self, png_bytes: bytes) -> None:
        try:
            with Image.open(BytesIO(png_bytes)) as image:
                image.load()
                image_format = image.format
                image_size = image.size
        except (OSError, UnidentifiedImageError, ValueError) as error:
            raise TemplateRenderError(f"PNG validation: {error}") from error
        if image_format != "PNG" or image_size != (1080, 1920):
            raise TemplateRenderError(
                f"PNG validation: got {image_format} {image_size}, expected PNG (1080, 1920)"
            )


def _css_number(value: float) -> str:
    """Keep validated Figma coordinates literal and free of trailing `.0`."""
    return format(value, "g")


def _register_page_collectors(page: Page, issues: list[str]) -> None:
    """Collect browser failures before navigation so none are missed."""

    def record_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            issues.append(f"console error: {message.text}")

    def record_failed_request(request: Request) -> None:
        issues.append(
            f"request failed: {request.url} ({request.failure or 'unknown failure'})"
        )

    page.on("pageerror", lambda error: issues.append(f"page error: {error}"))
    page.on("console", record_console)
    page.on("requestfailed", record_failed_request)
    page.on("crash", lambda _page: issues.append("page crashed"))


def _close_playwright_object(value: Any) -> None:
    if value is None:
        return
    try:
        value.close()
    except PlaywrightError:
        pass
