"""Command-line boundary contracts for one local forecast Story run."""

from datetime import date, datetime
import importlib
from pathlib import Path

import pytest

from src.app_paths import AppPaths
from src.clock import ISRAEL_TIMEZONE
from src.delivery.email_sender import (
    EmailConfigError,
    EmailDeliveryError,
    EmailDeliveryResult,
)
from src.settings import ConfigurationError
import src.main as main_module


FIXED_NOW = datetime(2026, 7, 21, 0, 15, tzinfo=ISRAEL_TIMEZONE)


def _application_module():
    return importlib.import_module("src.application")


class RecordingLogger:
    def __init__(self) -> None:
        self.errors = []
        self.exceptions = []

    def error(self, message, *args):
        self.errors.append(message % args if args else message)

    def exception(self, message, *args):
        self.exceptions.append(message % args if args else message)


def _install_success_boundary(monkeypatch, tmp_path, calls, *, fixed_now=FIXED_NOW):
    application = _application_module()
    paths = AppPaths(root=tmp_path)
    settings = object()
    renderer = object()

    class FixedClock:
        def now(self):
            calls.append("clock")
            return fixed_now

    monkeypatch.setattr(
        main_module.AppPaths,
        "from_repository",
        classmethod(lambda cls: calls.append("paths") or paths),
    )
    monkeypatch.setattr(
        main_module,
        "load_dotenv",
        lambda *, dotenv_path, override: calls.append(
            ("dotenv", dotenv_path, override)
        ),
    )
    monkeypatch.setattr(main_module, "SystemClock", lambda: FixedClock())
    monkeypatch.setattr(
        main_module,
        "configure_logging",
        lambda log_dir, now: calls.append(("logging", log_dir, now)),
    )
    monkeypatch.setattr(
        main_module,
        "load_settings",
        lambda received_paths: calls.append(("settings", received_paths)) or settings,
    )
    monkeypatch.setattr(
        main_module,
        "TemplateRenderer",
        lambda: calls.append("renderer") or renderer,
    )

    def generate(request, **kwargs):
        calls.append(("workflow", request, kwargs))
        return application.GenerationResult(
            target_date=request.target_date,
            source_mode=request.source_mode,
            output_path=(
                request.output_directory
                / f"forecast_{request.target_date.isoformat()}.png"
            ).resolve(),
            used_fallback=False,
            fallback_value_count=0,
        )

    monkeypatch.setattr(main_module, "generate_forecast_image", generate)
    return paths, settings, renderer


@pytest.mark.parametrize(
    ("argv", "expected_code"),
    [
        (["--help"], 0),
        (["--date", "20260721"], 2),
        (["--date", "2026-02-30"], 2),
        (["--source", "archive"], 2),
    ],
)
def test_help_and_invalid_usage_are_parsed_before_any_side_effect(
    monkeypatch,
    argv,
    expected_code,
):
    monkeypatch.setattr(
        main_module.AppPaths,
        "from_repository",
        classmethod(lambda cls: pytest.fail("arguments were not parsed first")),
    )

    with pytest.raises(SystemExit) as raised:
        main_module.main(argv)

    assert raised.value.code == expected_code


def test_help_documents_relative_output_resolution_without_old_flags(capsys):
    with pytest.raises(SystemExit) as raised:
        main_module.main(["--help"])

    help_text = capsys.readouterr().out
    assert raised.value.code == 0
    assert "--source" in help_text
    assert "--output-dir" in help_text
    assert "repository root" in help_text
    assert "--no-email" not in help_text
    assert "--layout" not in help_text


def test_live_default_uses_one_israel_run_start_date_and_explicit_boundary_order(
    monkeypatch,
    tmp_path,
):
    application = _application_module()
    calls = []
    paths, settings, renderer = _install_success_boundary(monkeypatch, tmp_path, calls)

    exit_code = main_module.main([])

    assert exit_code == 0
    workflow_call = calls[-1]
    request = workflow_call[1]
    kwargs = workflow_call[2]
    assert request == application.GenerationRequest(
        target_date=date(2026, 7, 21),
        source_mode=application.SourceMode.LIVE,
        output_directory=tmp_path / "output",
    )
    assert kwargs == {
        "paths": paths,
        "settings": settings,
        "now": FIXED_NOW,
        "renderer": renderer,
    }
    assert calls[:-1] == [
        "paths",
        ("dotenv", tmp_path / ".env", False),
        "clock",
        ("logging", tmp_path / "logs", FIXED_NOW),
        ("settings", paths),
        "renderer",
    ]


def test_fixture_default_date_is_fixed_and_independent_of_run_start(
    monkeypatch,
    tmp_path,
):
    application = _application_module()
    calls = []
    _install_success_boundary(
        monkeypatch,
        tmp_path,
        calls,
        fixed_now=datetime(2035, 1, 2, 23, 30, tzinfo=ISRAEL_TIMEZONE),
    )

    assert main_module.main(["--source", "fixture"]) == 0

    request = calls[-1][1]
    assert request.target_date == application.FIXTURE_DEFAULT_DATE == date(2025, 12, 18)
    assert request.source_mode is application.SourceMode.FIXTURE


def test_explicit_strict_date_and_relative_output_are_resolved_from_repository_root(
    monkeypatch,
    tmp_path,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)

    assert main_module.main(
        [
            "--source",
            "live",
            "--date",
            "2026-07-20",
            "--output-dir",
            str(Path("demo") / "stories"),
        ]
    ) == 0

    request = calls[-1][1]
    assert request.target_date == date(2026, 7, 20)
    assert request.output_directory == (tmp_path / "demo" / "stories").resolve()


@pytest.mark.parametrize(
    ("stage_name", "expected_exit"),
    [
        ("SOURCE", 4),
        ("FORECAST", 5),
        ("RENDER", 6),
        ("OUTPUT", 7),
    ],
)
def test_expected_run_errors_map_to_stable_exit_without_traceback(
    monkeypatch,
    tmp_path,
    stage_name,
    expected_exit,
):
    application = _application_module()
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    logger = RecordingLogger()
    monkeypatch.setattr(main_module, "logger", logger, raising=False)

    def fail_run(*args, **kwargs):
        raise application.ForecastRunError(
            application.RunStage[stage_name],
            "expected boundary failure",
        )

    monkeypatch.setattr(main_module, "generate_forecast_image", fail_run)

    assert main_module.main(["--source", "fixture"]) == expected_exit
    assert logger.errors == ["expected boundary failure"]
    assert logger.exceptions == []


def test_configuration_error_maps_to_exit_three_without_traceback(
    monkeypatch,
    tmp_path,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    logger = RecordingLogger()
    monkeypatch.setattr(main_module, "logger", logger, raising=False)
    monkeypatch.setattr(
        main_module,
        "load_settings",
        lambda paths: (_ for _ in ()).throw(ConfigurationError("bad settings")),
    )

    assert main_module.main([]) == 3
    assert logger.errors == ["bad settings"]
    assert logger.exceptions == []


def test_unexpected_programmer_error_maps_to_exit_one_with_traceback_logging(
    monkeypatch,
    tmp_path,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    logger = RecordingLogger()
    monkeypatch.setattr(main_module, "logger", logger, raising=False)
    monkeypatch.setattr(
        main_module,
        "generate_forecast_image",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("programmer defect")),
    )

    assert main_module.main([]) == 1
    assert logger.errors == []
    assert logger.exceptions == ["Unexpected forecast generation error"]


@pytest.mark.parametrize(
    ("source", "expected_source_text"),
    [("live", "live IMS"), ("fixture", "local fixture")],
)
def test_success_text_includes_date_source_fallback_and_absolute_png(
    monkeypatch,
    tmp_path,
    capsys,
    source,
    expected_source_text,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)

    assert main_module.main(["--source", source]) == 0

    output = capsys.readouterr().out
    assert "Forecast image created." in output
    expected_date = "2026-07-21" if source == "live" else "2025-12-18"
    assert f"Date: {expected_date}" in output
    assert f"Data source requested: {expected_source_text}" in output
    assert "Exact-date archived values used: no" in output
    assert f"PNG: {tmp_path.resolve()}" in output
    assert "Emailed to:" not in output


def _install_email_boundary(monkeypatch, calls, *, settings_error=None, send_error=None):
    email_settings = object()

    def load_email_settings():
        calls.append("email-settings")
        if settings_error is not None:
            raise settings_error
        return email_settings

    def send(image_path, *, settings, target_date):
        calls.append(("email-send", image_path, settings, target_date))
        if send_error is not None:
            raise send_error
        return EmailDeliveryResult(
            recipients=("weissno@ims.gov.il",),
            subject="תחזית יומית",
            attachment_name=image_path.name,
            attachment_bytes=1234,
        )

    monkeypatch.setattr(main_module, "load_email_settings", load_email_settings)
    monkeypatch.setattr(main_module, "send_forecast_email", send)
    return email_settings


def test_email_flag_is_absent_by_default_and_skips_all_delivery(monkeypatch, tmp_path):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    _install_email_boundary(monkeypatch, calls)

    assert main_module.main(["--source", "fixture"]) == 0
    assert not [call for call in calls if str(call).startswith("('email")]
    assert "email-settings" not in calls


def test_email_configuration_is_validated_before_any_generation(monkeypatch, tmp_path):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    _install_email_boundary(
        monkeypatch,
        calls,
        settings_error=EmailConfigError("EMAIL_PASSWORD must be set to a nonempty value"),
    )
    logger = RecordingLogger()
    monkeypatch.setattr(main_module, "logger", logger, raising=False)

    assert main_module.main(["--source", "fixture", "--email"]) == 3
    assert logger.errors == ["EMAIL_PASSWORD must be set to a nonempty value"]
    assert "email-settings" in calls
    assert not any(
        isinstance(call, tuple) and call[0] == "workflow" for call in calls
    )


def test_successful_email_run_reports_the_png_and_the_recipients(
    monkeypatch,
    tmp_path,
    capsys,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    email_settings = _install_email_boundary(monkeypatch, calls)

    assert main_module.main(["--source", "fixture", "--email"]) == 0

    send_call = calls[-1]
    assert send_call[0] == "email-send"
    assert send_call[1].name == "forecast_2025-12-18.png"
    assert send_call[2] is email_settings
    assert send_call[3] == date(2025, 12, 18)

    output = capsys.readouterr().out
    assert "PNG: " in output
    assert "Emailed to: weissno@ims.gov.il" in output


def test_delivery_failure_still_reports_the_saved_png_and_exits_eight(
    monkeypatch,
    tmp_path,
    capsys,
):
    calls = []
    _install_success_boundary(monkeypatch, tmp_path, calls)
    _install_email_boundary(
        monkeypatch,
        calls,
        send_error=EmailDeliveryError("SMTP delivery to smtp.gmail.com failed"),
    )
    logger = RecordingLogger()
    monkeypatch.setattr(main_module, "logger", logger, raising=False)

    assert main_module.main(["--source", "fixture", "--email"]) == 8

    output = capsys.readouterr().out
    assert "Forecast image created." in output
    assert "PNG: " in output
    assert "Emailed to:" not in output
    assert logger.errors == ["SMTP delivery to smtp.gmail.com failed"]
    assert logger.exceptions == []
