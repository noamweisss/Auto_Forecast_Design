"""Create ignored visual aids for normal-size Story comparison.

Run with ``python -m tests.story_visual`` from any working directory.
"""

from io import BytesIO
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat

from src.app_paths import PATHS
from src.design.render_context import build_story_render_context
from src.rendering import TemplateRenderer
from src.settings import load_settings
from tests.reference_fixture import build_story_reference_forecast


VISUAL_OUTPUT = PATHS.root / "test-results" / "story-visual"
REFERENCE_PNG = (
    PATHS.root / "docs" / "design-reference" / "forecast-story-node-1-2.png"
)


def create_visual_diagnostics(
    reference_path: Path,
    rendered_png: bytes,
    output_directory: Path,
) -> dict[str, Any]:
    """Write one render, overlay, amplified difference, and JSON diagnostics."""
    with Image.open(reference_path) as reference_source:
        reference = reference_source.convert("RGB")
    with Image.open(BytesIO(rendered_png)) as rendered_source:
        rendered = rendered_source.convert("RGB")

    if reference.size != rendered.size:
        raise ValueError(
            "Visual diagnostics require equal dimensions; "
            f"reference={reference.size}, rendered={rendered.size}"
        )

    difference = ImageChops.difference(reference, rendered)
    changed_bbox = difference.getbbox()
    mean_channels = [round(value, 6) for value in ImageStat.Stat(difference).mean]
    metrics: dict[str, Any] = {
        "dimensions": list(reference.size),
        "changed_pixel_bbox": (
            list(changed_bbox) if changed_bbox is not None else None
        ),
        "mean_absolute_channel_difference": mean_channels,
        "mean_absolute_color_difference": round(sum(mean_channels) / 3, 6),
        "changed_pixel_count": _changed_pixel_count(difference),
    }

    output_directory.mkdir(parents=True, exist_ok=True)
    (output_directory / "rendered.png").write_bytes(rendered_png)
    Image.blend(reference, rendered, 0.5).save(output_directory / "overlay.png")
    difference.point(lambda value: min(255, value * 4)).save(
        output_directory / "difference-amplified.png"
    )
    (output_directory / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metrics


def _changed_pixel_count(difference: Image.Image) -> int:
    red, green, blue = difference.split()
    changed_mask = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return sum(changed_mask.histogram()[1:])


def generate_frozen_story_diagnostics() -> dict[str, Any]:
    """Render the sanitized frozen fixture and compare it with the Figma PNG."""
    settings = load_settings(PATHS)
    forecast = build_story_reference_forecast(settings)
    context = build_story_render_context(forecast, settings, PATHS)
    rendered_png = TemplateRenderer().render(context)
    return create_visual_diagnostics(REFERENCE_PNG, rendered_png, VISUAL_OUTPUT)


if __name__ == "__main__":
    print(json.dumps(generate_frozen_story_diagnostics(), indent=2))
