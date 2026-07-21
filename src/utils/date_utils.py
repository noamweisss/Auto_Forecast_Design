"""Date text required by the verified Instagram Story header."""

from datetime import date

from pyluach.dates import HebrewDate  # type: ignore[import-untyped]


def format_hebrew_calendar_date(target_date: date) -> str:
    """Format one explicit civil date as the Hebrew-calendar header field."""
    hebrew_date = HebrewDate.from_pydate(target_date)
    day = hebrew_date.hebrew_day()
    month = hebrew_date.month_name(hebrew=True)
    # Pyluach uses the traditional חסר spelling; the approved IMS/Figma header
    # uses the common modern display spelling with two vavs.
    if month == "חשון":
        month = "חשוון"
    year_without_thousands = hebrew_date.hebrew_year()
    return f"{day} ב{month} ה{year_without_thousands}"
