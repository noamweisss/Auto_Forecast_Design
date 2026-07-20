"""The placeholder main establishes explicit boundaries in a readable order."""

from datetime import datetime

from src.app_paths import AppPaths
from src.clock import ISRAEL_TIMEZONE
import src.main as main_module


def test_main_sets_up_paths_env_clock_logging_and_settings_in_order(monkeypatch, tmp_path):
    calls = []
    paths = AppPaths(root=tmp_path)
    fixed_now = datetime(2026, 7, 20, 9, 30, tzinfo=ISRAEL_TIMEZONE)

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
        lambda received_paths: calls.append(("settings", received_paths)) or object(),
    )

    main_module.main()

    assert calls == [
        "paths",
        ("dotenv", tmp_path / ".env", False),
        "clock",
        ("logging", tmp_path / "logs", fixed_now),
        ("settings", paths),
    ]
