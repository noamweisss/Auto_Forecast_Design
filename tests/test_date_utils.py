"""Exact Hebrew-calendar formatting for the verified Story header."""

from datetime import date

from src.utils.date_utils import format_hebrew_calendar_date


def test_known_figma_header_date_uses_pyluach_hebrew_text():
    result = format_hebrew_calendar_date(date(2025, 11, 17))

    assert result == "כ״ו בחשוון התשפ״ו"
    assert "placeholder" not in result.lower()
    assert "[" not in result


def test_hebrew_leap_year_uses_adar_two_name():
    assert format_hebrew_calendar_date(date(2024, 3, 20)) == "י׳ באדר ב׳ התשפ״ד"
